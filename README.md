# AW Client Report Portal — User Guide & Setup Manual

A professional financial reporting portal built for **EF (Windbrook Solutions)**. This application replaces manual Canva and Word layout adjustments, enabling the team to record client quarterly balances and generate print-ready, visually structured **SACS** (Simple Automated Cash Flow System) and **TCC** (Total Client Chart) PDF reports in minutes.

---

## Core Application Workflows

### Step 1: One-Time Client Setup (Lightweight CRM)
* **What it does**: Establishes the static blueprint of the client's financial structure.
* **Fields Captured**:
  * **Primary Client Info**: Names, Date of Birth (calculates current age dynamically), and last 4 digits of SSN (SSNs are masked for compliance).
  * **Spouse Info (Optional)**: Support for married clients (`Client 1` and `Client 2` owner partitions).
  * **Static Cash Flow**: Monthly take-home salary and agreed monthly expense budget.
  * **Insurance Deductibles**: Auto, Home, Health, and Other deductibles (used to calculate the Private Reserve target).
  * **Primary Residence Trust**: Property address for Zillow lookup reference.
* **Account Structures Grid**: Define all accounts once (institution name, account subtype e.g. Roth IRA, owner e.g. Joint, and last 4 digits of the account number). Supported types:
  * **Retirement**: Portfolio assets mapped to specific spouses.
  * **Non-Retirement**: Checking, savings, or brokerage accounts.
  * **Liability**: Mortgages, auto loans, etc. (includes interest rate inputs).

### Step 2: Quarterly Data Entry Checklist
* **What it does**: Click **New Report** on the Client Directory to enter dynamic quarterly balances.
* **Previous Balance Reference**: Pre-populates the *previous quarter's balances* next to each input field as a reference. Clicking **Use Last** automatically carries the value forward, eliminating the need to search through historical documents.
* **Organizational Division**: Fields are clearly grouped into SACS parameters (Private Reserve checking/savings balance and Zillow Home Value) and individual portfolio account balances.

### Step 3: Real-Time Calculations Engine
As you type balances, the right-hand preview panel recalculates the client's financial status instantly:
* **SACS Math**:
  * `Monthly Inflow` = Client's Monthly Salary (Static)
  * `Monthly Outflow` = Agreed Expense Budget (Static)
  * `Monthly Excess` = Inflow - Outflow (Savings cushion transferred automatically)
  * `Private Reserve Target` = (6 × Monthly Outflow) + Auto + Home + Health + Other Deductibles
  * `Reserve Surplus/Deficit` = Actual Private Reserve Balance - Private Reserve Target
* **TCC Math**:
  * `Client 1 Retirement Total` = Sum of all Client 1 retirement balances
  * `Client 2 Retirement Total` = Sum of all Client 2 retirement balances
  * `Non-Retirement Total` = Sum of checking/brokerage joint balances (excluding primary residence)
  * `Trust Asset Value` = Property Zillow value
  * `Liabilities Total (Separate)` = Sum of mortgages and loans (displayed separately, **not** subtracted from net worth)
  * **`Net Worth Grand Total`** = Client 1 Retirement + Client 2 Retirement + Non-Retirement + Trust Asset Value

### Step 4: Automated PDF Compilation
* **SACS Report (2 Pages)**:
  * **Page 1 (Visual Flow)**: Renders a cashflow diagram consisting of a green Inflow circle, a red Outflow circle, and a blue Private Reserve bubble connected by flows. Features a red arrow (with an overlay "X") indicating the outflow spending, and a blue arrow routing the monthly excess.
  * **Page 2 (Details Table)**: Formats a structured table comparing the current Private Reserve balance against target thresholds, itemizing deductibles, and calculating liquid/portfolio assets.
* **TCC Report (1 Page)**:
  * Renders a Net Worth bubble map. The Primary Residence Trust is positioned in the center, Client 1/2 Retirement accounts are clustered at the top, joint non-retirement accounts at the bottom, and liabilities on the side.
  * **Auto-Arranging Grid**: If a client has more than 4 retirement accounts, the PDF engine automatically shifts the layout into a compact 2-column grid of smaller capsules with scaled-down fonts, preventing overlaps with the Net Worth card and Liabilities box.
  * **Symmetric Spacing**: Distributes non-retirement account bubbles horizontally, preventing right-margin page overflows.

### Step 5: Export and Canva Integration
* **Download PDF**: Standard HTML5 `download` links trigger immediate local browser downloads.
* **Canva Edit Workspace**:
  * **Public Server**: Clicking **Canva SACS** or **Canva TCC** launches Canva's official Design Button popup using your `CANVA_CLIENT_ID`, importing the PDF vector layout directly into your Canva design library.
  * **Localhost Fallback Mode**: Because cloud services cannot access local addresses (`localhost:5000`), the portal will automatically trigger a local file download and open Canva's upload workspace in a new tab, prompting you to drag and drop the PDF file to edit.

---

## Technology Stack

| Layer | Technology Used | Rationale |
| :--- | :--- | :--- |
| **Frontend Web App** | HTML5 / JavaScript (ES6) | Single Page Application (SPA) structure. Clean modular views (Directory, CRM form, Balance entries, History table) connected via fetch APIs. Handles real-time DOM updates and form serialization. |
| **Styling (CSS)** | Vanilla CSS3 | Modern CSS utilizing HSL color properties (deep slate, emerald, crimson, blue, gold), Outfit/Inter typography, flexbox/grid alignments, responsive media layouts, and button hover micro-animations. |
| **Backend Framework** | Python 3.12 / Flask 3.0 | Serves the web dashboard, exposes REST API routes for database CRUD operations, configuration parameters, and compiles ReportLab PDFs dynamically on download. |
| **Database** | SQLite 3 | Relational SQLite database using `sqlite3`. Relies on foreign keys and cascading deletes to store client profiles, configurations, and historic balance sheets. |
| **PDF Compiler** | ReportLab 5.0 | Low-level Python graphics library. Draws vector graphics, shapes, connecting arrows, client pills, and tables. Avoids heavy external C-dependencies (unlike WeasyPrint/wkhtmltopdf), ensuring cross-platform stability. |
| **Canva Integration** | Canva Design Button SDK | Cloud-based iframe/popup designer that converts PDF structures into editable vector layers on the Canva workspace. |

---

## Setup & Installation

### Local Setup (Windows / development)

1. **Clone/Navigate to the workspace**:
   ```bash
   cd "F:\My projects\AW Client Report Portal\AW-Client-Report-Portal"
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure local environment variables**:
   Open the [.env](file:///f:/My%20projects/AW%20Client%20Report%20Portal/AW-Client-Report-Portal/.env) file in the root of the project and set your Canva Client ID:
   ```env
   CANVA_CLIENT_ID=YOUR_CANVA_CLIENT_ID
   ```

4. **Run the Flask application**:
   ```bash
   python app.py
   ```
   The application will start serving locally on `http://localhost:5000/`.

5. **Run test assertions**:
   You can verify calculations and PDF compiling at any time by running:
   ```bash
   python verify_calculations.py
   ```

---

## Production Deployment (Railway)

To host this portal on Railway with persistent storage:

1. **Push the repository to GitHub**.
2. **Deploy on Railway** using the standard Python buildpack.
3. **Provision a Persistent Volume**:
   * Add a Railway Volume mount to prevent SQLite data loss when the container restarts.
4. **Configure Variables** in the Railway Dashboard:
   * `CANVA_CLIENT_ID`: Your Canva integrations Client ID.
   * `RAILWAY_DATABASE_PATH`: Set to your volume mount path (e.g. `/data/reports.db`).
