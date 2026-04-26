# phonebook.py — Practice 7: PhoneBook with PostgreSQL

import csv
import re
import psycopg2
from connect import get_connection

# ── Table setup ───────────────────────────────────────────────────────────────

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS contacts (
    id         SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name  VARCHAR(100),
    phone      VARCHAR(20) NOT NULL UNIQUE
);
"""

def init_db(conn):
    """Create the contacts table if it does not exist."""
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE)
    conn.commit()
    print("[DB] Table 'contacts' is ready.")


# ── Validation ────────────────────────────────────────────────────────────────

PHONE_RE = re.compile(r"^\+?[\d\s\-().]{7,20}$")

def validate_phone(phone):
    return bool(PHONE_RE.match(phone.strip()))


# ── CREATE ────────────────────────────────────────────────────────────────────

def insert_contact(conn, first_name, last_name, phone):
    """Insert a single contact. Skips duplicates silently."""
    sql = """
        INSERT INTO contacts (first_name, last_name, phone)
        VALUES (%s, %s, %s)
        ON CONFLICT (phone) DO NOTHING
        RETURNING id;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (first_name.strip(), last_name.strip(), phone.strip()))
        result = cur.fetchone()
    conn.commit()
    if result:
        print(f"  [+] Added: {first_name} {last_name} — {phone}")
    else:
        print(f"  [!] Phone '{phone}' already exists — skipped.")


def import_from_csv(conn, filepath="contacts.csv"):
    """Bulk-import contacts from a CSV file (columns: first_name, last_name, phone)."""
    inserted = errors = 0
    try:
        with open(filepath, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 2):
                first = (row.get("first_name") or "").strip()
                last  = (row.get("last_name")  or "").strip()
                phone = (row.get("phone")       or "").strip()

                if not first or not phone:
                    print(f"  [!] Row {i}: missing first_name or phone — skipped.")
                    errors += 1
                    continue
                if not validate_phone(phone):
                    print(f"  [!] Row {i}: invalid phone '{phone}' — skipped.")
                    errors += 1
                    continue

                sql = """
                    INSERT INTO contacts (first_name, last_name, phone)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (phone) DO NOTHING;
                """
                with conn.cursor() as cur:
                    cur.execute(sql, (first, last, phone))
                    if cur.rowcount:
                        inserted += 1
                conn.commit()

    except FileNotFoundError:
        print(f"[ERROR] File not found: {filepath}")
        return

    print(f"[CSV] Done — {inserted} inserted, {errors} skipped/invalid.")


def insert_from_console(conn):
    """Prompt the user for contact details and insert into the database."""
    print("\n--- Add new contact ---")
    first = input("  First name : ").strip()
    last  = input("  Last name  : ").strip()
    phone = input("  Phone      : ").strip()

    if not first:
        print("  [!] First name is required.")
        return
    if not validate_phone(phone):
        print(f"  [!] '{phone}' is not a valid phone number.")
        return

    insert_contact(conn, first, last, phone)


# ── READ ──────────────────────────────────────────────────────────────────────

def print_table(rows):
    if not rows:
        print("  (no contacts found)")
        return
    print(f"\n  {'ID':>4}  {'First Name':15}  {'Last Name':15}  {'Phone':20}")
    print("  " + "─" * 60)
    for cid, first, last, phone in rows:
        print(f"  {cid:>4}  {first or '':15}  {last or '':15}  {phone:20}")


def list_all(conn):
    """Display all contacts sorted by name."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, first_name, last_name, phone FROM contacts ORDER BY first_name, last_name;"
        )
        rows = cur.fetchall()
    print(f"\n[ALL] {len(rows)} contact(s) in PhoneBook:")
    print_table(rows)


def search_by_name(conn, pattern):
    """Search contacts by first or last name (partial, case-insensitive)."""
    sql = """
        SELECT id, first_name, last_name, phone
        FROM contacts
        WHERE first_name ILIKE %s OR last_name ILIKE %s
        ORDER BY first_name;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (f"%{pattern}%", f"%{pattern}%"))
        rows = cur.fetchall()
    print(f"\n[SEARCH] Results for name '{pattern}':")
    print_table(rows)


