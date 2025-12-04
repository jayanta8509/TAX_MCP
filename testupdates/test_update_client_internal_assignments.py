from mcp_update_functions import update_client_internal_assignments


def main() -> None:
    print("\n=== TEST: update_client_internal_assignments ===")

    sample_client_id = 127
    reference = "company"   # or "individual"

    result = update_client_internal_assignments(
        client_id=sample_client_id,
        reference=reference,
        # Only non-None fields will be updated
        # office=1,
        # brand_id=2,
        # partner=10,
        # manager=20,
        # assistant=30,
        property_manager="John Property",
        client_association="Primary",
        # practice_id="TAX-001",
        # referred_by_source=5,
        # referred_by_name="Referral Partner XYZ",
        # language_id=1,
        # status=1,
        # tenant_id="tenant-abc-123",
        # customer_vault_id="vault-xyz-789",
    )

    print(f"\nInput -> client_id={sample_client_id}, reference='{reference}'\n")
    print("Result:")
    for k, v in result.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
