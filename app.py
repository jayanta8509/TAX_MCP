from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
import time

from client import ask_question


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

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )