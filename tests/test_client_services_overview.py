from mcp_functions import get_client_services_overview


def main() -> None:
    print("\n TEST: get_client_services_overview")

    sample_company_client_id = 4
    sample_individual_client_id = 8

    # Company test
    print("\n--- Company services overview ---")
    company_result = get_client_services_overview(sample_company_client_id, "company")
    if company_result is None:
        print(" No services overview found for company (client_id =", sample_company_client_id, ")")
    else:
        print(" Services overview for company:")
        for k, v in company_result.items():
            print(f"{k}: {v}")

    # Individual test
    print("\n--- Individual services overview ---")
    individual_result = get_client_services_overview(sample_individual_client_id, "individual")
    if individual_result is None:
        print(" No services overview found for individual (client_id =", sample_individual_client_id, ")")
    else:
        print(" Services overview for individual:")
        for k, v in individual_result.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
