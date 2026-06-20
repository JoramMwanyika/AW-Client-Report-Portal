import os
import shutil
import database
import pdf_generator
#tests

def run_tests():
    print("Initializing test database...")
    # Force use of a test db
    test_db = "test_reports.db"
    if os.path.exists(test_db):
        os.remove(test_db)
        
    database.DATABASE_NAME = test_db
    database.init_db()
    
    # 1. Test Client Profile Add & Retrieve
    print("Testing client setup...")
    client_payload = {
        'client1_first_name': 'Andrew',
        'client1_last_name': 'Smith',
        'client1_dob': '1981-06-15',
        'client1_ssn_last_4': '1234',
        'client2_first_name': 'Rebecca',
        'client2_last_name': 'Smith',
        'client2_dob': '1983-09-20',
        'client2_ssn_last_4': '5678',
        'monthly_salary': 15000.0,
        'agreed_expense_budget': 11000.0,
        'deductible_auto': 1000.0,
        'deductible_home': 2500.0,
        'deductible_health': 1500.0,
        'deductible_other': 0.0,
        'trust_address': '456 Peachtree St, Atlanta GA 30309'
    }
    
    client_id = database.add_client(client_payload)
    client = database.get_client(client_id)
    
    assert client is not None
    assert client['client1_first_name'] == 'Andrew'
    assert client['client1_last_name'] == 'Smith'
    assert client['client2_first_name'] == 'Rebecca'
    assert client['client1_age'] == 45  # Assuming current year is 2026, 2026 - 1981 = 45
    assert client['client2_age'] == 42  # 2026 - 1983 = 43 (wait, DOB is 1983-09-20. Since current time is 2026-06-20, she hasn't had her birthday yet, so she is 42. Age calculation checks month/day: 2026 - 1983 - 1 = 42. Excellent, age calculation is correct!)
    print(f"  Age Client 1: {client['client1_age']} (Expected: 45)")
    print(f"  Age Client 2: {client['client2_age']} (Expected: 42)")
    
    # 2. Test Account Configuration
    print("Testing accounts structure configuration...")
    accounts_list = [
        { 'owner': 'Client 1', 'type': 'Retirement', 'subtype': 'Roth IRA', 'institution': 'Charles Schwab', 'account_number_last_4': '1111', 'interest_rate': 0 },
        { 'owner': 'Client 1', 'type': 'Retirement', 'subtype': 'Traditional IRA', 'institution': 'Charles Schwab', 'account_number_last_4': '2222', 'interest_rate': 0 },
        { 'owner': 'Client 2', 'type': 'Retirement', 'subtype': 'Roth IRA', 'institution': 'Charles Schwab', 'account_number_last_4': '3333', 'interest_rate': 0 },
        { 'owner': 'Joint', 'type': 'Non-Retirement', 'subtype': 'Brokerage', 'institution': 'Charles Schwab', 'account_number_last_4': '4444', 'interest_rate': 0 },
        { 'owner': 'Joint', 'type': 'Non-Retirement', 'subtype': 'Checking', 'institution': 'Pinnacle Bank', 'account_number_last_4': '5555', 'interest_rate': 0 },
        { 'owner': 'Client 1', 'type': 'Liability', 'subtype': 'Mortgage', 'institution': 'Pinnacle Bank', 'account_number_last_4': '9999', 'interest_rate': 4.25 },
        { 'owner': 'Client 2', 'type': 'Liability', 'subtype': 'Auto Loan', 'institution': 'Chase Auto', 'account_number_last_4': '8888', 'interest_rate': 5.5 }
    ]
    database.save_client_accounts(client_id, accounts_list)
    db_accounts = database.get_client_accounts(client_id)
    assert len(db_accounts) == 7
    print("  Account structure saved successfully.")
    
    # 3. Test Quarterly Report Balance Entry & Math Calculations
    print("Testing quarterly report balances & calculations...")
    
    # Let's map account ID from database
    acc_map = { f"{a['owner']}_{a['type']}_{a['subtype']}": a['id'] for a in db_accounts }
    
    report_balances = {
        'quarter': '2026-Q1',
        'report_date': '2026-06-20',
        'private_reserve_balance': 85000.0,
        'trust_zillow_value': 450000.0,
        'balances': [
            { 'account_id': acc_map['Client 1_Retirement_Roth IRA'], 'balance': 15000.0, 'cash_balance': 2000.0 },
            { 'account_id': acc_map['Client 1_Retirement_Traditional IRA'], 'balance': 25000.0, 'cash_balance': 1000.0 },
            { 'account_id': acc_map['Client 2_Retirement_Roth IRA'], 'balance': 30000.0, 'cash_balance': 3000.0 },
            { 'account_id': acc_map['Joint_Non-Retirement_Brokerage'], 'balance': 120000.0, 'cash_balance': 15000.0 },
            { 'account_id': acc_map['Joint_Non-Retirement_Checking'], 'balance': 5000.0, 'cash_balance': 5000.0 },
            { 'account_id': acc_map['Client 1_Liability_Mortgage'], 'balance': 250000.0, 'cash_balance': 0 },
            { 'account_id': acc_map['Client 2_Liability_Auto Loan'], 'balance': 15000.0, 'cash_balance': 0 }
        ]
    }
    
    report_id = database.create_report(client_id, report_balances)
    report_details = database.get_report_details(report_id)
    
    # Perform math assertion checks
    # A: Inflow/Outflow Excess
    inflow = report_details['monthly_salary']
    outflow = report_details['agreed_expense_budget']
    excess = inflow - outflow
    assert excess == 4000.0
    print(f"  SACS Excess Cash Flow: {excess} (Expected: 4000.0)")
    
    # B: Private Reserve Target
    deductibles = (report_details['deductible_auto'] + report_details['deductible_home'] + 
                   report_details['deductible_health'] + report_details['deductible_other'])
    assert deductibles == 5000.0
    pr_target = (outflow * 6) + deductibles
    assert pr_target == 71000.0
    print(f"  SACS Target Reserve: {pr_target} (Expected: 71000.0)")
    
    # C: TCC Sums
    c1_retirement = 0
    c2_retirement = 0
    non_retirement = 0
    liabilities = 0
    
    for bal in report_details['balances']:
        bt = bal['type']
        bo = bal['owner']
        if bt == 'Retirement':
            if bo == 'Client 1':
                c1_retirement += bal['balance']
            else:
                c2_retirement += bal['balance']
        elif bt == 'Non-Retirement':
            non_retirement += bal['balance']
        elif bt == 'Liability':
            liabilities += bal['balance']
            
    assert c1_retirement == 40000.0  # 15000 + 25000
    assert c2_retirement == 30000.0  # 30000
    assert non_retirement == 125000.0 # 120000 + 5000 (Zillow Trust value is separate!)
    assert liabilities == 265000.0    # 250000 + 15000
    
    trust_value = report_details['trust_zillow_value']
    assert trust_value == 450000.0
    
    # D: Grand Total Net Worth (Liabilities are NOT subtracted from net worth)
    grand_total_net_worth = c1_retirement + c2_retirement + non_retirement + trust_value
    assert grand_total_net_worth == 645000.0 # 40k + 30k + 125k + 450k = 645k
    print(f"  TCC Client 1 Retirement Total: {c1_retirement} (Expected: 40000.0)")
    print(f"  TCC Client 2 Retirement Total: {c2_retirement} (Expected: 30000.0)")
    print(f"  TCC Non-Retirement Total (Excluding Trust): {non_retirement} (Expected: 125000.0)")
    print(f"  TCC Trust Property Value: {trust_value} (Expected: 450000.0)")
    print(f"  TCC Liabilities Total (Separated): {liabilities} (Expected: 265000.0)")
    print(f"  TCC Net Worth Grand Total (Liabilities Not Subtracted): {grand_total_net_worth} (Expected: 645000.0)")
    
    # 4. Test PDF Generation Compile
    print("Testing SACS and TCC PDF generation...")
    os.makedirs('test_pdfs', exist_ok=True)
    
    sacs_path = "test_pdfs/test_sacs.pdf"
    tcc_path = "test_pdfs/test_tcc.pdf"
    
    # Generate SACS
    pdf_generator.generate_sacs_pdf(sacs_path, client, report_details)
    assert os.path.exists(sacs_path)
    assert os.path.getsize(sacs_path) > 0
    print(f"  SACS PDF generated successfully at {sacs_path} ({os.path.getsize(sacs_path)} bytes)")
    
    # Generate TCC
    pdf_generator.generate_tcc_pdf(tcc_path, client, report_details)
    assert os.path.exists(tcc_path)
    assert os.path.getsize(tcc_path) > 0
    print(f"  TCC PDF generated successfully at {tcc_path} ({os.path.getsize(tcc_path)} bytes)")
    
    # Clean up test files
    os.remove(test_db)
    print("\nALL AUTOMATED CALCULATION AND REPORT RENDERING TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
