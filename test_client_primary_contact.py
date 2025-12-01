from mcp_functions import get_client_primary_contact
from connection import get_connection


def debug_raw_contact_rows(client_id: int, reference: str):
    print("\n RAW contact_info rows for client:-")
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM contact_info
            WHERE reference = %s AND reference_id = %s
            """,
            (reference.lower(), client_id)
        )
        rows = cursor.fetchall()

        if not rows:
            print("No contact_info records found at all!")
        else:
            for row in rows:
                print(row)


def main():
    print("\n TEST: get_client_primary_contact:-")

    client_id = 3             
    reference = "company"  

    debug_raw_contact_rows(client_id, reference)

    print("\n=== Function Output ===")
    result = get_client_primary_contact(client_id, reference)
    print(result)

    if result is None:
        print("\nFunction returned None — no primary contact found.")
    else:
        print("\nPrimary contact retrieved successfully!")
        for k, v in result.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
