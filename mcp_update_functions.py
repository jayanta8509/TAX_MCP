from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING, List
from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    from mysql.connector.connection import MySQLConnection

from connection import get_connection

mcp = FastMCP("Data_Updater")


#helpers

def _get_table_and_pk(reference: str) -> Tuple[str, str]:
    ref = reference.lower()
    if ref == "company":
        return "company", "company_id"
    elif ref == "individual":
        return "individual", "id"
    else:
        raise ValueError(f"Unsupported reference type: {reference!r}")


def _resolve_reference_id(
    conn: get_connection,
    client_id: int,
    reference: str,
) -> int:
    ref_type = reference.lower()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT reference_id
        FROM internal_data
        WHERE id = %s AND reference = %s
        LIMIT 1
        """,
        (client_id, ref_type),
    )
    row = cursor.fetchone()
    if row and row.get("reference_id") is not None:
        return int(row["reference_id"])
    return client_id


def _build_update_query(
    table: str,
    pk_col: str,
    pk_value: int,
    fields: Dict[str, Any],
) -> Optional[Tuple[str, List[Any]]]:
    if not fields:
        return None

    set_clauses = []
    params: List[Any] = []

    for col, val in fields.items():
        set_clauses.append(f"{col} = %s")
        params.append(val)

    query = f"""
        UPDATE {table}
        SET {", ".join(set_clauses)}
        WHERE {pk_col} = %s
        LIMIT 1
    """
    params.append(pk_value)
    return query, params


# Update individual identity & tax/residency

@mcp.tool()
def get_master_languages_and_countries() -> Dict[str, Any]:
    """
    Purpose:
        Provide the MCP / chatbot with a complete view of the languages and
        countries master data, so it can map between human-friendly names
        (e.g. "India", "Brazil", "Japanese") and their corresponding IDs
        in the database.

        This function does NOT update anything. It is a read-only helper
        that is typically called internally by the assistant before or
        during update flows such as:
            - "Change my current country of residence to India"
            - "Set my language to Japanese"

    Args:
        None

    Returns:
        dict:
            {
                "languages": [
                    {
                        "id": int,
                        "language": str,
                        "status": int,
                    },
                    ...
                ],
                "countries": [
                    {
                        "id": int,
                        "country_code": str | None,
                        "country_phone_code": str | None,
                        "country_name": str,
                        "sort_order": int | None,
                    },
                    ...
                ],
            }

    Example usage:
        >>> master = get_master_languages_and_countries()
        >>> langs = master["languages"]
        >>> countries = master["countries"]

    Example questions this function helps answer (for the bot, internally):
        - "Which language_id corresponds to Japanese?"
        - "Which country id corresponds to India or Brazil?"
        - "What are all supported countries and languages in this system?"
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                language,
                status
            FROM languages
            ORDER BY language ASC
            """
        )
        languages = cursor.fetchall() or []

        cursor.execute(
            """
            SELECT
                id,
                country_code,
                country_phone_code,
                country_name,
                sort_order
            FROM countries
            ORDER BY country_name ASC
            """
        )
        countries = cursor.fetchall() or []

    return {
        "languages": languages,
        "countries": countries,
    }


@mcp.tool()
def update_individual_identity_and_tax_id(
    client_id: int,
    reference: str,
    first_name: Optional[str] = None,
    middle_name: Optional[str] = None,
    last_name: Optional[str] = None,
    birth_date: Optional[str] = None,
    ssn_itin_type: Optional[str] = None,
    ssn_itin: Optional[str] = None,
    language_id: Optional[int] = None,
    country_residence_id: Optional[int] = None,
    country_citizenship_id: Optional[int] = None,
    filing_status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Purpose:
        Update basic identity, tax ID, and residency fields for an individual
        client. Only non-None arguments are updated.

    Args:
        client_id (int):
            Global client ID.
        reference (str):
            Expected to be "individual". If not, no update is performed.
        first_name / middle_name / last_name (str | None):
            Update name components if provided.
        birth_date (str | None):
            Date of birth in "YYYY-MM-DD" format; updated if provided.
        ssn_itin_type (str | None):
            Type of tax ID, e.g. "SSN", "ITIN".
        ssn_itin (str | None):
            The SSN/ITIN value (stored as-is, so ensure validation upstream).
        language_id (int | None):
            ID from the languages master table.
        country_residence_id (int | None):
            ID from the countries master table for place of residence.
        country_citizenship_id (int | None):
            ID from the countries master table for citizenship.
        filing_status (str | None):
            Filing status text (e.g. "Single", "Married Filing Jointly").

    Returns:
        dict:
            {
                "reference": "individual",
                "client_id": <global id>,
                "reference_id": <individual.id>,
                "success": bool,
                "updated_fields": [list of column names updated],
                "rows_affected": int,
                "message": str,
            }
    """
    ref_type = reference.lower()
    if ref_type != "individual":
        return {
            "reference": ref_type,
            "client_id": client_id,
            "success": False,
            "updated_fields": [],
            "rows_affected": 0,
            "message": "update_individual_identity_and_tax_id only supports reference='individual'.",
        }

    table, pk_col = _get_table_and_pk(ref_type)

    with get_connection() as conn:
        resolved_id = _resolve_reference_id(conn, client_id, ref_type)

        fields: Dict[str, Any] = {}
        if first_name is not None:
            fields["first_name"] = first_name
        if middle_name is not None:
            fields["middle_name"] = middle_name
        if last_name is not None:
            fields["last_name"] = last_name
        if birth_date is not None:
            fields["birth_date"] = birth_date
        if ssn_itin_type is not None:
            fields["ssn_itin_type"] = ssn_itin_type
        if ssn_itin is not None:
            fields["ssn_itin"] = ssn_itin
        if language_id is not None:
            fields["language"] = language_id
        if country_residence_id is not None:
            fields["country_residence"] = country_residence_id
        if country_citizenship_id is not None:
            fields["country_citizenship"] = country_citizenship_id
        if filing_status is not None:
            fields["filing_status"] = filing_status

        built = _build_update_query(table, pk_col, resolved_id, fields)
        if not built:
            return {
                "reference": ref_type,
                "client_id": client_id,
                "reference_id": resolved_id,
                "success": False,
                "updated_fields": [],
                "rows_affected": 0,
                "message": "No fields provided to update.",
            }

        query, params = built
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

        return {
            "reference": ref_type,
            "client_id": client_id,
            "reference_id": resolved_id,
            "success": cursor.rowcount > 0,
            "updated_fields": list(fields.keys()),
            "rows_affected": cursor.rowcount,
            "message": "Update applied." if cursor.rowcount > 0 else "No rows updated.",
        }


