from connect import open_db
def add_user(nm, ph):
    con = open_db()
    cur = con.cursor()
    cur.execute("CALL add_or_update(%s, %s);", (nm, ph))
    con.commit()
    cur.close()
    con.close()
def search_user(txt):
    con = open_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM find_people(%s);", (txt,))
    data = cur.fetchall()
    for d in data:
        print(d)
    cur.close()
    con.close()
def delete_user(v):
    con = open_db()
    cur = con.cursor()
    cur.execute("CALL remove_person(%s);", (v,))
    con.commit()
    cur.close()
    con.close()
def show_page(lim, off):
    con = open_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM show_by_parts(%s, %s);", (lim, off))
    data = cur.fetchall()
    for d in data:
        print(d)
    cur.close()
    con.close()
if __name__ == "__main__":
    add_user("Aqjol", "87770000001")
    add_user("Dias", "87770000002")

    print("\nSEARCH:")
    search_user("Aq")

    print("\nPAGE:")
    show_page(5, 0)

    print("\nDELETE:")
    delete_user("Dias")