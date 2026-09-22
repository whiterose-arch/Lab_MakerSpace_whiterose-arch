"""Application entry point for the Campus MakerSpace Checkout System.

Keep this file focused on:
- displaying menus;
- collecting input;
- calling service-layer operations;
- presenting results and friendly messages.

Do not put database SQL directly into the menu functions.
"""

from datetime import date, timedelta
from pathlib import Path
import re
import sys
from typing import Any, Optional

from database import Database
from services import MakerSpaceService


# ======================================================================
# Formatting and Input Helpers
# ======================================================================

def print_banner(title: str) -> None:
    """Print a visually distinct header banner."""
    width = 68
    print("\n" + "=" * width)
    print(f"  {title.center(width - 4)}")
    print("=" * width)


def print_table(headers: list[str], rows: list[list[Any]]) -> None:
    """Format and print tabular data with aligned borders."""
    if not rows:
        print("\n  (No records found)\n")
        return

    str_rows = [[str(cell) for cell in row] for row in rows]
    col_widths = [len(h) for h in headers]

    for row in str_rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(cell))
            else:
                col_widths.append(len(cell))

    sep = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    header_line = "| " + " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers)) + " |"

    print("\n" + sep)
    print(header_line)
    print(sep)
    for row in str_rows:
        line = "| " + " | ".join(f"{cell:<{col_widths[i]}}" for i, cell in enumerate(row)) + " |"
        print(line)
    print(sep + "\n")


def prompt_str(
    prompt: str,
    required: bool = True,
    default: Optional[str] = None,
    accepted_type: Optional[str] = None,
) -> Optional[str]:
    """Prompt the user for a string with whitespace trimming, defaults, and validation.

    accepted_type options:
    - "name" or "alpha": must contain letters and cannot contain numbers or digits.
    - "email": must match valid email format (e.g. user@example.com).
    - "phone" or "phone number": must contain only valid phone digits, spaces, and '+'.
    - None: any text.
    """
    while True:
        default_hint = f" [{default}]" if default is not None else ""
        try:
            val = input(f"{prompt}{default_hint}: ").strip()
        except EOFError:
            return default

        if not val and default is not None:
            val = default

        if not val:
            if required:
                print("  [!] This field cannot be empty. Please enter a value.")
                continue
            return None

        # Type-specific validation
        if accepted_type in ("name", "alpha"):
            if any(c.isdigit() for c in val):
                print("  [!] Invalid name: names cannot contain numbers or digits.")
                continue
            if not any(c.isalpha() for c in val) or not re.match(r"^[A-Za-z\s\-\'\.]+$", val):
                print("  [!] Invalid name: must contain letters (allowed: letters, spaces, hyphens, apostrophes).")
                continue

        elif accepted_type == "email":
            if not re.match(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,}$", val):
                print("  [!] Invalid email format. Please enter a valid address (e.g. student@example.com).")
                continue

        elif accepted_type in ("phone", "phone number"):
            if not re.match(r"^[\d\s\-\+\(\)]+$", val):
                print("  [!] Invalid phone number: may only contain digits, spaces, hyphens, and a leading '+'.")
                continue

        return val


def prompt_int(prompt: str, required: bool = True, default: Optional[int] = None) -> Optional[int]:
    """Prompt the user for an integer, catching invalid entries gracefully."""
    while True:
        default_hint = f" [{default}]" if default is not None else ""
        try:
            val = input(f"{prompt}{default_hint}: ").strip()
        except EOFError:
            return default
        if not val and default is not None:
            return default
        if not val and not required:
            return None
        if not val and required:
            print("  [!] An integer value is required.")
            continue
        try:
            return int(val)
        except ValueError:
            print("  [!] Invalid number. Please enter a valid integer.")


def prompt_date(prompt: str, default: Optional[date] = None) -> Optional[date]:
    """Prompt the user for a date in YYYY-MM-DD format."""
    while True:
        default_hint = f" [{default.isoformat()}]" if default else ""
        try:
            val = input(f"{prompt}{default_hint}: ").strip()
        except EOFError:
            return default
        if not val and default:
            return default
        if not val:
            print("  [!] Date is required.")
            continue
        try:
            return date.fromisoformat(val)
        except ValueError:
            print("  [!] Invalid date format. Please use YYYY-MM-DD (e.g., 2026-10-15).")


