"""
Test script for MCP functions - Direct database testing
This bypasses the MCP server and tests the database functions directly
"""
from mcp_functions import get_client_itin_number

def test_individual_identity_and_tax_id():
    client_id = "EUSEBIMARI1"
    reference = "individual"
    result = get_client_itin_number(client_id, reference)
    print(result)


if __name__ == "__main__":
    test_individual_identity_and_tax_id()
