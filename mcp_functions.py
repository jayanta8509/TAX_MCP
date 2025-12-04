import os
from mcp.server.fastmcp import FastMCP
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from mysql.connector.connection import MySQLConnection

from connection import get_connection

mcp = FastMCP("Data_Fetcher")


def _get_table_and_pk(reference: str) -> Tuple[str, str]:
    """
    Internal helper: map reference string to table and primary key column.
    """
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


@mcp.tool()
def get_client_basic_profile(
    client_id: int,
    reference: str,
) -> Optional[Dict[str, Any]]:
    """
    Purpose:
        Retrieve a basic profile for a specific client (business or individual),
        including key identity and status fields that are most relevant for
        a client-facing chatbot.

    Args:
        client_id (int):
            The primary key ID of the client in the corresponding table.
            For business clients this is company.company_id,
            for individual clients this is individual.id.
        reference (str):
            The type of client to look up. Expected values:
            - "company" for business clients
            - "individual" for individual clients

    Returns:
        dict | None:
            A dictionary with a normalized shape, or None if no client is found.
    """
    table, pk_col = _get_table_and_pk(reference)

    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        if table == "company":
            query = f"""
                SELECT
                    {pk_col} AS client_id,
                    name,
                    dba,
                    fein,
                    email,
                    status,
                    filing_status,
                    created_time,
                    date_of_dissolution,
                    total_amount
                FROM {table}
                WHERE {pk_col} = %s
                LIMIT 1
            """
            cursor.execute(query, (client_id,))
            row = cursor.fetchone()
            if not row:
                return None

            return {
                "reference": "company",
                "client_id": row["client_id"],
                "display_name": row["name"],
                "legal_name": row["name"],
                "dba": row["dba"],
                "fein_or_ssn": row["fein"],
                "email": row["email"],
                "status": row["status"],
                "filing_status": row["filing_status"],
                "created_time": str(row["created_time"]),
                "date_of_dissolution": str(row["date_of_dissolution"]) if row["date_of_dissolution"] else None,
                "total_amount": float(row["total_amount"]),
            }

        elif table == "individual":
            query = f"""
                SELECT
                    {pk_col} AS client_id,
                    first_name,
                    middle_name,
                    last_name,
                    ssn_itin_type,
                    ssn_itin,
                    filing_status,
                    status,
                    created_time,
                    date_of_dissolution,
                    total_amount
                FROM {table}
                WHERE {pk_col} = %s
                LIMIT 1
            """
            cursor.execute(query, (client_id,))
            row = cursor.fetchone()
            if not row:
                return None

            full_name_parts = [
                row.get("first_name"),
                row.get("middle_name"),
                row.get("last_name"),
            ]
            display_name = " ".join([p for p in full_name_parts if p]).strip() or None

            return {
                "reference": "individual",
                "client_id": row["client_id"],
                "display_name": display_name,
                "first_name": row["first_name"],
                "middle_name": row["middle_name"],
                "last_name": row["last_name"],
                "fein_or_ssn": row["ssn_itin"],
                "ssn_itin_type": row["ssn_itin_type"],
                "status": row["status"],
                "filing_status": row["filing_status"],
                "created_time": str(row["created_time"]),
                "date_of_dissolution": str(row["date_of_dissolution"]) if row["date_of_dissolution"] else None,
                "total_amount": float(row["total_amount"]),
            }
        else:
            return None


