from mcp_functions import get_client_fiscal_profile


def main() -> None:
    print("\n TEST: get_client_fiscal_profile")

    sample_company_client_id = 4      
    sample_individual_client_id = 8 
      
    # Company Test
    print("\n  Company fiscal profile ")
    company_result = get_client_fiscal_profile(sample_company_client_id, "company")
    if company_result is None:
        print("No fiscal profile found for company (client_id =", sample_company_client_id, ")")
    else:
        print("Fiscal profile for company:")
        for k, v in company_result.items():
            print(f"{k}: {v}")

    #Individual test
    print("\n Individual fiscal profile:-")
    individual_result = get_client_fiscal_profile(sample_individual_client_id, "individual")
    if individual_result is None:
        print(" No fiscal profile found for individual (client_id =", sample_individual_client_id, ")")
    else:
        print("Fiscal profile for individual:")
        for k, v in individual_result.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
