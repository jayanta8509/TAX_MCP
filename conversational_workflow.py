"""
Conversational Workflow Handler
Manages the 3-agent workflow through a single chat-like interface
"""

import asyncio
import re
from typing import Dict, Any, Optional
from datetime import datetime

from agent1_question_master import QuestionMaster
from agent2_wrapper import AnswerProvider
from client import get_workflow_state, update_workflow_state, get_conversation_memory, store_conversation_memory


class ConversationalWorkflowHandler:
    """
    Handles conversational workflow - single endpoint interface
    User just chats naturally, system manages workflow internally
    """
    
    def __init__(self):
        self.qm = QuestionMaster()
        self.ap = None
    
    def _extract_value_from_message(self, message: str, data_type: str, field_name: str) -> str:
        """
        Extract the actual value from natural language messages
        
        Examples:
        - "No, it's 1990-05-16" → "1990-05-16"
        - "No my name is Alex" → "Alex"
        - "It's Jane Smith" → "Jane Smith"
        - "The correct name is John Doe" → "John Doe"
        - "1990-05-16" → "1990-05-16"
        """
        message = message.strip()
        
        # For date fields, extract date pattern first
        if data_type == 'date':
            date_pattern = r'\d{4}-\d{2}-\d{2}'
            match = re.search(date_pattern, message)
            if match:
                return match.group(0)
        
        # For ITIN, extract ITIN pattern
        if field_name == 'itin_number':
            itin_pattern = r'9\d{2}-\d{2}-\d{4}'
            match = re.search(itin_pattern, message)
            if match:
                return match.group(0)
        
        # Common prefixes to remove (expanded to handle rejections)
        prefixes_to_remove = [
            r"^no,?\s*it'?s\s+",
            r"^no,?\s*my\s+\w+\s+is\s+",
            r"^no,?\s*the\s+correct\s+(?:value|name|answer)\s+is\s+",
            r"^no,?\s*",  # Remove leading "no" with optional comma and spaces
            r"^it'?s\s+",
            r"^the\s+correct\s+(?:value|name|answer)\s+is\s+",
            r"^my\s+\w+\s+is\s+",
            r"^(?:actually|correct)\s+",
            r"^change\s+(?:it\s+)?to\s+",
            r"^update\s+(?:it\s+)?to\s+",
        ]
        
        cleaned = message
        for prefix_pattern in prefixes_to_remove:
            cleaned = re.sub(prefix_pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove trailing punctuation
        cleaned = re.sub(r'[.,;!?]+$', '', cleaned.strip())
        
        return cleaned
    
    async def initialize(self):
        """Initialize async components"""
        if not self.ap:
            self.ap = AnswerProvider()
            await self.ap.initialize()
    
    async def process_message(
        self,
        user_id: str,
        client_id: int,
        reference: str,
        user_message: str
    ) -> str:
        """
        Process user's message and return next question or confirmation
        
        Workflow:
        1. Check if user is in an active workflow
        2. If not, start workflow and ask first question
        3. If yes, process their answer (yes/no/correction)
        4. Update database if needed
        5. Return next question
        
        Returns natural language response
        """
        await self.initialize()
        
        # Get workflow state
        workflow_state = get_workflow_state(user_id)
        current_q_id = workflow_state.get('current_question_id')
        previous_answers = workflow_state.get('answers', {})
        
        # Get or create session in Redis
        memory_data = get_conversation_memory(user_id)
        if not memory_data.get('client_id'):
            # Store client info in session
            store_conversation_memory(
                user_id=user_id,
                messages=[],
                client_id=client_id,
                reference=reference
            )
        
        # Determine if starting new workflow or continuing
        if not current_q_id:
            # Starting new workflow
            return await self._start_workflow(user_id, client_id, reference, previous_answers)
        else:
            # Process user's answer to current question
            return await self._process_answer(
                user_id=user_id,
                client_id=client_id,
                reference=reference,
                user_message=user_message,
                current_q_id=current_q_id,
                previous_answers=previous_answers
            )
    
    async def _start_workflow(
        self,
        user_id: str,
        client_id: int,
        reference: str,
        previous_answers: Dict
    ) -> str:
        """Start workflow and return first question"""
        
        # Get first question
        first_question = self.qm.get_next_question(None, previous_answers)
        
        if not first_question:
            return "It looks like your 1040NR filing is already complete! All questions have been answered."
        
        # Get current answer from database
        answer_result = await self.ap.get_answer(
            question_metadata=first_question,
            user_id=user_id,
            client_id=client_id,
            reference=reference
        )
        
        # Update workflow state
        update_workflow_state(
            user_id=user_id,
            question_id=first_question['question_id']
        )
        
        # Format response
        if answer_result.get('exists') and answer_result.get('answer'):
            response = (
                f"Hi! Let's start your 1040NR filing. **{first_question['question_text']}**\n\n"
                f"I found your {first_question['field_name'].replace('_', ' ')} as: **{answer_result['answer']}**\n\n"
                f"Is this correct? Please reply with 'Yes' to confirm or provide the correct value."
            )
        else:
            response = (
                f"Hi! Let's start your 1040NR filing. **{first_question['question_text']}**\n\n"
                f"I don't have this information on file. Please provide your {first_question['field_name'].replace('_', ' ')}."
            )
        
        return response
    
    async def _process_answer(
        self,
        user_id: str,
        client_id: int,
        reference: str,
        user_message: str,
        current_q_id: str,
        previous_answers: Dict
    ) -> str:
        """Process user's answer and return next question"""
        
        # Get current question metadata
        current_question = self.qm.get_question_by_id(current_q_id)
        
        if not current_question:
            return "Sorry, I encountered an error. Please start over."
        
        # Determine if user confirmed or provided new value
        user_message_lower = user_message.lower().strip()
        
        # Enhanced confirmation detection - recognize natural confirmations
        confirmation_phrases = [
            'yes', 'y', 'correct', 'ok', 'okay', 'yeah', 'yep', 'yup', 'sure', 
            'that\'s right', 'that is right', 'right', 'exactly', 'absolutely',
            'yes that\'s correct', 'yes that is correct', 'yes correct',
            'yes that\'s my', 'yes that is my', 'that\'s my', 'that is my',
            'that\'s correct', 'that is correct', 'looks good', 'confirm',
            'affirmative', 'indeed', 'si', 'oui'
        ]
        
        rejection_phrases = [
            'no', 'n', 'incorrect', 'wrong', 'nope', 'nah',
            'that\'s not', 'that is not', 'not correct', 'not right'
        ]
        
        # Check if message is a confirmation
        is_confirmation = any(user_message_lower == phrase or user_message_lower.startswith(phrase + ' ') 
                             for phrase in confirmation_phrases)
        
        # Check if message is a rejection
        is_rejection = any(user_message_lower == phrase or user_message_lower.startswith(phrase + ' ')
                          for phrase in rejection_phrases)
        
        if is_confirmation:
            # User confirmed - get existing answer and move to next
            answer_result = await self.ap.get_answer(
                question_metadata=current_question,
                user_id=user_id,
                client_id=client_id,
                reference=reference
            )
            
            final_value = answer_result.get('answer')
            update_message = "Great! "
            
        elif is_rejection:
            # User said no - check if they also provided the value in same message
            # Examples: "no my name is Alex", "no, it's 1990-05-16"
            
            # Try to extract value from the rejection message
            extracted_value = self._extract_value_from_message(
                user_message,
                current_question.get('data_type'),
                current_question.get('field_name')
            )
            
            # Check if we got a meaningful value (not just "no" or empty)
            if extracted_value and extracted_value.lower() not in ['no', 'n', 'incorrect', 'wrong', 'nope', 'nah']:
                # User provided value in same message - validate and update
                validation = self.qm.validate_answer(current_q_id, extracted_value)
                
                if not validation['valid']:
                    return f"❌ {validation['error_message']} Please try again."
                
                # Update database
                update_result = await self.ap.update_answer(
                    question_metadata=current_question,
                    new_value=extracted_value,
                    user_id=user_id,
                    client_id=client_id,
                    reference=reference
                )
                
                if not update_result['success']:
                    return f"Sorry, I couldn't update the database. Error: {update_result.get('message')}"
                
                final_value = extracted_value
                update_message = f"Updated! Your {current_question['field_name'].replace('_', ' ')} is now **{extracted_value}**.\n\n"
            else:
                # User only said no, ask for correct value
                return (
                    f"I understand the current value is incorrect. "
                    f"Please provide the correct {current_question['field_name'].replace('_', ' ')}."
                )
        
        else:
            # User provided a value (either correction or initial answer)
            # Extract the actual value from natural language
            new_value = self._extract_value_from_message(
                user_message, 
                current_question.get('data_type'),
                current_question.get('field_name')
            )
            
            # Validate the new value
            validation = self.qm.validate_answer(current_q_id, new_value)
            
            if not validation['valid']:
                return f"❌ {validation['error_message']} Please try again."
            
            # Update database
            update_result = await self.ap.update_answer(
                question_metadata=current_question,
                new_value=new_value,
                user_id=user_id,
                client_id=client_id,
                reference=reference
            )
            
            if not update_result['success']:
                return f"Sorry, I couldn't update the database. Error: {update_result.get('message')}"
            
            final_value = new_value
            update_message = f"Updated! Your {current_question['field_name'].replace('_', ' ')} is now **{new_value}**.\n\n"
        
        # Save answer to workflow state
        previous_answers[current_q_id] = {
            "value": final_value,
            "confirmed": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Get next question
        next_question = self.qm.get_next_question(current_q_id, previous_answers)
        
        if not next_question:
            # Workflow complete
            update_workflow_state(
                user_id=user_id,
                question_id=None,
                completed_task=current_question.get('task_id')
            )
            
            total_answered = len(previous_answers)
            return (
                f"{update_message}"
                f"🎉 **Congratulations!** You've completed all {total_answered} questions for your 1040NR filing!\n\n"
                f"Your information has been saved. We'll proceed with generating your tax return."
            )
        
        # Get answer for next question
        next_answer = await self.ap.get_answer(
            question_metadata=next_question,
            user_id=user_id,
            client_id=client_id,
            reference=reference
        )
        
        # Get progress
        progress = self.qm.get_progress_info(next_question['question_id'])
        
        # Update workflow state
        update_workflow_state(
            user_id=user_id,
            question_id=next_question['question_id'],
            completed_subtask=current_question.get('subtask_id')
        )
        
        # Format next question response
        if next_answer.get('exists') and next_answer.get('answer'):
            response = (
                f"{update_message}"
                f"**{next_question['question_text']}**\n\n"
                f"I have your {next_question['field_name'].replace('_', ' ')} as: **{next_answer['answer']}**\n\n"
                f"Is this correct? Reply 'Yes' to confirm or provide the correct value."
            )
        else:
            response = (
                f"{update_message}"
                f"**{next_question['question_text']}**\n\n"
                f"I don't have this information on file. Please provide your {next_question['field_name'].replace('_', ' ')}."
            )
        
        return response


# Global handler instance
_workflow_handler = None

async def get_workflow_handler() -> ConversationalWorkflowHandler:
    """Get or create global workflow handler"""
    global _workflow_handler
    if _workflow_handler is None:
        _workflow_handler = ConversationalWorkflowHandler()
        await _workflow_handler.initialize()
    return _workflow_handler