@mcp.tool()
def get_client_primary_contact(
    client_id: int,
    reference: str,
) -> Optional[Dict[str, Any]]:
    """
    Retrieve the primary contact information for a client.
    
    Returns contact name, email, phone, and address details.
    """
    ref_type = reference.lower()

    with get_connection() as conn:
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
        internal_row = cursor.fetchone()

        if internal_row and internal_row.get("reference_id") is not None:
            resolved_reference_id = internal_row["reference_id"]
        else:
            resolved_reference_id = client_id

        query = """
            SELECT 
                CONCAT(
                    COALESCE(first_name, ''), 
                    CASE 
                        WHEN (first_name IS NOT NULL AND first_name <> '' 
                              AND last_name IS NOT NULL AND last_name <> '') 
                        THEN ' ' 
                        ELSE '' 
                    END,
                    COALESCE(last_name, '')
                ) AS name,
                email1 AS email,
                phone1 AS phone,
                address1 AS address,
                city,
                state,
                zip,
                country
            FROM contact_info
            WHERE reference = %s AND reference_id = %s
            ORDER BY status DESC, id ASC
            LIMIT 1
        """
        cursor.execute(query, (ref_type, resolved_reference_id))
        row = cursor.fetchone()

        if not row:
            return None

        return {
            "reference": ref_type,
            "client_id": client_id,                
            "reference_id": resolved_reference_id,
            "name": (row.get("name") or "").strip(),
            "email": row.get("email"),
            "phone": row.get("phone"),
            "address": row.get("address"),
            "city": row.get("city"),
            "state": row.get("state"),
            "zip": row.get("zip"),
            "country": row.get("country"),
        }


