import csv
import psycopg2
from config import load_config

def get_connection():
    """Establishes a connection to the PostgreSQL database"""
    params = load_config()
    return psycopg2.connect(**params)

def import_from_csv(file_path):
    """Imports contacts from a CSV file into the database."""
    query = "INSERT INTO phonebook(first_name, phone_number) VALUES(%s, %s) ON CONFLICT (phone_number) DO NOTHING;"
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                with open(file_path, mode='r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header row
                    for row in reader:
                        cur.execute(query, (row[0], row[1]))
            conn.commit()
            print("Successfully imported contacts from CSV.")
    except Exception as e:
        print(f"Error importing from CSV: {e}")

def add_contact(name, phone):
    """Inserts a new contact via console input."""
    query = "INSERT INTO phonebook(first_name, phone_number) VALUES(%s, %s);"
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (name, phone))
            conn.commit()
            print(f"Contact '{name}' added successfully.")
    except Exception as e:
        print(f"Error adding contact: {e}")

def update_contact(name, new_phone):
    """Updates a contact's phone number based on their name."""
    query = "UPDATE phonebook SET phone_number = %s WHERE first_name = %s;"
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (new_phone, name))
                if cur.rowcount == 0:
                    print(f"No contact found with the name '{name}'.")
                else:
                    print(f"Contact '{name}' updated successfully.")
            conn.commit()
    except Exception as e:
        print(f"Error updating contact: {e}")

def query_contacts(search_term):
    """Queries contacts using a filter for name or phone prefix."""
    query = "SELECT * FROM phonebook WHERE first_name ILIKE %s OR phone_number LIKE %s;"
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (f'%{search_term}%', f'{search_term}%'))
                results = cur.fetchall()
                if not results:
                    print("No contacts found matching the criteria.")
                else:
                    print("\n--- Search Results ---")
                    for contact in results:
                        print(f"ID: {contact[0]} | Name: {contact[1]} | Phone: {contact[2]}")
    except Exception as e:
        print(f"Error querying contacts: {e}")

def delete_contact(identifier):
    """Deletes a contact by name or phone number."""
    query = "DELETE FROM phonebook WHERE first_name = %s OR phone_number = %s;"
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (identifier, identifier))
                if cur.rowcount == 0:
                    print(f"No contact found for '{identifier}'.")
                else:
                    print(f"Contact '{identifier}' deleted successfully.")
            conn.commit()
    except Exception as e:
        print(f"Error deleting contact: {e}")

def main_menu():
    """Main terminal interface."""
    while True:
        print("\n===== PhoneBook Application =====")
        print("1. Import contacts from CSV")
        print("2. Add new contact (Manual)")
        print("3. Update contact phone")
        print("4. Search contacts (Filter)")
        print("5. Delete contact")
        print("6. Exit")
        
        choice = input("\nSelect an option (1-6): ")
        
        if choice == '1':
            path = input("Enter CSV file path (e.g., contacts.csv): ")
            import_from_csv(path)
        elif choice == '2':
            name = input("Enter first name: ")
            phone = input("Enter phone number: ")
            add_contact(name, phone)
        elif choice == '3':
            name = input("Enter the name of the contact to update: ")
            new_phone = input("Enter the new phone number: ")
            update_contact(name, new_phone)
        elif choice == '4':
            term = input("Enter search term (Name or Phone prefix): ")
            query_contacts(term)
        elif choice == '5':
            target = input("Enter name or phone to delete: ")
            delete_contact(target)
        elif choice == '6':
            print("Exiting application. Goodbye!")
            break
        else:
            print("Invalid selection. Please try again.")

if __name__ == "__main__":
    main_menu()