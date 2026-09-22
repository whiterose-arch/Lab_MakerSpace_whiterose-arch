"""Domain models for the Campus MakerSpace Checkout System.

These classes represent the core business entities:
- Member
- Equipment
- Loan

Keep business behaviour close to the object it belongs to.
Avoid putting SQLite-specific code in these classes.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

@dataclass
class Member:
    """Represent a registered makerspace member.

    Attributes:
    - id: Optional[int] = None
    - name: str = ""
    - email: str = ""
    - phone: str = ""
    """

    id: Optional[int] = None
    name: str = ""
    email: str = ""
    phone: str = ""

    def display_name(self) -> str:
        """Return a readable member name.

        This function returns the name of the member in the format "Last, First".
        """
        return f"{self.name.split(' ')[1]}, {self.name.split(' ')[0]}"


@dataclass
class Equipment:
    """Represent one item of makerspace equipment.

    Attributes:
    - id: Optional[int] = None
    - name: str = ""
    - category: str = ""
    - description: str = ""
    - status: str = "available" # available, unavailable, damaged, lost
    """

    id: Optional[int] = None
    name: str = ""
    category: str = ""
    description: str = ""
    status: str = "available" # available, unavailable, damaged, lost

    def is_available(self) -> bool:
        """Return True when the equipment can be borrowed.

        This function returns True when the equipment is available.
        """
        return self.status == "available"

    def mark_borrowed(self) -> None:
        """Mark this equipment as unavailable because it is on loan.

        This function marks the equipment as unavailable.
        """
        self.update_status("unavailable")

    def mark_damaged(self) -> None:
        """Mark this equipment as damaged.

        This function marks the equipment as damaged.
        """
        self.update_status("damaged")

    def mark_lost(self) -> None:
        """Mark this equipment as lost.

        This function marks the equipment as lost.
        """
        self.update_status("lost")

    def mark_available(self) -> None:
        """Mark this equipment as available again.

        This function marks the equipment as available.
        """
        self.update_status("available")

    def update_status(self, status: str) -> None:
        """Update the equipment's status

        This function updates the status of the equipment.
        """
        if status == "available":
            self.status = "available"
        elif status == "unavailable":
            self.status = "unavailable"
        elif status == "damaged":
            self.status = "damaged"
        elif status == "lost":
            self.status = "lost"
        else:
            raise ValueError(f"Invalid equipment status: {status}")


@dataclass
class Loan:
    """Represent a checkout transaction between a member and equipment.

    Attributes:
    - id: Optional[int] = None
    - member: Member = Member()
    - equipment: Equipment = Equipment()
    - checkout_date: Optional[date] = None
    - due_date: Optional[date] = None
    - return_date: Optional[date] = None
    - status: str = "active" # active, closed
    """

    id: Optional[int] = None
    member: Member = field(default_factory=Member)
    equipment: Equipment = field(default_factory=Equipment)
    checkout_date: Optional[date] = None
    due_date: Optional[date] = None
    return_date: Optional[date] = None
    status: str = "active" # active, closed

    def is_active(self) -> bool:
        """Return True when this loan has not been returned.

        This function returns True when the loan is active.
        """
        return self.status == "active"

    def is_overdue(self, today: Optional[date] = None) -> bool:
        """Return True when an active loan is past its due date.

        This function returns True when the loan is overdue.
        """
        if not self.due_date or not self.is_active():
            return False
        current_date = today or date.today()
        return self.due_date < current_date

    def close(self, returned_on: Optional[date] = None) -> None:
        """Close the loan and record the return date.

        This function closes the loan and records the return date.
        """
        if self.status == "closed":
            raise ValueError(f"Loan with ID {self.id} is already closed")
        self.return_date = returned_on if returned_on else date.today()
        self.status = "closed"
        self.equipment.update_status("available")
