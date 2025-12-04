from mcp_functions import get_client_team_assignment_details


def main() -> None:
    print("\nTEST: get_client_team_assignment_details")

    sample_company_client_id = 4
    sample_individual_client_id = 8

    # Company test 
    print("\nCompany team assignment")
    company_result = get_client_team_assignment_details(sample_company_client_id, "company")
    if company_result is None:
        print(" No team assignment found for company (client_id =", sample_company_client_id, ")")
    else:
        print("Team assignment for company:")
        for k, v in company_result.items():
            print(f"{k}: {v}")

    #Individual test
    print("\n Individual team assignment ")
    individual_result = get_client_team_assignment_details(sample_individual_client_id, "individual")
    if individual_result is None:
        print(" No team assignment found for individual (client_id =", sample_individual_client_id, ")")
    else:
        print(" Team assignment for individual:")
        for k, v in individual_result.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
