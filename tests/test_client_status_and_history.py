from mcp_functions import get_client_status_and_history


def main() -> None:
    print("\n TEST: get_client_status_and_history")

    sample_company_client_id = 4
    sample_individual_client_id = 8

    #Company test
    print("\n--- Company status & history ---")
    company_result = get_client_status_and_history(sample_company_client_id, "company")
    if company_result is None:
        print(" No status/history found for company (client_id =", sample_company_client_id, ")")
    else:
        print(" Status & history for company:")
        for k, v in company_result.items():
            print(f"{k}: {v}")

    # Individual test 
    print("\n--- Individual status & history ---")
    individual_result = get_client_status_and_history(sample_individual_client_id, "individual")
    if individual_result is None:
        print(" No status/history found for individual (client_id =", sample_individual_client_id, ")")
    else:
        print(" Status & history for individual:")
        for k, v in individual_result.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
