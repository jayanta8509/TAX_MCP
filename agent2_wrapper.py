"""
Agent 2: Answer Provider Wrapper
Wraps the existing client.py to provide structured answers for the orchestrator
"""

import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
import re

# Import existing client functions
from client import (
    ask_question,
    get_or_create_agent,
    get_conversation_memory,
    store_conversation_memory
)


class AnswerProvider:
    def __init__(self):
        """Initialize Answer Provider"""
        self.agent = None
        self.mcp_tool_cache = {}
    
    async def initialize(self):
        """Initialize the MCP agent"""
        if not self.agent:
            self.agent = await get_or_create_agent()
        return self.agent
    
    async def get_answer(
        self,
        question_metadata: Dict,
        user_id: str,
        client_id: int,
        reference: str
    ) -> Dict[str, Any]:
        """
        Get answer for a specific question from the database
        
        Args:
            question_metadata: Question info from Agent 1
            user_id: User session ID
            client_id: Client ID
            reference: "individual" or "company"
        
        Returns:
            {
                "answer": str or None,
                "exists": bool,
                "needs_update": bool,
                "confidence": float,
                "source": "database" or "not_found",
                "field_name": str,
                "raw_data": dict (optional)
            }
        """
        await self.initialize()
        
        field_name = question_metadata.get('field_name')
        mcp_read_tool = question_metadata.get('mcp_read_tool')
        data_type = question_metadata.get('data_type')
        
        # Build query to check if data exists
        query = f"What is the value of '{field_name}' for this client? Just return the value, nothing else."
        
        try:
            # Use existing ask_question function
            response = await ask_question(
                question=query,
                user_id=user_id,
                client_id=client_id,
                reference=reference
            )
            
            # Parse the response to extract the actual value
            parsed_value = self._parse_response(response, field_name, data_type)
            
            return {
                "answer": parsed_value,
                "exists": parsed_value is not None and parsed_value != "",
                "needs_update": False,
                "confidence": 0.9 if parsed_value else 0.5,
                "source": "database" if parsed_value else "not_found",
                "field_name": field_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            print(f"Error getting answer: {e}")
            return {
                "answer": None,
                "exists": False,
                "needs_update": False,
                "confidence": 0.0,
                "source": "error",
                "field_name": field_name,
                "error": str(e)
            }
    
    def _parse_response(self, response: str, field_name: str, data_type: str) -> Optional[Any]:
        """
        Parse the LLM response to extract the actual value
        
        Handles responses like:
        - "The client's name is John Doe"
        - "value of 'full_legal_name' for this client is **Robert SEBASTIAO Da Elvis**."
        - "client is June 16, 1999"
        - "Not provided"
        - "John Doe"
        """
        response_lower = response.lower().strip()
        original_response = response.strip()
        
        # Check for common "not found" indicators
        not_found_indicators = [
            'not provided', 'not found', 'no data', 'null', 'none',
            'not available', 'missing', 'not specified', 'unknown',
            'does not have', 'hasn\'t provided', 'no information'
        ]
        
        for indicator in not_found_indicators:
            if indicator in response_lower:
                return None
        
        # For boolean fields
        if data_type == 'boolean':
            if 'yes' in response_lower or 'true' in response_lower:
                return True
            elif 'no' in response_lower or 'false' in response_lower:
                return False
        
        # For date fields, extract date pattern (YYYY-MM-DD or Month Day, Year)
        if data_type == 'date':
            # Try YYYY-MM-DD format first
            date_pattern = r'\d{4}-\d{2}-\d{2}'
            match = re.search(date_pattern, original_response)
            if match:
                return match.group(0)
            
            # Try "Month Day, Year" format (e.g., "June 16, 1999")
            month_day_year_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
            match = re.search(month_day_year_pattern, original_response, re.IGNORECASE)
            if match:
                date_str = match.group(0)
                # Convert to YYYY-MM-DD
                try:
                    from datetime import datetime
                    parsed_date = datetime.strptime(date_str.replace(',', ''), '%B %d %Y')
                    return parsed_date.strftime('%Y-%m-%d')
                except:
                    return date_str  # Return as-is if parsing fails
        
        # For ITIN, extract ITIN pattern
        if field_name == 'itin_number':
            itin_pattern = r'9\d{2}-\d{2}-\d{4}'
            match = re.search(itin_pattern, original_response)
            if match:
                return match.group(0)
        
        # Extract value from common LLM response patterns
        # Pattern 1: "value of 'field_name' ... is **VALUE**."
        pattern1 = r'\*\*(.*?)\*\*'
        match = re.search(pattern1, original_response)
        if match:
            return match.group(1).strip()
        
        # Pattern 2: "The [field] is: VALUE" or "The [field] is VALUE"
        pattern2 = r'(?:is|are)[\s:]+(.+?)(?:\.|$)'
        match = re.search(pattern2, original_response, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            # Remove trailing punctuation
            value = re.sub(r'[.,;!?]+$', '', value)
            return value
        
        # Pattern 3: Clean common verbose prefixes
        cleaned = original_response
        
        # Remove verbose prefixes (expanded list) - apply in order
        verbose_prefixes = [
            r"^value of ['\"].*?['\"] for (?:this )?client is\s+",
            r"^(?:the\s+)?client(?:'s|\s+is)\s+",
            r"^for (?:this )?client,?\s+(?:it\s+)?is\s+",
            r"^(?:the\s+)?client['']s\s+",
            r"^the\s+",
            r"^it is\s+",
            r"^they are\s+",
            r"^this is\s+",
            r"^currently\s+",
            r"^(?:his|her|their)\s+.*?\s+is\s+",
        ]
        
        for prefix_pattern in verbose_prefixes:
            cleaned = re.sub(prefix_pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove markdown formatting
        cleaned = re.sub(r'\*\*', '', cleaned)
        cleaned = re.sub(r'__', '', cleaned)
        
        # Remove quotation marks at start/end
        cleaned = re.sub(r'^["\']|["\']$', '', cleaned.strip())
        
        # Remove trailing punctuation
        cleaned = re.sub(r'[.,;!?]+$', '', cleaned.strip())
        
        return cleaned if cleaned else None
    
    async def update_answer(
        self,
        question_metadata: Dict,
        new_value: Any,
        user_id: str,
        client_id: int,
        reference: str
    ) -> Dict[str, Any]:
        """
        Update an incorrect answer in the database
        
        Args:
            question_metadata: Question info
            new_value: Corrected value
            user_id, client_id, reference: Session info
        
        Returns:
            {
                "success": bool,
                "message": str,
                "updated_value": Any,
                "timestamp": str
            }
        """
        await self.initialize()
        
        field_name = question_metadata.get('field_name')
        mcp_update_tool = question_metadata.get('mcp_update_tool')
        
        # Build update command
        update_query = f"""
        Please update the client's {field_name} to: {new_value}
        
        Use the appropriate MCP update tool ({mcp_update_tool}) to make this change.
        Confirm the update was successful.
        """
        
        try:
            response = await ask_question(
                question=update_query,
                user_id=user_id,
                client_id=client_id,
                reference=reference
            )
            
            # Check if update was successful
            success_indicators = ['success', 'updated', 'saved', 'changed', 'confirmed']
            success = any(indicator in response.lower() for indicator in success_indicators)
            
            return {
                "success": success,
                "message": response,
                "updated_value": new_value,
                "field_name": field_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            print(f"Error updating answer: {e}")
            return {
                "success": False,
                "message": f"Failed to update: {str(e)}",
                "updated_value": new_value,
                "field_name": field_name,
                "error": str(e)
            }
    
    async def check_data_exists(
        self,
        field_names: list,
        user_id: str,
        client_id: int,
        reference: str
    ) -> Dict[str, bool]:
        """
        Batch check if multiple fields exist
        Useful for optimizing "skip_if_exists" logic
        
        Returns:
            {
                "full_legal_name": True,
                "date_of_birth": False,
                ...
            }
        """
        results = {}
        
        for field_name in field_names:
            question_meta = {"field_name": field_name, "data_type": "string"}
            answer = await self.get_answer(question_meta, user_id, client_id, reference)
            results[field_name] = answer['exists']
        
        return results


# Example usage for testing
async def test_answer_provider():
    ap = AnswerProvider()
    
    # Test getting an answer
    question_meta = {
        "question_id": "1.1",
        "field_name": "full_legal_name",
        "data_type": "string",
        "mcp_read_tool": "get_client_basic_profile"
    }
    
    result = await ap.get_answer(
        question_metadata=question_meta,
        user_id="test_user",
        client_id=456,
        reference="individual"
    )
    
    print(f"Answer Result: {result}")
    
    # Test updating an answer
    if not result['exists']:
        update_result = await ap.update_answer(
            question_metadata=question_meta,
            new_value="John Doe",
            user_id="test_user",
            client_id=456,
            reference="individual"
        )
        print(f"Update Result: {update_result}")


if __name__ == "__main__":
    asyncio.run(test_answer_provider())
