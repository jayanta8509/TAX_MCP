from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
import sys
import time
import redis
import json
from datetime import datetime, timedelta
from typing import Dict, Any

HOST= os.environ["HOST"] = os.getenv("HOST")
PORT= os.environ["PORT"] = os.getenv("PORT")
PASSWORD = os.environ["PASSWORD"] = os.getenv("PASSWORD")

# Redis Cloud connection for memory storage
redis_client = redis.Redis(
    host=HOST,
    port=PORT,
    decode_responses=True,
    username="default",
    password=PASSWORD,
)

# Test Redis connection
try:
    redis_client.ping()
    print("✅ Redis Cloud connected successfully")
except redis.ConnectionError as e:
    print(f"❌ Redis Cloud connection failed: {e}")
    print("⚠️  Falling back to memory-only mode")



def store_conversation_memory(user_id: str, messages: list, client_id: int = None, reference: str = None, metadata: dict = None):
    """Store conversation in Redis with 12-hour TTL including client_id and reference"""
    try:
        memory_data = {
            "messages": messages,
            "client_id": client_id,  # Store client_id
            "reference": reference,  # Store reference (company or individual)
            "metadata": metadata or {},
            "last_updated": datetime.utcnow().isoformat(),
            "user_id": user_id
        }

        # Store with 12-hour expiration (43200 seconds)
        redis_client.setex(
            f"conversation:{user_id}",
            43200,  # 12 hours in seconds
            json.dumps(memory_data)
        )
        print(f"💾 Stored conversation for user {user_id} with client_id={client_id}, reference={reference}")
    except Exception as e:
        print(f"❌ Error storing conversation: {e}")

def get_conversation_memory(user_id: str) -> dict:
    """Retrieve conversation from Redis"""
    try:
        data = redis_client.get(f"conversation:{user_id}")
        if data:
            return json.loads(data)
        return {"messages": [], "metadata": {}}
    except Exception as e:
        print(f"❌ Error retrieving conversation: {e}")
        return {"messages": [], "metadata": {}}


def clear_conversation_memory(user_id: str):
    """Clear conversation memory for a specific user"""
    try:
        redis_client.delete(f"conversation:{user_id}")
        print(f"🧹 Cleared conversation memory for user: {user_id}")
    except Exception as e:
        print(f"❌ Error clearing conversation: {e}")


def get_conversation_summary(user_id: str) -> str:
    """Get a summary of the conversation for continuity"""
    return f"Conversation thread: {user_id} - Tax Filing Assistant (1040NR)"


# Global MCP client and agent (singleton pattern to avoid TaskGroup errors)
_mcp_client = None
_agent = None
_client_lock = asyncio.Lock()


async def get_or_create_agent():
    """Get or create the global MCP client and agent (singleton pattern)"""
    global _mcp_client, _agent
    
    async with _client_lock:
        if _agent is None:
            print("🔧 Initializing MCP client and agent...")
            
            try:
                # Use the current Python interpreter (from virtual environment)
                python_executable = sys.executable
                print(f"📍 Using Python: {python_executable}")
                
                # Create MCP client
                _mcp_client = MultiServerMCPClient(
                    {
                        "Data_Fetch": {
                            "command": python_executable,  # Use full path to Python
                            "args": ["mcp_functions.py"],
                            "transport": "stdio",
                        }
                    }
                )
                
                os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
                
                # Get tools and create agent
                print("📡 Connecting to MCP server...")
                tools = await _mcp_client.get_tools()
                print(f"✅ Got {len(tools)} tools from MCP server")
                
                model = ChatOpenAI(model="gpt-4o-mini")
                _agent = create_react_agent(model, tools)
                
                print("✅ MCP client and agent initialized successfully")
            except Exception as e:
                print(f"❌ Error initializing MCP client: {e}")
                print(f"❌ Error type: {type(e).__name__}")
                import traceback
                print(f"❌ Full traceback:\n{traceback.format_exc()}")
                raise
        
        return _agent




