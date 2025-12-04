from mcp_functions import get_individual_identity_and_tax_id


def main() -> None:
    print("\nTEST: get_individual_identity_and_tax_id--")
    sample_individual_client_id = 8
    result = get_individual_identity_and_tax_id(
        client_id=sample_individual_client_id,
        reference="individual",
    )

    print(f"\nInput -> client_id={sample_individual_client_id}, reference='individual'\n")

    if result is None:
        print("No identity / tax ID record found for this individual client.")
    else:
        print("Identity & Tax ID data retrieved successfully:")
        for key, value in result.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
