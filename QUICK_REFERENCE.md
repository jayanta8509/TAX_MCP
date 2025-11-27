# Tax Filing Assistant - Quick Reference

## Key Changes Summary

### Parameter Migration
```diff
- reference_id: str  # Old: arbitrary string ID
+ reference: str     # New: "company" or "individual"
```

### API Request Format
```json
{
  "user_id": "user_123",
  "client_id": 456,
  "reference": "individual",
  "query": "Help me file my 1040NR"
}
```

### MCP Functions Available
1. `get_client_basic_profile(client_id, reference)`
2. `get_client_primary_contact(client_id, reference)`
3. `get_client_all_contacts(client_id, reference)`
4. `get_client_financial_summary(client_id, reference)`
5. `get_client_mail_service_info(client_id, reference)`
6. `get_client_internal_data(client_id, reference)`

### Testing Commands
```bash
# Start MCP Server
python mcp_functions.py

# Start API Server
python -m uvicorn app:app --reload

# Test Request
curl -X POST "http://localhost:8000/chat/agent" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "client_id": 1,
    "reference": "individual",
    "query": "What is my basic profile?"
  }'
```

### Files Modified
- ✅ `client.py` - Complete transformation
- ✅ `app.py` - API updates