# ======================================================================
# Menu Displays & Action Handlers
# ======================================================================

def print_main_menu():
    """Display the main application menu."""
    print_banner("Campus MakerSpace Checkout System")
    print("  1. Member Management       (Register, List, Update, Search)")
    print("  2. Equipment Management    (Register, List, Update, Status, Search)")
    print("  3. Loans & Checkouts       (Checkout, Return, Active Loans)")
    print("  4. SQL Reports             (Borrowed, Overdue, Member History)")
    print("  0. Exit Application")
    print("-" * 68)


def handle_member_menu(service: MakerSpaceService):
    """Handle member-related CLI actions."""
    while True:
        print_banner("Member Management")
        print("  1. Register New Member")
        print("  2. List All Members")
        print("  3. Update Member")
        print("  4. Search Members")
        print("  0. Back to Main Menu")
        print("-" * 68)

        choice = prompt_str("Select an option", required=True)
        if choice == "0":
            break

        elif choice == "1":
            print("\n-- Register New Member --")
            name = prompt_str("Member Full Name", accepted_type="name")
            email = prompt_str("Member Email", accepted_type="email")
            phone = prompt_str("Member Phone (optional)", required=False, accepted_type="phone") or ""
            if not name or not email:
                print("  [!] Name and email are required.")
                continue
            try:
                member = service.register_member(name, email, phone)
                print(f"  [+] Member registered successfully! (Name: {member.name}, Email: {member.email})")
            except ValueError as e:
                print(f"  [!] Error: {e}")

        elif choice == "2":
            members = service.list_members()
            rows = [[m.id, m.name, m.email, m.phone or "-"] for m in members]
            print_table(["ID", "Name", "Email", "Phone"], rows)

        elif choice == "3":
            print("\n-- Update Member --")
            member_id = prompt_int("Enter Member ID to update")
            if not member_id:
                continue
            existing = service.get_member(member_id)
            if not existing:
                print(f"  [!] Member with ID {member_id} not found.")
                continue

            print(f"  Updating Member: {existing.name} ({existing.email})")
            name = prompt_str("New Name", required=True, default=existing.name, accepted_type="name")
            email = prompt_str("New Email", required=True, default=existing.email, accepted_type="email")
            phone = prompt_str("New Phone", required=False, default=existing.phone, accepted_type="phone") or ""
            if not name or not email:
                print("  [!] Name and email cannot be empty.")
                continue

            try:
                updated = service.update_member(member_id, name, email, phone)
                print(f"  [+] Member updated successfully! (ID: {updated.id}, Name: {updated.name})")
            except ValueError as e:
                print(f"  [!] Error: {e}")

        elif choice == "4":
            print("\n-- Search Members --")
            query = prompt_str("Enter name, email, or member ID to search")
            if not query:
                continue
            results = service.search_members(query)
            rows = [[m.id, m.name, m.email, m.phone or "-"] for m in results]
            print_table(["ID", "Name", "Email", "Phone"], rows)

        else:
            print("  [!] Invalid choice. Please choose from the numbered menu.")


