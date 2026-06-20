import sqlite3
import os
from datetime import datetime

DATABASE_NAME = os.environ.get('RAILWAY_DATABASE_PATH', 'reports.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Pre-seed persistent database from committed local reports.db if it doesn't exist yet
    if DATABASE_NAME != 'reports.db' and not os.path.exists(DATABASE_NAME):
        import shutil
        local_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports.db')
        if os.path.exists(local_db):
            try:
                db_dir = os.path.dirname(DATABASE_NAME)
                if db_dir:
                    os.makedirs(db_dir, exist_ok=True)
                shutil.copy(local_db, DATABASE_NAME)
                print(f"Pre-seeded persistent database from {local_db} to {DATABASE_NAME}")
            except Exception as e:
                print(f"Failed to pre-seed database: {e}")
        else:
            print(f"Pre-seed source database {local_db} not found!")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Create clients table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client1_first_name TEXT NOT NULL,
        client1_last_name TEXT NOT NULL,
        client1_dob TEXT,
        client1_ssn_last_4 TEXT,
        client2_first_name TEXT,
        client2_last_name TEXT,
        client2_dob TEXT,
        client2_ssn_last_4 TEXT,
        monthly_salary REAL DEFAULT 0,
        agreed_expense_budget REAL DEFAULT 0,
        deductible_auto REAL DEFAULT 0,
        deductible_home REAL DEFAULT 0,
        deductible_health REAL DEFAULT 0,
        deductible_other REAL DEFAULT 0,
        trust_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Create client_accounts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS client_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        owner TEXT NOT NULL, -- 'Client 1', 'Client 2', 'Joint', 'Trust'
        type TEXT NOT NULL,  -- 'Retirement', 'Non-Retirement', 'Trust', 'Liability'
        subtype TEXT,        -- 'Roth IRA', 'Traditional IRA', '401K', 'Pension', 'Brokerage', 'Checking', 'Savings', 'Mortgage', 'Auto Loan', 'Primary Residence'
        institution TEXT,
        account_number_last_4 TEXT,
        interest_rate REAL DEFAULT 0, -- only for liabilities
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
    );
    """)
    
    # Create reports table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        quarter TEXT NOT NULL, -- e.g. '2026-Q1'
        report_date TEXT NOT NULL, -- e.g. '2026-06-20'
        private_reserve_balance REAL DEFAULT 0,
        trust_zillow_value REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
    );
    """)
    
    # Create report_balances table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS report_balances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id INTEGER NOT NULL,
        account_id INTEGER NOT NULL,
        balance REAL DEFAULT 0,
        cash_balance REAL DEFAULT 0, -- cash portion, for investment accounts
        FOREIGN KEY (report_id) REFERENCES reports (id) ON DELETE CASCADE,
        FOREIGN KEY (account_id) REFERENCES client_accounts (id) ON DELETE CASCADE
    );
    """)
    
    conn.commit()
    conn.close()

# Client Operations
def calculate_age(dob_str):
    if not dob_str:
        return None
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except Exception:
        return None

def get_all_clients():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, 
               (SELECT MAX(r.quarter) FROM reports r WHERE r.client_id = c.id) as last_report_quarter,
               (SELECT MAX(r.report_date) FROM reports r WHERE r.client_id = c.id) as last_report_date
        FROM clients c
        ORDER BY c.client1_last_name ASC, c.client1_first_name ASC
    """)
    rows = cursor.fetchall()
    clients = []
    for r in rows:
        client_dict = dict(r)
        client_dict['client1_age'] = calculate_age(r['client1_dob'])
        client_dict['client2_age'] = calculate_age(r['client2_dob'])
        clients.append(client_dict)
    conn.close()
    return clients

