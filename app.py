import os
import tempfile
import re
import requests
from flask import Flask, jsonify, request, send_file, render_template, redirect, session
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
import database
import pdf_generator

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'windbrook-secure-key-2026')

# Apply ProxyFix middleware to trust headers forwarded by reverse proxies (like Railway's load balancer)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Initialize DB on startup
database.init_db()

# Create folder for generated PDFs
PDF_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated_pdfs')
os.makedirs(PDF_STORAGE_DIR, exist_ok=True)

# AUTHENTICATION
@app.before_request
def require_login():
    # Allow access to login route, login API, and static files without authentication
    if request.endpoint in ('login', 'api_login', 'static'):
        return
        
    if not session.get('logged_in'):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Unauthorized"}), 401
        else:
            return redirect('/login')

@app.route('/login')
def login():
    if session.get('logged_in'):
        return redirect('/')
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if email == 'jorammwanyika@gmail.com' and password == 'Joram123':
        session['logged_in'] = True
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('logged_in', None)
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        "canva_client_id": os.environ.get('CANVA_CLIENT_ID') or os.environ.get('CANVA_API_KEY')
    }), 200

# CLIENT ENDPOINTS
@app.route('/api/clients', methods=['GET'])
def get_clients():
    try:
        clients = database.get_all_clients()
        return jsonify(clients)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clients', methods=['POST'])
def add_client():
    try:
        data = request.json
        if not data or not data.get('client1_first_name') or not data.get('client1_last_name'):
            return jsonify({"error": "Client 1 First and Last names are required"}), 400
        client_id = database.add_client(data)
        return jsonify({"id": client_id, "message": "Client created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    try:
        client = database.get_client(client_id)
        if not client:
            return jsonify({"error": "Client not found"}), 404
        return jsonify(client)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    try:
        data = request.json
        if not data or not data.get('client1_first_name') or not data.get('client1_last_name'):
            return jsonify({"error": "Client 1 First and Last names are required"}), 400
        success = database.update_client(client_id, data)
        return jsonify({"message": "Client updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# CLIENT ACCOUNTS ENDPOINTS
@app.route('/api/clients/<int:client_id>/accounts', methods=['GET'])
def get_client_accounts(client_id):
    try:
        accounts = database.get_client_accounts(client_id)
        return jsonify(accounts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clients/<int:client_id>/accounts', methods=['POST'])
def save_client_accounts(client_id):
    try:
        data = request.json
        if not isinstance(data, list):
            return jsonify({"error": "Accounts payload must be a list"}), 400
        database.save_client_accounts(client_id, data)
        return jsonify({"message": "Accounts saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# REPORT ENDPOINTS
@app.route('/api/clients/<int:client_id>/reports', methods=['GET'])
def get_client_reports(client_id):
    try:
        reports = database.get_client_reports(client_id)
        return jsonify(reports)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clients/<int:client_id>/reports', methods=['POST'])
def create_report(client_id):
    try:
        data = request.json
        if not data or not data.get('quarter') or not data.get('report_date'):
            return jsonify({"error": "Quarter and Report Date are required"}), 400
        
        report_id = database.create_report(client_id, data)
        return jsonify({"id": report_id, "message": "Report balances saved successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clients/<int:client_id>/recent-report', methods=['GET'])
def get_recent_report(client_id):
    try:
        report = database.get_most_recent_report(client_id)
        if not report:
            return jsonify(None)
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/<int:report_id>', methods=['GET'])
def get_report_json(report_id):
    try:
        report_details = database.get_report_details(report_id)
        if not report_details:
            return jsonify({"error": "Report not found"}), 404
        return jsonify(report_details)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    try:
        success = database.delete_report(report_id)
        if success:
            return jsonify({"message": "Report deleted successfully"}), 200
        else:
            return jsonify({"error": "Failed to delete report"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# DOWNLOAD PDF ENDPOINTS
@app.route('/api/reports/<int:report_id>/download/sacs', methods=['GET'])
def download_sacs(report_id):
    try:
        report_details = database.get_report_details(report_id)
        if not report_details:
            return jsonify({"error": "Report not found"}), 404
            
        client = {
            'client1_first_name': report_details['client1_first_name'],
            'client1_last_name': report_details['client1_last_name'],
            'client2_first_name': report_details['client2_first_name'],
            'client2_last_name': report_details['client2_last_name'],
            'monthly_salary': report_details['monthly_salary'],
            'agreed_expense_budget': report_details['agreed_expense_budget'],
            'deductible_auto': report_details['deductible_auto'],
            'deductible_home': report_details['deductible_home'],
            'deductible_health': report_details['deductible_health'],
            'deductible_other': report_details['deductible_other']
        }
        
        filename = f"SACS_{report_details['client1_last_name']}_{report_details['quarter']}.pdf"
        filepath = os.path.join(PDF_STORAGE_DIR, filename)
        
        # Draw SACS
        pdf_generator.generate_sacs_pdf(filepath, client, report_details)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/<int:report_id>/download/tcc', methods=['GET'])
def download_tcc(report_id):
    try:
        report_details = database.get_report_details(report_id)
        if not report_details:
            return jsonify({"error": "Report not found"}), 404
            
        client = {
            'client1_first_name': report_details['client1_first_name'],
            'client1_last_name': report_details['client1_last_name'],
            'client1_dob': report_details['client1_dob'],
            'client1_age': report_details['client1_age'],
            'client1_ssn_last_4': report_details['client1_ssn_last_4'],
            'client2_first_name': report_details['client2_first_name'],
            'client2_last_name': report_details['client2_last_name'],
            'client2_dob': report_details['client2_dob'],
            'client2_age': report_details['client2_age'],
            'client2_ssn_last_4': report_details['client2_ssn_last_4'],
            'trust_address': report_details['trust_address']
        }
        
        filename = f"TCC_{report_details['client1_last_name']}_{report_details['quarter']}.pdf"
        filepath = os.path.join(PDF_STORAGE_DIR, filename)
        
        # Draw TCC
        pdf_generator.generate_tcc_pdf(filepath, client, report_details)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