def handle_equipment_menu(service: MakerSpaceService):
    """Handle equipment-related CLI actions."""
    while True:
        print_banner("Equipment Inventory Management")
        print("  1. Register New Equipment")
        print("  2. List All Equipment")
        print("  3. Update Equipment Details")
        print("  4. Update Equipment Status")
        print("  5. Search Equipment")
        print("  0. Back to Main Menu")
        print("-" * 68)

        choice = prompt_str("Select an option", required=True)
        if choice == "0":
            break

        elif choice == "1":
            print("\n-- Register New Equipment --")
            name = prompt_str("Equipment Name")
            category = prompt_str("Category (e.g. 3D Printing, Woodworking, Electronics)")
            desc = prompt_str("Description (optional)", required=False) or ""
            if not name or not category:
                print("  [!] Name and category are required.")
                continue
            try:
                eq = service.register_equipment(name, category, desc)
                print(f"  [+] Equipment registered successfully! (Name: {eq.name}, Status: {eq.status})")
            except ValueError as e:
                print(f"  [!] Error: {e}")

        elif choice == "2":
            equipments = service.list_equipment()
            rows = [[e.id, e.name, e.category, e.description or "-", e.status] for e in equipments]
            print_table(["ID", "Name", "Category", "Description", "Status"], rows)

        elif choice == "3":
            print("\n-- Update Equipment Details --")
            eq_id = prompt_int("Enter Equipment ID to update")
            if not eq_id:
                continue
            existing = service.get_equipment(eq_id)
            if not existing:
                print(f"  [!] Equipment with ID {eq_id} not found.")
                continue

            name = prompt_str("New Name", required=True, default=existing.name)
            category = prompt_str("New Category", required=True, default=existing.category)
            desc = prompt_str("New Description", required=False, default=existing.description) or ""
            if not name or not category:
                print("  [!] Name and category cannot be empty.")
                continue

            try:
                updated = service.update_equipment(eq_id, name, category, desc)
                print(f"  [+] Equipment details updated! (ID: {updated.id}, Name: {updated.name})")
            except ValueError as e:
                print(f"  [!] Error: {e}")

        elif choice == "4":
            print("\n-- Update Equipment Status --")
            eq_id = prompt_int("Enter Equipment ID")
            if not eq_id:
                continue
            existing = service.get_equipment(eq_id)
            if not existing:
                print(f"  [!] Equipment with ID {eq_id} not found.")
                continue

            print(f"  Current status: {existing.status}")
            print("  Allowed statuses: available, unavailable, damaged, lost")
            new_status = prompt_str("New Status", required=True)
            if not new_status:
                continue

            try:
                updated = service.update_equipment_status(eq_id, new_status.strip().lower())
                print(f"  [+] Equipment status updated to '{updated.status}'!")
            except ValueError as e:
                print(f"  [!] Error: {e}")

        elif choice == "5":
            print("\n-- Search Equipment --")
            query = prompt_str("Enter name, category, description, or ID")
            if not query:
                continue
            results = service.search_equipment(query)
            rows = [[e.id, e.name, e.category, e.description or "-", e.status] for e in results]
            print_table(["ID", "Name", "Category", "Description", "Status"], rows)

        else:
            print("  [!] Invalid choice. Please choose from the numbered menu.")


def handle_loan_menu(service: MakerSpaceService):
    """Handle loan-related CLI actions."""
    while True:
        print_banner("Loan & Checkout Operations")
        print("  1. Create New Loan / Checkout")
        print("  2. Return Loan (Check In)")
        print("  3. List Active Loans")
        print("  0. Back to Main Menu")
        print("-" * 68)

        choice = prompt_str("Select an option", required=True)
        if choice == "0":
            break

        elif choice == "1":
            print("\n-- Create New Loan / Checkout --")
            member_id = prompt_int("Enter Member ID")
            if not member_id:
                continue
            member = service.get_member(member_id)
            if not member:
                print(f"  [!] Member with ID {member_id} not found.")
                continue

            equipment_id = prompt_int("Enter Equipment ID")
            if not equipment_id:
                continue
            equipment = service.get_equipment(equipment_id)
            if not equipment:
                print(f"  [!] Equipment with ID {equipment_id} not found.")
                continue
            if not equipment.is_available():
                print(f"  [!] Equipment '{equipment.name}' is currently '{equipment.status}' and cannot be borrowed.")
                continue

            default_due = date.today() + timedelta(days=14)
            due_date = prompt_date("Enter Due Date (YYYY-MM-DD)", default=default_due)
            if not due_date:
                continue

            try:
                loan = service.create_loan(member_id, equipment_id, due_date)
                print(f"\n  [+] Loan created successfully!")
                print(f"      Loan ID    : {loan.id}")
                print(f"      Member     : {loan.member.name}")
                print(f"      Equipment  : {loan.equipment.name}")
                print(f"      Due Date   : {loan.due_date}")
                print(f"      Status     : {loan.status}")
            except ValueError as e:
                print(f"  [!] Error: {e}")

        elif choice == "2":
            print("\n-- Return Loan --")
            loan_id = prompt_int("Enter Loan ID to return")
            if not loan_id:
                continue
            loan = service.get_loan(loan_id)
            if not loan:
                print(f"  [!] Loan with ID {loan_id} not found.")
                continue
            if not loan.is_active():
                print(f"  [!] Loan {loan_id} is already marked closed (returned on {loan.return_date}).")
                continue

            returned_on = prompt_date("Enter Return Date (YYYY-MM-DD)", default=date.today())
            try:
                closed_loan = service.return_loan(loan_id, returned_on)
                print(f"  [+] Loan #{closed_loan.id} returned successfully!")
                print(f"      Equipment '{closed_loan.equipment.name}' is now marked available.")
            except ValueError as e:
                print(f"  [!] Error: {e}")

        elif choice == "3":
            active_loans = service.list_active_loans()
            rows = [
                [
                    loan.id,
                    loan.member.name,
                    loan.equipment.name,
                    loan.checkout_date,
                    loan.due_date,
                    loan.status,
                ]
                for loan in active_loans
            ]
            print_table(
                ["Loan ID", "Member", "Equipment", "Checkout Date", "Due Date", "Status"],
                rows,
            )

        else:
            print("  [!] Invalid choice. Please choose from the numbered menu.")