async def process_question(agent, user_question, user_id="default_user", client_id=None, reference=None):
    """Send any user question to the agent with Redis memory and IDs"""
    print(f"\n🔍 Question: {user_question}")
    print(f"👤 User ID: {user_id}, Client ID: {client_id}, Reference: {reference}")
    print("🔄 Processing...")

    # Get existing conversation from Redis
    memory_data = get_conversation_memory(user_id)
    
    # Update or set client_id and reference in memory
    if client_id:
        memory_data['client_id'] = client_id
    if reference:
        memory_data['reference'] = reference

    # Build message history with new question
    messages = memory_data.get("messages", [])
    messages.append({"role": "user", "content": user_question})

    # Add IDs to the context for the agent
    system_context = f"""
    SESSION INFORMATION:
    - User ID: {user_id}
    - Client ID: {client_id}
    - Reference Type: {reference} (company or individual)
    
    IMPORTANT: When calling any MCP tools, you MUST pass these two parameters:
    - client_id: {client_id}
    - reference: {reference}
    """

    # Add conversation context to messages for the agent
    if len(messages) > 1:
        context_messages = messages[-6:]  # Keep last 6 messages for context
        full_messages = [
            {"role": "system", "content": system_context},
            *context_messages
        ]
    else:
        full_messages = [
            {"role": "system", "content": system_context},
            {"role": "user", "content": user_question}
        ]

    # Get response from agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
import sys
import time
import redis
import json
from datetime import datetime, timedelta
from typing import Dict, Any

HOST= os.environ["HOST"] = os.getenv("HOST")
PORT= os.environ["PORT"] = os.getenv("PORT")
PASSWORD = os.environ["PASSWORD"] = os.getenv("PASSWORD")

# Redis Cloud connection for memory storage
redis_client = redis.Redis(
    host=HOST,
    port=PORT,
    decode_responses=True,
    username="default",
    password=PASSWORD,
)

# Test Redis connection
try:
    redis_client.ping()
    print("✅ Redis Cloud connected successfully")
except redis.ConnectionError as e:
    print(f"❌ Redis Cloud connection failed: {e}")
    print("⚠️  Falling back to memory-only mode")



def store_conversation_memory(user_id: str, messages: list, client_id: int = None, reference: str = None, metadata: dict = None):
    """Store conversation in Redis with 12-hour TTL including client_id and reference"""
    try:
        memory_data = {
            "messages": messages,
            "client_id": client_id,  # Store client_id
            "reference": reference,  # Store reference (company or individual)
            "metadata": metadata or {},
            "last_updated": datetime.utcnow().isoformat(),
            "user_id": user_id
        }

        # Store with 12-hour expiration (43200 seconds)
        redis_client.setex(
            f"conversation:{user_id}",
            43200,  # 12 hours in seconds
            json.dumps(memory_data)
        )
        print(f"💾 Stored conversation for user {user_id} with client_id={client_id}, reference={reference}")
    except Exception as e:
        print(f"❌ Error storing conversation: {e}")

def get_conversation_memory(user_id: str) -> dict:
    """Retrieve conversation from Redis"""
    try:
        data = redis_client.get(f"conversation:{user_id}")
        if data:
            return json.loads(data)
        return {"messages": [], "metadata": {}}
    except Exception as e:
        print(f"❌ Error retrieving conversation: {e}")
        return {"messages": [], "metadata": {}}


def clear_conversation_memory(user_id: str):
    """Clear conversation memory for a specific user"""
    try:
        redis_client.delete(f"conversation:{user_id}")
        print(f"🧹 Cleared conversation memory for user: {user_id}")
    except Exception as e:
        print(f"❌ Error clearing conversation: {e}")


def get_conversation_summary(user_id: str) -> str:
    """Get a summary of the conversation for continuity"""
    return f"Conversation thread: {user_id} - Tax Filing Assistant (1040NR)"


# Global MCP client and agent (singleton pattern to avoid TaskGroup errors)
_mcp_client = None
_agent = None
_client_lock = asyncio.Lock()


