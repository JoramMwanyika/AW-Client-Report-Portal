import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime

# Brand Colors (Hex & ReportLab equivalents)
COLOR_PRIMARY_NAVY = colors.HexColor('#0f172a') # Slate-900
COLOR_TEXT_MUTED = colors.HexColor('#475569')   # Slate-600
COLOR_INFLOW_GREEN = colors.HexColor('#10b981') # Emerald-500
COLOR_OUTFLOW_RED = colors.HexColor('#ef4444')  # Red-500
COLOR_RESERVE_BLUE = colors.HexColor('#2563eb') # Blue-600
COLOR_BG_CARD = colors.HexColor('#f8fafc')      # Slate-50
COLOR_BORDER = colors.HexColor('#e2e8f0')       # Slate-200
COLOR_GOLD_ACCENT = colors.HexColor('#b45309')  # Amber-700
COLOR_WHITE = colors.HexColor('#ffffff')

def format_currency(val):
    if val is None:
        return "$0"
    return f"${val:,.0f}"

def format_percent(val):
    if val is None:
        return "0.0%"
    return f"{val:.2f}%"

def draw_header(c, title, client_name, date_str, period_str):
    """Draws a clean brand header with an accent color line."""
    # Top brand bar
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.rect(0, 755, 612, 37, fill=1, stroke=0)
    
    # Windbrook Brand Text
    c.setFillColor(COLOR_WHITE)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(36, 768, "WINDBROOK SOLUTIONS")
    
    c.setFillColor(COLOR_WHITE)
    c.setFont("Helvetica", 10)
    c.drawRightString(576, 768, f"REPORTING SYSTEM")
    
    # Sub-header
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(36, 725, title)
    
    # Client name & Period metadata
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_TEXT_MUTED)
    meta_text = f"Client: {client_name}   |   Period: {period_str}   |   Date: {date_str}"
    c.drawString(36, 708, meta_text)
    
    # Accent line
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(1)
    c.line(36, 700, 576, 700)

def draw_wrapped_text(c, text, x, y, max_width, line_height, font_name="Helvetica", font_size=9, align="center"):
    if not text:
        return 0
    c.setFont(font_name, font_size)
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        if c.stringWidth(test_line, font_name, font_size) < max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
        
    for i, line in enumerate(lines):
        line_y = y - i * line_height
        if align == "center":
            width = c.stringWidth(line, font_name, font_size)
            c.drawString(x - width/2, line_y, line)
        elif align == "right":
            width = c.stringWidth(line, font_name, font_size)
            c.drawString(x - width, line_y, line)
        else:
            c.drawString(x, line_y, line)
    return len(lines) * line_height

def draw_arrow(c, x1, y1, x2, y2, color=COLOR_TEXT_MUTED, thickness=2, with_x=False):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(thickness)
    c.line(x1, y1, x2, y2)
    
    # Arrow head
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    head_len = 8
    
    pt1_x = x2 - head_len * math.cos(angle - math.pi / 6)
    pt1_y = y2 - head_len * math.sin(angle - math.pi / 6)
    
    pt2_x = x2 - head_len * math.cos(angle + math.pi / 6)
    pt2_y = y2 - head_len * math.sin(angle + math.pi / 6)
    
    p = c.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(pt1_x, pt1_y)
    p.lineTo(pt2_x, pt2_y)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    
    if with_x:
        # Draw a small "X" over the middle of the line
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        r = 6
        c.setStrokeColor(COLOR_OUTFLOW_RED)
        c.setLineWidth(2.5)
        c.line(mx - r, my - r, mx + r, my + r)
        c.line(mx - r, my + r, mx + r, my - r)

