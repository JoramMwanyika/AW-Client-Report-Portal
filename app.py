import os
import tempfile
import re
import requests
from flask import Flask, jsonify, request, send_file, render_template, redirect
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
import database
import pdf_generator

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Apply ProxyFix middleware to trust headers forwarded by reverse proxies (like Railway's load balancer)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Initialize DB on startup
database.init_db()

# Create folder for generated PDFs
PDF_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated_pdfs')
os.makedirs(PDF_STORAGE_DIR, exist_ok=True)

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

def upload_to_temp_host(filepath):
    # Host 1: tmpfiles.org (high reliability, no registration)
    try:
        with open(filepath, 'rb') as f:
            r = requests.post('https://tmpfiles.org/api/v1/upload', files={'file': f}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('status') == 'success':
                url = data['data']['url']
                # Transform to direct download URL (insert /dl/)
                direct_url = url.replace('https://tmpfiles.org/', 'https://tmpfiles.org/dl/')
                return direct_url
    except Exception as e:
        print(f"tmpfiles.org upload failed: {e}")

    # Host 2: file.io (fallback)
    try:
        with open(filepath, 'rb') as f:
            r = requests.post('https://file.io', files={'file': f}, data={'expires': '1h'}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('success'):
                return data['link']
    except Exception as e:
        print(f"file.io upload failed: {e}")

    return None
def is_public_host(host_header):
    # Remove port if present
    host_name = host_header.split(':')[0]
    
    # Check if it's localhost or internal loopbacks
    if host_name in ('localhost', '127.0.0.1', '0.0.0.0'):
        return False
        
    # Check if it is a local private network IP range:
    # 10.x.x.x, 192.168.x.x, 172.16.x.x to 172.31.x.x
    private_ip_patterns = [
        r'^127\.',
        r'^10\.',
        r'^192\.168\.',
        r'^172\.(1[6-9]|2[0-9]|3[0-1])\.'
    ]
    if any(re.match(pattern, host_name) for pattern in private_ip_patterns):
        return False
        
    # Check if it is a local domain suffix or contains no dot (single hostname)
    if host_name.endswith('.local') or '.' not in host_name:
        return False
        
    return True

@app.route('/api/reports/<int:report_id>/export/canva', methods=['GET'])
def export_to_canva(report_id):
    try:
        report_type = request.args.get('type', 'sacs')
        report_details = database.get_report_details(report_id)
        if not report_details:
            return "Report not found", 404
            
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
            'monthly_salary': report_details['monthly_salary'],
            'agreed_expense_budget': report_details['agreed_expense_budget'],
            'deductible_auto': report_details['deductible_auto'],
            'deductible_home': report_details['deductible_home'],
            'deductible_health': report_details['deductible_health'],
            'deductible_other': report_details['deductible_other'],
            'trust_address': report_details['trust_address']
        }
        
        prefix = "SACS" if report_type == 'sacs' else "TCC"
        filename = f"{prefix}_{report_details['client1_last_name']}_{report_details['quarter']}.pdf"
        filepath = os.path.join(PDF_STORAGE_DIR, filename)
        
        # Generate the PDF file
        if report_type == 'sacs':
            pdf_generator.generate_sacs_pdf(filepath, client, report_details)
        else:
            pdf_generator.generate_tcc_pdf(filepath, client, report_details)
            
        # Determine if host is public and accessible
        public_pdf_url = None
        if is_public_host(request.host):
            public_pdf_url = f"{request.host_url.rstrip('/')}/api/reports/{report_id}/download/{report_type}"


        # If direct URL is local, private, or unreachable, upload to temporary public host
        if not public_pdf_url:
            public_pdf_url = upload_to_temp_host(filepath)
        
        if public_pdf_url:
            canva_import_url = f"https://www.canva.com/folder/upload?file_url={public_pdf_url}"
            return redirect(canva_import_url)
        else:
            return "Failed to generate public URL for Canva import", 500
            
    except Exception as e:
        return f"Error: {str(e)}", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