@mcp.tool()
def get_client_all_contacts(
    client_id: int,
    reference: str,
) -> List[Dict[str, Any]]:
    """
    Retrieve all contact records for a client.
    
    Returns a list of all contacts associated with the client.
    """
    # Normalize reference
    ref_type = reference.lower()
    
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                CONCAT(COALESCE(first_name, ''), ' ', COALESCE(last_name, '')) as name,
                email1 as email,
                phone1 as phone,
                address1 as address,
                city,
                state,
                zip,
                country
            FROM contact_info
            WHERE reference = %s AND reference_id = %s
        """
        cursor.execute(query, (ref_type, client_id))
        rows = cursor.fetchall()
        
        return [
            {
                "reference": ref_type,
                "client_id": client_id,
                "name": row.get("name", "").strip(),
                "email": row.get("email"),
                "phone": row.get("phone"),
                "address": row.get("address"),
                "city": row.get("city"),
                "state": row.get("state"),
                "zip": row.get("zip"),
                "country": row.get("country"),
            }
            for row in rows
        ]


@mcp.tool()
def get_client_financial_summary(
    client_id: int,
    reference: str,
) -> Optional[Dict[str, Any]]:
    """
    Retrieve financial summary for a client.
    
    Returns total_amount, status, and temp_client flag.
    """
    table, pk_col = _get_table_and_pk(reference)
    
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        query = f"""
            SELECT 
                total_amount, status, temp_client
            FROM {table}
            WHERE {pk_col} = %s
            LIMIT 1
        """
        cursor.execute(query, (client_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        return {
            "reference": reference,
            "client_id": client_id,
            "total_amount": float(row.get("total_amount", 0)),
            "status": row.get("status"),
            "temp_client": row.get("temp_client"),
        }


@mcp.tool()
def get_client_mail_service_info(
    client_id: int,
    reference: str,
) -> Optional[Dict[str, Any]]:
    """
    Retrieve mail service information for a client.
    
    Returns mail service status, start/due dates, and late fee information.
    """
    table, pk_col = _get_table_and_pk(reference)
    
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        query = f"""
            SELECT 
                mail_service, mail_service_start_date, mail_service_due_date,
                late_fee, why_client_left
            FROM {table}
            WHERE {pk_col} = %s
            LIMIT 1
        """
        cursor.execute(query, (client_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        return {
            "reference": reference,
            "client_id": client_id,
            "mail_service_status": row.get("mail_service"),
            "mail_service_start_date": str(row.get("mail_service_start_date")) if row.get("mail_service_start_date") else None,
            "mail_service_due_date": str(row.get("mail_service_due_date")) if row.get("mail_service_due_date") else None,
            "late_fee_status": row.get("late_fee"),
            "why_client_left": row.get("why_client_left"),
        }


@mcp.tool()
def get_client_internal_data(
    client_id: int,
    reference: str,
) -> Optional[Dict[str, Any]]:
    """
    Retrieve internal data for a client.
    
    Returns office, manager, partner assignments, and practice_id.
    """
    table, pk_col = _get_table_and_pk(reference)
    
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        query = f"""
            SELECT 
                office, manager, partner, practice_id
            FROM {table}
            WHERE {pk_col} = %s
            LIMIT 1
        """
        cursor.execute(query, (client_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        return {
            "reference": reference,
            "client_id": client_id,
            "office": row.get("office"),
            "manager": row.get("manager"),
            "partner": row.get("partner"),
            "practice_id": row.get("practice_id"),
        }



# //new-func

@mcp.tool()
def get_client_fiscal_profile(
    client_id: int,
    reference: str,
) -> Optional[Dict[str, Any]]:
    
    ref_type = reference.lower()
    table, pk_col = _get_table_and_pk(ref_type)

    with get_connection() as conn:
        resolved_id = _resolve_reference_id(conn, client_id, ref_type)
        cursor = conn.cursor(dictionary=True)

        if ref_type == "company":
            query = f"""
                SELECT
                    {pk_col} AS reference_id,
                    fye,
                    start_month_year,
                    filing_status,
                    filling_status,
                    incorporated_date
                FROM {table}
                WHERE {pk_col} = %s
                LIMIT 1
            """
            cursor.execute(query, (resolved_id,))
            row = cursor.fetchone()
            if not row:
                return None

            return {
                "reference": ref_type,
                "client_id": client_id,
                "reference_id": row["reference_id"],
                "fye": row.get("fye"),
                "start_month_year": row.get("start_month_year"),
                "filing_status": row.get("filing_status"),
                "filling_status": row.get("filling_status"),
                "incorporated_date": (
                    str(row["incorporated_date"])
                    if row.get("incorporated_date")
                    else None
                ),
            }

        elif ref_type == "individual":
            query = f"""
                SELECT
                    {pk_col} AS reference_id,
                    filing_status,
                    birth_date
                FROM {table}
                WHERE {pk_col} = %s
                LIMIT 1
            """
            cursor.execute(query, (resolved_id,))
            row = cursor.fetchone()
            if not row:
                return None

            return {
                "reference": ref_type,
                "client_id": client_id,
                "reference_id": row["reference_id"],
                "filing_status": row.get("filing_status"),
                "birth_date": (
                    str(row["birth_date"])
                    if row.get("birth_date")
                    else None
                ),
            }

        return None


@mcp.tool()
def get_client_services_overview(
    client_id: int,
    reference: str,
) -> Optional[Dict[str, Any]]:
    ref_type = reference.lower()
    table, pk_col = _get_table_and_pk(ref_type)

    with get_connection() as conn:
        resolved_id = _resolve_reference_id(conn, client_id, ref_type)
        cursor = conn.cursor(dictionary=True)

        if ref_type == "company":
            query = f"""
                SELECT
                    {pk_col} AS reference_id,
                    services,
                    principal_activity,
                    business_description,
                    website,
                    individuals
                FROM {table}
                WHERE {pk_col} = %s
                LIMIT 1
            """
            cursor.execute(query, (resolved_id,))
            row = cursor.fetchone()
            if not row:
                return None

            return {
                "reference": ref_type,
                "client_id": client_id,
                "reference_id": row["reference_id"],
                "services": row.get("services"),
                "principal_activity": row.get("principal_activity"),
                "business_description": row.get("business_description"),
                "website": row.get("website"),
                "individuals": row.get("individuals"),
            }

        elif ref_type == "individual":
            query = f"""
                SELECT
                    {pk_col} AS reference_id,
                    type,
                    language
                FROM {table}
                WHERE {pk_col} = %s
                LIMIT 1
            """
            cursor.execute(query, (resolved_id,))
            row = cursor.fetchone()
            if not row:
                return None

            return {
                "reference": ref_type,
                "client_id": client_id,
                "reference_id": row["reference_id"],
                "type": row.get("type"),
                "language": row.get("language"),
            }

        return None

@mcp.tool()
def get_client_status_and_history(
    client_id: int,
    reference: str,
) -> Optional[Dict[str, Any]]:
    ref_type = reference.lower()
    table, pk_col = _get_table_and_pk(ref_type)

    with get_connection() as conn:
        resolved_id = _resolve_reference_id(conn, client_id, ref_type)
        cursor = conn.cursor(dictionary=True)

        query = f"""
            SELECT
                {pk_col} AS reference_id,
                status,
                temp_client,
                late_fee_status,
                why_client_left,
                created_time,
                deleted_date,
                date_of_dissolution
            FROM {table}
            WHERE {pk_col} = %s
            LIMIT 1
        """
        cursor.execute(query, (resolved_id,))
        row = cursor.fetchone()
        if not row:
            return None

        return {
            "reference": ref_type,
            "client_id": client_id,
            "reference_id": row["reference_id"],
            "status": row.get("status"),
            "temp_client": row.get("temp_client"),
            "late_fee_status": row.get("late_fee_status"),
            "why_client_left": row.get("why_client_left"),
            "created_time": str(row["created_time"]) if row.get("created_time") else None,
            "deleted_date": str(row["deleted_date"]) if row.get("deleted_date") else None,
            "date_of_dissolution": (
                str(row["date_of_dissolution"])
                if row.get("date_of_dissolution")
                else None
            ),
        }

@mcp.tool()
def get_client_origin_and_referral_info(
    client_id: int,
    reference: str,
) -> Optional[Dict[str, Any]]:
    ref_type = reference.lower()
    table, pk_col = _get_table_and_pk(ref_type)

    with get_connection() as conn:
        resolved_id = _resolve_reference_id(conn, client_id, ref_type)
        cursor = conn.cursor(dictionary=True)

        query_main = f"""
            SELECT
                {pk_col} AS reference_id,
                converted_from_lead,
                client_added_from,
                lead_id,
                association_type,
                client_association_status
            FROM {table}
            WHERE {pk_col} = %s
            LIMIT 1
        """
        cursor.execute(query_main, (resolved_id,))
        main_row = cursor.fetchone()
        if not main_row:
            return None

        cursor.execute(
            """
            SELECT
                referred_by_source,
                referred_by_name
            FROM internal_data
            WHERE reference = %s
              AND reference_id = %s
            LIMIT 1
            """,
            (ref_type, resolved_id),
        )
        internal_row = cursor.fetchone() or {}

        return {
            "reference": ref_type,
            "client_id": client_id,
            "reference_id": main_row["reference_id"],
            "converted_from_lead": main_row.get("converted_from_lead"),
            "client_added_from": main_row.get("client_added_from"),
            "lead_id": main_row.get("lead_id"),
            "association_type": main_row.get("association_type"),
            "client_association_status": main_row.get("client_association_status"),
            "referred_by_source": internal_row.get("referred_by_source"),
            "referred_by_name": internal_row.get("referred_by_name"),
        }

@mcp.tool()
def get_client_team_assignment_details(
    client_id: int,
    reference: str,
) -> Optional[Dict[str, Any]]:
    
    ref_type = reference.lower()

    with get_connection() as conn:
        resolved_id = _resolve_reference_id(conn, client_id, ref_type)
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                id,
                reference,
                reference_id,
                office,
                brand_id,
                partner,
                manager,
                assistant,
                property_manager,
                client_association,
                practice_id,
                referred_by_source,
                referred_by_name,
                language,
                status,
                tenantId,
                customer_vault_id
            FROM internal_data
            WHERE reference = %s
              AND reference_id = %s
            LIMIT 1
        """
        cursor.execute(query, (ref_type, resolved_id))
        row = cursor.fetchone()
        if not row:
            return None

        return {
            "reference": ref_type,
            "client_id": client_id,
            "reference_id": row.get("reference_id"),
            "office": row.get("office"),
            "brand_id": row.get("brand_id"),
            "partner": row.get("partner"),
            "manager": row.get("manager"),
            "assistant": row.get("assistant"),
            "property_manager": row.get("property_manager"),
            "client_association": row.get("client_association"),
            "practice_id": row.get("practice_id"),
            "referred_by_source": row.get("referred_by_source"),
            "referred_by_name": row.get("referred_by_name"),
            "language": row.get("language"),
            "status": row.get("status"),
            "tenantId": row.get("tenantId"),
            "customer_vault_id": row.get("customer_vault_id"),
        }