def generate_sacs_pdf(filepath, client, report):
    """Generates the Simple Automated Cash Flow System (SACS) PDF report."""
    # Setup Canvas
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter # 612, 792
    
    # Client Name mapping
    client_name = f"{client['client1_first_name']} {client['client1_last_name']}"
    if client.get('client2_first_name'):
        client_name += f" & {client['client2_first_name']} {client['client2_last_name']}"
        
    # Math calculations
    inflow = client['monthly_salary']
    outflow = client['agreed_expense_budget']
    excess = inflow - outflow
    
    deductibles = (client['deductible_auto'] + client['deductible_home'] + 
                   client['deductible_health'] + client['deductible_other'])
    pr_target = (6 * outflow) + deductibles
    pr_balance = report['private_reserve_balance']
    pr_diff = pr_balance - pr_target
    
    # Page 1: Cashflow Visual Diagram
    draw_header(c, "SIMPLE AUTOMATED CASH FLOW SYSTEM (SACS)", client_name, report['report_date'], report['quarter'])
    
    # Draw Inflow Bubble (Green, Left)
    cx_in, cy_in = 130, 480
    c.setFillColor(COLOR_INFLOW_GREEN)
    c.circle(cx_in, cy_in, 60, stroke=0, fill=1)
    c.setFillColor(COLOR_WHITE)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(cx_in, cy_in + 15, "INFLOW")
    c.setFont("Helvetica", 9)
    c.drawCentredString(cx_in, cy_in - 2, "Monthly Salary")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(cx_in, cy_in - 22, format_currency(inflow))
    
    # Draw Outflow Bubble (Red, Right)
    cx_out, cy_out = 482, 480
    c.setFillColor(COLOR_OUTFLOW_RED)
    c.circle(cx_out, cy_out, 60, stroke=0, fill=1)
    c.setFillColor(COLOR_WHITE)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(cx_out, cy_out + 15, "OUTFLOW")
    c.setFont("Helvetica", 9)
    c.drawCentredString(cx_out, cy_out - 2, "Agreed Expenses")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(cx_out, cy_out - 22, format_currency(outflow))
    
    # Draw Private Reserve Bubble (Blue, Bottom Center)
    cx_pr, cy_pr = 306, 260
    c.setFillColor(COLOR_RESERVE_BLUE)
    c.circle(cx_pr, cy_pr, 70, stroke=0, fill=1)
    c.setFillColor(COLOR_WHITE)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(cx_pr, cy_pr + 25, "PRIVATE RESERVE")
    c.setFont("Helvetica", 9)
    c.drawCentredString(cx_pr, cy_pr + 5, "(Monthly Savings)")
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(cx_pr, cy_pr - 18, format_currency(excess))
    c.setFont("Helvetica", 8)
    c.drawCentredString(cx_pr, cy_pr - 34, "Transferred Automatically")
    
    # Draw Connecting Arrows
    # Inflow -> Outflow (Red arrow with X in middle)
    draw_arrow(c, cx_in + 60, cy_in, cx_out - 60, cy_out, color=COLOR_OUTFLOW_RED, thickness=3, with_x=True)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(306, cy_in + 15, f"Agreed Budget: {format_currency(outflow)} / mo")
    
    # Inflow/Outflow Path -> Private Reserve
    # Let's draw diagonal arrows pointing to Private Reserve from both
    # A beautiful arrow from the bottom edge of Inflow to top edge of Private Reserve
    # Inflow edge at (cx_in + 35, cy_in - 48) -> PR edge at (cx_pr - 35, cy_pr + 60)
    draw_arrow(c, cx_in + 45, cy_in - 40, cx_pr - 50, cy_pr + 50, color=COLOR_RESERVE_BLUE, thickness=3, with_x=False)
    c.setFillColor(COLOR_RESERVE_BLUE)
    c.setFont("Helvetica-Bold", 10)
    
    # Draw text: Monthly Excess
    c.drawString(135, 345, "Monthly Excess Cash")
    c.drawString(135, 330, format_currency(excess))
    
    # Explanatory caption
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(36, 130, "System Overview & Operation:")
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT_MUTED)
    desc_text = (
        "The Simple Automated Cash Flow System (SACS) operates on a dual-bucket cash management "
        "framework. Every month, the take-home monthly salary (Inflow) is deposited. The pre-arranged "
        "monthly expense budget (Outflow) is systematically transferred to the client's spending account, "
        "leaving a safety buffer. All excess cash flow is swept automatically into the Private Reserve "
        "high-yield savings bucket to fund mid-term savings goals and build the cash cushion."
    )
    draw_wrapped_text(c, desc_text, 36, 110, 540, 14, font_size=9, align="left")
    
    # Page Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawRightString(576, 30, "Page 1 of 2")
    c.drawString(36, 30, "Windbrook Solutions | Confidential Client Financial Plan")
    
    # ------------------ PAGE 2 ------------------
    c.showPage()
    
    draw_header(c, "PRIVATE RESERVE SUMMARY & LIQUID ASSETS", client_name, report['report_date'], report['quarter'])
    
    # Calculation Box (Target Reserve)
    c.setFillColor(COLOR_BG_CARD)
    c.roundRect(36, 440, 260, 220, 8, fill=1, stroke=1)
    c.setStrokeColor(COLOR_BORDER)
    
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, 640, "Target Private Reserve Calculation")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(50, 610, "6 Months Expenses Buffer")
    c.drawRightString(280, 610, format_currency(outflow * 6))
    
    # Itemized Deductibles
    c.drawString(50, 580, "Auto Insurance Deductible")
    c.drawRightString(280, 580, format_currency(client['deductible_auto']))
    
    c.drawString(50, 560, "Homeowners Insurance Deductible")
    c.drawRightString(280, 560, format_currency(client['deductible_home']))
    
    c.drawString(50, 540, "Health Insurance Deductible")
    c.drawRightString(280, 540, format_currency(client['deductible_health']))
    
    c.drawString(50, 520, "Other Insurance Deductible")
    c.drawRightString(280, 520, format_currency(client['deductible_other']))
    
    c.setStrokeColor(COLOR_BORDER)
    c.line(50, 505, 280, 505)
    
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 485, "Total Private Reserve Target")
    c.drawRightString(280, 485, format_currency(pr_target))
    
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(50, 455, "*Formula: (6 × Monthly Outflow) + Deductibles")
    
    # Actual Reserves Box (Right)
    c.setFillColor(COLOR_BG_CARD)
    c.roundRect(316, 440, 260, 220, 8, fill=1, stroke=1)
    
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(330, 640, "Actual Reserve Cushion Details")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(330, 610, "Current Private Reserve Balance")
    c.setFillColor(COLOR_RESERVE_BLUE)
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(560, 610, format_currency(pr_balance))
    
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(330, 580, "Private Reserve Target Threshold")
    c.drawRightString(560, 580, format_currency(pr_target))
    
    c.line(330, 565, 560, 565)
    
    # Net Surplus/Deficit
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    if pr_diff >= 0:
        c.drawString(330, 545, "Surplus Reserve Cushion")
        c.setFillColor(COLOR_INFLOW_GREEN)
        c.drawRightString(560, 545, f"+{format_currency(pr_diff)}")
        
        # Draw status badge
        c.setFillColor(COLOR_INFLOW_GREEN)
        c.roundRect(330, 475, 230, 45, 4, fill=1, stroke=0)
        c.setFillColor(COLOR_WHITE)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(445, 492, "RESERVES FULLY FUNDED")
    else:
        c.drawString(330, 545, "Required Reserve Funding")
        c.setFillColor(COLOR_OUTFLOW_RED)
        c.drawRightString(560, 545, format_currency(abs(pr_diff)))
        
        # Draw status badge
        c.setFillColor(COLOR_OUTFLOW_RED)
        c.roundRect(330, 475, 230, 45, 4, fill=1, stroke=0)
        c.setFillColor(COLOR_WHITE)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(445, 492, "FUNDING DEFICIT")
        
    # Liquid Assets Table (Bottom Half)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(36, 385, "Total Investment & Liquidity Summary")
    c.setStrokeColor(COLOR_PRIMARY_NAVY)
    c.setLineWidth(1.5)
    c.line(36, 375, 576, 375)
    
    # Draw table headers
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.drawString(45, 355, "Asset Group")
    c.drawString(200, 355, "Institution & Details")
    c.drawRightString(420, 355, "Cash Balance")
    c.drawRightString(565, 355, "Total Value")
    
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.5)
    c.line(36, 345, 576, 345)
    
    # Calculate Schwab assets sum
    schwab_total = 0
    schwab_cash = 0
    for bal in report['balances']:
        if 'schwab' in bal['institution'].lower():
            schwab_total += bal['balance']
            schwab_cash += bal['cash_balance']
            
    # Draw Rows
    # Row 1: Private Reserve
    c.setFont("Helvetica", 9)
    c.drawString(45, 325, "Private Reserve")
    c.drawString(200, 325, "Pinnacle Bank (Savings)")
    c.drawRightString(420, 325, format_currency(pr_balance))
    c.drawRightString(565, 325, format_currency(pr_balance))
    c.line(36, 315, 576, 315)
    
    # Row 2: Schwab Investments
    c.drawString(45, 295, "Investment Portfolio")
    c.drawString(200, 295, "Charles Schwab (Aggregated Assets)")
    c.drawRightString(420, 295, format_currency(schwab_cash))
    c.drawRightString(565, 295, format_currency(schwab_total))
    c.line(36, 285, 576, 285)
    
    # Total row
    c.setFillColor(COLOR_BG_CARD)
    c.rect(36, 245, 540, 30, fill=1, stroke=0)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(45, 255, "Total Liquid Reserve Assets")
    c.drawRightString(420, 255, format_currency(pr_balance + schwab_cash))
    c.drawRightString(565, 255, format_currency(pr_balance + schwab_total))
    c.setStrokeColor(COLOR_PRIMARY_NAVY)
    c.setLineWidth(1)
    c.line(36, 245, 576, 245)
    
    # Bottom Advice Notes
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(36, 180, "Quarterly Recommendations:")
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_TEXT_MUTED)
    
    recs = [
        "1. Maintain the Private Reserve target buffer to support cash outflows without incurring credit interest.",
        f"2. Keep the account floor of $1,000 in your primary transaction checking accounts at all times.",
        "3. Portfolio cash yields must be reviewed quarterly to ensure excess cash is swept into money market funds."
    ]
    for idx, rec in enumerate(recs):
        c.drawString(36, 160 - (idx * 18), rec)
        
    # Page Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawRightString(576, 30, "Page 2 of 2")
    c.drawString(36, 30, "Windbrook Solutions | Confidential Client Financial Plan")
    
    c.save()

