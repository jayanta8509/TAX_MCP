from pprint import pprint

from mcp_update_functions import (
    update_client_full_legal_name,
    update_client_date_of_birth,
    update_client_current_us_address,
    update_client_occupation_and_us_income_source,
    update_client_itin_number,
    update_company_fein_number,
    update_company_business_description,
)
PRACTICE_ID_INDIVIDUAL = "TAILORSTORY"
PRACTICE_ID_COMPANY = "FASANOINVES"
REF_INDIVIDUAL = "individual"
REF_COMPANY = "company"


def main():
    print("\n=== 1) Update Individual: Full Legal Name ===")
    pprint(update_client_full_legal_name(PRACTICE_ID_INDIVIDUAL, REF_INDIVIDUAL, "John Doe"))

    print("\n=== 2) Update Individual: Date of Birth ===")
    pprint(update_client_date_of_birth(PRACTICE_ID_INDIVIDUAL, REF_INDIVIDUAL, "1992-05-20"))

    print("\n=== 3) Update Individual: Current US Address ===")
    #country_id is countries.id (e.g. 230 for United States)
    pprint(
        update_client_current_us_address(
            practice_id=PRACTICE_ID_INDIVIDUAL,
            reference=REF_INDIVIDUAL,
            address1="123 Main St",
            address2="Apt 4B",
            city="Denver",
            state="Colorado",
            zip_code="80202",
            country_id=230,
        )
    )

    print("\n=== 4) Update Individual: Occupation + US Income Source ===")
    pprint(
        update_client_occupation_and_us_income_source(
            PRACTICE_ID_INDIVIDUAL,
            REF_INDIVIDUAL,
            occupation="Software Developer",
            source_of_us_income="Salary / Services rendered in the United States",
        )
    )

    print("\n=== 5) Update Individual: ITIN Number (set) ===")
    pprint(update_client_itin_number(PRACTICE_ID_INDIVIDUAL, REF_INDIVIDUAL, "912-34-5678"))

    print("\n=== 6) Update Individual: ITIN Number (clear) ===")
    pprint(update_client_itin_number(PRACTICE_ID_INDIVIDUAL, REF_INDIVIDUAL, ""))

    print("\n=== 7) Update Company: FEIN Number ===")
    pprint(update_company_fein_number(PRACTICE_ID_COMPANY, REF_COMPANY, "98-1335105"))

    print("\n=== 8) Update Company: Business Description ===")
    pprint(
        update_company_business_description(
            PRACTICE_ID_COMPANY,
            REF_COMPANY,
            "We provide consulting and professional services in the United States.",
        )
    )


if __name__ == "__main__":
    main()
