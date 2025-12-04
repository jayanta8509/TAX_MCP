from mcp_functions import get_individual_residency_and_citizenship


def main() -> None:
    print("\n TEST: get_individual_residency_and_citizenship")

    sample_individual_client_id = 8

    result = get_individual_residency_and_citizenship(sample_individual_client_id, "individual")
    if result is None:
        print("No residency/citizenship info found for individual (client_id =",
              sample_individual_client_id, ")")
    else:
        print("Residency & citizenship info for individual:")
        for k, v in result.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