async def get_or_create_agent():
    """Get or create the global MCP client and agent (singleton pattern)"""
    global _mcp_client, _agent
    
    async with _client_lock:
        if _agent is None:
            print("🔧 Initializing MCP client and agent...")
            
            try:
                # Use the current Python interpreter (from virtual environment)
                python_executable = sys.executable
                print(f"📍 Using Python: {python_executable}")
                
                # Create MCP client
                _mcp_client = MultiServerMCPClient(
                    {
                        "Data_Fetch": {
                            "command": python_executable,  # Use full path to Python
                            "args": ["mcp_functions.py"],
                            "transport": "stdio",
                        }
                    }
                )
                
                os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
                
                # Get tools and create agent
                print("📡 Connecting to MCP server...")
                tools = await _mcp_client.get_tools()
                print(f"✅ Got {len(tools)} tools from MCP server")
                
                model = ChatOpenAI(model="gpt-4o-mini")
                _agent = create_react_agent(model, tools)
                
                print("✅ MCP client and agent initialized successfully")
            except Exception as e:
                print(f"❌ Error initializing MCP client: {e}")
                print(f"❌ Error type: {type(e).__name__}")
                import traceback
                print(f"❌ Full traceback:\n{traceback.format_exc()}")
                raise
        
        return _agent




async def process_question(agent, user_question, user_id="default_user", client_id=None, reference=None):
    """Send any user question to the agent with Redis memory and IDs"""
    print(f"\n🔍 Question: {user_question}")
    print(f"👤 User ID: {user_id}, Client ID: {client_id}, Reference: {reference}")
    print("🔄 Processing...")

    # Get existing conversation from Redis
    memory_data = get_conversation_memory(user_id)
    
    # Update or set client_id and reference in memory
    if client_id:
        memory_data['client_id'] = client_id
    if reference:
        memory_data['reference'] = reference

    # Build message history with new question
    messages = memory_data.get("messages", [])
    messages.append({"role": "user", "content": user_question})

    # Add IDs to the context for the agent
    system_context = f"""
    SESSION INFORMATION:
    - User ID: {user_id}
    - Client ID: {client_id}
    - Reference Type: {reference} (company or individual)
    
    IMPORTANT: When calling any MCP tools, you MUST pass these two parameters:
    - client_id: {client_id}
    - reference: {reference}
    """

    # Add conversation context to messages for the agent
    if len(messages) > 1:
        context_messages = messages[-6:]  # Keep last 6 messages for context
        full_messages = [
            {"role": "system", "content": system_context},
            *context_messages
        ]
    else:
        full_messages = [
            {"role": "system", "content": system_context},
            {"role": "user", "content": user_question}
        ]

    # Get response from agent
    response = await agent.ainvoke({"messages": full_messages})

    # Extract and store response
    response_content = response['messages'][-1].content
    messages.append({"role": "assistant", "content": response_content})

    # Save updated conversation to Redis with 12-hour TTL including IDs
    store_conversation_memory(user_id, messages, client_id=client_id, reference=reference)

    return response_content