def get_client(client_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    client_dict = dict(row)
    client_dict['client1_age'] = calculate_age(row['client1_dob'])
    client_dict['client2_age'] = calculate_age(row['client2_dob'])
    conn.close()
    return client_dict

def add_client(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clients (
            client1_first_name, client1_last_name, client1_dob, client1_ssn_last_4,
            client2_first_name, client2_last_name, client2_dob, client2_ssn_last_4,
            monthly_salary, agreed_expense_budget,
            deductible_auto, deductible_home, deductible_health, deductible_other,
            trust_address
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['client1_first_name'], data['client1_last_name'], data.get('client1_dob'), data.get('client1_ssn_last_4'),
        data.get('client2_first_name'), data.get('client2_last_name'), data.get('client2_dob'), data.get('client2_ssn_last_4'),
        data.get('monthly_salary', 0), data.get('agreed_expense_budget', 0),
        data.get('deductible_auto', 0), data.get('deductible_home', 0), data.get('deductible_health', 0), data.get('deductible_other', 0),
        data.get('trust_address')
    ))
    client_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return client_id

def update_client(client_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE clients SET
            client1_first_name = ?, client1_last_name = ?, client1_dob = ?, client1_ssn_last_4 = ?,
            client2_first_name = ?, client2_last_name = ?, client2_dob = ?, client2_ssn_last_4 = ?,
            monthly_salary = ?, agreed_expense_budget = ?,
            deductible_auto = ?, deductible_home = ?, deductible_health = ?, deductible_other = ?,
            trust_address = ?
        WHERE id = ?
    """, (
        data['client1_first_name'], data['client1_last_name'], data.get('client1_dob'), data.get('client1_ssn_last_4'),
        data.get('client2_first_name'), data.get('client2_last_name'), data.get('client2_dob'), data.get('client2_ssn_last_4'),
        data.get('monthly_salary', 0), data.get('agreed_expense_budget', 0),
        data.get('deductible_auto', 0), data.get('deductible_home', 0), data.get('deductible_health', 0), data.get('deductible_other', 0),
        data.get('trust_address'), client_id
    ))
    conn.commit()
    conn.close()
    return True

# Account Operations
def get_client_accounts(client_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM client_accounts WHERE client_id = ? AND is_active = 1", (client_id,))
    rows = cursor.fetchall()
    accounts = [dict(r) for r in rows]
    conn.close()
    return accounts

def save_client_accounts(client_id, accounts_list):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Simple strategy: Soft delete existing and insert new ones
    # (Or hard delete if they are not referenced, since we have cascading delete, but better to replace)
    cursor.execute("DELETE FROM client_accounts WHERE client_id = ?", (client_id,))
    
    for acc in accounts_list:
        cursor.execute("""
            INSERT INTO client_accounts (
                client_id, owner, type, subtype, institution, account_number_last_4, interest_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            client_id, acc['owner'], acc['type'], acc.get('subtype'), acc.get('institution'),
            acc.get('account_number_last_4'), acc.get('interest_rate', 0)
        ))
        
    conn.commit()
    conn.close()
    return True

# Report Operations
def get_client_reports(client_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE client_id = ? ORDER BY report_date DESC, id DESC", (client_id,))
    rows = cursor.fetchall()
    reports = [dict(r) for r in rows]
    conn.close()
    return reports

def get_report_details(report_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT r.*, c.client1_first_name, c.client1_last_name, c.client2_first_name, c.client2_last_name,
               c.monthly_salary, c.agreed_expense_budget, 
               c.deductible_auto, c.deductible_home, c.deductible_health, c.deductible_other,
               c.client1_dob, c.client2_dob, c.client1_ssn_last_4, c.client2_ssn_last_4,
               c.trust_address
        FROM reports r
        JOIN clients c ON r.client_id = c.id
        WHERE r.id = ?
    """, (report_id,))
    
    report_row = cursor.fetchone()
    if not report_row:
        conn.close()
        return None
        
    report = dict(report_row)
    report['client1_age'] = calculate_age(report['client1_dob'])
    report['client2_age'] = calculate_age(report['client2_dob'])
    
    # Get balances linked to this report
    cursor.execute("""
        SELECT rb.*, ca.owner, ca.type, ca.subtype, ca.institution, ca.account_number_last_4, ca.interest_rate
        FROM report_balances rb
        JOIN client_accounts ca ON rb.account_id = ca.id
        WHERE rb.report_id = ?
    """, (report_id,))
    
    balances = [dict(b) for b in cursor.fetchall()]
    report['balances'] = balances
    conn.close()
    return report

def create_report(client_id, data):
    """
    data format:
    {
      'quarter': '2026-Q1',
      'report_date': '2026-06-20',
      'private_reserve_balance': 15000,
      'trust_zillow_value': 450000,
      'balances': [
         { 'account_id': 12, 'balance': 5000, 'cash_balance': 500 },
         ...
      ]
    }
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if report for this client and quarter already exists
        cursor.execute("SELECT id FROM reports WHERE client_id = ? AND quarter = ?", (client_id, data['quarter']))
        existing = cursor.fetchone()
        if existing:
            # Overwrite existing report
            report_id = existing['id']
            cursor.execute("""
                UPDATE reports SET
                    report_date = ?,
                    private_reserve_balance = ?,
                    trust_zillow_value = ?
                WHERE id = ?
            """, (data['report_date'], data['private_reserve_balance'], data.get('trust_zillow_value', 0), report_id))
            
            # Remove old balances
            cursor.execute("DELETE FROM report_balances WHERE report_id = ?", (report_id,))
        else:
            # Insert new report record
            cursor.execute("""
                INSERT INTO reports (
                    client_id, quarter, report_date, private_reserve_balance, trust_zillow_value
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                client_id, data['quarter'], data['report_date'], data['private_reserve_balance'], data.get('trust_zillow_value', 0)
            ))
            report_id = cursor.lastrowid
            
        # Insert current balances
        for bal in data['balances']:
            cursor.execute("""
                INSERT INTO report_balances (
                    report_id, account_id, balance, cash_balance
                ) VALUES (?, ?, ?, ?)
            """, (
                report_id, bal['account_id'], bal['balance'], bal.get('cash_balance', 0)
            ))
            
        conn.commit()
        conn.close()
        return report_id
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e

# Helper to get the most recent report data for a client as data-entry pre-fill reference
def get_most_recent_report(client_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id FROM reports 
        WHERE client_id = ? 
        ORDER BY report_date DESC, id DESC 
        LIMIT 1
    """, (client_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return get_report_details(row['id'])
    return None
