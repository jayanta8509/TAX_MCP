from mcp_update_functions import update_individual_identity_and_tax_id


def main() -> None:
    print("\n TEST: update_individual_identity_and_tax_id ")
    sample_individual_client_id = 8

    result = update_individual_identity_and_tax_id(
        client_id=sample_individual_client_id,
        reference="individual",
        first_name="RENATO",
        # middle_name="M",
        # last_name="User",
        birth_date="1974-04-28",     # YYYY-MM-DD
        # ssn_itin_type="SSN",
        # ssn_itin="123-45-6789",
        # language_id=1,               #languages.id
        # country_residence_id=31,    #countries.id
        # country_citizenship_id=31,  #countries.id
        # filing_status="Single",
    )

    print("\nInput -> client_id =", sample_individual_client_id, ", reference='individual'\n")
    print("Result:")
    for k, v in result.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