async def ask_question(question, style_preference=None, user_id="default_user", client_id=None, reference=None):
    """Function to directly ask a question with client_id and reference"""
    
    # Get recent conversation context
    recent_context = await get_recent_context(user_id)
    
    # Get stored client_id and reference from memory if not provided
    memory_data = get_conversation_memory(user_id)
    if not client_id:
        client_id = memory_data.get('client_id', None)
    if not reference:
        reference = memory_data.get('reference', 'individual')

    # Include session context in the question
    contextual_question = f"""
    You are an intelligent Tax Filing Assistant specialized in helping non-resident clients file their 1040NR tax returns.

    **Your Role:**
    You help collect information, validate documents, and guide clients through the 1040NR filing process by asking smart, conditional questions based on what information is already available in their stored documents.

    **SESSION CONTEXT:**
    - User ID: {user_id}
    - Client ID: {client_id}
    - Reference Type: {reference} (company or individual)

    {recent_context}

    **How You Work:**
    1. **Check First, Ask Later**: Before asking any question, ALWAYS use the MCP tools to check if the information already exists. Never ask for information that's already stored.

    2. **Follow the Task Flow**: Guide clients through these tasks in order:
       - Task 1: Request & Receive Information (7 subtasks: Personal Info → ITIN → Previous Returns → Income/Expense → Real Estate → Form Signing → W7)
       - Task 2: Add-On Services (suggest based on previous year's data)
       - Task 3: Invoice Generation
       - Task 4: Review & Submission

    3. **Ask Conditional Questions**: Only ask questions when:
       - Data is missing from the user's stored documents
       - Data needs to be updated or confirmed
       - It's required for the next step in the workflow

    4. **Be Context-Aware**: 
       - Remember what documents the user has already uploaded
       - Reference their previous year's tax return to suggest relevant add-ons
       - Skip questions if the answer is already in their documents

    5. **Document Collection**: When requesting documents, specify:
       - Exact form names (e.g., "FORM 1042-S", "Schedule C", "FORM 1098")
       - Why it's needed
       - What validation you'll perform

    6. **Smart Suggestions**: Based on retrieved documents:
       - Auto-suggest add-on services they used last year
       - Remind them of forms they filed previously
       - Flag missing but likely needed documents

    **AVAILABLE MCP TOOLS (ALL require client_id and reference):**
    
    📋 CLIENT PROFILE:
    1. get_client_basic_profile(client_id, reference)
       - Returns: name, email, SSN/ITIN, filing status, account status
       - Use for: Identity verification, basic account info

    2. get_client_primary_contact(client_id, reference)
       - Returns: primary contact name, email, phone, address
       - Use for: Contact information, mailing address

    3. get_client_all_contacts(client_id, reference)
       - Returns: all contact records
       - Use for: Multiple addresses, alternate contacts

    💰 FINANCIAL DATA:
    4. get_client_financial_summary(client_id, reference)
       - Returns: total_amount, status, temp_client flag
       - Use for: Billing questions, account status

    📧 MAIL SERVICE:
    5. get_client_mail_service_info(client_id, reference)
       - Returns: mail service status, start/due dates, late fees
       - Use for: Mail forwarding service questions

    🏢 INTERNAL DATA:
    6. get_client_internal_data(client_id, reference)
       - Returns: office, manager, partner assignments, practice_id
       - Use for: Account management, team assignments

    **Response Format:**
    - Be conversational and professional
    - Ask ONE question at a time (don't overwhelm)
    - Confirm information before moving to next step
    - If information exists, say: "I see you already provided [X]. Let me confirm: [show data]. Is this still correct?"
    - If information is missing, say: "I need to collect [X] to proceed. [Ask specific question]"

    **Critical Rules:**
    ❌ NEVER ask for information that's already in retrieved documents
    ❌ NEVER ask multiple questions at once
    ❌ NEVER proceed without validating required documents
    ❌ NEVER share Client ID or Reference type in your responses (keep them internal)
    ✅ ALWAYS retrieve context before asking any question
    ✅ ALWAYS reference previous year's data when suggesting add-ons
    ✅ ALWAYS explain WHY you need each document

    **User's Question:** {question}

    Please use the appropriate MCP tools with the client_id and reference provided above.
    """

    # Get or create the global agent (singleton pattern)
    agent = await get_or_create_agent()
    
    # Process the question
    return await process_question(agent, contextual_question, user_id, client_id, reference)


async def get_recent_context(user_id: str) -> str:
    """Get recent conversation context for better follow-up handling using Redis"""
    try:
        # Get conversation from Redis
        memory_data = get_conversation_memory(user_id)
        messages = memory_data.get("messages", [])

        if messages:
            # Extract recent tax document and form discussions
            recent_forms = []
            recent_topics = []
            import re
            
            for msg in messages[-4:]:  # Look at last 4 messages
                if isinstance(msg, dict) and 'content' in msg:
                    content = msg['content']
                    
                    # Look for tax form names (FORM 1042-S, 1098, W-7, Schedule C, etc.)
                    form_patterns = re.findall(r'(?:FORM\s+)?(?:1042-S|1098|W-?7|Schedule\s+[A-Z]|1040NR|8843)', content, re.IGNORECASE)
                    recent_forms.extend(form_patterns)
                    
                    # Look for ITIN mentions
                    if re.search(r'ITIN|Individual Taxpayer Identification Number', content, re.IGNORECASE):
                        recent_topics.append("ITIN")
                    
                    # Look for tax year mentions
                    tax_years = re.findall(r'20\d{2}', content)
                    if tax_years:
                        recent_topics.append(f"Tax Year {tax_years[-1]}")

            context_parts = []
            if recent_forms:
                context_parts.append(f"Recently discussed forms: {', '.join(set(recent_forms))}")
            if recent_topics:
                context_parts.append(f"Topics: {', '.join(set(recent_topics))}")
            
            if context_parts:
                return f"RECENT CONTEXT: {'. '.join(context_parts)}. Use this context when the client refers to 'that form' or 'the document we discussed'."

        return ""

    except Exception as e:
        print(f"Error getting context: {e}")
        return ""