#Update company basic profile

@mcp.tool()
def update_company_basic_profile(
    client_id: int,
    reference: str,
    name: Optional[str] = None,
    dba: Optional[str] = None,
    fein: Optional[str] = None,
    email: Optional[str] = None,
    fax: Optional[str] = None,
    contact_name: Optional[str] = None,
    principal_activity: Optional[str] = None,
    business_description: Optional[str] = None,
    website: Optional[str] = None,
    state_others: Optional[str] = None,
    services: Optional[str] = None,
    individuals: Optional[str] = None,
    fye: Optional[int] = None,
    filing_status: Optional[str] = None,
    filling_status: Optional[str] = None,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Purpose:
        Update basic profile fields for a company client (business client).
        Only non-None arguments are updated.

    Args:
        client_id (int):
            Global client ID (usually internal_data.id for company).
        reference (str):
            Expected to be "company".
        name, dba, fein, email, fax, contact_name (str | None):
            Basic identity and contact fields.
        principal_activity, business_description, website, state_others,
        services, individuals (str | None):
            Business activity and descriptive fields.
        fye (int | None):
            Fiscal year end (e.g. 12 for December).
        filing_status, filling_status (str | None):
            Filing status fields.
        message (str | None):
            Free-form message/notes.

    Returns:
        dict with success status and which fields were updated.
    """
    ref_type = reference.lower()
    if ref_type != "company":
        return {
            "reference": ref_type,
            "client_id": client_id,
            "success": False,
            "updated_fields": [],
            "rows_affected": 0,
            "message": "update_company_basic_profile only supports reference='company'.",
        }

    table, pk_col = _get_table_and_pk(ref_type)

    with get_connection() as conn:
        resolved_id = _resolve_reference_id(conn, client_id, ref_type)

        fields: Dict[str, Any] = {}
        if name is not None:
            fields["name"] = name
        if dba is not None:
            fields["dba"] = dba
        if fein is not None:
            fields["fein"] = fein
        if email is not None:
            fields["email"] = email
        if fax is not None:
            fields["fax"] = fax
        if contact_name is not None:
            fields["contact_name"] = contact_name
        if principal_activity is not None:
            fields["principal_activity"] = principal_activity
        if business_description is not None:
            fields["business_description"] = business_description
        if website is not None:
            fields["website"] = website
        if state_others is not None:
            fields["state_others"] = state_others
        if services is not None:
            fields["services"] = services
        if individuals is not None:
            fields["individuals"] = individuals
        if fye is not None:
            fields["fye"] = fye
        if filing_status is not None:
            fields["filing_status"] = filing_status
        if filling_status is not None:
            fields["filling_status"] = filling_status
        if message is not None:
            fields["message"] = message

        built = _build_update_query(table, pk_col, resolved_id, fields)
        if not built:
            return {
                "reference": ref_type,
                "client_id": client_id,
                "reference_id": resolved_id,
                "success": False,
                "updated_fields": [],
                "rows_affected": 0,
                "message": "No fields provided to update.",
            }

        query, params = built
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

        return {
            "reference": ref_type,
            "client_id": client_id,
            "reference_id": resolved_id,
            "success": cursor.rowcount > 0,
            "updated_fields": list(fields.keys()),
            "rows_affected": cursor.rowcount,
            "message": "Update applied." if cursor.rowcount > 0 else "No rows updated.",
        }


#Update primary contact info (contact_info)

@mcp.tool()
def update_client_primary_contact_info(
    client_id: int,
    reference: str,
    first_name: Optional[str] = None,
    middle_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone1_country: Optional[int] = None,
    phone1: Optional[str] = None,
    phone2_country: Optional[int] = None,
    phone2: Optional[str] = None,
    email1: Optional[str] = None,
    email2: Optional[str] = None,
    whatsapp_country: Optional[int] = None,
    whatsapp: Optional[str] = None,
    website: Optional[str] = None,
    address1: Optional[str] = None,
    address2: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    country_id: Optional[int] = None,
    company_name: Optional[str] = None,
    status: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Purpose:
        Update the primary contact_info record for a client. If a contact row
        exists for (reference, reference_id), we update the "top" contact
        (ORDER BY status DESC, id ASC). Only non-None fields are updated.

    Args:
        client_id (int):
            Global client ID (internal_data.id if available).
        reference (str):
            "company" or "individual".
        ... (all other args are optional fields to update and map directly
            to contact_info columns, with slight renaming for zip_code/country_id).

    Returns:
        dict:
            {
                "reference": "company" | "individual",
                "client_id": <global id>,
                "reference_id": <underlying id>,
                "contact_id": <contact_info.id or None>,
                "success": bool,
                "updated_fields": [...],
                "rows_affected": int,
                "message": str,
            }
    """
    ref_type = reference.lower()

    with get_connection() as conn:
        resolved_id = _resolve_reference_id(conn, client_id, ref_type)
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM contact_info
            WHERE reference = %s
              AND reference_id = %s
            ORDER BY status DESC, id ASC
            LIMIT 1
            """,
            (ref_type, resolved_id),
        )
        existing = cursor.fetchone()

        if not existing:
            return {
                "reference": ref_type,
                "client_id": client_id,
                "reference_id": resolved_id,
                "contact_id": None,
                "success": False,
                "updated_fields": [],
                "rows_affected": 0,
                "message": "No existing contact_info record found to update.",
            }

        contact_id = existing["id"]

        fields: Dict[str, Any] = {}
        if first_name is not None:
            fields["first_name"] = first_name
        if middle_name is not None:
            fields["middle_name"] = middle_name
        if last_name is not None:
            fields["last_name"] = last_name
        if phone1_country is not None:
            fields["phone1_country"] = phone1_country
        if phone1 is not None:
            fields["phone1"] = phone1
        if phone2_country is not None:
            fields["phone2_country"] = phone2_country
        if phone2 is not None:
            fields["phone2"] = phone2
        if email1 is not None:
            fields["email1"] = email1
        if email2 is not None:
            fields["email2"] = email2
        if whatsapp_country is not None:
            fields["whats_app_country"] = whatsapp_country
        if whatsapp is not None:
            fields["whatsapp"] = whatsapp
        if website is not None:
            fields["website"] = website
        if address1 is not None:
            fields["address1"] = address1
        if address2 is not None:
            fields["address2"] = address2
        if city is not None:
            fields["city"] = city
        if state is not None:
            fields["state"] = state
        if zip_code is not None:
            fields["zip"] = zip_code
        if country_id is not None:
            fields["country"] = country_id
        if company_name is not None:
            fields["company"] = company_name
        if status is not None:
            fields["status"] = status

        built = _build_update_query("contact_info", "id", contact_id, fields)
        if not built:
            return {
                "reference": ref_type,
                "client_id": client_id,
                "reference_id": resolved_id,
                "contact_id": contact_id,
                "success": False,
                "updated_fields": [],
                "rows_affected": 0,
                "message": "No fields provided to update.",
            }

        query, params = built
        cursor2 = conn.cursor()
        cursor2.execute(query, params)
        conn.commit()

        return {
            "reference": ref_type,
            "client_id": client_id,
            "reference_id": resolved_id,
            "contact_id": contact_id,
            "success": cursor2.rowcount > 0,
            "updated_fields": list(fields.keys()),
            "rows_affected": cursor2.rowcount,
            "message": "Update applied." if cursor2.rowcount > 0 else "No rows updated.",
        }


#Update internal_data assignments

@mcp.tool()
def update_client_internal_assignments(
    client_id: int,
    reference: str,
    office: Optional[int] = None,
    brand_id: Optional[int] = None,
    partner: Optional[int] = None,
    manager: Optional[int] = None,
    assistant: Optional[int] = None,
    property_manager: Optional[str] = None,
    client_association: Optional[str] = None,
    practice_id: Optional[str] = None,
    referred_by_source: Optional[int] = None,
    referred_by_name: Optional[str] = None,
    language_id: Optional[int] = None,
    status: Optional[int] = None,
    tenant_id: Optional[str] = None,
    customer_vault_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Purpose:
        Update internal assignment-related fields in internal_data for a client.
        This covers office/brand/partner/manager/assistant, property manager,
        practice_id, referral info, language, tenantId, and customer_vault_id.

    Args:
        client_id (int):
            Global client ID (usually internal_data.id).
        reference (str):
            "company" or "individual".
        All other fields are optional and applied only if non-None.

    Returns:
        dict:
            {
                "reference": "company" | "individual",
                "client_id": <global id>,
                "internal_data_id": <internal_data.id or None>,
                "reference_id": <underlying id or None>,
                "success": bool,
                "updated_fields": [...],
                "rows_affected": int,
                "message": str,
            }
    """
    ref_type = reference.lower()

    with get_connection() as conn:
        resolved_id = _resolve_reference_id(conn, client_id, ref_type)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, reference_id
            FROM internal_data
            WHERE reference = %s
              AND reference_id = %s
            LIMIT 1
            """,
            (ref_type, resolved_id),
        )
        row = cursor.fetchone()
        if not row:
            return {
                "reference": ref_type,
                "client_id": client_id,
                "internal_data_id": None,
                "reference_id": resolved_id,
                "success": False,
                "updated_fields": [],
                "rows_affected": 0,
                "message": "No internal_data record found to update.",
            }

        internal_id = row["id"]

        fields: Dict[str, Any] = {}
        if office is not None:
            fields["office"] = office
        if brand_id is not None:
            fields["brand_id"] = brand_id
        if partner is not None:
            fields["partner"] = partner
        if manager is not None:
            fields["manager"] = manager
        if assistant is not None:
            fields["assistant"] = assistant
        if property_manager is not None:
            fields["property_manager"] = property_manager
        if client_association is not None:
            fields["client_association"] = client_association
        if practice_id is not None:
            fields["practice_id"] = practice_id
        if referred_by_source is not None:
            fields["referred_by_source"] = referred_by_source
        if referred_by_name is not None:
            fields["referred_by_name"] = referred_by_name
        if language_id is not None:
            fields["language"] = language_id
        if status is not None:
            fields["status"] = status
        if tenant_id is not None:
            fields["tenantId"] = tenant_id
        if customer_vault_id is not None:
            fields["customer_vault_id"] = customer_vault_id

        built = _build_update_query("internal_data", "id", internal_id, fields)
        if not built:
            return {
                "reference": ref_type,
                "client_id": client_id,
                "internal_data_id": internal_id,
                "reference_id": resolved_id,
                "success": False,
                "updated_fields": [],
                "rows_affected": 0,
                "message": "No fields provided to update.",
            }

        query, params = built
        cursor2 = conn.cursor()
        cursor2.execute(query, params)
        conn.commit()

        return {
            "reference": ref_type,
            "client_id": client_id,
            "internal_data_id": internal_id,
            "reference_id": resolved_id,
            "success": cursor2.rowcount > 0,
            "updated_fields": list(fields.keys()),
            "rows_affected": cursor2.rowcount,
            "message": "Update applied." if cursor2.rowcount > 0 else "No rows updated.",
        }


if __name__ == "__main__":
    mcp.run()
