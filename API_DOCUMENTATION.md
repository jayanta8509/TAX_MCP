# Multi-Agent Workflow API Documentation

## 🚀 New Endpoints Added to app.py

Your `app.py` now has **3 new workflow endpoints** alongside your existing endpoints.

---

## 📍 API Endpoints Overview

### Existing Endpoints (Unchanged)
- `POST /chat/agent` - Simple Q&A with AI assistant
- `POST /welcome/message` - Get welcome message for client

### New Multi-Agent Workflow Endpoints
- `POST /workflow/start` - Start guided workflow
- `POST /workflow/next` - Process confirmation and get next question
- `GET /workflow/status/{user_id}` - Get workflow progress

---

## 🔥 Endpoint Details

### 1. **POST /workflow/start**

Start a new workflow or resume existing one.

#### Request Body
```json
{
  "user_id": "user123",
  "client_id": 456,
  "reference": "individual",  // or "company"
  "resume": true  // optional, default: true
}
```

#### Response (Success)
```json
{
  "status": "active",
  "question": {
    "id": "1.1",
    "text": "Can you confirm your full legal name?",
    "task_name": "REQUEST & RECEIVE INFORMATION",
    "subtask_name": "Personal Information",
    "field_name": "full_legal_name",
    "data_type": "string",
    "required": true
  },
  "current_answer": {
    "value": "John Doe",
    "exists": true,
    "confidence": 0.9
  },
  "progress": {
    "current_position": 1,
    "total_questions": 30,
    "percentage": 3.3
  },
  "timestamp": 1733424800.123
}
```

#### Response (Already Complete)
```json
{
  "status": "complete",
  "message": "Workflow already completed",
  "total_answered": 30,
  "timestamp": 1733424800.123
}
```

---

### 2. **POST /workflow/next**

Process user's confirmation and move to next question.

#### Request Body (Answer is Correct)
```json
{
  "user_id": "user123",
  "confirmed": true
}
```

#### Request Body (Answer is Incorrect - Update Database)
```json
{
  "user_id": "user123",
  "confirmed": false,
  "new_value": "Jane Smith"
}
```

#### Response (Next Question)
```json
{
  "status": "active",
  "question": {
    "id": "1.2",
    "text": "Please provide your date of birth.",
    "task_name": "REQUEST & RECEIVE INFORMATION",
    "subtask_name": "Personal Information",
    "field_name": "date_of_birth",
    "data_type": "date",
    "required": true
  },
  "current_answer": {
    "value": "1990-01-15",
    "exists": true,
    "confidence": 0.9
  },
  "progress": {
    "current_position": 2,
    "total_questions": 30,
    "percentage": 6.7
  },
  "previous_answer_saved": {
    "question_id": "1.1",
    "value": "Jane Smith"
  },
  "timestamp": 1733424810.456
}
```

#### Response (Workflow Complete)
```json
{
  "status": "complete",
  "message": "All questions answered! Workflow complete.",
  "total_answered": 30,
  "timestamp": 1733424900.789
}
```

---

### 3. **GET /workflow/status/{user_id}**

Get current workflow status and progress.

#### Request
```
GET /workflow/status/user123
```

#### Response (Active Workflow)
```json
{
  "status": "active",
  "current_question": {
    "id": "2.3",
    "text": "Is this ITIN still valid?",
    "task": 1,
    "subtask": 2
  },
  "progress": {
    "current_position": 8,
    "total_questions": 30,
    "percentage": 26.7
  },
  "answers_collected": 7,
  "completed_tasks": [],
  "completed_subtasks": [1],
  "timestamp": 1733424850.123
}
```

#### Response (Not Started)
```json
{
  "status": "not_started",
  "message": "No active workflow found",
  "timestamp": 1733424800.123
}
```

---

## 🎯 Usage Examples

### Example 1: Complete Workflow Flow

```bash
# Step 1: Start workflow
curl -X POST "http://localhost:8002/workflow/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "client_id": 456,
    "reference": "individual",
    "resume": true
  }'

# Response:
# {
#   "status": "active",
#   "question": {
#     "id": "1.1",
#     "text": "Can you confirm your full legal name?",
#     ...
#   },
#   "current_answer": {
#     "value": "John Doe",
#     "exists": true
#   },
#   ...
# }

# Step 2a: Answer is correct - confirm and move to next
curl -X POST "http://localhost:8002/workflow/next" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "confirmed": true
  }'

# Step 2b: Answer is incorrect - update and move to next
curl -X POST "http://localhost:8002/workflow/next" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "confirmed": false,
    "new_value": "Jane Smith"
  }'

# Step 3: Check status anytime
curl -X GET "http://localhost:8002/workflow/status/demo_user"
```

---

### Example 2: Python Client

```python
import requests

BASE_URL = "http://localhost:8002"
session_data = {
    "user_id": "user123",
    "client_id": 456,
    "reference": "individual"
}

# Start workflow
response = requests.post(f"{BASE_URL}/workflow/start", json=session_data)
data = response.json()

while data["status"] == "active":
    question = data["question"]
    current_answer = data["current_answer"]
    
    print(f"\nQuestion {question['id']}: {question['text']}")
    print(f"Current Answer: {current_answer.get('value', 'Not provided')}")
    
    # Simulate user input
    user_input = input("Is this correct? (y/n): ")
    
    if user_input.lower() == 'y':
        # Confirm and move to next
        response = requests.post(
            f"{BASE_URL}/workflow/next",
            json={
                "user_id": session_data["user_id"],
                "confirmed": True
            }
        )
    else:
        # Edit and move to next
        new_value = input("Enter correct value: ")
        response = requests.post(
            f"{BASE_URL}/workflow/next",
            json={
                "user_id": session_data["user_id"],
                "confirmed": False,
                "new_value": new_value
            }
        )
    
    data = response.json()

print("\n✅ Workflow Complete!")
print(f"Total questions answered: {data.get('total_answered')}")
```

