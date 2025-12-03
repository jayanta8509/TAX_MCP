"""
Test script for MCP functions - Direct database testing
This bypasses the MCP server and tests the database functions directly
"""
from mcp_functions import get_client_primary_contact

def test_client_primary_contact():
    client_id = 3
    reference = "company"
    result = get_client_primary_contact(client_id, reference)
    print(result)


if __name__ == "__main__":
    test_client_primary_contact()
