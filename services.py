"""Business operations for the Campus MakerSpace Checkout System.

This layer coordinates:
- domain models from models.py;
- database operations from database.py;
- validation and business rules.

The CLI should call these methods instead of writing SQL directly. 
"""

from datetime import date, timedelta
import re
from typing import Any, Optional

from database import Database
from models import Equipment, Loan, Member


class MakerSpaceService:
    """Coordinate members, equipment, loans, and reports."""

    def __init__(self, database: Database):
        """Create a service using the provided database.

        This function creates a service using the provided database.
        """
        self.database = database

    def register_member(
        self,
        name: str,
        email: str,
        phone: str = "",
    ) -> Member:
        """Create and persist a new member.

        This function creates a new member and returns the created Member object.
        """
        name = name.strip()
        email = email.strip().lower()
        phone = phone.strip()

        if not name:
            raise ValueError("Member name is required and cannot be empty")
        if any(c.isdigit() for c in name):
            raise ValueError("Member name cannot contain numbers or digits")
        if not any(c.isalpha() for c in name) or not re.match(r"^[A-Za-z\s\-\'\.]+$", name):
            raise ValueError("Member name must contain valid letters and cannot consist of symbols or numbers")

        if not email or not re.match(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,}$", email):
            raise ValueError(f"Invalid email format: '{email}'. Expected format: user@example.com")

        if phone and not re.match(r"^[\d\s\-\+\(\)]+$", phone):
            raise ValueError(f"Invalid phone number: '{phone}'. Allowed characters: digits, spaces, hyphens, and a leading '+'")

        is_exist = self.database.fetch_one("SELECT * FROM members WHERE email = ?", (email,))
        if is_exist:
            raise ValueError(f"Member with email {email} already exists")
        member = Member(name=name, email=email, phone=phone)
        self.database.execute("INSERT INTO members (name, email, phone) VALUES (?, ?, ?)", (member.name, member.email, member.phone))
        
        return member

    def list_members(self) -> list[Member]:
        """Return all registered members.

        This function returns all registered members.
        """
        members = self.database.fetch_all("SELECT * FROM members")
        return [
            Member(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                phone=row["phone"] or "",
            )
            for row in members
        ]

    def update_member(
        self,
        member_id: int,
        name: str,
        email: str,
        phone: str = "",
    ) -> Member:
        """Update an existing member.

        This function updates an existing member and returns the updated Member object.
        """
        name = name.strip()
        email = email.strip().lower()
        phone = phone.strip()

        if not member_id:
            raise ValueError("Member ID is required for updating a member")

        if not name:
            raise ValueError("Member name is required and cannot be empty")
        if any(c.isdigit() for c in name):
            raise ValueError("Member name cannot contain numbers or digits")
        if not any(c.isalpha() for c in name) or not re.match(r"^[A-Za-z\s\-\'\.]+$", name):
            raise ValueError("Member name must contain valid letters and cannot consist of symbols or numbers")

        if not email or not re.match(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,}$", email):
            raise ValueError(f"Invalid email format: '{email}'. Expected format: user@example.com")

        if phone and not re.match(r"^[\d\s\-\+\(\)]+$", phone):
            raise ValueError(f"Invalid phone number: '{phone}'. Allowed characters: digits, spaces, hyphens, and a leading '+'")

        member = self.get_member(member_id)
        if not member:
            raise ValueError(f"Member with ID {member_id} not found")

        # Check if email is already used by another member
        existing_owner = self.database.fetch_one(
            "SELECT id FROM members WHERE email = ? AND id != ?",
            (email, member_id),
        )
        if existing_owner:
            raise ValueError(f"Member with email {email} already exists")

        self.database.execute("UPDATE members SET name = ?, email = ?, phone = ? WHERE id = ?", (name, email, phone, member_id))

        updated_member = self.get_member(member_id)
        if not updated_member:
            raise ValueError(f"Member with ID {member_id} not found")
        return updated_member

    def get_member(self, member_id: int) -> Optional[Member]:
        """Find one member by ID.

        This function returns a member by ID.
        """
        if not member_id:
            raise ValueError("Member ID is required for getting a member")
            
        member = self.database.fetch_one("SELECT * FROM members WHERE id = ?", (member_id,))
        if not member:
            return None
        return Member(
            id=member["id"],
            name=member["name"],
            email=member["email"],
            phone=member["phone"] or "",
        )

    def register_equipment(
        self,
        name: str,
        category: str,
        description: str = "",
    ) -> Equipment:
        """Create and persist equipment.

        This function registers equipment and returns the registered Equipment object.
        """
        category = category.strip().lower()
        name = name.strip()
        description = description.strip()

        if not name or not category:
            raise ValueError("Name and category are required for registering equipment")

        is_exist = self.database.fetch_one("SELECT * FROM equipment WHERE name = ? AND category = ?", (name, category))
        if is_exist:
            raise ValueError(f"Equipment with name {name} and category {category} already exists")

        equipment = Equipment(name=name, category=category, description=description)
        self.database.execute("INSERT INTO equipment (name, category, description) VALUES (?, ?, ?)", (equipment.name, equipment.category, equipment.description))
        return equipment

    def list_equipment(self) -> list[Equipment]:
        """Return all equipment.

        This function returns all equipment.
        """
        equipments_db = self.database.fetch_all("SELECT * FROM equipment")
        return [
            Equipment(
                id=row["id"],
                name=row["name"],
                category=row["category"],
                description=row["description"] or "",
                status=row["status"],
            )
            for row in equipments_db
        ]

    def update_equipment(
        self,
        equipment_id: int,
        name: str,
        category: str,
        description: str,
    ) -> Equipment:
        """Update equipment information.

        This function updates equipment information and returns the updated Equipment object.
        """
        name = name.strip()
        category = category.strip().lower()
        description = description.strip()

        if not equipment_id:
            raise ValueError("Equipment ID is required for updating equipment")
        equipment = self.get_equipment(equipment_id)
        if not equipment:
            raise ValueError(f"Equipment with ID {equipment_id} not found")

        self.database.execute("UPDATE equipment SET name = ?, category = ?, description = ? WHERE id = ?", (name, category, description, equipment_id))

        updated_equipment = self.get_equipment(equipment_id)
        if not updated_equipment:
            raise ValueError(f"Equipment with ID {equipment_id} not found")
        return updated_equipment

    def update_equipment_status(self, equipment_id: int, status: str) -> Equipment:
        """Update equipment status

        This function updates equipment status and return the updated equipment.
        """
        if not equipment_id:
            raise ValueError("Equipment ID is required for updating equipment status")
        equipment = self.get_equipment(equipment_id)
        if not equipment:
            raise ValueError(f"Equipment with ID {equipment_id} not found")
        
        equipment.update_status(status)
        self.database.execute("UPDATE equipment SET status = ? WHERE id = ?", (equipment.status, equipment_id))
        return equipment

    def get_equipment(self, equipment_id: int) -> Optional[Equipment]:
        """Find one equipment item by ID.

        This function returns equipment by ID.
        """
        if not equipment_id:
            raise ValueError("Equipment ID is required for getting equipment")
        equipment = self.database.fetch_one("SELECT * FROM equipment WHERE id = ?", (equipment_id,))
        if not equipment:
            return None
        
        return Equipment(
            id=equipment["id"],
            name=equipment["name"],
            category=equipment["category"],
            description=equipment["description"] or "",
            status=equipment["status"],
        )

    def create_loan(
        self,
        member_id: int,
        equipment_id: int,
        due_date: date,
    ) -> Loan:
        """Create a checkout after applying all required business rules.

        This function creates a loan and returns the created Loan object.
        """
        if not member_id or not equipment_id or not due_date:
            raise ValueError("Member ID, equipment ID, and due date are required for creating a loan")

        member = self.get_member(member_id)
        if not member:
            raise ValueError(f"Member with ID {member_id} not found")

        equipment = self.get_equipment(equipment_id)
        if not equipment:
            raise ValueError(f"Equipment with ID {equipment_id} not found")

        if equipment.status != "available":
            raise ValueError(f"Equipment with ID {equipment_id} is not available")

        if due_date < date.today():
            raise ValueError("Due date must be in the future")

        if due_date > date.today() + timedelta(days=30):
            raise ValueError("Due date must be within 30 days")
        
        still_loaning = self.database.fetch_one("SELECT * FROM loans WHERE equipment_id = ? AND return_date IS NULL", (equipment_id,))
        if still_loaning:
            raise ValueError(f"Equipment with ID {equipment_id} is still loaned")

        due_date_val = due_date.isoformat() if hasattr(due_date, "isoformat") else str(due_date)
        cursor = self.database.execute(
            "INSERT INTO loans (member_id, equipment_id, due_date) VALUES (?, ?, ?)",
            (member_id, equipment_id, due_date_val),
        )
        self.database.execute(
            "UPDATE equipment SET status = 'unavailable' WHERE id = ?",
            (equipment_id,),
        )

        equipment.mark_borrowed()
        loan = Loan(
            id=cursor.lastrowid,
            member=member,
            equipment=equipment,
            checkout_date=date.today(),
            due_date=due_date,
        )
        return loan

    def return_loan(
        self,
        loan_id: int,
        returned_on: Optional[date] = None,
    ) -> Loan:
        """Return/close an active loan."""
        if not loan_id:
            raise ValueError("Loan ID is required for returning a loan")
        loan = self.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan with ID {loan_id} not found")
        if loan.equipment.id is None:
            raise ValueError("Loan equipment has no valid ID")
        equipment = self.get_equipment(loan.equipment.id)
        if not equipment:
            raise ValueError(f"Equipment with ID {loan.equipment.id} not found")
        if not loan.is_active():
            raise ValueError(f"Loan with ID {loan_id} is not active")

        loan.close(returned_on)

        return_date_val = (
            loan.return_date.isoformat()
            if loan.return_date is not None
            else date.today().isoformat()
        )
        self.database.execute(
            "UPDATE loans SET return_date = ?, status = 'closed' WHERE id = ?",
            (return_date_val, loan_id),
        )
        self.database.execute(
            "UPDATE equipment SET status = 'available' WHERE id = ?",
            (loan.equipment.id,),
        )

        return loan

    def _row_to_loan(self, row: Any) -> Loan:
        """Convert a joined loan database row into a Loan model."""
        member = Member(
            id=row["member_id"],
            name=row["member_name"],
            email=row["member_email"],
            phone=row["member_phone"] or "",
        )
        equipment = Equipment(
            id=row["equipment_id"],
            name=row["equipment_name"],
            category=row["equipment_category"],
            description=row["equipment_description"] or "",
            status=row["equipment_status"],
        )
        checkout_date = (
            date.fromisoformat(row["checkout_date"][:10])
            if isinstance(row["checkout_date"], str)
            else row["checkout_date"]
        )
        due_date = (
            date.fromisoformat(row["due_date"][:10])
            if isinstance(row["due_date"], str)
            else row["due_date"]
        )
        return_date = (
            date.fromisoformat(row["return_date"][:10])
            if isinstance(row["return_date"], str) and row["return_date"]
            else row["return_date"]
        )
        return Loan(
            id=row["loan_id"],
            member=member,
            equipment=equipment,
            checkout_date=checkout_date,
            due_date=due_date,
            return_date=return_date,
            status=row["loan_status"],
        )

    def get_loan(self, loan_id: int) -> Optional[Loan]:
        """Find a loan by ID.

        This function returns a loan by ID.
        """
        if not loan_id:
            raise ValueError("Loan ID is required for getting a loan")

        query = """
            SELECT 
                l.id AS loan_id,
                l.checkout_date,
                l.due_date,
                l.return_date,
                l.status AS loan_status,
                m.id AS member_id,
                m.name AS member_name,
                m.email AS member_email,
                m.phone AS member_phone,
                e.id AS equipment_id,
                e.name AS equipment_name,
                e.category AS equipment_category,
                e.description AS equipment_description,
                e.status AS equipment_status
            FROM loans l
            JOIN members m ON l.member_id = m.id
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.id = ?
        """
        row = self.database.fetch_one(query, (loan_id,))
        if not row:
            return None
        return self._row_to_loan(row)

    def list_active_loans(self) -> list[Loan]:
        """Return currently active loans.

        This function returns all active loans.
        """
        query = """
            SELECT 
                l.id AS loan_id,
                l.checkout_date,
                l.due_date,
                l.return_date,
                l.status AS loan_status,
                m.id AS member_id,
                m.name AS member_name,
                m.email AS member_email,
                m.phone AS member_phone,
                e.id AS equipment_id,
                e.name AS equipment_name,
                e.category AS equipment_category,
                e.description AS equipment_description,
                e.status AS equipment_status
            FROM loans l
            JOIN members m ON l.member_id = m.id
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.status = 'active'
        """
        rows = self.database.fetch_all(query)
        return [self._row_to_loan(row) for row in rows]

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_members(self, query: str) -> list[Member]:
        """Search members by name, email, or ID as appropriate.

        Uses a parameterized SQL query to match query against ID, name, or email.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        search_pattern = f"%{clean_query}%"
        sql = """
            SELECT id, name, email, phone 
            FROM members 
            WHERE id = ? OR name LIKE ? OR email LIKE ?
            ORDER BY name ASC
        """
        member_id = int(clean_query) if clean_query.isdigit() else -1
        rows = self.database.fetch_all(sql, (member_id, search_pattern, search_pattern))
        return [
            Member(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                phone=row["phone"] or "",
            )
            for row in rows
        ]

    def search_equipment(self, query: str) -> list[Equipment]:
        """Search equipment by name, category, or ID as appropriate.

        Uses a parameterized SQL query to match query against ID, name, category, or description.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        search_pattern = f"%{clean_query}%"
        sql = """
            SELECT id, name, category, description, status 
            FROM equipment 
            WHERE id = ? OR name LIKE ? OR category LIKE ? OR description LIKE ?
            ORDER BY name ASC
        """
        equipment_id = int(clean_query) if clean_query.isdigit() else -1
        rows = self.database.fetch_all(
            sql,
            (equipment_id, search_pattern, search_pattern, search_pattern),
        )
        return [
            Equipment(
                id=row["id"],
                name=row["name"],
                category=row["category"],
                description=row["description"] or "",
                status=row["status"],
            )
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    def report_currently_borrowed(self) -> list[dict[str, Any]]:
        """Return a SQL report of currently borrowed equipment.

        Joins loans, members, and equipment to present active checkouts.
        """
        query = """
            SELECT 
                l.id AS loan_id,
                l.checkout_date,
                l.due_date,
                l.status AS loan_status,
                m.id AS member_id,
                m.name AS member_name,
                m.email AS member_email,
                m.phone AS member_phone,
                e.id AS equipment_id,
                e.name AS equipment_name,
                e.category AS equipment_category
            FROM loans l
            JOIN members m ON l.member_id = m.id
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.status = 'active'
            ORDER BY l.due_date ASC
        """
        rows = self.database.fetch_all(query)
        report = []
        for row in rows:
            report.append({
                "loan_id": row["loan_id"],
                "member_id": row["member_id"],
                "member_name": row["member_name"],
                "member_email": row["member_email"],
                "member_phone": row["member_phone"] or "",
                "equipment_id": row["equipment_id"],
                "equipment_name": row["equipment_name"],
                "equipment_category": row["equipment_category"],
                "checkout_date": row["checkout_date"],
                "due_date": row["due_date"],
                "status": row["loan_status"],
            })
        return report

    def report_overdue_loans(self, today: Optional[date] = None) -> list[dict[str, Any]]:
        """Return a SQL report of overdue active loans.

        Uses SQL to identify active loans whose due date has passed compared to today.
        """
        check_date = today or date.today()
        query = """
            SELECT 
                l.id AS loan_id,
                l.checkout_date,
                l.due_date,
                l.status AS loan_status,
                m.id AS member_id,
                m.name AS member_name,
                m.email AS member_email,
                m.phone AS member_phone,
                e.id AS equipment_id,
                e.name AS equipment_name,
                e.category AS equipment_category
            FROM loans l
            JOIN members m ON l.member_id = m.id
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.status = 'active' AND l.due_date < ?
            ORDER BY l.due_date ASC
        """
        rows = self.database.fetch_all(query, (check_date.isoformat(),))
        report = []
        for row in rows:
            due = (
                date.fromisoformat(row["due_date"][:10])
                if isinstance(row["due_date"], str)
                else row["due_date"]
            )
            days_overdue = (check_date - due).days
            report.append({
                "loan_id": row["loan_id"],
                "member_id": row["member_id"],
                "member_name": row["member_name"],
                "member_email": row["member_email"],
                "member_phone": row["member_phone"] or "",
                "equipment_id": row["equipment_id"],
                "equipment_name": row["equipment_name"],
                "equipment_category": row["equipment_category"],
                "checkout_date": row["checkout_date"],
                "due_date": row["due_date"],
                "days_overdue": days_overdue,
                "status": row["loan_status"],
            })
        return report

    def report_member_history(self, member_id: int) -> list[dict[str, Any]]:
        """Return the loan history for one member.

        Uses a SQL join between loans and equipment for a specific member.
        """
        if not member_id:
            raise ValueError("Member ID is required to retrieve loan history")

        member = self.get_member(member_id)
        if not member:
            raise ValueError(f"Member with ID {member_id} not found")

        query = """
            SELECT 
                l.id AS loan_id,
                l.checkout_date,
                l.due_date,
                l.return_date,
                l.status AS loan_status,
                e.id AS equipment_id,
                e.name AS equipment_name,
                e.category AS equipment_category
            FROM loans l
            JOIN equipment e ON l.equipment_id = e.id
            WHERE l.member_id = ?
            ORDER BY l.checkout_date DESC, l.id DESC
        """
        rows = self.database.fetch_all(query, (member_id,))
        history = []
        for row in rows:
            history.append({
                "loan_id": row["loan_id"],
                "equipment_id": row["equipment_id"],
                "equipment_name": row["equipment_name"],
                "equipment_category": row["equipment_category"],
                "checkout_date": row["checkout_date"],
                "due_date": row["due_date"],
                "return_date": row["return_date"],
                "status": row["loan_status"],
            })
        return history
