# phonebook.py — TSIS 1: Extended PhoneBook
# Builds on Practice 7-8. Does NOT re-implement features already done there.
# New features: groups, multi-phone, email, birthday, JSON export/import,
#               extended CSV, filter/sort/paginate console UI, stored procedures.

import csv
import json
import re
import psycopg2
from datetime import date, datetime
from connect import get_connection

# ── Constants ────────────────────────────────────────────────────────────────

PAGE_SIZE   = 5
PHONE_RE    = re.compile(r"^\+?[\d\s\-().]{7,20}$")
DATE_FMT    = "%Y-%m-%d"
VALID_TYPES = ("home", "work", "mobile")

# ── Schema bootstrap ─────────────────────────────────────────────────────────

def init_db(conn):
    """Apply schema.sql and procedures.sql to the live database."""
    for filepath in ("schema.sql", "procedures.sql"):
        try:
            with open(filepath, encoding="utf-8") as f:
                sql = f.read()
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            print(f"[DB] Applied {filepath}")
        except FileNotFoundError:
            print(f"[WARN] {filepath} not found — skipping.")
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] {filepath}: {e}")


# ── Helpers ──────────────────────────────────────────────────────────────────

def validate_phone(p): return bool(PHONE_RE.match(p.strip()))

def parse_date(s):
    try:
        return datetime.strptime(s.strip(), DATE_FMT).date()
    except (ValueError, AttributeError):
        return None

def json_serial(obj):
    """JSON serialiser for date objects."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Not serialisable: {type(obj)}")

def resolve_group_id(conn, name):
    """Return group id for name, inserting it if needed."""
    if not name:
        return None
    with conn.cursor() as cur:
        cur.execute("INSERT INTO groups(name) VALUES(%s) ON CONFLICT(name) DO NOTHING;", (name,))
        cur.execute("SELECT id FROM groups WHERE name=%s;", (name,))
        row = cur.fetchone()
    return row[0] if row else None

def list_groups(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM groups ORDER BY name;")
        return cur.fetchall()

def _print_contacts(rows, phones_map=None):
    """Pretty-print a list of (id, first, last, email, birthday, group_name) rows."""
    if not rows:
        print("  (no contacts found)")
        return
    sep = "  " + "─" * 80
    print(sep)
    print(f"  {'ID':>4}  {'Name':22}  {'Email':22}  {'Birthday':10}  {'Group':10}")
    print(sep)
    for row in rows:
        cid, first, last, email, bday, grp = row
        name  = f"{first} {last or ''}".strip()
        print(f"  {cid:>4}  {name:22}  {str(email or ''):22}  "
              f"{str(bday or ''):10}  {str(grp or ''):10}")
        if phones_map and cid in phones_map:
            for ph, ptype in phones_map[cid]:
                print(f"  {'':>4}    📞 {ph} ({ptype})")
    print(sep)

def fetch_phones_map(conn, contact_ids):
    """Return {contact_id: [(phone, type), ...]} for the given ids."""
    if not contact_ids:
        return {}
    with conn.cursor() as cur:
        cur.execute(
            "SELECT contact_id, phone, type FROM phones WHERE contact_id = ANY(%s) ORDER BY id;",
            (list(contact_ids),)
        )
        rows = cur.fetchall()
    result = {}
    for cid, ph, ptype in rows:
        result.setdefault(cid, []).append((ph, ptype))
    return result


# ── INSERT helpers ───────────────────────────────────────────────────────────

def _insert_contact_row(conn, first, last, email, birthday, group_id):
    """Insert into contacts, return new id or None on error."""
    sql = """
        INSERT INTO contacts (first_name, last_name, email, birthday, group_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (first, last or None, email or None, birthday, group_id))
        return cur.fetchone()[0]

