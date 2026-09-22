# Campus MakerSpace Checkout System

An Object-Oriented Python CLI application backed by SQLite to manage makerspace members, equipment inventory, and checkout transactions.

Built for **Introduction to Programming and Databases (BSc Hons Software Engineering, Year 1)**.

---

## 1. Features

- **Member Management**:
  - Register members with unique emails and contact details.
  - List all registered members in formatted tables.
  - Update member contact details.
  - Search members by ID, name, or email.

- **Equipment Inventory**:
  - Register equipment with category and description.
  - List inventory with live status indicators.
  - Update equipment metadata and status (`available`, `unavailable`, `damaged`, `lost`).
  - Search equipment by ID, name, category, or description.

- **Loans & Checkouts**:
  - Create checkout loans with business rule validation (equipment availability, member check, future due date within 30 days).
  - Return loans (records return date, marks loan as closed, sets equipment back to available).
  - Single-query SQL `JOIN` listing of active loans.

- **SQL Reports**:
  - **Currently Borrowed Equipment**: Real-time view of all active loans with joined member and equipment info.
  - **Overdue Loans Report**: Identifies active loans whose due date has passed, calculating days overdue.
  - **Member Loan History**: Complete chronological history of active and returned items for a specific member.

- **Robust Error Handling**:
  - Non-crashing input validation for integers, dates, and menu selections.
  - Clear, user-friendly feedback on validation errors.
  - Safe database connection teardown on application exit.

---

## 2. Project Structure

```text
Lab_MakerSpace_Yembot31013/
├── main.py              # CLI entry point, menus, input prompts, and table formatting
├── models.py            # OOP domain models (Member, Equipment, Loan)
├── database.py          # SQLite connection manager, row factory, and query execution
├── services.py          # Business logic, validation rules, and parameterized SQL
├── schema.sql           # SQLite database schema and foreign key constraints
├── requirements.txt     # Dependency documentation (standard library only)
├── README.md            # Project documentation and user guide
├── data/
│   └── makerspace.db    # Persistent SQLite database file
└── tests/
    ├── __init__.py
    └── test_services.py # Comprehensive 21-scenario unit test suite
```

### Layered Architecture
- **Presentation (`main.py`)**: Gathers operator input and renders clean tables without containing direct database SQL.
- **Service Layer (`services.py`)**: Enforces business rules and coordinates domain models with SQLite queries.
- **Domain Models (`models.py`)**: Encapsulates entity state and behaviour (`Member`, `Equipment`, `Loan`).
- **Data Access (`database.py`)**: Manages the SQLite database connection, schema initialization, and parameterized queries.

---

## 3. Requirements

- **Python 3.10+** (tested on Python 3.10 – 3.14)
- **SQLite 3** (included with Python)
- **Git**

No external packages are required. The system exclusively uses Python's standard library (`sqlite3`, `dataclasses`, `datetime`, `pathlib`, `typing`, `unittest`).

---

## 4. Setup & How to Run

### Step 1: Clone or Navigate to the Repository

```bash
cd Lab_MakerSpace_Yembot31013
```

### Step 2: (Optional) Create and Activate Virtual Environment

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### Step 3: Run the CLI Application

```bash
python3 main.py
```
*(On Windows, use `python main.py` or `py main.py`)*

Upon launch, the application automatically initializes the SQLite schema in `data/makerspace.db` and displays the main menu:

```text
====================================================================
                 Campus MakerSpace Checkout System                
====================================================================
  1. Member Management       (Register, List, Update, Search)
  2. Equipment Management    (Register, List, Update, Status, Search)
  3. Loans & Checkouts       (Checkout, Return, Active Loans)
  4. SQL Reports             (Borrowed, Overdue, Member History)
  0. Exit Application
--------------------------------------------------------------------
Select a main menu option:
```

### Step 4: Run the Automated Test Suite

To run all 21 unit tests covering positive flows, validation checks, and edge cases:

```bash
python3 -m unittest discover -s tests -v
```

All tests run in isolated temporary SQLite databases and do not alter the persistent `data/makerspace.db` file.

---

## 5. Typical Usage Workflow

1. **Register a Member**:
   - Select `1` (Member Management) $\rightarrow$ `1` (Register New Member).
   - Enter member name, email, and phone.
2. **Register Equipment**:
   - Select `2` (Equipment Management) $\rightarrow$ `1` (Register New Equipment).
   - Enter equipment name (e.g. `3D Printer`), category (e.g. `Fabrication`), and description.
3. **Checkout an Item (Create Loan)**:
   - Select `3` (Loans & Checkouts) $\rightarrow$ `1` (Create New Loan / Checkout).
   - Enter Member ID, Equipment ID, and Due Date (defaults to 14 days ahead).
   - The equipment is automatically marked as `unavailable`.
4. **View Active Loans / Reports**:
   - Select `4` (SQL Reports) $\rightarrow$ `1` (Currently Borrowed Equipment).
   - View currently borrowed items in a formatted table.
5. **Return an Item**:
   - Select `3` (Loans & Checkouts) $\rightarrow$ `2` (Return Loan).
   - Enter the Loan ID and return date.
   - The loan is closed and the equipment status is restored to `available`.

---

## 6. Database Schema

The database uses SQLite foreign keys (`PRAGMA foreign_keys = ON`) with the following normalized tables:

```sql
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'available',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    equipment_id INTEGER NOT NULL,
    checkout_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date TEXT NOT NULL,
    return_date TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    FOREIGN KEY (member_id) REFERENCES members(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);
```

### SQL JOIN Design
Loan retrieval and reports use SQL `JOIN` statements across `loans`, `members`, and `equipment` to prevent the N+1 query problem, fetching relational data in a single parameterized trip.

---

## 7. Validation Rules Enforced

| Rule | Enforcement Location | Behaviour |
|---|---|---|
| **Unique Member Email** | `MakerSpaceService.register_member` | Rejects duplicate emails with `ValueError` |
| **Required Fields** | `services.py` & `main.py` | Enforces non-empty names, categories, and emails |
| **Equipment Availability** | `MakerSpaceService.create_loan` | Rejects checkout if equipment is unavailable, damaged, or lost |
| **Double Checkout Prevention** | `MakerSpaceService.create_loan` | Verifies equipment is not on another active loan |
| **Due Date Rules** | `MakerSpaceService.create_loan` | Due date must be in the future and $\le$ 30 days ahead |
| **Closed Loan Return** | `MakerSpaceService.return_loan` | Prevents closing an already closed loan |
| **Integer & Date Input** | `main.py` prompt helpers | Catches non-numeric or malformed dates gracefully without crashing |

---

## 8. AI Assistance Disclosure

> **Generative AI Disclosure**: Generative AI was used only as an aid for writing and structuring the automated unit test cases in `tests/test_services.py` to ensure comprehensive test coverage across edge cases and validation rules. All core application components, object-oriented models, database schema, service operations, and CLI interface were implemented, reviewed, and tested by the student.
