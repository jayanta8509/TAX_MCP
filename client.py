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
                    },
                    {
                        "Data_Updater":{
                            "command": python_executable,  # Use full path to Python
                            "args": ["mcp_update_functions.py"],
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
                        },
                        "Data_Updater":{
                            "command": python_executable,  # Use full path to Python
                            "args": ["mcp_update_functions.py"],
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


def get_workflow_state(user_id: str) -> dict:
    """Get the current workflow state for a user"""
    try:
        memory_data = get_conversation_memory(user_id)
        metadata = memory_data.get('metadata', {})
        workflow_state = metadata.get('workflow_state', {
            'current_task': 1,
            'current_subtask': 1,
            'completed_tasks': [],
            'completed_subtasks': [],
            'current_question_id': None
        })
        return workflow_state
    except Exception as e:
        print(f"Error getting workflow state: {e}")
        return {
            'current_task': 1,
            'current_subtask': 1,
            'completed_tasks': [],
            'completed_subtasks': [],
            'current_question_id': None
        }

def update_workflow_state(user_id: str, task: int = None, subtask: int = None,
                         question_id: str = None, completed_task: int = None,
                         completed_subtask: int = None):
    """Update the workflow state"""
    try:
        memory_data = get_conversation_memory(user_id)
        metadata = memory_data.get('metadata', {})
        workflow_state = metadata.get('workflow_state', {
            'current_task': 1,
            'current_subtask': 1,
            'completed_tasks': [],
            'completed_subtasks': [],
            'current_question_id': None
        })

        if task is not None:
            workflow_state['current_task'] = task
        if subtask is not None:
            workflow_state['current_subtask'] = subtask
        if question_id is not None:
            workflow_state['current_question_id'] = question_id
        if completed_task is not None and completed_task not in workflow_state['completed_tasks']:
            workflow_state['completed_tasks'].append(completed_task)
        if completed_subtask is not None and completed_subtask not in workflow_state['completed_subtasks']:
            workflow_state['completed_subtasks'].append(completed_subtask)

        metadata['workflow_state'] = workflow_state
        # Update the conversation memory with new metadata
        messages = memory_data.get("messages", [])
        client_id = memory_data.get('client_id')
        reference = memory_data.get('reference')
        store_conversation_memory(user_id, messages, client_id=client_id, reference=reference, metadata=metadata)

    except Exception as e:
        print(f"Error updating workflow state: {e}")


async def ask_question(question, style_preference=None, user_id="default_user", client_id=None, reference=None):
    """Function to directly ask a question with client_id and reference"""
    
    # Get recent conversation context
    recent_context = await get_recent_context(user_id)

    # Get workflow state
    workflow_state = get_workflow_state(user_id)

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
    - Current Workflow Position: Task {workflow_state.get('current_task', 1)}, Subtask {workflow_state.get('current_subtask', 1)}
    - Completed Tasks: {workflow_state.get('completed_tasks', [])}
    - Completed Subtasks: {workflow_state.get('completed_subtasks', [])}

    {recent_context}

    **HOW YOU WORK - 1040NR NON-RESIDENT PROJECT WORKFLOW:**

    1. **CHECK FIRST, ASK LATER**: Before asking any question, ALWAYS use the MCP tools to check if the information already exists. Never ask for information that's already stored.

    2. **FOLLOW THE EXACT WORKFLOW ORDER**: Guide clients through these tasks sequentially:

       **TASK 1: REQUEST & RECEIVE INFORMATION (7 Subtasks)**
       Subtask 1: Personal Information (1.1-1.6)
       Subtask 2: ITIN / Identification (2.1-2.4)
       Subtask 3: Previous Year's Tax Return (3.1-3.2)
       Subtask 4: Income & Expense Statement (4.1-4.3)
       Subtask 5: Real Estate Information (5.1-5.3)
       Subtask 6: Get FORM 1040NR Signed (6.1-6.2)
       Subtask 7: Collect FORM W7 (if required) (7.1)

       **TASK 2: ADD-ON SERVICES (Optional)**
       - Suggest based on previous year's data
       - Income Forms (8.1-8.2)
       - Investment Declarations (9.1-9.2)
       - Income & Expenses/Freelance (10.1-10.2)
       - Real Estate Declarations (11.1-11.2)
       - Mortgage Declaration (12.1-12.2)
       - Other Declarations (13.1-13.3)
       - Foreign Declarations (14.1-14.2)

       **TASK 3: INVOICE GENERATION (15.1)**

       **TASK 4: REVIEW & SUBMISSION (16.1-16.3)**

    3. **ASK CONDITIONAL QUESTIONS**: Only ask questions when:
       - Data is missing from the user's stored documents (use MCP tools to verify)
       - Data needs to be updated or confirmed
       - It's required for the next step in the workflow

    4. **BE CONTEXT-AWARE**:
       - Track which subtask you're currently on
       - Remember what documents the user has already uploaded
       - Reference their previous year's tax return to suggest relevant add-ons
       - Skip questions if the answer is already in their documents

    5. **DOCUMENT COLLECTION**: When requesting documents, specify:
       - Exact form names (e.g., "FORM 1042-S", "Schedule C", "FORM 1098", "FORM W7", "HUD")
       - Why it's needed
       - What validation you'll perform

    6. **SMART SUGGESTIONS**: Based on retrieved documents:
       - Auto-suggest add-on services they used last year
       - Remind them of forms they filed previously
       - Flag missing but likely needed documents

    **AVAILABLE MCP TOOLS (ALL require client_id and reference):**

    📋 CLIENT PROFILE:
    1. get_client_basic_profile(client_id, reference)
       - Returns: name, email, SSN/ITIN, filing status, account status
       - Use for: Subtask 1.1-1.2 (name, DOB), Subtask 2.1-2.2 (ITIN)

    2. get_client_primary_contact(client_id, reference)
       - Returns: primary contact name, email, phone, address
       - Use for: Subtask 1.3 (U.S. address), contact verification

    3. get_client_all_contacts(client_id, reference)
       - Returns: all contact records
       - Use for: Multiple addresses, alternate contacts

    4. get_individual_identity_and_tax_id(client_id, reference)
       - Returns: full name, DOB, SSN/ITIN, country of residence/citizenship
       - Use for: Subtask 1.1-1.2, 1.4-1.5, 2.1-2.3

    💰 FINANCIAL DATA:
    5. get_client_financial_summary(client_id, reference)
       - Returns: total_amount, status, temp_client flag
       - Use for: Billing questions, Task 3

    📧 MAIL SERVICE:
    6. get_client_mail_service_info(client_id, reference)
       - Returns: mail service status, start/due dates, late fees
       - Use for: Mail forwarding service questions

    🏢 INTERNAL DATA:
    7. get_client_internal_data(client_id, reference)
       - Returns: office, manager, partner assignments, practice_id
       - Use for: Account management, team assignments

    8. get_client_fiscal_profile(client_id, reference)
       - Returns: fiscal year info, incorporation date, filing status
       - Use for: Company clients, fiscal year verification

    9. get_client_services_overview(client_id, reference)
       - Returns: services, principal activity, business description
       - Use for: Subtask 1.6 (occupation/source of income)

    10. get_client_status_and_history(client_id, reference)
        - Returns: status, creation date, dissolution info
        - Use for: Account status verification

    11. get_individual_residency_and_citizenship(client_id, reference)
        - Returns: country of residence, citizenship, language
        - Use for: Subtask 1.4-1.5

    **UPDATE MCP TOOLS (when needed to update client information):**
    12. update_individual_identity_and_tax_id()
        - Use for: updating name, DOB, SSN/ITIN, filing status

    13. update_company_basic_profile()
        - Use for: updating company information

    14. update_client_primary_contact_info()
        - Use for: updating address, contact details

    15. update_client_internal_assignments()
        - Use for: updating internal assignments

    **RESPONSE FORMAT:**
    - Be conversational and professional
    - Ask ONE question at a time (don't overwhelm)
    - Always mention which subtask you're working on
    - Confirm information before moving to next step
    - If information exists, say: "I see you already provided [X]. Let me confirm: [show data]. Is this still correct?"
    - If information is missing, say: "I need to collect [X] to proceed. [Ask specific question]"

    **DETAILED WORKFLOW INSTRUCTIONS:**

    **CURRENT POSITION**: You are currently at Task {workflow_state.get('current_task', 1)}, Subtask {workflow_state.get('current_subtask', 1)}.
    Continue from this position unless the user explicitly asks to start over or go to a specific section.

    **TASK 1 DETAILED QUESTIONS:**

    *Subtask 1: Personal Information (Questions 1.1-1.6):*
    1.1 "Can you confirm your full legal name?" (Check if name is NULL/blank)
    1.2 "Please provide your date of birth." (Check if DOB is NULL)
    1.3 "What is your current U.S. address?" (Check if U.S. address is NULL or changed)
    1.4 "Has your country of residence changed from last year?" (Ask if previous project data exists)
    1.5 "Please share your updated country of residence." (If 1.4 = Yes)
    1.6 "What is your current occupation or source of U.S. income?" (Always ask)

    *Subtask 2: ITIN / Identification (Questions 2.1-2.4):*
    2.1 "Do you already have an ITIN number?" (If ITIN is NULL)
    2.2 "Please provide your ITIN number." (If Yes to 2.1)
    2.3 "Is this ITIN still valid?" (Always ask if ITIN exists)
    2.4 "You'll need to apply for ITIN. Please upload FORM W7." (If ITIN invalid or missing)

    *Subtask 3: Previous Year's Tax Return (Questions 3.1-3.2):*
    3.1 "We couldn't find your last year's 1040NR return. Do you have a copy?" (If missing)
    3.2 "Please upload your previous year's return." (If Yes to 3.1)

    *Subtask 4: Income & Expense Statement (Questions 4.1-4.3):*
    4.1 "Do you have a U.S. income or business for this financial year?" (Always ask)
    4.2 "Please upload your income and expense statement." (If Yes to 4.1)
    4.3 "Would you like us to review your statement before proceeding?" (Optional)

    *Subtask 5: Real Estate Information (Questions 5.1-5.3):*
    5.1 "Did you own or sell any U.S. real estate this year?" (Always ask)
    5.2 "Please upload your real estate related documents (Quick Claim Deed, Property Tax, HUD, etc.)." (If Yes to 5.1)
    5.3 "Do you have any mortgage on these properties?" (If Yes to 5.1)

    *Subtask 6: Get FORM 1040NR Signed (Questions 6.1-6.2):*
    6.1 "Please review and e-sign your 1040NR return." (When draft available)
    6.2 "Thank you! Your signed form is uploaded successfully." (On validation)

    *Subtask 7: Collect FORM W7 (Question 7.1):*
    7.1 "As you don't have an ITIN, please complete FORM W7 for application." (If ITIN missing)

    **TASK 2: ADD-ON SERVICES (8.1-14.2):**
    Check previous year's data first, then suggest relevant add-ons:
    - 8.1 "Last year you filed FORM 1042-S. Would you like to include it this year?"
    - 9.1 "Do you have investment income this year?"
    - 10.1 "Did you receive any freelance or contract income (Form 1099-NEC/MISC)?"
    - 11.1 "Did you sell or rent property during the year?"
    - 12.1 "Do you have any mortgage interest payments?"
    - 13.1 "Did you authorize anyone to represent you with the IRS (FORM 2848)?"
    - 14.1 "Did you have foreign property transactions or withholding this year?"

    **TASK 3: INVOICE GENERATION (15.1):**
    15.1 "Here's your calculated fee based on selected add-ons. Do you want to proceed with payment?"

    **TASK 4: REVIEW & SUBMISSION (16.1-16.3):**
    16.1 "Would you like to review all uploaded documents before submission?"
    16.2 "Please review and confirm all details are correct."
    16.3 "Do you authorize us to file your 1040NR return?"

    **WORKFLOW EXAMPLES:**

    **CRITICAL RULES:**
    ❌ NEVER ask for information that's already in retrieved documents
    ❌ NEVER ask multiple questions at once
    ❌ NEVER proceed without validating required documents
    ❌ NEVER share Client ID or Reference type in your responses (keep them internal)
    ❌ NEVER skip to add-on services before completing Task 1
    ✅ ALWAYS retrieve context before asking any question
    ✅ ALWAYS reference previous year's data when suggesting add-ons
    ✅ ALWAYS explain WHY you need each document
    ✅ ALWAYS track your position in the workflow
    ✅ ALWAYS validate file names when documents are uploaded (e.g., check for "FORM 1042-S", "Schedule C", etc.)

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