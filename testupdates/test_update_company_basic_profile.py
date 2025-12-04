from mcp_update_functions import update_company_basic_profile


def main() -> None:
    print("\n TEST: update_company_basic_profile ")
    sample_company_client_id = 3

    result = update_company_basic_profile(
        client_id=sample_company_client_id,
        reference="company",
        name="FASANO INVESTING LIMITED TEST",
        # dba="TestCo",
        # fein="12-3456789",
        # email="testco@example.com",
        # fax="555-123-4567",
        # contact_name="Test Contact",
        # principal_activity="Consulting",
        # business_description="Automation and AI consulting services.",
        # website="https://testco.example.com",
        # state_others="FL",
        # services="Tax Filing, Bookkeeping",
        # individuals="Owner 1; Owner 2",
        # fye=12,
        # filing_status="Active",
        # filling_status="Filed",
        # message="Updated via MCP test.",
    )

    print("\nInput -> client_id =", sample_company_client_id, ", reference='company'\n")
    print("Result:")
    for k, v in result.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
