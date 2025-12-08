# Conversational Workflow API - Usage Guide

## 🎯 Single Endpoint for Everything!

**Endpoint:** `POST /chat/workflow`

**Use the same format you already know:**
```json
{
  "user_id": "string",
  "client_id": 0,
  "reference": "string",
  "query": "string",
  "use_agent": true
}
```

---

## 🚀 Complete Example Flow

### Step 1: Start Workflow
```bash
POST http://localhost:8002/chat/workflow
```

**Request:**
```json
{
  "user_id": "jayanta234",
  "client_id": 8,
  "reference": "individual",
  "query": "start"
}
```

**Response:**
```json
{
  "response": "Hi! Let's start your 1040NR filing. **Can you confirm your full legal name?**\n\nI found your full legal name as: **Robert SEBASTIAO Da Elvis**\n\nIs this correct? Please reply with 'Yes' to confirm or provide the correct value.",
  "status_code": 200,
  "timestamp": 1733425800.123
}
```

---

### Step 2a: User Confirms (Answer is Correct)

**Request:**
```json
{
  "user_id": "jayanta234",
  "client_id": 8,
  "reference": "individual",
  "query": "Yes"
}
```

**Response:**
```json
{
  "response": "Great! **Please provide your date of birth.**\n\nI have your date of birth as: **1990-05-15**\n\nIs this correct? Reply 'Yes' to confirm or provide the correct value.\n\n_Progress: 2/31 (6.5%)_",
  "status_code": 200
}
```

---

### Step 2b: User Corrects (Answer is Wrong)

**Request:**
```json
{
  "user_id": "jayanta234",
  "client_id": 8,
  "reference": "individual",
  "query": "No, it's 1990-05-16"
}
```

**Response:**
```json
{
  "response": "Updated! Your date of birth is now **1990-05-16**.\n\n**What is your current U.S. address?**\n\nI have your us address as: **123 Main St, NY**\n\nIs this correct? Reply 'Yes' to confirm or provide the correct value.\n\n_Progress: 3/31 (9.7%)_",
  "status_code": 200
}
```

---

### Step 3: Continue Until Complete

**Request (continuous):**
```json
{
  "user_id": "jayanta234",
  "client_id": 8,
  "reference": "individual",
  "query": "Yes"  // or provide corrections
}
```

**Final Response (When Complete):**
```json
{
  "response": "🎉 **Congratulations!** You've completed all 31 questions for your 1040NR filing!\n\nYour information has been saved. We'll proceed with generating your tax return.",
  "status_code": 200
}
```

---

## 🎭 Natural Language Examples

Users can reply naturally:

| User Says | System Understands |
|-----------|-------------------|
| "Yes" | ✅ Confirmed |
| "Y" | ✅ Confirmed |
| "Correct" | ✅ Confirmed |
| "That's right" | ✅ Confirmed |
| "No" | ❌ Needs correction (asks for value) |
| "No, it's Jane Smith" | ❌ Updates to "Jane Smith" |
| "Jane Smith" | Updates to "Jane Smith" |
| "1990-05-16" | Updates to "1990-05-16" |

---

## 📝 Complete cURL Example

```bash
# Step 1: Start
curl -X POST "http://localhost:8002/chat/workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "jayanta234",
    "client_id": 8,
    "reference": "individual",
    "query": "start"
  }'

# Step 2: Confirm correct answer
curl -X POST "http://localhost:8002/chat/workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "jayanta234",
    "client_id": 8,
    "reference": "individual",
    "query": "yes"
  }'

# Step 3: Correct wrong answer
curl -X POST "http://localhost:8002/chat/workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "jayanta234",
    "client_id": 8,
    "reference": "individual",
    "query": "No, 1990-05-16"
  }'

# Step 4: Continue...
curl -X POST "http://localhost:8002/chat/workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "jayanta234",
    "client_id": 8,
    "reference": "individual",
    "query": "yes"
  }'
```

---

## 💻 JavaScript/Python Integration

### JavaScript Example

```javascript
const BASE_URL = "http://localhost:8002";

async function chatWorkflow(userId, clientId, reference, message) {
  const response = await fetch(`${BASE_URL}/chat/workflow`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      client_id: clientId,
      reference: reference,
      query: message,
      use_agent: true
    })
  });
  
  const data = await response.json();
  return data.response;
}

// Usage
async function runWorkflow() {
  let reply;
  
  // Start
  reply = await chatWorkflow("user123", 8, "individual", "start");
  console.log("System:", reply);
  
  // User confirms
  reply = await chatWorkflow("user123", 8, "individual", "yes");
  console.log("System:", reply);
  
  // User corrects
  reply = await chatWorkflow("user123", 8, "individual", "No, Jane Smith");
  console.log("System:", reply);
  
  // Keep going...
}
```

---

### Python Example

```python
import requests

BASE_URL = "http://localhost:8002"

def chat_workflow(user_id, client_id, reference, message):
    response = requests.post(
        f"{BASE_URL}/chat/workflow",
        json={
            "user_id": user_id,
            "client_id": client_id,
            "reference": reference,
            "query": message,
            "use_agent": True
        }
    )
    return response.json()["response"]

# Usage
user_id = "user123"
client_id = 8
reference = "individual"

# Start workflow
reply = chat_workflow(user_id, client_id, reference, "start")
print(f"System: {reply}")

while True:
    # Get user input
    user_input = input("You: ")
    
    if user_input.lower() == "quit":
        break
    
    # Send to workflow
    reply = chat_workflow(user_id, client_id, reference, user_input)
    print(f"\nSystem: {reply}\n")
    
    # Check if complete
    if "Congratulations" in reply:
        print("✅ Workflow Complete!")
        break
```

---

## 🔄 Workflow State Management

The endpoint automatically:
- ✅ Tracks which question user is on
- ✅ Saves all answers to Redis (12-hour TTL)
- ✅ Updates database when user provides corrections
- ✅ Shows progress with each question
- ✅ Handles resume (just send new message with same user_id)

---

## 🎯 Your Exact Use Case

```bash
# User starts
POST /chat/workflow
{
  "user_id": "jayanta234",
  "client_id": 8,
  "reference": "individual",
  "query": "start"
}
# → "Can you confirm your full legal name? I found 'Robert Elvis'. Is this correct?"

# User says no, wrong name
POST /chat/workflow
{
  "user_id": "jayanta234",
  "client_id": 8,
  "reference": "individual",
  "query": "No, it's Jane Smith"
}
# → "Updated! Your full legal name is now Jane Smith. Next question..."

# User confirms next answer
POST /chat/workflow
{
  "user_id": "jayanta234",
  "client_id": 8,
  "reference": "individual",
  "query": "yes"
}
# → "Great! Moving to next question..."
```

---

## ✅ Benefits

1. **Single Endpoint** - Only one URL to remember
2. **Natural Conversation** - Users chat like talking to a person
3. **Auto State Management** - System tracks progress automatically
4. **Auto Database Updates** - Corrections saved immediately
5. **Same Format** - Uses your existing request format

---

## 🚀 Ready to Use!

Your server is already running with this endpoint. Just call:

```bash
POST http://localhost:8002/chat/workflow
```

With your standard format! 🎉
