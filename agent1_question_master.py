"""
Agent 1: Question Master
Responsible for determining which question to ask next based on workflow state
"""

import json
from typing import Dict, Optional, List, Any
from pathlib import Path


class QuestionMaster:
    def __init__(self, workflow_file: str = "workflow_questions.json"):
        """Initialize Question Master with workflow definition"""
        self.workflow_file = workflow_file
        self.workflow_data = self._load_workflow()
        
    def _load_workflow(self) -> Dict:
        """Load workflow questions from JSON file"""
        try:
            with open(self.workflow_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Workflow file not found: {self.workflow_file}")
    
    def get_question_by_id(self, question_id: str) -> Optional[Dict]:
        """Get a specific question by its ID (e.g., '1.1', '2.3')"""
        for task in self.workflow_data['tasks']:
            for subtask in task['subtasks']:
                for question in subtask['questions']:
                    if question['question_id'] == question_id:
                        return {
                            **question,
                            'task_id': task['task_id'],
                            'task_name': task['task_name'],
                            'subtask_id': subtask['subtask_id'],
                            'subtask_name': subtask['subtask_name']
                        }
        return None
    
    def get_next_question(
        self, 
        current_question_id: Optional[str] = None,
        previous_answers: Dict[str, Any] = None
    ) -> Optional[Dict]:
        """
        Determine the next question to ask based on:
        1. Current position in workflow
        2. Previous answers (for conditional logic)
        
        Returns:
            Question metadata dict or None if workflow complete
        """
        previous_answers = previous_answers or {}
        
        # If no current question, start from beginning
        if not current_question_id:
            return self.get_question_by_id("1.1")
        
        # Parse current question ID (e.g., "1.1" -> task=1, section=1)
        current_question = self.get_question_by_id(current_question_id)
        if not current_question:
            return None
        
        # Find all questions in order
        all_questions = self._get_all_questions_in_order()
        current_index = next(
            (i for i, q in enumerate(all_questions) if q['question_id'] == current_question_id),
            None
        )
        
        if current_index is None or current_index >= len(all_questions) - 1:
            return None  # Workflow complete
        
        # Get next question(s) and check conditions
        for i in range(current_index + 1, len(all_questions)):
            next_question = all_questions[i]
            
            # Check if question should be skipped based on conditions
            if self._should_ask_question(next_question, previous_answers):
                return next_question
        
        return None  # No more questions
    
    def _get_all_questions_in_order(self) -> List[Dict]:
        """Get all questions in sequential order"""
        all_questions = []
        for task in self.workflow_data['tasks']:
            for subtask in task['subtasks']:
                for question in subtask['questions']:
                    all_questions.append({
                        **question,
                        'task_id': task['task_id'],
                        'task_name': task['task_name'],
                        'subtask_id': subtask['subtask_id'],
                        'subtask_name': subtask['subtask_name']
                    })
        return all_questions
    
    def _should_ask_question(self, question: Dict, previous_answers: Dict[str, Any]) -> bool:
        """
        Determine if a question should be asked based on conditions
        
        Conditions can be:
        - "answer_2.1_is_yes": Only ask if answer to 2.1 was "yes"
        - "no_valid_itin": Only ask if ITIN is invalid or missing
        - "previous_year_exists": Only ask if previous year data exists
        """
        condition = question.get('condition')
        
        if not condition:
            return True  # No condition, always ask
        
        # Handle different condition types
        if condition.startswith('answer_') and '_is_yes' in condition:
            # Extract question ID (e.g., "answer_2.1_is_yes" -> "2.1")
            ref_question_id = condition.replace('answer_', '').replace('_is_yes', '')
            ref_answer = previous_answers.get(ref_question_id, {}).get('value')
            return ref_answer in ['yes', True, 'YES', 'Yes']
        
        elif condition.startswith('answer_') and '_is_no' in condition:
            ref_question_id = condition.replace('answer_', '').replace('_is_no', '')
            ref_answer = previous_answers.get(ref_question_id, {}).get('value')
            return ref_answer in ['no', False, 'NO', 'No']
        
        elif condition == 'no_valid_itin':
            # Check if ITIN is missing or invalid
            has_itin = previous_answers.get('2.1', {}).get('value')
            itin_valid = previous_answers.get('2.3', {}).get('value')
            return not has_itin or not itin_valid
        
        elif condition == 'has_itin':
            has_itin = previous_answers.get('2.1', {}).get('value')
            return has_itin in ['yes', True, 'YES', 'Yes']
        
        elif condition == 'previous_year_exists':
            # This should be checked against database
            return previous_answers.get('has_previous_year_data', False)
        
        elif condition.startswith('previous_year_had_'):
            # Check if previous year had specific form
            form_type = condition.replace('previous_year_had_', '')
            return previous_answers.get(f'prev_year_{form_type}', False)
        
        # Default: ask the question
        return True
    
    def get_progress_info(self, current_question_id: str) -> Dict:
        """Get progress information (for UI display)"""
        all_questions = self._get_all_questions_in_order()
        current_index = next(
            (i for i, q in enumerate(all_questions) if q['question_id'] == current_question_id),
            0
        )
        
        return {
            'current_position': current_index + 1,
            'total_questions': len(all_questions),
            'percentage': round((current_index + 1) / len(all_questions) * 100, 1)
        }
    
    def validate_answer(self, question_id: str, answer: Any) -> Dict[str, Any]:
        """
        Validate an answer based on question validation rules
        
        Returns:
            {
                "valid": bool,
                "error_message": str (if invalid)
            }
        """
        question = self.get_question_by_id(question_id)
        if not question:
            return {"valid": False, "error_message": "Invalid question ID"}
        
        validation = question.get('validation')
        data_type = question.get('data_type')
        
        # Check required fields
        if question.get('required') and not answer:
            return {"valid": False, "error_message": "This field is required"}
        
        # Type validation
        if data_type == 'boolean':
            if answer not in [True, False, 'yes', 'no', 'YES', 'NO', 'Yes', 'No']:
                return {"valid": False, "error_message": "Please answer yes or no"}
        
        elif data_type == 'date':
            # Basic date validation (can be enhanced)
            import re
            if not re.match(r'\d{4}-\d{2}-\d{2}', str(answer)):
                return {"valid": False, "error_message": "Please use YYYY-MM-DD format"}
        
        # Custom validation rules
        if validation == 'non_empty':
            if not answer or str(answer).strip() == '':
                return {"valid": False, "error_message": "This field cannot be empty"}
        
        elif validation == 'valid_itin':
            import re
            # ITIN format: 9XX-XX-XXXX (starts with 9)
            if not re.match(r'^9\d{2}-\d{2}-\d{4}$', str(answer)):
                return {"valid": False, "error_message": "Invalid ITIN format (9XX-XX-XXXX)"}
        
        return {"valid": True}


# Example usage for testing
if __name__ == "__main__":
    qm = QuestionMaster()
    
    # Get first question
    question = qm.get_next_question()
    print(f"First Question: {question['question_id']} - {question['question_text']}")
    
    # Simulate answering questions
    answers = {
        "1.1": {"value": "John Doe", "confirmed": True},
        "1.2": {"value": "1990-01-15", "confirmed": True},
        "2.1": {"value": "yes", "confirmed": True}
    }
    
    # Get next question after 2.1
    next_q = qm.get_next_question("2.1", answers)
    print(f"\nNext Question: {next_q['question_id']} - {next_q['question_text']}")
    
    # Get progress
    progress = qm.get_progress_info("2.1")
    print(f"\nProgress: {progress['current_position']}/{progress['total_questions']} ({progress['percentage']}%)")