@mcp.tool()
def get_individual_residency_and_citizenship(
    client_id: int,
    reference: str,
) -> Optional[Dict[str, Any]]:
    
    ref_type = reference.lower()
    if ref_type != "individual":
        return None

    table, pk_col = _get_table_and_pk(ref_type)

    with get_connection() as conn:
        resolved_id = _resolve_reference_id(conn, client_id, ref_type)
        cursor = conn.cursor(dictionary=True)

        query = f"""
            SELECT
                {pk_col} AS reference_id,
                country_residence,
                country_citizenship,
                language
            FROM {table}
            WHERE {pk_col} = %s
            LIMIT 1
        """
        cursor.execute(query, (resolved_id,))
        row = cursor.fetchone()
        if not row:
            return None

        return {
            "reference": ref_type,
            "client_id": client_id,
            "reference_id": row["reference_id"],
            "country_residence": row.get("country_residence"),
            "country_citizenship": row.get("country_citizenship"),
            "language": row.get("language"),
        }

@mcp.tool()
def get_individual_identity_and_tax_id(
    client_id: int,
    reference: str,
) -> Optional[Dict[str, Any]]:
   
    ref_type = reference.lower()
    if ref_type != "individual":
        return None

    table, pk_col = _get_table_and_pk(ref_type)

    with get_connection() as conn:
        resolved_id = _resolve_reference_id(conn, client_id, ref_type)
        cursor = conn.cursor(dictionary=True)

        query = f"""
            SELECT
                i.{pk_col} AS reference_id,
                i.first_name,
                i.middle_name,
                i.last_name,
                i.birth_date,
                i.ssn_itin_type,
                i.ssn_itin,
                i.status,
                i.created_time,
                i.deleted_date,
                i.date_of_dissolution,

                -- language master
                i.language AS language_id,
                l.language AS language_name,

                -- country of residence master
                i.country_residence AS country_residence_id,
                cr.country_name AS country_residence_name,
                cr.country_code AS country_residence_code,

                -- country of citizenship master
                i.country_citizenship AS country_citizenship_id,
                cc.country_name AS country_citizenship_name,
                cc.country_code AS country_citizenship_code

            FROM {table} AS i
            LEFT JOIN languages AS l
                ON l.id = i.language
            LEFT JOIN countries AS cr
                ON cr.id = i.country_residence
            LEFT JOIN countries AS cc
                ON cc.id = i.country_citizenship
            WHERE i.{pk_col} = %s
            LIMIT 1
        """
        cursor.execute(query, (resolved_id,))
        row = cursor.fetchone()
        if not row:
            return None
        name_parts = [
            row.get("first_name"),
            row.get("middle_name"),
            row.get("last_name"),
        ]
        full_name = " ".join([p for p in name_parts if p]).strip() or None

        return {
            "reference": ref_type,
            "client_id": client_id,
            "reference_id": row["reference_id"],

            "first_name": row.get("first_name"),
            "middle_name": row.get("middle_name"),
            "last_name": row.get("last_name"),
            "full_name": full_name,

            "birth_date": (
                str(row["birth_date"]) if row.get("birth_date") else None
            ),
            "ssn_itin_type": row.get("ssn_itin_type"),
            "ssn_itin": row.get("ssn_itin"),

            "status": row.get("status"),
            "created_time": (
                str(row["created_time"]) if row.get("created_time") else None
            ),
            "deleted_date": (
                str(row["deleted_date"]) if row.get("deleted_date") else None
            ),
            "date_of_dissolution": (
                str(row["date_of_dissolution"])
                if row.get("date_of_dissolution")
                else None
            ),
            "language_id": row.get("language_id"),
            "language_name": row.get("language_name"),

            "country_residence_id": row.get("country_residence_id"),
            "country_residence_name": row.get("country_residence_name"),
            "country_residence_code": row.get("country_residence_code"),

            "country_citizenship_id": row.get("country_citizenship_id"),
            "country_citizenship_name": row.get("country_citizenship_name"),
            "country_citizenship_code": row.get("country_citizenship_code"),
        }

@mcp.tool()
def get_client_welcome_message(
    client_id: int,
    reference: str,
) -> Dict[str, Any]:
    """
    Purpose:
        Return a personalized welcome message for the logged-in client.

        The message format is:
            "Welcome, {first_name}. Would you like me to help you with your
             \"1040NR non-resident tax filing\"?"

        For:
        - Individual clients: attempts to use individual.first_name.
        - Company clients: attempts to use the primary contact's first_name
          from contact_info; if not available, falls back to company.contact_name,
          and finally to the first token of company.name.

    Args:
        client_id (int):
            Global client ID used by your application (typically internal_data.id).
        reference (str):
            Client type: "company" or "individual" (case-insensitive).
    """
    ref_type = reference.lower()

    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        resolved_id = _resolve_reference_id(conn, client_id, ref_type)

        first_name: str | None = None
        display_name_source: str = "fallback"

        if ref_type == "individual":
            cursor.execute(
                """
                SELECT first_name, middle_name, last_name
                FROM individual
                WHERE id = %s
                LIMIT 1
                """,
                (resolved_id,),
            )
            row = cursor.fetchone()
            if row and row.get("first_name"):
                first_name = (row["first_name"] or "").strip()
                display_name_source = "individual"


        elif ref_type == "company":
            cursor.execute(
                """
                SELECT first_name, last_name
                FROM contact_info
                WHERE reference = %s
                  AND reference_id = %s
                ORDER BY status DESC, id ASC
                LIMIT 1
                """,
                (ref_type, resolved_id),
            )
            contact_row = cursor.fetchone()
            if contact_row and contact_row.get("first_name"):
                first_name = (contact_row["first_name"] or "").strip()
                display_name_source = "contact_info"

            if not first_name:
                cursor.execute(
                    """
                    SELECT name, contact_name
                    FROM company
                    WHERE company_id = %s
                    LIMIT 1
                    """,
                    (resolved_id,),
                )
                comp_row = cursor.fetchone() or {}
                contact_name = (comp_row.get("contact_name") or "").strip()
                company_name = (comp_row.get("name") or "").strip()

                if contact_name:
                    first_name = contact_name.split()[0]
                    display_name_source = "company_contact_name"
                elif company_name:
                    first_name = company_name.split()[0]
                    display_name_source = "company_name"

        if not first_name:
            first_name = "there"
            display_name_source = "fallback"

        welcome_message = (
            f'Welcome, {first_name}. '
            'Would you like me to help you with your "1040NR non-resident tax filing"?'
        )

        return {
            "reference": ref_type,
            "client_id": client_id,
            "reference_id": resolved_id,
            "first_name": first_name,
            "display_name_source": display_name_source,
            "welcome_message": welcome_message,
        }


if __name__ == "__main__":
    mcp.run()