"""
Test script for MCP functions - Direct database testing
This bypasses the MCP server and tests the database functions directly
"""
from mcp_functions import get_individual_identity_and_tax_id

def test_individual_identity_and_tax_id():
    client_id = 8
    reference = "individual"
    result = get_individual_identity_and_tax_id(client_id, reference)
    print(result)


if __name__ == "__main__":
    test_individual_identity_and_tax_id()