---

### Example 3: JavaScript/TypeScript Client

```typescript
const BASE_URL = "http://localhost:8002";

interface WorkflowSession {
  user_id: string;
  client_id: number;
  reference: "individual" | "company";
}

async function runWorkflow(session: WorkflowSession) {
  // Start workflow
  let response = await fetch(`${BASE_URL}/workflow/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(session)
  });
  
  let data = await response.json();
  
  while (data.status === "active") {
    const question = data.question;
    const currentAnswer = data.current_answer;
    
    console.log(`\nQuestion ${question.id}: ${question.text}`);
    console.log(`Current Answer: ${currentAnswer.value || "Not provided"}`);
    
    // Show to user and get confirmation
    const confirmed = await getUserConfirmation();
    
    if (confirmed) {
      // Move to next
      response = await fetch(`${BASE_URL}/workflow/next`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: session.user_id,
          confirmed: true
        })
      });
    } else {
      const newValue = await getUserInput();
      response = await fetch(`${BASE_URL}/workflow/next`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: session.user_id,
          confirmed: false,
          new_value: newValue
        })
      });
    }
    
    data = await response.json();
  }
  
  console.log("✅ Workflow Complete!");
}
```

---

## 🔄 Workflow State Management

### Redis Storage

The workflow state is automatically saved to Redis with 12-hour TTL:

```json
{
  "conversation:user123": {
    "messages": [...],
    "client_id": 456,
    "reference": "individual",
    "metadata": {
      "workflow_state": {
        "current_question_id": "2.3",
        "current_task": 1,
        "current_subtask": 2,
        "completed_tasks": [],
        "completed_subtasks": [1],
        "answers": {
          "1.1": {"value": "Jane Smith", "confirmed": true, "timestamp": 1733424800},
          "1.2": {"value": "1990-01-15", "confirmed": true, "timestamp": 1733424810}
        }
      }
    }
  }
}
```

### Resume Capability

Users can pause and resume:

1. **Pause**: Simply stop making requests
2. **Resume**: Call `/workflow/start` with `resume: true`
3. **Start Fresh**: Call `/workflow/start` with `resume: false`

---

## 🔒 Security & Validation

### Input Validation

All endpoints validate:
- ✅ `user_id` is not empty
- ✅ `client_id` is valid integer
- ✅ `reference` is "individual" or "company"
- ✅ Answer values match expected data types
- ✅ ITIN format: `9XX-XX-XXXX`
- ✅ Date format: `YYYY-MM-DD`

### Error Responses

```json
{
  "detail": "User ID cannot be empty"
}
// Status: 400 Bad Request

{
  "detail": "No active workflow found. Please start workflow first."
}
// Status: 400 Bad Request

{
  "detail": "Invalid ITIN format (9XX-XX-XXXX)"
}
// Status: 400 Bad Request

{
  "detail": "Error updating database: connection timeout"
}
// Status: 500 Internal Server Error
```

---

## 📊 Testing the API

### Using Swagger UI

1. Start server: `python app.py`
2. Open browser: `http://localhost:8002/docs`
3. Try the new `/workflow/*` endpoints interactively

### Using Postman

1. Import collection from:
   - Base URL: `http://localhost:8002`
   - Endpoints: `/workflow/start`, `/workflow/next`, `/workflow/status/{user_id}`

### Using curl

See examples above in "Usage Examples" section.

---

## 🚀 Deployment Notes

### Environment Variables

No new environment variables needed! Uses existing:
```env
OPENAI_API_KEY=sk-...
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=...
DB_NAME=...
HOST=redis-host  # Redis
PORT=6379
PASSWORD=redis-password
```

### Starting the Server

```bash
# Development
python app.py

# Production with gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8002
```

---

## 🎯 Comparison: Old vs New

### Old Endpoint (Still Available)
```bash
# Free-form Q&A
POST /chat/agent
{
  "user_id": "user123",
  "client_id": 456,
  "reference": "individual",
  "query": "What is my full name in your records?"
}
```

### New Workflow Endpoint
```bash
# Guided workflow with structured questions
POST /workflow/start
{
  "user_id": "user123",
  "client_id": 456,
  "reference": "individual"
}
# Returns: Question 1.1 with auto-fetched answer
```

---

## 💡 When to Use Which Endpoint?

| Use Case | Endpoint |
|----------|----------|
| User asks random tax questions | `/chat/agent` |
| User wants to complete full 1040NR workflow | `/workflow/start` |
| User needs to update specific information | `/workflow/start` (or `/chat/agent`) |
| You need structured data collection | `/workflow/start` + `/workflow/next` |
| You want to track completion progress | `/workflow/status` |

---

## 🎉 Benefits of New Endpoints

1. **Structured Data Collection**: Ensures all 45 questions are asked
2. **Progress Tracking**: Know exactly how far users have progressed
3. **Automatic Validation**: Validates answers before saving
4. **Database Updates**: Automatically updates incorrect data
5. **Resume Capability**: Users can pause and resume anytime
6. **Conditional Logic**: Skips irrelevant questions (e.g., ITIN path)

---

## 📞 Need Help?

- **API Documentation**: `http://localhost:8002/docs`
- **Error Logs**: Check console output from `python app.py`
- **Redis Inspection**: `redis-cli GET conversation:user123`

---

**Your API server now has both simple Q&A and structured workflow capabilities!** 🚀
