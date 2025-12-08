# Workflow API Quick Reference

## 🚀 Complete Workflow Example

### Step 1: Start Workflow
```bash
POST http://localhost:8002/workflow/start
```
**Request:**
```json
{
  "user_id": "jayanta234",
  "client_id": 8,
  "reference": "individual",
  "resume": true
}
```

**Response:**
```json
{
  "status": "active",
  "question": {
    "id": "1.1",
    "text": "Can you confirm your full legal name?",
    "field_name": "full_legal_name"
  },
  "current_answer": {
    "value": "Robert SEBASTIAO Da Elvis",  // Now cleaned!
    "exists": true,
    "confidence": 0.9
  },
  "progress": {
    "current_position": 1,
    "total_questions": 31,
    "percentage": 3.2
  }
}
```

---

### Step 2a: Answer is CORRECT ✅
```bash
POST http://localhost:8002/workflow/next
```
**Request:**
```json
{
  "user_id": "jayanta234",
  "confirmed": true
}
```

**Response:** Next question (1.2)

---

### Step 2b: Answer is INCORRECT ❌ (Update Database)
```bash
POST http://localhost:8002/workflow/next
```
**Request:**
```json
{
  "user_id": "jayanta234",
  "confirmed": false,
  "new_value": "Jane Smith"
}
```

**Response:** 
- Database updated with "Jane Smith"
- Returns next question (1.2)

---

### Step 3: Check Progress Anytime
```bash
GET http://localhost:8002/workflow/status/jayanta234
```

**Response:**
```json
{
  "status": "active",
  "current_question": {
    "id": "2.3",
    "text": "Is this ITIN still valid?"
  },
  "progress": {
    "current_position": 8,
    "total_questions": 31,
    "percentage": 25.8
  },
  "answers_collected": 7
}
```

---

## 🎯 Complete Flow in cURL

```bash
# 1. Start workflow
curl -X POST "http://localhost:8002/workflow/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "jayanta234",
    "client_id": 8,
    "reference": "individual"
  }'

# 2a. Confirm correct answer
curl -X POST "http://localhost:8002/workflow/next" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "jayanta234",
    "confirmed": true
  }'

# 2b. Update incorrect answer
curl -X POST "http://localhost:8002/workflow/next" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "jayanta234",
    "confirmed": false,
    "new_value": "Correct Name Here"
  }'

# 3. Check status
curl -X GET "http://localhost:8002/workflow/status/jayanta234"
```

---

## 🔄 Frontend Integration Example

```javascript
const userId = "jayanta234";
const BASE_URL = "http://localhost:8002";

async function runWorkflow() {
  // 1. Start workflow
  let response = await fetch(`${BASE_URL}/workflow/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      client_id: 8,
      reference: "individual",
      resume: true
    })
  });
  
  let data = await response.json();
  
  // Loop through questions
  while (data.status === "active") {
    const question = data.question;
    const currentAnswer = data.current_answer;
    
    // Display to user
    console.log(`Question: ${question.text}`);
    console.log(`Current Answer: ${currentAnswer.value || "Not provided"}`);
    
    // Get user confirmation
    const isCorrect = confirm(`Is "${currentAnswer.value}" correct?`);
    
    if (isCorrect) {
      // Confirm and move to next
      response = await fetch(`${BASE_URL}/workflow/next`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          confirmed: true
        })
      });
    } else {
      // Get new value and update
      const newValue = prompt("Enter correct value:");
      response = await fetch(`${BASE_URL}/workflow/next`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          confirmed: false,
          new_value: newValue
        })
      });
    }
    
    data = await response.json();
  }
  
  console.log("✅ Workflow Complete!");
  console.log(`Total answers: ${data.total_answered}`);
}
```

---

## 📊 Question Types & Validation

| Question ID | Field | Data Type | Validation |
|------------|-------|-----------|------------|
| 1.1 | full_legal_name | string | Non-empty |
| 1.2 | date_of_birth | date | YYYY-MM-DD |
| 1.3 | us_address | string | Non-empty |
| 2.1 | has_itin | boolean | yes/no |
| 2.2 | itin_number | string | 9XX-XX-XXXX |
| 2.3 | itin_valid | boolean | yes/no |

---

## 🐛 Common Issues

### Issue: "No active workflow found"
**Solution:** Call `/workflow/start` first before `/workflow/next`

### Issue: "new_value is required when confirmed=False"
**Solution:** Always provide `new_value` when `confirmed: false`

### Issue: "Invalid ITIN format"
**Solution:** Use format `9XX-XX-XXXX` (e.g., `900-12-3456`)

### Issue: Answer shows extra text
**Solution:** ✅ Fixed! Now returns clean values like "Robert SEBASTIAO Da Elvis" instead of full sentences

---

## 🎯 Your Use Case (Name Update)

```bash
# You got this question with answer
{
  "question": { "id": "1.1", "text": "Can you confirm your full legal name?" },
  "current_answer": { "value": "Robert SEBASTIAO Da Elvis" }
}

# User says: "That's not my name, it's Jane Smith"
# Call this:
curl -X POST "http://localhost:8002/workflow/next" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "jayanta234",
    "confirmed": false,
    "new_value": "Jane Smith"
  }'

# What happens:
# 1. ✅ Database updates full_legal_name to "Jane Smith"
# 2. ✅ Workflow state saves the answer
# 3. ✅ Returns next question (1.2 - Date of Birth)
```

---

## 🔒 Important Notes

1. **Session Management**: `user_id` maintains the session across calls
2. **Resume**: Set `resume: false` in `/workflow/start` to start fresh
3. **Progress Saved**: All answers saved to Redis (12-hour TTL)
4. **Database Updates**: Automatically uses your MCP update tools
5. **Validation**: Input validated before database update

---

## ✅ Testing Checklist

- [x] Start workflow → Get question 1.1
- [ ] Confirm correct answer → Move to 1.2
- [ ] Update incorrect answer → Database updated, move to next
- [ ] Check status → See progress
- [ ] Complete all 31 questions → Workflow complete
