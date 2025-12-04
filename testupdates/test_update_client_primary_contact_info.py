from mcp_update_functions import update_client_primary_contact_info


def main() -> None:
    print("\n=== TEST: update_client_primary_contact_info ===")
    sample_client_id = 625
    reference = "company"   # or "individual" 

    result = update_client_primary_contact_info(
        client_id=sample_client_id,
        reference=reference,
        # # Only non-None fields will be updated
        # first_name="Gabriel",
        # middle_name="P",
        # last_name="Lafitte",
        # phone1_country=230,
        # phone1="555-111-2222",
        email1="updated_email@yopmail.com",
        # address1="123 Updated St",
        # city="Updated City",
        # state="10",
        # zip_code="33065",
        # country_id=230,
        # company_name="Updated Company Name",
        # status=1,
    )

    print(f"\nInput -> client_id={sample_client_id}, reference='{reference}'\n")
    print("Result:")
    for k, v in result.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
