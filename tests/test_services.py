"""Tests for the MakerSpace service layer.

Comprehensive test suite covering:
- Member management and validation
- Equipment inventory and status transitions
- Loan checkout, business rules, and returns
- Search capabilities (members and equipment)
- SQL reports (currently borrowed, overdue loans, and member history)
"""

from datetime import date, timedelta
from pathlib import Path
import tempfile
import unittest

from database import Database
from services import MakerSpaceService


class TestMakerSpaceService(unittest.TestCase):
    """Test business rules, SQL operations, and edge cases in MakerSpaceService."""

    def setUp(self):
        """Set up an isolated temporary database for each test case."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_makerspace.db"
        self.db = Database(self.db_path)
        self.db.initialize_schema()
        self.service = MakerSpaceService(self.db)

    def tearDown(self):
        """Close database connection and clean up temporary directory."""
        self.db.close()
        self.temp_dir.cleanup()

    # ------------------------------------------------------------------
    # Member Tests
    # ------------------------------------------------------------------

    def test_register_member(self):
        """Verify a member can be created, persisted, and retrieved."""
        member = self.service.register_member("Alan Turing", "alan@cambridge.ac.uk", "0123456789")
        self.assertEqual(member.name, "Alan Turing")
        self.assertEqual(member.email, "alan@cambridge.ac.uk")

        members = self.service.list_members()
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].id, 1)
        self.assertEqual(members[0].name, "Alan Turing")
        self.assertEqual(members[0].email, "alan@cambridge.ac.uk")
        self.assertEqual(members[0].phone, "0123456789")

    def test_register_member_duplicate_email(self):
        """Verify duplicate member emails are rejected."""
        self.service.register_member("Grace Hopper", "grace@navy.mil")
        with self.assertRaises(ValueError):
            self.service.register_member("Grace Duplicate", "grace@navy.mil")

    def test_update_member(self):
        """Verify updating member information."""
        self.service.register_member("Ada Byron", "ada@example.com", "111")
        updated = self.service.update_member(1, "Ada Lovelace", "ada.lovelace@example.com", "999")
        self.assertEqual(updated.name, "Ada Lovelace")
        self.assertEqual(updated.email, "ada.lovelace@example.com")
        self.assertEqual(updated.phone, "999")

        fetched = self.service.get_member(1)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched.name, "Ada Lovelace")

    def test_update_member_not_found(self):
        """Verify updating a non-existent member raises ValueError."""
        with self.assertRaises(ValueError):
            self.service.update_member(999, "Ghost", "ghost@example.com")

    def test_get_member(self):
        """Verify get_member retrieves existing member and returns None for missing."""
        self.assertIsNone(self.service.get_member(404))
        with self.assertRaises(ValueError):
            self.service.get_member(0)

        created = self.service.register_member("Charles Babbage", "charles@babbage.org")
        fetched = self.service.get_member(1)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched.name, created.name)

    def test_search_members(self):
        """Verify member search by ID, name substring, and email substring."""
        self.service.register_member("Katherine Johnson", "katherine@nasa.gov", "123")
        self.service.register_member("Dorothy Vaughan", "dorothy@nasa.gov", "456")
        self.service.register_member("Mary Jackson", "mary@nasa.gov", "789")

        # By name substring
        name_results = self.service.search_members("johnson")
        self.assertEqual(len(name_results), 1)
        self.assertEqual(name_results[0].name, "Katherine Johnson")

        # By email domain
        email_results = self.service.search_members("nasa.gov")
        self.assertEqual(len(email_results), 3)

        # By exact ID
        id_results = self.service.search_members("2")
        self.assertEqual(len(id_results), 1)
        self.assertEqual(id_results[0].name, "Dorothy Vaughan")

        # Non-matching
        self.assertEqual(len(self.service.search_members("Einstein")), 0)

        # Empty or whitespace query
        self.assertEqual(len(self.service.search_members("   ")), 0)

    # ------------------------------------------------------------------
    # Equipment Tests
    # ------------------------------------------------------------------

    def test_create_equipment(self):
        """Verify equipment starts with the expected availability status."""
        eq = self.service.register_equipment("Soldering Station", "Electronics", "Adjustable temp")
        self.assertEqual(eq.name, "Soldering Station")
        self.assertEqual(eq.category, "electronics")
        self.assertEqual(eq.status, "available")
        self.assertTrue(eq.is_available())

        all_eq = self.service.list_equipment()
        self.assertEqual(len(all_eq), 1)
        self.assertEqual(all_eq[0].id, 1)
        self.assertEqual(all_eq[0].status, "available")

    def test_create_equipment_duplicate(self):
        """Verify duplicate equipment in the same category is rejected."""
        self.service.register_equipment("Laser Cutter", "Fabrication", "40W CO2")
        with self.assertRaises(ValueError):
            self.service.register_equipment("Laser Cutter", "Fabrication", "Duplicate")

    def test_create_equipment_missing_required_fields(self):
        """Verify creating equipment without name or category fails."""
        with self.assertRaises(ValueError):
            self.service.register_equipment("", "Fabrication")
        with self.assertRaises(ValueError):
            self.service.register_equipment("Lathe", "")

    def test_update_equipment(self):
        """Verify updating equipment properties."""
        self.service.register_equipment("Oscilloscope", "Electronics", "2-channel")
        updated = self.service.update_equipment(1, "Digital Oscilloscope", "electronics", "4-channel 100MHz")
        self.assertEqual(updated.name, "Digital Oscilloscope")
        self.assertEqual(updated.description, "4-channel 100MHz")

        fetched = self.service.get_equipment(1)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched.name, "Digital Oscilloscope")

    def test_update_equipment_status(self):
        """Verify updating equipment status transitions and invalid status rejection."""
        self.service.register_equipment("Multimeter", "Electronics")

        # Mark damaged
        damaged = self.service.update_equipment_status(1, "damaged")
        self.assertEqual(damaged.status, "damaged")

        # Mark lost
        lost = self.service.update_equipment_status(1, "lost")
        self.assertEqual(lost.status, "lost")

        # Restore available
        avail = self.service.update_equipment_status(1, "available")
        self.assertEqual(avail.status, "available")

        # Invalid status
        with self.assertRaises(ValueError):
            self.service.update_equipment_status(1, "destroyed")

    def test_search_equipment(self):
        """Verify equipment search by ID, name, category, and description."""
        self.service.register_equipment("Ultimaker Pro", "fabrication", "FDM printer")
        self.service.register_equipment("Formlabs Resin", "stereolithography", "SLA resin printer")
        self.service.register_equipment("Sewing Machine", "textiles", "Heavy duty stitcher")

        # By category
        cat_results = self.service.search_equipment("fabrication")
        self.assertEqual(len(cat_results), 1)
        self.assertEqual(cat_results[0].name, "Ultimaker Pro")

        # By description keyword
        desc_results = self.service.search_equipment("resin")
        self.assertEqual(len(desc_results), 1)
        self.assertEqual(desc_results[0].name, "Formlabs Resin")

        # By exact ID
        id_results = self.service.search_equipment("3")
        self.assertEqual(len(id_results), 1)
        self.assertEqual(id_results[0].name, "Sewing Machine")

        # Empty search
        self.assertEqual(len(self.service.search_equipment("")), 0)

    # ------------------------------------------------------------------
    # Loan & Checkout Tests
    # ------------------------------------------------------------------

    def test_checkout_requires_existing_member(self):
        """Verify checkout fails for an unknown member."""
        self.service.register_equipment("Drill Press", "Woodworking")
        due = date.today() + timedelta(days=7)
        with self.assertRaises(ValueError):
            self.service.create_loan(999, 1, due)

    def test_checkout_requires_available_equipment(self):
        """Verify unavailable, damaged, or lost equipment cannot be checked out."""
        self.service.register_member("Linus Torvalds", "linus@kernel.org")
        self.service.register_equipment("CNC Mill", "Machining")
        due = date.today() + timedelta(days=7)

        # Unknown equipment
        with self.assertRaises(ValueError):
            self.service.create_loan(1, 999, due)

        # Damaged equipment
        self.service.update_equipment_status(1, "damaged")
        with self.assertRaises(ValueError):
            self.service.create_loan(1, 1, due)

        # Lost equipment
        self.service.update_equipment_status(1, "lost")
        with self.assertRaises(ValueError):
            self.service.create_loan(1, 1, due)

    def test_checkout_due_date_rules(self):
        """Verify due date must be strictly in the future and <= 30 days."""
        self.service.register_member("Margaret Hamilton", "margaret@mit.edu")
        self.service.register_equipment("Logic Analyzer", "Electronics")

        # Past due date
        past_date = date.today() - timedelta(days=1)
        with self.assertRaises(ValueError):
            self.service.create_loan(1, 1, past_date)

        # Due date exceeding 30 days
        too_far = date.today() + timedelta(days=31)
        with self.assertRaises(ValueError):
            self.service.create_loan(1, 1, too_far)

    def test_checkout_success_and_duplicate_active_loan_fails(self):
        """Verify successful loan checkout and that double checkout of the same item fails."""
        self.service.register_member("Barbara Liskov", "barbara@mit.edu")
        self.service.register_member("Hedy Lamarr", "hedy@invention.com")
        self.service.register_equipment("VR Headset", "Gaming")

        due = date.today() + timedelta(days=14)
        loan = self.service.create_loan(1, 1, due)

        self.assertIsNotNone(loan.id)
        self.assertEqual(loan.member.name, "Barbara Liskov")
        self.assertEqual(loan.equipment.name, "VR Headset")
        self.assertEqual(loan.status, "active")

        # Equipment should now be marked unavailable
        eq = self.service.get_equipment(1)
        self.assertIsNotNone(eq)
        assert eq is not None
        self.assertEqual(eq.status, "unavailable")

        # Second member attempting to check out the same equipment must fail
        with self.assertRaises(ValueError):
            self.service.create_loan(2, 1, due)

    def test_return_makes_equipment_available(self):
        """Verify returning a loan changes equipment status back to available and closes loan."""
        self.service.register_member("Claude Shannon", "claude@bell-labs.com")
        self.service.register_equipment("Band Saw", "Woodworking")
        due = date.today() + timedelta(days=7)

        loan = self.service.create_loan(1, 1, due)
        self.assertEqual(loan.status, "active")

        # Return loan
        returned = self.service.return_loan(loan.id or 1)
        self.assertEqual(returned.status, "closed")
        self.assertEqual(returned.return_date, date.today())

        # Verify equipment is available again
        eq = self.service.get_equipment(1)
        self.assertIsNotNone(eq)
        assert eq is not None
        self.assertEqual(eq.status, "available")
        self.assertTrue(eq.is_available())

        # Attempting to return an already closed loan must raise ValueError
        with self.assertRaises(ValueError):
            self.service.return_loan(loan.id or 1)

    def test_list_active_loans(self):
        """Verify list_active_loans returns only currently active loans."""
        self.service.register_member("Member One", "m1@test.com")
        self.service.register_member("Member Two", "m2@test.com")
        self.service.register_equipment("Item A", "General")
        self.service.register_equipment("Item B", "General")

        due = date.today() + timedelta(days=5)
        loan1 = self.service.create_loan(1, 1, due)
        loan2 = self.service.create_loan(2, 2, due)

        active = self.service.list_active_loans()
        self.assertEqual(len(active), 2)

        # Return loan 1
        self.service.return_loan(loan1.id or 1)

        active_after = self.service.list_active_loans()
        self.assertEqual(len(active_after), 1)
        self.assertEqual(active_after[0].id, loan2.id)

    # ------------------------------------------------------------------
    # Report Tests
    # ------------------------------------------------------------------

    def test_report_currently_borrowed(self):
        """Verify report_currently_borrowed returns joined active loan details."""
        self.service.register_member("Borrower Alice", "alice@makerspace.org", "555-0100")
        self.service.register_equipment("Laser Welder", "Metalworking", "Precision welder")

        due = date.today() + timedelta(days=10)
        self.service.create_loan(1, 1, due)

        report = self.service.report_currently_borrowed()
        self.assertEqual(len(report), 1)
        row = report[0]
        self.assertEqual(row["member_name"], "Borrower Alice")
        self.assertEqual(row["member_email"], "alice@makerspace.org")
        self.assertEqual(row["equipment_name"], "Laser Welder")
        self.assertEqual(row["equipment_category"], "metalworking")
        self.assertEqual(row["status"], "active")

        # After returning, the report should be empty
        self.service.return_loan(row["loan_id"])
        self.assertEqual(len(self.service.report_currently_borrowed()), 0)

    def test_overdue_report(self):
        """Verify the overdue report correctly detects overdue active loans."""
        self.service.register_member("Late Member", "late@student.edu")
        self.service.register_member("OnTime Member", "ontime@student.edu")
        self.service.register_equipment("Air Compressor", "Pneumatics")
        self.service.register_equipment("Angle Grinder", "Metalworking")

        # Create loans with due dates
        due_late = date.today() + timedelta(days=3)
        due_ontime = date.today() + timedelta(days=10)

        loan_late = self.service.create_loan(1, 1, due_late)
        self.service.create_loan(2, 2, due_ontime)

        # Checking today: none are overdue
        self.assertEqual(len(self.service.report_overdue_loans(date.today())), 0)

        # Simulate checking 5 days in the future (loan 1 is overdue by 2 days, loan 2 is not)
        future_day = date.today() + timedelta(days=5)
        overdue_report = self.service.report_overdue_loans(future_day)
        self.assertEqual(len(overdue_report), 1)
        self.assertEqual(overdue_report[0]["loan_id"], loan_late.id)
        self.assertEqual(overdue_report[0]["member_name"], "Late Member")
        self.assertEqual(overdue_report[0]["days_overdue"], 2)

        # If the late loan is returned, it should no longer show in overdue report
        self.service.return_loan(loan_late.id or 1, returned_on=future_day)
        self.assertEqual(len(self.service.report_overdue_loans(future_day)), 0)

    def test_report_member_history(self):
        """Verify member history returns full chronological checkouts for a member."""
        self.service.register_member("History Member", "history@makerspace.org")
        self.service.register_equipment("Tool 1", "General")
        self.service.register_equipment("Tool 2", "General")

        due = date.today() + timedelta(days=7)
        l1 = self.service.create_loan(1, 1, due)
        self.service.return_loan(l1.id or 1)

        self.service.create_loan(1, 2, due)

        history = self.service.report_member_history(1)
        self.assertEqual(len(history), 2)
        # Verify one is closed, one is active
        statuses = {entry["status"] for entry in history}
        self.assertEqual(statuses, {"active", "closed"})

        # Non-existent member raises ValueError
        with self.assertRaises(ValueError):
            self.service.report_member_history(999)


if __name__ == "__main__":
    unittest.main()