def generate_tcc_pdf(filepath, client, report):
    """Generates the Total Client Chart (TCC) Net Worth PDF report."""
    # TCC is a dense visual map, let's build it as a Landscape page
    # width = 792 pt, height = 612 pt (landscape)
    c = canvas.Canvas(filepath, pagesize=(792, 612))
    
    # Client Name mapping
    client_name = f"{client['client1_first_name']} {client['client1_last_name']}"
    if client.get('client2_first_name'):
        client_name += f" & {client['client2_first_name']} {client['client2_last_name']}"
        
    # Draw Landscape Header
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.rect(0, 575, 792, 37, fill=1, stroke=0)
    c.setFillColor(COLOR_WHITE)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(36, 588, "WINDBROOK SOLUTIONS")
    c.drawRightString(756, 588, "TOTAL CLIENT CHART (TCC)")
    
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(36, 545, "TOTAL CLIENT NET WORTH CHART")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_TEXT_MUTED)
    meta_text = f"Client: {client_name}   |   Period: {report['quarter']}   |   Date: {report['report_date']}"
    c.drawString(36, 528, meta_text)
    
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(1)
    c.line(36, 520, 756, 520)
    
    # Process account types and balances
    c1_ret_total = 0
    c2_ret_total = 0
    non_ret_total = 0
    liabilities_total = 0
    
    c1_ret_accs = []
    c2_ret_accs = []
    non_ret_accs = []
    liabilities_accs = []
    
    for bal in report['balances']:
        # Sort balances into lists
        bt = bal['type']
        bo = bal['owner']
        
        if bt == 'Retirement':
            if bo == 'Client 1':
                c1_ret_accs.append(bal)
                c1_ret_total += bal['balance']
            else:
                c2_ret_accs.append(bal)
                c2_ret_total += bal['balance']
        elif bt == 'Non-Retirement':
            non_ret_accs.append(bal)
            non_ret_total += bal['balance']
        elif bt == 'Liability':
            liabilities_accs.append(bal)
            liabilities_total += bal['balance']
            
    trust_value = report['trust_zillow_value']
    grand_total_net_worth = c1_ret_total + c2_ret_total + non_ret_total + trust_value
    
    # --- Client Profile Info Pills (Green) ---
    c.setFillColor(COLOR_INFLOW_GREEN)
    c.roundRect(36, 455, 340, 52, 6, fill=1, stroke=0)
    c.setFillColor(COLOR_WHITE)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(48, 492, f"{client['client1_first_name']} {client['client1_last_name']}")
    c.setFont("Helvetica", 8)
    dob1 = client['client1_dob'] or "N/A"
    age1 = f"Age: {client['client1_age']}" if client['client1_age'] else "Age: N/A"
    ssn1 = f"SSN: ***-**-{client['client1_ssn_last_4']}" if client['client1_ssn_last_4'] else "SSN: N/A"
    c.drawString(48, 478, f"DOB: {dob1}   |   {age1}   |   {ssn1}")
    
    # Client 2 info if present
    if client.get('client2_first_name'):
        c.setFillColor(COLOR_INFLOW_GREEN)
        c.roundRect(416, 455, 340, 52, 6, fill=1, stroke=0)
        c.setFillColor(COLOR_WHITE)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(428, 492, f"{client['client2_first_name']} {client['client2_last_name']}")
        c.setFont("Helvetica", 8)
        dob2 = client['client2_dob'] or "N/A"
        age2 = f"Age: {client['client2_age']}" if client['client2_age'] else "Age: N/A"
        ssn2 = f"SSN: ***-**-{client['client2_ssn_last_4']}" if client['client2_ssn_last_4'] else "SSN: N/A"
        c.drawString(428, 478, f"DOB: {dob2}   |   {age2}   |   {ssn2}")
        
    # --- LAYOUT DESIGN FOR TCC ---
    # Center: Primary Residence / Trust Bubble
    cx_tr, cy_tr = 396, 270
    w_tr, h_tr = 180, 85
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.roundRect(cx_tr - w_tr/2, cy_tr - h_tr/2, w_tr, h_tr, 12, fill=1, stroke=0)
    c.setFillColor(COLOR_WHITE)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(cx_tr, cy_tr + 24, "PRIMARY RESIDENCE TRUST")
    c.setFont("Helvetica", 8)
    
    # Wrap address inside bubble
    addr = client.get('trust_address', 'Address not specified')
    draw_wrapped_text(c, addr, cx_tr, cy_tr + 8, w_tr - 20, 10, font_size=8, align="center")
    
    c.setFillColor(COLOR_WHITE)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(cx_tr, cy_tr - 24, f"Zestimate: {format_currency(trust_value)}")
    
    # Connect Trust bubble to Grand Total net worth
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(1)
    c.line(cx_tr, cy_tr - h_tr/2, cx_tr, 110) # Line straight down to Non-Retirement/Totals
    
    # --- Top Left: Client 1 Retirement Box & Accounts ---
    c1_ret_box_x, c1_ret_box_y = 36, 380
    c.setFillColor(COLOR_BG_CARD)
    c.roundRect(c1_ret_box_x, c1_ret_box_y, 160, 48, 6, fill=1, stroke=1)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(c1_ret_box_x + 10, c1_ret_box_y + 32, f"{client['client1_first_name']}'s Retirement")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(c1_ret_box_x + 10, c1_ret_box_y + 12, format_currency(c1_ret_total))
    
    # Layout Client 1 Retirement Accounts Bubbles (Pills)
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.8)
    count1 = len(c1_ret_accs)
    for idx, acc in enumerate(c1_ret_accs):
        if count1 <= 4:
            w = 160
            h = 45
            px = c1_ret_box_x
            py = c1_ret_box_y - 50 - (idx * 52)
            font_title = 8
            font_desc = 7.5
            font_val = 8.5
            inner_padding = 8
        else:
            w = 115
            h = 38
            col = idx % 2
            row = idx // 2
            px = c1_ret_box_x + (col * 125)
            py = c1_ret_box_y - 45 - (row * 45)
            font_title = 7
            font_desc = 6.5
            font_val = 7.5
            inner_padding = 6
            
        c.setFillColor(COLOR_WHITE)
        c.roundRect(px, py, w, h, 6, fill=1, stroke=1)
        
        c.setFillColor(COLOR_PRIMARY_NAVY)
        c.setFont("Helvetica-Bold", font_title)
        c.drawString(px + inner_padding, py + h - 12, f"{acc['institution']} {acc['subtype']}")
        
        c.setFont("Helvetica", font_desc)
        c.setFillColor(COLOR_TEXT_MUTED)
        c.drawString(px + inner_padding, py + h - 22, f"Account: *{acc['account_number_last_4']}")
        
        c.setFont("Helvetica-Bold", font_val)
        c.setFillColor(COLOR_PRIMARY_NAVY)
        val_str = format_currency(acc['balance'])
        if acc['cash_balance'] > 0:
            val_str += f" (Cash: {format_currency(acc['cash_balance'])})"
        c.drawString(px + inner_padding, py + h - 33, val_str)
        
        c.setStrokeColor(COLOR_BORDER)
        if count1 <= 4:
            c.line(px + 80, py + h, px + 80, py + h + 7 if idx == 0 else py + h + 5)
        else:
            c.line(px + w/2, py + h, px + w/2, py + h + 5)
    
    # Connect box to client info
    c.line(c1_ret_box_x + 80, c1_ret_box_y + 48, c1_ret_box_x + 80, 455)
    
    # --- Top Right: Client 2 Retirement Box & Accounts ---
    if client.get('client2_first_name'):
        c2_ret_box_x, c2_ret_box_y = 596, 380
        c.setFillColor(COLOR_BG_CARD)
        c.roundRect(c2_ret_box_x, c2_ret_box_y, 160, 48, 6, fill=1, stroke=1)
        c.setFillColor(COLOR_PRIMARY_NAVY)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(c2_ret_box_x + 10, c2_ret_box_y + 32, f"{client['client2_first_name']}'s Retirement")
        c.setFont("Helvetica-Bold", 12)
        c.drawString(c2_ret_box_x + 10, c2_ret_box_y + 12, format_currency(c2_ret_total))
        
        # Layout Client 2 Retirement Accounts Bubbles (Pills)
        count2 = len(c2_ret_accs)
        for idx, acc in enumerate(c2_ret_accs):
            if count2 <= 4:
                w = 160
                h = 45
                px = c2_ret_box_x
                py = c2_ret_box_y - 50 - (idx * 52)
                font_title = 8
                font_desc = 7.5
                font_val = 8.5
                inner_padding = 8
            else:
                col = idx % 2
                row = idx // 2
                w = 115
                h = 38
                px = 521 + (col * 125)
                py = c2_ret_box_y - 45 - (row * 45)
                font_title = 7
                font_desc = 6.5
                font_val = 7.5
                inner_padding = 6
                
            c.setFillColor(COLOR_WHITE)
            c.roundRect(px, py, w, h, 6, fill=1, stroke=1)
            
            c.setFillColor(COLOR_PRIMARY_NAVY)
            c.setFont("Helvetica-Bold", font_title)
            c.drawString(px + inner_padding, py + h - 12, f"{acc['institution']} {acc['subtype']}")
            
            c.setFont("Helvetica", font_desc)
            c.setFillColor(COLOR_TEXT_MUTED)
            c.drawString(px + inner_padding, py + h - 22, f"Account: *{acc['account_number_last_4']}")
            
            c.setFont("Helvetica-Bold", font_val)
            c.setFillColor(COLOR_PRIMARY_NAVY)
            val_str = format_currency(acc['balance'])
            if acc['cash_balance'] > 0:
                val_str += f" (Cash: {format_currency(acc['cash_balance'])})"
            c.drawString(px + inner_padding, py + h - 33, val_str)
            
            c.setStrokeColor(COLOR_BORDER)
            if count2 <= 4:
                c.line(px + 80, py + h, px + 80, py + h + 5)
            else:
                c.line(px + w/2, py + h, px + w/2, py + h + 5)
                
        c.line(c2_ret_box_x + 80, c2_ret_box_y + 48, c2_ret_box_x + 80, 455)
        
    # --- Bottom: Non-Retirement Box & Accounts (Joint accounts, Schwab brokerage etc.) ---
    # Centered in the lower-middle half
    non_ret_box_x, non_ret_box_y = 220, 200
    c.setFillColor(COLOR_BG_CARD)
    c.roundRect(non_ret_box_x, non_ret_box_y, 160, 48, 6, fill=1, stroke=1)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(non_ret_box_x + 10, non_ret_box_y + 32, "Non-Retirement Assets")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(non_ret_box_x + 10, non_ret_box_y + 12, format_currency(non_ret_total))
    
    # Lay out Non-Retirement account bubbles horizontally below the box
    count_non = len(non_ret_accs)
    for idx, acc in enumerate(non_ret_accs):
        w = 120
        h = 42
        if count_non == 1:
            px = 396 - w/2
        else:
            spacing = (720 - w) / (count_non - 1)
            px = 36 + (idx * spacing)
        py = non_ret_box_y - 65
        
        c.setFillColor(COLOR_WHITE)
        c.roundRect(px, py, w, h, 6, fill=1, stroke=1)
        
        c.setFillColor(COLOR_PRIMARY_NAVY)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(px + 6, py + h - 12, f"{acc['institution']} {acc['subtype']}")
        
        c.setFont("Helvetica", 7)
        c.setFillColor(COLOR_TEXT_MUTED)
        c.drawString(px + 6, py + h - 22, f"Account: *{acc['account_number_last_4']}")
        
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(COLOR_PRIMARY_NAVY)
        val_str = format_currency(acc['balance'])
        if acc['cash_balance'] > 0:
            val_str += f" (Cash: {format_currency(acc['cash_balance'])})"
        c.drawString(px + 6, py + h - 33, val_str)
        
        c.setStrokeColor(COLOR_BORDER)
        c.line(px + w/2, py + h, non_ret_box_x + 80, non_ret_box_y)
        
    # Line from Non-retirement box up to Trust
    c.line(non_ret_box_x + 80, non_ret_box_y + 48, cx_tr, cy_tr - h_tr/2)
    
    # --- Bottom Left: Liabilities Summary Card (Not subtracted from NW) ---
    lia_box_x, lia_box_y = 36, 40
    c.setFillColor(colors.HexColor('#fee2e2')) # Light red
    c.roundRect(lia_box_x, lia_box_y, 340, 80, 8, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#991b1b')) # Deep red
    c.setFont("Helvetica-Bold", 10)
    c.drawString(lia_box_x + 12, lia_box_y + 64, "LIABILITIES & OUTSTANDING DEBTS")
    
    # List first two liabilities text
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    for idx, acc in enumerate(liabilities_accs[:3]):
        lia_text = f"• {acc['institution']} {acc['subtype']} (*{acc['account_number_last_4']}) @ {format_percent(acc['interest_rate'])}"
        c.drawString(lia_box_x + 12, lia_box_y + 45 - (idx * 12), lia_text)
        c.drawRightString(lia_box_x + 328, lia_box_y + 45 - (idx * 12), format_currency(acc['balance']))
        
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor('#991b1b'))
    c.drawString(lia_box_x + 12, lia_box_y + 10, "Total Liabilities")
    c.drawRightString(lia_box_x + 328, lia_box_y + 10, format_currency(liabilities_total))
    
    # --- Bottom Right: Grand Total Net Worth Box ---
    gt_box_x, gt_box_y = 416, 40
    c.setFillColor(colors.HexColor('#dcfce7')) # Light green
    c.roundRect(gt_box_x, gt_box_y, 340, 80, 8, fill=1, stroke=0)
    c.setFillColor(COLOR_GOLD_ACCENT)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(gt_box_x + 12, gt_box_y + 62, "ESTIMATED CLIENT NET WORTH")
    
    # Breakdown labels
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.drawString(gt_box_x + 12, gt_box_y + 45, "Total Retirement Portfolio:")
    c.drawRightString(gt_box_x + 328, gt_box_y + 45, format_currency(c1_ret_total + c2_ret_total))
    
    c.drawString(gt_box_x + 12, gt_box_y + 32, "Total Non-Retirement Portfolio:")
    c.drawRightString(gt_box_x + 328, gt_box_y + 32, format_currency(non_ret_total))
    
    c.drawString(gt_box_x + 12, gt_box_y + 19, "Primary Residence Trust Value:")
    c.drawRightString(gt_box_x + 328, gt_box_y + 19, format_currency(trust_value))
    
    # Line
    c.setStrokeColor(COLOR_PRIMARY_NAVY)
    c.setLineWidth(1)
    c.line(gt_box_x + 12, gt_box_y + 15, gt_box_x + 328, gt_box_y + 15)
    
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.drawString(gt_box_x + 12, gt_box_y + 4, "Grand Total Net Worth")
    c.drawRightString(gt_box_x + 328, gt_box_y + 4, format_currency(grand_total_net_worth))
    
    # Landscape Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(36, 15, "Windbrook Solutions | Confidential Financial Assessment - TCC Chart")
    c.drawRightString(756, 15, "Page 1 of 1")
    
    c.save()
