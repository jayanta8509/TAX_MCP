from mcp_functions import get_client_origin_and_referral_info


def main() -> None:
    print("\n TEST: get_client_origin_and_referral_info ")

    sample_company_client_id = 4
    sample_individual_client_id = 8

    # Company test ----
    print("\nCompany origin & referral info")
    company_result = get_client_origin_and_referral_info(sample_company_client_id, "company")
    if company_result is None:
        print("No origin/referral info found for company (client_id =", sample_company_client_id, ")")
    else:
        print("Origin & referral info for company:")
        for k, v in company_result.items():
            print(f"{k}: {v}")

    #Individual test 
    print("\n--- Individual origin & referral info ---")
    individual_result = get_client_origin_and_referral_info(sample_individual_client_id, "individual")
    if individual_result is None:
        print("No origin/referral info found for individual (client_id =", sample_individual_client_id, ")")
    else:
        print("Origin & referral info for individual:")
        for k, v in individual_result.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