def search_by_phone_prefix(conn, prefix):
    """Search contacts by phone number prefix."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, first_name, last_name, phone FROM contacts WHERE phone LIKE %s ORDER BY phone;",
            (f"{prefix}%",)
        )
        rows = cur.fetchall()
    print(f"\n[SEARCH] Contacts with phone prefix '{prefix}':")
    print_table(rows)


# ── UPDATE ────────────────────────────────────────────────────────────────────

def update_contact(conn):
    """Find a contact, then update their name and/or phone."""
    print("\n--- Update contact ---")
    search = input("  Search by name or phone: ").strip()
    if not search:
        return

    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, first_name, last_name, phone FROM contacts
               WHERE phone = %s OR first_name ILIKE %s OR last_name ILIKE %s
               LIMIT 10;""",
            (search, f"%{search}%", f"%{search}%")
        )
        rows = cur.fetchall()

    if not rows:
        print("  [!] No contacts found.")
        return

    print_table(rows)
    try:
        cid = int(input("  Enter ID to update: ").strip())
    except ValueError:
        print("  [!] Invalid ID.")
        return

    new_first = input("  New first name  (blank = keep): ").strip()
    new_last  = input("  New last name   (blank = keep): ").strip()
    new_phone = input("  New phone       (blank = keep): ").strip()

    if new_phone and not validate_phone(new_phone):
        print(f"  [!] '{new_phone}' is not a valid phone number.")
        return

    updates, params = [], []
    if new_first: updates.append("first_name = %s"); params.append(new_first)
    if new_last:  updates.append("last_name = %s");  params.append(new_last)
    if new_phone: updates.append("phone = %s");      params.append(new_phone)

    if not updates:
        print("  [!] Nothing to update.")
        return

    params.append(cid)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE contacts SET {', '.join(updates)} WHERE id = %s RETURNING id;",
                params
            )
            result = cur.fetchone()
        conn.commit()
        if result:
            print(f"  [✓] Contact ID={cid} updated successfully.")
        else:
            print(f"  [!] No contact with ID={cid}.")
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        print(f"  [!] Phone '{new_phone}' is already used by another contact.")


# ── DELETE ────────────────────────────────────────────────────────────────────

def delete_by_name(conn, name):
    """Delete all contacts matching the given name."""
    with conn.cursor() as cur:
        cur.execute(
            """DELETE FROM contacts
               WHERE first_name ILIKE %s OR last_name ILIKE %s
               RETURNING first_name, last_name, phone;""",
            (f"%{name}%", f"%{name}%")
        )
        deleted = cur.fetchall()
    conn.commit()
    if deleted:
        print(f"  [−] Deleted {len(deleted)} contact(s) matching '{name}':")
        for r in deleted:
            print(f"      {r[0]} {r[1]} — {r[2]}")
    else:
        print(f"  [!] No contacts found with name '{name}'.")


def delete_by_phone(conn, phone):
    """Delete the contact with the given phone number."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM contacts WHERE phone = %s RETURNING first_name, last_name, phone;",
            (phone.strip(),)
        )
        row = cur.fetchone()
    conn.commit()
    if row:
        print(f"  [−] Deleted: {row[0]} {row[1]} — {row[2]}")
    else:
        print(f"  [!] No contact with phone '{phone}'.")


def delete_menu(conn):
    print("\n--- Delete contact ---")
    print("  1. By name")
    print("  2. By phone number")
    choice = input("  Choice: ").strip()
    if choice == "1":
        name = input("  Name (full or partial): ").strip()
        if name:
            delete_by_name(conn, name)
    elif choice == "2":
        phone = input("  Phone: ").strip()
        if phone:
            delete_by_phone(conn, phone)
    else:
        print("  [!] Invalid choice.")


# ── MENU ──────────────────────────────────────────────────────────────────────

MENU = """
╔══════════════════════════════════════╗
║      📒  PhoneBook — Practice 7      ║
╠══════════════════════════════════════╣
║  1. List all contacts                ║
║  2. Search by name                   ║
║  3. Search by phone prefix           ║
║  4. Add contact (console)            ║
║  5. Import from CSV                  ║
║  6. Update a contact                 ║
║  7. Delete a contact                 ║
║  0. Exit                             ║
╚══════════════════════════════════════╝"""


def run(conn):
    init_db(conn)
    while True:
        print(MENU)
        choice = input("  Select: ").strip()

        if choice == "1":
            list_all(conn)
        elif choice == "2":
            p = input("  Name: ").strip()
            if p:
                search_by_name(conn, p)
        elif choice == "3":
            p = input("  Phone prefix: ").strip()
            if p:
                search_by_phone_prefix(conn, p)
        elif choice == "4":
            insert_from_console(conn)
        elif choice == "5":
            path = input("  CSV path [contacts.csv]: ").strip() or "contacts.csv"
            import_from_csv(conn, path)
        elif choice == "6":
            update_contact(conn)
        elif choice == "7":
            delete_menu(conn)
        elif choice == "0":
            print("  Goodbye! 👋")
            break
        else:
            print("  [!] Invalid option, try again.")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    conn = get_connection()
    if conn is None:
        raise SystemExit(1)
    try:
        run(conn)
    finally:
        conn.close()