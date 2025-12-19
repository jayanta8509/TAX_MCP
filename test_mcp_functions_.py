from pprint import pprint
from mcp_functions import (
    get_client_full_legal_name,
    get_client_date_of_birth,
    get_client_current_us_address,
    get_client_occupation_and_us_income_source,
    get_client_itin_exists,
    get_client_itin_number,
    get_company_fein_number,
    get_company_business_description,
)

def main():
    PRACTICE_ID_INDIVIDUAL = "TAILORSTORY"
    PRACTICE_ID_COMPANY = "FASANOINVES"
    REF_INDIVIDUAL = "individual"
    REF_COMPANY = "company"

    print("\n=== 1) Individual: Full Legal Name ===")
    pprint(get_client_full_legal_name(PRACTICE_ID_INDIVIDUAL, REF_INDIVIDUAL))

    print("\n=== 2) Company: Full Legal Name ===")
    pprint(get_client_full_legal_name(PRACTICE_ID_COMPANY, REF_COMPANY))

    print("\n=== 3) Individual: Date of Birth ===")
    pprint(get_client_date_of_birth(PRACTICE_ID_INDIVIDUAL, REF_INDIVIDUAL))

    print("\n=== 4) Individual: Current US Address ===")
    pprint(get_client_current_us_address(PRACTICE_ID_INDIVIDUAL, REF_INDIVIDUAL))

    print("\n=== 5) Company: Current US Address ===")
    pprint(get_client_current_us_address(PRACTICE_ID_COMPANY, REF_COMPANY))

    print("\n=== 6) Individual: Occupation + US Income Source ===")
    pprint(get_client_occupation_and_us_income_source(PRACTICE_ID_INDIVIDUAL, REF_INDIVIDUAL))

    print("\n=== 7) Company: Occupation + US Income Source ===")
    pprint(get_client_occupation_and_us_income_source(PRACTICE_ID_COMPANY, REF_COMPANY))

    print("\n=== 8) Individual: ITIN Exists? ===")
    pprint(get_client_itin_exists(PRACTICE_ID_INDIVIDUAL, REF_INDIVIDUAL))

    print("\n=== 9) Individual: ITIN Number ===")
    pprint(get_client_itin_number(PRACTICE_ID_INDIVIDUAL, REF_INDIVIDUAL))

    print("\n=== 10) Company: FEIN Number ===")
    pprint(get_company_fein_number(PRACTICE_ID_COMPANY, REF_COMPANY))

    print("\n=== 11) Company: Business Description ===")
    pprint(get_company_business_description(PRACTICE_ID_COMPANY, REF_COMPANY))


if __name__ == "__main__":
    main()
