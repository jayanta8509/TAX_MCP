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


# @mcp.tool()
# def get_client_primary_contact(
#     client_id: int,
#     reference: str,
# ) -> Optional[Dict[str, Any]]:
#     """
#     Retrieve the primary contact information for a client.
    
#     Returns contact name, email, phone, and address details.
#     """
#     ref_type = reference.lower()
    
#     with get_connection() as conn:
#         cursor = conn.cursor(dictionary=True)
        
#         query = """
#             SELECT 
#                 CONCAT(COALESCE(first_name, ''), ' ', COALESCE(last_name, '')) as name,
#                 email1 as email,
#                 phone1 as phone,
#                 address1 as address,
#                 city,
#                 state,
#                 zip,
#                 country
#             FROM contact_info
#             WHERE reference = %s AND reference_id = %s
#             LIMIT 1
#         """
#         cursor.execute(query, (ref_type, client_id))
#         row = cursor.fetchone()
        
#         if not row:
#             return None
            
#         return {
#             "reference": ref_type,
#             "client_id": client_id,
#             "name": row.get("name", "").strip(),
#             "email": row.get("email"),
#             "phone": row.get("phone"),
#             "address": row.get("address"),
#             "city": row.get("city"),
#             "state": row.get("state"),
#             "zip": row.get("zip"),
#             "country": row.get("country"),
#         }


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


if __name__ == "__main__":
    mcp.run()