def _insert_phone(conn, contact_id, phone, ptype="mobile"):
    sql = """
        INSERT INTO phones (contact_id, phone, type)
        VALUES (%s, %s, %s)
        ON CONFLICT (contact_id, phone) DO NOTHING;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (contact_id, phone, ptype))


# ── IMPORT: CSV ──────────────────────────────────────────────────────────────
# Extended from Practice 7 to handle email, birthday, group, phone_type.

def import_from_csv(conn, filepath="contacts.csv"):
    inserted = skipped = errors = 0
    try:
        with open(filepath, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 2):
                first = (row.get("first_name") or "").strip()
                last  = (row.get("last_name")  or "").strip()
                phone = (row.get("phone")       or "").strip()
                if not first or not phone:
                    print(f"  [!] Row {i}: missing first_name or phone — skipped.")
                    errors += 1; continue
                if not validate_phone(phone):
                    print(f"  [!] Row {i}: invalid phone '{phone}' — skipped.")
                    errors += 1; continue

                email    = (row.get("email")      or "").strip() or None
                birthday = parse_date(row.get("birthday", ""))
                grp_name = (row.get("group")      or "").strip() or None
                ptype    = (row.get("phone_type") or "mobile").strip()
                if ptype not in VALID_TYPES:
                    ptype = "mobile"

                try:
                    group_id   = resolve_group_id(conn, grp_name)
                    contact_id = _insert_contact_row(conn, first, last, email, birthday, group_id)
                    _insert_phone(conn, contact_id, phone, ptype)
                    conn.commit()
                    inserted += 1
                except Exception as e:
                    conn.rollback()
                    print(f"  [!] Row {i}: {e} — skipped.")
                    errors += 1

    except FileNotFoundError:
        print(f"[ERROR] File not found: {filepath}"); return

    print(f"[CSV] Done — {inserted} inserted, {errors} errors/skipped.")


# ── IMPORT: JSON ─────────────────────────────────────────────────────────────

def import_from_json(conn, filepath="contacts.json"):
    """
    Import contacts from JSON. Each object may have:
      first_name, last_name, email, birthday, group,
      phones: [{"phone": "...", "type": "mobile"}, ...]
    On duplicate first_name: ask user to skip or overwrite.
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] File not found: {filepath}"); return
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON: {e}"); return

    if not isinstance(data, list):
        print("[ERROR] JSON root must be an array of contact objects."); return

    inserted = updated = skipped = 0

    for obj in data:
        first = (obj.get("first_name") or "").strip()
        last  = (obj.get("last_name")  or "").strip()
        if not first:
            print("  [!] Entry missing first_name — skipped.")
            skipped += 1; continue

        # Check for duplicate by first+last name
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM contacts WHERE first_name ILIKE %s AND COALESCE(last_name,'') ILIKE %s LIMIT 1;",
                (first, last)
            )
            existing = cur.fetchone()

        if existing:
            ans = input(f"  [?] '{first} {last}' already exists. Overwrite? (y/n): ").strip().lower()
            if ans != "y":
                skipped += 1; continue
            # Delete old record (CASCADE removes phones)
            with conn.cursor() as cur:
                cur.execute("DELETE FROM contacts WHERE id=%s;", (existing[0],))
            conn.commit()

        email    = (obj.get("email")    or "").strip() or None
        birthday = parse_date(obj.get("birthday", ""))
        grp_name = (obj.get("group")    or "").strip() or None
        phones   = obj.get("phones", [])

        try:
            group_id   = resolve_group_id(conn, grp_name)
            contact_id = _insert_contact_row(conn, first, last, email, birthday, group_id)
            for ph_obj in phones:
                ph    = (ph_obj.get("phone") or "").strip()
                ptype = (ph_obj.get("type")  or "mobile").strip()
                if ph and validate_phone(ph):
                    _insert_phone(conn, contact_id, ph, ptype if ptype in VALID_TYPES else "mobile")
            conn.commit()
            if existing:
                updated += 1
            else:
                inserted += 1
        except Exception as e:
            conn.rollback()
            print(f"  [!] {first} {last}: {e}")
            skipped += 1

    print(f"[JSON] Done — {inserted} inserted, {updated} overwritten, {skipped} skipped.")


# ── EXPORT: JSON ─────────────────────────────────────────────────────────────

