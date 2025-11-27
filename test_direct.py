"""
Test script for MCP functions - Direct database testing
This bypasses the MCP server and tests the database functions directly
"""
from connection import get_connection

def test_client_basic_profile():
    """Test get_client_basic_profile function"""
    sample_company_id = 3
    sample_individual_id = 8
    
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Test company profile
        print("=== Company basic profile ===")
        query = """
            SELECT
                company_id AS client_id,
                name,
                dba,
                fein,
                email,
                status,
                filing_status,
                created_time,
                date_of_dissolution,
                total_amount
            FROM company
            WHERE company_id = %s
            LIMIT 1
        """
        cursor.execute(query, (sample_company_id,))
        company_row = cursor.fetchone()
        
        if company_row:
            company_profile = {
                "reference": "company",
                "client_id": company_row["client_id"],
                "display_name": company_row["name"],
                "legal_name": company_row["name"],
                "dba": company_row["dba"],
                "fein_or_ssn": company_row["fein"],
                "email": company_row["email"],
                "status": company_row["status"],
                "filing_status": company_row["filing_status"],
                "created_time": company_row["created_time"],
                "date_of_dissolution": company_row["date_of_dissolution"],
                "total_amount": company_row["total_amount"],
            }
            print(company_profile)
        else:
            print(f"No company found with ID {sample_company_id}")
        
        # Test individual profile
        print("\n=== Individual basic profile ===")
        query = """
            SELECT
                id AS client_id,
                first_name,
                middle_name,
                last_name,
                ssn_itin_type,
                ssn_itin,
                filing_status,
                status,
                created_time,
                date_of_dissolution,
                total_amount
            FROM individual
            WHERE id = %s
            LIMIT 1
        """
        cursor.execute(query, (sample_individual_id,))
        individual_row = cursor.fetchone()
        
        if individual_row:
            full_name_parts = [
                individual_row.get("first_name"),
                individual_row.get("middle_name"),
                individual_row.get("last_name"),
            ]
            display_name = " ".join([p for p in full_name_parts if p]).strip() or None
            
            individual_profile = {
                "reference": "individual",
                "client_id": individual_row["client_id"],
                "display_name": display_name,
                "first_name": individual_row["first_name"],
                "middle_name": individual_row["middle_name"],
                "last_name": individual_row["last_name"],
                "fein_or_ssn": individual_row["ssn_itin"],
                "ssn_itin_type": individual_row["ssn_itin_type"],
                "status": individual_row["status"],
                "filing_status": individual_row["filing_status"],
                "created_time": individual_row["created_time"],
                "date_of_dissolution": individual_row["date_of_dissolution"],
                "total_amount": individual_row["total_amount"],
            }
            print(individual_profile)
        else:
            print(f"No individual found with ID {sample_individual_id}")


if __name__ == "__main__":
    test_client_basic_profile()