def handle_reports_menu(service: MakerSpaceService):
    """Handle report-related CLI actions."""
    while True:
        print_banner("SQL Reports")
        print("  1. Currently Borrowed Equipment")
        print("  2. Overdue Loans Report")
        print("  3. Member Loan History")
        print("  0. Back to Main Menu")
        print("-" * 68)

        choice = prompt_str("Select an option", required=True)
        if choice == "0":
            break

        elif choice == "1":
            report = service.report_currently_borrowed()
            rows = [
                [
                    item["loan_id"],
                    item["equipment_name"],
                    item["equipment_category"],
                    item["member_name"],
                    item["member_email"],
                    item["checkout_date"],
                    item["due_date"],
                ]
                for item in report
            ]
            print_banner("Report: Currently Borrowed Equipment")
            print_table(
                ["Loan ID", "Equipment", "Category", "Borrower", "Email", "Checkout Date", "Due Date"],
                rows,
            )

        elif choice == "2":
            check_date = prompt_date("Enter reference date for overdue check", default=date.today())
            report = service.report_overdue_loans(check_date)
            rows = [
                [
                    item["loan_id"],
                    item["member_name"],
                    item["equipment_name"],
                    item["due_date"],
                    f"{item['days_overdue']} days",
                    item["status"],
                ]
                for item in report
            ]
            print_banner(f"Report: Overdue Loans (as of {check_date})")
            print_table(
                ["Loan ID", "Borrower", "Equipment", "Due Date", "Overdue By", "Status"],
                rows,
            )

        elif choice == "3":
            member_id = prompt_int("Enter Member ID for loan history")
            if not member_id:
                continue
            member = service.get_member(member_id)
            if not member:
                print(f"  [!] Member with ID {member_id} not found.")
                continue

            history = service.report_member_history(member_id)
            rows = [
                [
                    item["loan_id"],
                    item["equipment_name"],
                    item["equipment_category"],
                    item["checkout_date"],
                    item["due_date"],
                    item["return_date"] or "Still Checked Out",
                    item["status"],
                ]
                for item in history
            ]
            print_banner(f"Loan History for {member.name} (ID: {member.id})")
            print_table(
                ["Loan ID", "Equipment", "Category", "Checkout Date", "Due Date", "Returned On", "Status"],
                rows,
            )

        else:
            print("  [!] Invalid choice. Please choose from the numbered menu.")


def run_application():
    """Start and continuously run the CLI application."""
    db_path = Path("data/makerspace.db")
    database = Database(db_path)

    try:
        database.initialize_schema()
        service = MakerSpaceService(database)

        print("\nWelcome to the Campus MakerSpace Checkout System!")
        print("Database initialised and ready.")

        while True:
            print_main_menu()
            choice = prompt_str("Select a main menu option", required=True)

            if choice == "0":
                print("\nThank you for using Campus MakerSpace Checkout System. Goodbye!\n")
                break
            elif choice == "1":
                handle_member_menu(service)
            elif choice == "2":
                handle_equipment_menu(service)
            elif choice == "3":
                handle_loan_menu(service)
            elif choice == "4":
                handle_reports_menu(service)
            else:
                print("  [!] Invalid option. Please enter a number between 0 and 4.")

    except KeyboardInterrupt:
        print("\n\nApplication interrupted by operator. Exiting cleanly...")
    except Exception as e:
        print(f"\n[!] Unexpected error encountered: {e}")
    finally:
        database.close()


if __name__ == "__main__":
    run_application()