def export_to_json(conn, filepath="contacts.json"):
    sql = """
        SELECT c.id, c.first_name, c.last_name, c.email, c.birthday, g.name
        FROM   contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        ORDER  BY c.first_name, c.last_name;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        contacts = cur.fetchall()

    ids = [r[0] for r in contacts]
    phones_map = fetch_phones_map(conn, ids)

    out = []
    for cid, first, last, email, bday, grp in contacts:
        out.append({
            "first_name": first,
            "last_name":  last,
            "email":      email,
            "birthday":   bday,
            "group":      grp,
            "phones":     [{"phone": ph, "type": pt} for ph, pt in phones_map.get(cid, [])],
        })

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=json_serial)

    print(f"[JSON] Exported {len(out)} contacts to '{filepath}'.")


# ── QUERY / FILTER / SORT ────────────────────────────────────────────────────

def _base_select():
    return """
        SELECT c.id, c.first_name, c.last_name, c.email, c.birthday, g.name AS group_name
        FROM   contacts c
        LEFT JOIN groups g ON g.id = c.group_id
    """

def filter_by_group(conn):
    groups = list_groups(conn)
    if not groups:
        print("  No groups found."); return
    print("\n  Available groups:")
    for gid, gname in groups:
        print(f"    {gid}. {gname}")
    try:
        gid = int(input("  Enter group ID: ").strip())
    except ValueError:
        print("  [!] Invalid ID."); return

    sort = _ask_sort()
    sql  = _base_select() + f" WHERE c.group_id = %s ORDER BY {sort};"
    with conn.cursor() as cur:
        cur.execute(sql, (gid,))
        rows = cur.fetchall()
    pm = fetch_phones_map(conn, [r[0] for r in rows])
    _print_contacts(rows, pm)

def search_by_email(conn):
    pattern = input("  Email pattern (e.g. gmail): ").strip()
    if not pattern: return
    sort = _ask_sort()
    sql  = _base_select() + f" WHERE c.email ILIKE %s ORDER BY {sort};"
    with conn.cursor() as cur:
        cur.execute(sql, (f"%{pattern}%",))
        rows = cur.fetchall()
    pm = fetch_phones_map(conn, [r[0] for r in rows])
    _print_contacts(rows, pm)

def _ask_sort():
    print("  Sort by: 1=Name  2=Birthday  3=Date added")
    choice = input("  Choice [1]: ").strip()
    return {
        "2": "c.birthday NULLS LAST",
        "3": "c.created_at",
    }.get(choice, "c.first_name, c.last_name")

def full_search(conn):
    """Uses the search_contacts DB function (extended in TSIS1 to cover email + phones)."""
    query = input("  Search (name / email / phone): ").strip()
    if not query: return
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM search_contacts(%s);", (query,))
        rows = cur.fetchall()
    pm = fetch_phones_map(conn, [r[0] for r in rows])
    print(f"\n[SEARCH] {len(rows)} result(s) for '{query}':")
    _print_contacts(rows, pm)


# ── PAGINATED NAVIGATION ─────────────────────────────────────────────────────
# Uses the paginated_contacts() DB function from Practice 8.

def paginated_browse(conn):
    offset = 0
    sql = _base_select() + " ORDER BY c.first_name, c.last_name LIMIT %s OFFSET %s;"
    while True:
        with conn.cursor() as cur:
            cur.execute(sql, (PAGE_SIZE, offset))
            rows = cur.fetchall()

        page = offset // PAGE_SIZE + 1
        print(f"\n  ── Page {page} (showing {len(rows)} of {PAGE_SIZE} per page) ──")
        if rows:
            pm = fetch_phones_map(conn, [r[0] for r in rows])
            _print_contacts(rows, pm)
        else:
            print("  (no more contacts)")

        print("  [n]ext  [p]rev  [q]uit")
        cmd = input("  > ").strip().lower()
        if cmd == "n":
            if len(rows) < PAGE_SIZE:
                print("  Already on last page.")
            else:
                offset += PAGE_SIZE
        elif cmd == "p":
            offset = max(0, offset - PAGE_SIZE)
        elif cmd == "q":
            break


# ── CONSOLE: ADD CONTACT ─────────────────────────────────────────────────────

def add_contact_console(conn):
    print("\n--- Add contact ---")
    first = input("  First name : ").strip()
    if not first: print("  [!] Required."); return
    last    = input("  Last name  : ").strip()
    email   = input("  Email      : ").strip() or None
    bday_s  = input("  Birthday   (YYYY-MM-DD, blank to skip): ").strip()
    birthday = parse_date(bday_s) if bday_s else None

    groups = list_groups(conn)
    print("  Groups:")
    for gid, gname in groups:
        print(f"    {gid}. {gname}")
    grp_input = input("  Group ID (blank to skip): ").strip()
    group_id  = int(grp_input) if grp_input.isdigit() else None

    phones = []
    while True:
        ph = input("  Phone (blank to finish): ").strip()
        if not ph: break
        if not validate_phone(ph):
            print("  [!] Invalid phone format."); continue
        ptype = input("  Type (home/work/mobile) [mobile]: ").strip() or "mobile"
        if ptype not in VALID_TYPES: ptype = "mobile"
        phones.append((ph, ptype))

    if not phones:
        print("  [!] At least one phone is required."); return

    try:
        contact_id = _insert_contact_row(conn, first, last, email, birthday, group_id)
        for ph, pt in phones:
            _insert_phone(conn, contact_id, ph, pt)
        conn.commit()
        print(f"  [+] Contact '{first} {last}' added (id={contact_id}).")
    except Exception as e:
        conn.rollback()
        print(f"  [ERROR] {e}")


# ── STORED PROCEDURE CALLERS ─────────────────────────────────────────────────

def call_add_phone(conn):
    print("\n--- Add phone to contact ---")
    name  = input("  Contact name: ").strip()
    phone = input("  Phone       : ").strip()
    ptype = input("  Type (home/work/mobile) [mobile]: ").strip() or "mobile"
    if not validate_phone(phone):
        print("  [!] Invalid phone."); return
    try:
        with conn.cursor() as cur:
            cur.execute("CALL add_phone(%s, %s, %s);", (name, phone, ptype))
        conn.commit()
        print("  [✓] Phone added.")
    except Exception as e:
        conn.rollback()
        print(f"  [ERROR] {e}")

def call_move_to_group(conn):
    print("\n--- Move contact to group ---")
    name  = input("  Contact name : ").strip()
    group = input("  Group name   : ").strip()
    if not name or not group:
        print("  [!] Both fields required."); return
    try:
        with conn.cursor() as cur:
            cur.execute("CALL move_to_group(%s, %s);", (name, group))
        conn.commit()
        print(f"  [✓] '{name}' moved to group '{group}'.")
    except Exception as e:
        conn.rollback()
        print(f"  [ERROR] {e}")


# ── MAIN MENU ────────────────────────────────────────────────────────────────

MENU = """
╔══════════════════════════════════════════════════╗
║       📒  PhoneBook — Extended (TSIS 1)          ║
╠══════════════════════════════════════════════════╣
║  Search & Browse                                 ║
║    1. Full search (name / email / phone)         ║
║    2. Filter by group                            ║
║    3. Search by email                            ║
║    4. Browse all contacts (paginated)            ║
╠══════════════════════════════════════════════════╣
║  Create                                          ║
║    5. Add contact (console)                      ║
║    6. Import from CSV                            ║
║    7. Import from JSON                           ║
╠══════════════════════════════════════════════════╣
║  Manage                                          ║
║    8. Add phone to contact (procedure)           ║
║    9. Move contact to group (procedure)          ║
╠══════════════════════════════════════════════════╣
║  Export                                          ║
║   10. Export all contacts to JSON                ║
╠══════════════════════════════════════════════════╣
║    0. Exit                                       ║
╚══════════════════════════════════════════════════╝"""


def run(conn):
    init_db(conn)
    while True:
        print(MENU)
        choice = input("  Select: ").strip()

        if   choice == "1":  full_search(conn)
        elif choice == "2":  filter_by_group(conn)
        elif choice == "3":  search_by_email(conn)
        elif choice == "4":  paginated_browse(conn)
        elif choice == "5":  add_contact_console(conn)
        elif choice == "6":
            path = input("  CSV path [contacts.csv]: ").strip() or "contacts.csv"
            import_from_csv(conn, path)
        elif choice == "7":
            path = input("  JSON path [contacts.json]: ").strip() or "contacts.json"
            import_from_json(conn, path)
        elif choice == "8":  call_add_phone(conn)
        elif choice == "9":  call_move_to_group(conn)
        elif choice == "10":
            path = input("  Output path [contacts.json]: ").strip() or "contacts.json"
            export_to_json(conn, path)
        elif choice == "0":
            print("  Goodbye! 👋"); break
        else:
            print("  [!] Unknown option.")


if __name__ == "__main__":
    conn = get_connection()
    if conn is None:
        raise SystemExit(1)
    try:
        run(conn)
    finally:
        conn.close()