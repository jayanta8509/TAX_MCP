from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
import time
import asyncio
from typing import Optional, Dict, Any

from client import ask_question

# Import multi-agent components (only the ones we use)
from agent1_question_master import QuestionMaster
from agent2_wrapper import AnswerProvider
from client import get_workflow_state, update_workflow_state


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Tax Filing Assistant API",
    description="AI-powered Tax Filing Assistant for 1040NR returns with conversation memory",
    version="1.0.0"
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaxFilingRequest(BaseModel):
    user_id: str
    client_id: int  # Integer primary key
    reference: str  # "company" or "individual"
    query: str
    use_agent: bool = True

class WelcomeMessageRequest(BaseModel):
    user_id: str
    client_id: int  # Integer primary key
    reference: str  # "company" or "individual"

# Conversational Workflow Model (Single Endpoint)
class ConversationalWorkflowRequest(BaseModel):
    user_id: str
    client_id: int
    reference: str  # "individual" or "company"
    query: str  # User's message/answer
    use_agent: bool = True  # Keep for compatibility


@app.post("/chat/agent")
async def ask_question_endpoint(request: TaxFilingRequest):
    """
    Ask a tax filing question with memory support
    """
    try:
        logger.info(f"Received query from user {request.user_id}: {request.query}")

        if not request.query or request.query.strip() == "":
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        if not request.user_id or request.user_id.strip() == "":
            raise HTTPException(status_code=400, detail="User ID cannot be empty")
        
        if not request.client_id:
            raise HTTPException(status_code=400, detail="Client ID cannot be empty")
        
        if not request.reference or request.reference.strip() == "":
            raise HTTPException(status_code=400, detail="Reference cannot be empty")
        
        if request.reference.lower() not in ["company", "individual"]:
            raise HTTPException(status_code=400, detail="Reference must be 'company' or 'individual'")

        # Process the query with memory and IDs
        answer = await ask_question(
            question=request.query, 
            user_id=request.user_id,
            client_id=request.client_id,  # Pass client_id as int
            reference=request.reference.lower()  # Pass reference as "company" or "individual"
        )

        logger.info(f"Successfully processed query for user {request.user_id}")
        return {
            "response": answer,
            "status_code": 200,
            "query": request.query,
            "timestamp": time.time(),
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/welcome/message")
async def get_welcome_message_endpoint(request: WelcomeMessageRequest):
    """
    Get the welcome message for a client
    """
    try:
        logger.info(f"Received welcome message request for user {request.user_id}, client_id {request.client_id}")

        if not request.user_id or request.user_id.strip() == "":
            raise HTTPException(status_code=400, detail="User ID cannot be empty")

        if not request.client_id:
            raise HTTPException(status_code=400, detail="Client ID cannot be empty")

        if not request.reference or request.reference.strip() == "":
            raise HTTPException(status_code=400, detail="Reference cannot be empty")

        if request.reference.lower() not in ["company", "individual"]:
            raise HTTPException(status_code=400, detail="Reference must be 'company' or 'individual'")

        # Import the function from mcp_functions
        from welcome_message import get_client_welcome_message

        # Get the welcome message
        welcome_message = get_client_welcome_message(
            client_id=request.client_id,
            reference=request.reference.lower()
        )

        logger.info(f"Successfully processed welcome message for user {request.user_id}")
        return {
            "response": welcome_message,
            "status_code": 200,
            "timestamp": time.time(),
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error processing welcome message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing welcome message: {str(e)}")

# ============================================================
# CONVERSATIONAL WORKFLOW ENDPOINT (SINGLE CHAT INTERFACE)
# ============================================================

@app.post("/chat/workflow")
async def conversational_workflow(request: ConversationalWorkflowRequest):
    """
    Single conversational endpoint for entire workflow
    
    User just chats naturally:
    - System asks questions one by one
    - User answers with "yes" or provides correct value
    - Workflow managed internally
    
    Example flow:
    1. POST {"user_id": "user123", "client_id": 456, "reference": "individual", "query": "start"}
       → Returns: "Hi! Can you confirm your full legal name? I found 'John Smith'. Is this correct?"
    
    2. POST {"user_id": "user123", "client_id": 456, "reference": "individual", "query": "yes"}
       → Returns: "Great! Please provide your date of birth. I have '1990-05-15'. Is this correct?"
    
    3. POST {"user_id": "user123", "client_id": 456, "reference": "individual", "query": "no, 1990-05-16"}
       → Returns: "Updated! Your date of birth is now 1990-05-16. Next question..."
    """
    try:
        logger.info(f"Conversational workflow - User: {request.user_id}, Query: {request.query}")
        
        # Validate inputs
        if not request.user_id or request.user_id.strip() == "":
            raise HTTPException(status_code=400, detail="User ID cannot be empty")
        
        if not request.client_id:
            raise HTTPException(status_code=400, detail="Client ID cannot be empty")
        
        if request.reference.lower() not in ["company", "individual"]:
            raise HTTPException(status_code=400, detail="Reference must be 'company' or 'individual'")
        
        if not request.query or request.query.strip() == "":
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Import and initialize conversational handler
        from conversational_workflow import get_workflow_handler
        
        handler = await get_workflow_handler()
        
        # Process user's message
        response_text = await handler.process_message(
            user_id=request.user_id,
            client_id=request.client_id,
            reference=request.reference.lower(),
            user_message=request.query
        )
        
        logger.info(f"Conversational workflow response generated for {request.user_id}")
        
        return {
            "response": response_text,
            "status_code": 200,
            "query": request.query,
            "timestamp": time.time()
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in conversational workflow: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing workflow: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )