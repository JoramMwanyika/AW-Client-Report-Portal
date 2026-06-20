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

def draw_elbow_arrow(c, x1, y1, x2, y2, color, thickness=1, arrow_size=6):
    c.setStrokeColor(color)
    c.setLineWidth(thickness)
    c.setFillColor(color)
    
    mid_y = y1 - (y1 - y2) / 2
    c.line(x1, y1, x1, mid_y)
    c.line(x1, mid_y, x2, mid_y)
    c.line(x2, mid_y, x2, y2)
    
    # Draw arrow head pointing down
    c.path = c.beginPath()
    c.path.moveTo(x2 - arrow_size/2, y2 + arrow_size)
    c.path.lineTo(x2 + arrow_size/2, y2 + arrow_size)
    c.path.lineTo(x2, y2)
    c.drawPath(c.path, stroke=0, fill=1)

def draw_straight_arrow(c, x1, y1, x2, y2, color, thickness=1, arrow_size=6):
    c.setStrokeColor(color)
    c.setLineWidth(thickness)
    c.setFillColor(color)
    c.line(x1, y1, x2, y2)
    
    # Draw right pointing arrow head
    c.path = c.beginPath()
    c.path.moveTo(x2 - arrow_size, y2 + arrow_size/2)
    c.path.lineTo(x2 - arrow_size, y2 - arrow_size/2)
    c.path.lineTo(x2, y2)
    c.drawPath(c.path, stroke=0, fill=1)

def generate_sacs_pdf(filepath, client, report):
    """Generates the Simple Automated Cash Flow System (SACS) PDF report with premium design."""
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter # 612, 792
    
    # Background
    c.setFillColor(colors.HexColor('#F8FAFC'))
    c.rect(0, 0, width, height, fill=1, stroke=0)
    
    client_name = f"{client['client1_first_name']} {client['client1_last_name']}"
    if client.get('client2_first_name'):
        client_name += f" & {client['client2_first_name']} {client['client2_last_name']}"
        
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
    
    # Define Layout Metrics
    card_w = 180
    card_h = 90
    in_x, in_y = 60, 480
    out_x, out_y = 372, 480
    pr_x, pr_y = 216, 260
    
    # Connection logic (draw first so they are behind cards)
    line_col = colors.HexColor('#94A3B8')
    
    # Arrow from Inflow to Outflow
    # From right edge of inflow to left edge of outflow
    draw_straight_arrow(c, in_x + card_w, in_y + card_h/2, out_x, out_y + card_h/2, line_col, 2, 8)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString((in_x + card_w + out_x)/2, in_y + card_h/2 + 10, f"Agreed Budget: {format_currency(outflow)} / mo")
    
    # Arrow from Inflow to PR (bottom edge to top edge)
    draw_elbow_arrow(c, in_x + card_w/2, in_y, pr_x + card_w/4, pr_y + card_h, colors.HexColor('#10B981'), 2, 8)
    
    # Arrow from Outflow to PR (bottom edge to top edge)
    draw_elbow_arrow(c, out_x + card_w/2, out_y, pr_x + (card_w*3)/4, pr_y + card_h, colors.HexColor('#F59E0B'), 2, 8)

    # Inflow Card
    draw_shadow_rect(c, in_x, in_y, card_w, card_h, 8, 3, -3, 0.08)
    c.setFillColor(COLOR_WHITE)
    c.setStrokeColor(colors.HexColor('#E2E8F0'))
    c.roundRect(in_x, in_y, card_w, card_h, 8, fill=1, stroke=1)
    
    # Green accent strip
    c.setFillColor(colors.HexColor('#10B981'))
    c.path = c.beginPath()
    c.path.moveTo(in_x + 6, in_y)
    c.path.lineTo(in_x, in_y)
    c.path.lineTo(in_x, in_y + card_h)
    c.path.lineTo(in_x + 6, in_y + card_h)
    c.drawPath(c.path, stroke=0, fill=1)
    
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(in_x + 16, in_y + card_h - 22, "INFLOW")
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(in_x + 16, in_y + card_h - 38, "Monthly Salary")
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.drawString(in_x + 16, in_y + 20, format_currency(inflow))
    
    # Outflow Card
    draw_shadow_rect(c, out_x, out_y, card_w, card_h, 8, 3, -3, 0.08)
    c.setFillColor(COLOR_WHITE)
    c.roundRect(out_x, out_y, card_w, card_h, 8, fill=1, stroke=1)
    
    # Amber/Red accent strip
    c.setFillColor(colors.HexColor('#EF4444'))
    c.path = c.beginPath()
    c.path.moveTo(out_x + 6, out_y)
    c.path.lineTo(out_x, out_y)
    c.path.lineTo(out_x, out_y + card_h)
    c.path.lineTo(out_x + 6, out_y + card_h)
    c.drawPath(c.path, stroke=0, fill=1)
    
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(out_x + 16, out_y + card_h - 22, "OUTFLOW")
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(out_x + 16, out_y + card_h - 38, "Agreed Expenses")
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.drawString(out_x + 16, out_y + 20, format_currency(outflow))
    
    # Private Reserve Card (Centered)
    draw_shadow_rect(c, pr_x, pr_y, card_w, card_h + 10, 8, 3, -3, 0.1)
    c.setFillColor(COLOR_WHITE)
    c.roundRect(pr_x, pr_y, card_w, card_h + 10, 8, fill=1, stroke=1)
    
    # Blue accent strip
    c.setFillColor(colors.HexColor('#3B82F6'))
    c.path = c.beginPath()
    c.path.moveTo(pr_x + 6, pr_y)
    c.path.lineTo(pr_x, pr_y)
    c.path.lineTo(pr_x, pr_y + card_h + 10)
    c.path.lineTo(pr_x + 6, pr_y + card_h + 10)
    c.drawPath(c.path, stroke=0, fill=1)
    
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(pr_x + 16, pr_y + card_h - 12, "PRIVATE RESERVE")
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(pr_x + 16, pr_y + card_h - 28, "(Monthly Savings Goal)")
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.HexColor('#059669')) # Emerald highlight
    c.drawString(pr_x + 16, pr_y + 30, format_currency(excess))
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor('#3B82F6'))
    c.drawString(pr_x + 16, pr_y + 12, "Transferred Automatically")
    
    # Explanatory caption
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(36, 160, "System Overview & Operation:")
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT_MUTED)
    desc_text = (
        "The Simple Automated Cash Flow System (SACS) operates on a dual-bucket cash management "
        "framework. Every month, the take-home monthly salary (Inflow) is deposited. The pre-arranged "
        "monthly expense budget (Outflow) is systematically transferred to the client's spending account, "
        "leaving a safety buffer. All excess cash flow is swept automatically into the Private Reserve "
        "high-yield savings bucket to fund mid-term savings goals and build the cash cushion."
    )
    draw_wrapped_text(c, desc_text, 36, 140, 540, 15, font_size=9, align="left")
    
    # Page Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawRightString(576, 30, "Page 1 of 2")
    c.drawString(36, 30, "Windbrook Solutions | Confidential Client Financial Plan")
    
    # ------------------ PAGE 2 ------------------
    c.showPage()
    
    # Background
    c.setFillColor(colors.HexColor('#F8FAFC'))
    c.rect(0, 0, width, height, fill=1, stroke=0)
    
    draw_header(c, "PRIVATE RESERVE SUMMARY & LIQUID ASSETS", client_name, report['report_date'], report['quarter'])
    
    # Calculation Box (Target Reserve)
    draw_shadow_rect(c, 36, 440, 260, 220, 8, 3, -3, 0.08)
    c.setFillColor(COLOR_WHITE)
    c.setStrokeColor(colors.HexColor('#E2E8F0'))
    c.roundRect(36, 440, 260, 220, 8, fill=1, stroke=1)
    
    c.setFillColor(colors.HexColor('#3B82F6')) # Blue top bar
    c.roundRect(36, 640, 260, 20, 4, fill=1, stroke=0)
    c.rect(36, 640, 260, 10, fill=1, stroke=0)
    c.setFillColor(COLOR_WHITE)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 646, "TARGET RESERVE CALCULATION")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(50, 610, "6 Months Expenses Buffer")
    c.drawRightString(280, 610, format_currency(outflow * 6))
    
    # Itemized Deductibles
    c.drawString(50, 580, "Auto Insurance Deductible")
    c.drawRightString(280, 580, format_currency(client['deductible_auto']))
    c.drawString(50, 560, "Homeowners Deductible")
    c.drawRightString(280, 560, format_currency(client['deductible_home']))
    c.drawString(50, 540, "Health Insurance Deductible")
    c.drawRightString(280, 540, format_currency(client['deductible_health']))
    c.drawString(50, 520, "Other Deductibles")
    c.drawRightString(280, 520, format_currency(client['deductible_other']))
    
    c.setStrokeColor(colors.HexColor('#E2E8F0'))
    c.line(50, 505, 280, 505)
    
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, 485, "Total Reserve Target")
    c.setFillColor(colors.HexColor('#3B82F6'))
    c.drawRightString(280, 485, format_currency(pr_target))
    
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(50, 455, "*Formula: (6 × Monthly Outflow) + Deductibles")
    
    # Actual Reserves Box (Right)
    draw_shadow_rect(c, 316, 440, 260, 220, 8, 3, -3, 0.08)
    c.setFillColor(COLOR_WHITE)
    c.setStrokeColor(colors.HexColor('#E2E8F0'))
    c.roundRect(316, 440, 260, 220, 8, fill=1, stroke=1)
    
    c.setFillColor(colors.HexColor('#0F172A')) # Navy top bar
    c.roundRect(316, 640, 260, 20, 4, fill=1, stroke=0)
    c.rect(316, 640, 260, 10, fill=1, stroke=0)
    c.setFillColor(COLOR_WHITE)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(330, 646, "ACTUAL RESERVE CUSHION")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(330, 610, "Current Private Reserve Balance")
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(560, 610, format_currency(pr_balance))
    
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(330, 580, "Private Reserve Target Threshold")
    c.setFont("Helvetica", 11)
    c.drawRightString(560, 580, format_currency(pr_target))
    
    c.line(330, 560, 560, 560)
    
    # Net Surplus/Deficit
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    if pr_diff >= 0:
        c.drawString(330, 535, "Surplus Reserve Cushion")
        c.setFillColor(colors.HexColor('#059669'))
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(560, 535, f"+{format_currency(pr_diff)}")
        
        # Status badge (Premium Light Green)
        c.setFillColor(colors.HexColor('#D1FAE5'))
        c.roundRect(330, 465, 230, 45, 6, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#065F46'))
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(445, 482, "RESERVES FULLY FUNDED")
    else:
        c.drawString(330, 535, "Required Reserve Funding")
        c.setFillColor(colors.HexColor('#DC2626'))
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(560, 535, format_currency(abs(pr_diff)))
        
        # Status badge (Premium Light Red)
        c.setFillColor(colors.HexColor('#FEE2E2'))
        c.roundRect(330, 465, 230, 45, 6, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#991B1B'))
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(445, 482, "FUNDING DEFICIT")
        
    # Liquid Assets Table (Bottom Half)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(36, 395, "Total Investment & Liquidity Summary")
    
    # Table Box with Shadow
    draw_shadow_rect(c, 36, 235, 540, 140, 8, 3, -3, 0.08)
    c.setFillColor(COLOR_WHITE)
    c.roundRect(36, 235, 540, 140, 8, fill=1, stroke=1)
    
    # Table Header Row
    c.setFillColor(colors.HexColor('#F1F5F9')) # Light grey header row
    c.roundRect(36, 345, 540, 30, 8, fill=1, stroke=0)
    c.rect(36, 345, 540, 15, fill=1, stroke=0)
    
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor('#475569'))
    c.drawString(45, 356, "ASSET GROUP")
    c.drawString(200, 356, "INSTITUTION & DETAILS")
    c.drawRightString(420, 356, "CASH BALANCE")
    c.drawRightString(565, 356, "TOTAL VALUE")
    
    c.setStrokeColor(colors.HexColor('#E2E8F0'))
    c.setLineWidth(1)
    c.line(36, 345, 576, 345)
    
    schwab_total = 0
    schwab_cash = 0
    for bal in report['balances']:
        if 'schwab' in bal['institution'].lower():
            schwab_total += bal['balance']
            schwab_cash += bal['cash_balance']
            
    # Row 1: Private Reserve
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica", 9)
    c.drawString(45, 320, "Private Reserve")
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(200, 320, "Pinnacle Bank (Savings)")
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.drawRightString(420, 320, format_currency(pr_balance))
    c.drawRightString(565, 320, format_currency(pr_balance))
    c.line(36, 305, 576, 305)
    
    # Row 2: Schwab Investments
    c.drawString(45, 280, "Investment Portfolio")
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(200, 280, "Charles Schwab (Aggregated Assets)")
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.drawRightString(420, 280, format_currency(schwab_cash))
    c.drawRightString(565, 280, format_currency(schwab_total))
    c.line(36, 265, 576, 265)
    
    # Total row
    c.setFillColor(colors.HexColor('#F8FAFC'))
    c.roundRect(36, 235, 540, 30, 8, fill=1, stroke=0)
    c.rect(36, 265, 540, 15, fill=1, stroke=0)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(45, 246, "Total Liquid Reserve Assets")
    c.setFillColor(colors.HexColor('#059669')) # Emerald Total
    c.drawRightString(420, 246, format_currency(pr_balance + schwab_cash))
    c.drawRightString(565, 246, format_currency(pr_balance + schwab_total))
    c.setStrokeColor(COLOR_BORDER)
    c.line(36, 235, 576, 235)
    
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

def draw_shadow_rect(c, x, y, w, h, radius=6, offset_x=3, offset_y=-3, alpha=0.1):
    c.saveState()
    c.setFillColor(colors.HexColor('#94A3B8'))
    # Simulate simple shadow without opacity by using a very light solid color,
    # or use fill alpha if supported by reportlab (setStrokeAlpha/setFillAlpha).
    c.setFillAlpha(alpha)
    c.roundRect(x + offset_x, y + offset_y, w, h, radius, fill=1, stroke=0)
    c.restoreState()

def draw_elbow_line(c, x1, y1, x2, y2, color, thickness=1):
    c.setStrokeColor(color)
    c.setLineWidth(thickness)
    # Simple elbow joint: go down halfway, then across, then down
    mid_y = y1 - (y1 - y2) / 2
    c.line(x1, y1, x1, mid_y)
    c.line(x1, mid_y, x2, mid_y)
    c.line(x2, mid_y, x2, y2)

def generate_tcc_pdf(filepath, client, report):
    """Generates the Total Client Chart (TCC) Net Worth PDF report with a premium design."""
    c = canvas.Canvas(filepath, pagesize=(792, 612))
    
    # Base Premium Background
    c.setFillColor(colors.HexColor('#F8FAFC'))
    c.rect(0, 0, 792, 612, fill=1, stroke=0)
    
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
    c.setFont("Helvetica-Bold", 16)
    c.drawString(36, 542, "TOTAL CLIENT NET WORTH CHART")
    
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT_MUTED)
    meta_text = f"Client: {client_name}   |   Period: {report['quarter']}   |   Date: {report['report_date']}"
    c.drawString(36, 524, meta_text)
    
    c.setStrokeColor(colors.HexColor('#CBD5E1'))
    c.setLineWidth(1)
    c.line(36, 514, 756, 514)
    
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
    
    # --- Client Profile Info Pills (Deep Emerald) ---
    c.setFillColor(colors.HexColor('#059669'))
    draw_shadow_rect(c, 36, 445, 340, 56, 8, 2, -2, 0.1)
    c.roundRect(36, 445, 340, 56, 8, fill=1, stroke=0)
    c.setFillColor(COLOR_WHITE)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(48, 484, f"{client['client1_first_name']} {client['client1_last_name']}")
    c.setFont("Helvetica", 9)
    dob1 = client['client1_dob'] or "N/A"
    age1 = f"Age: {client['client1_age']}" if client['client1_age'] else "Age: N/A"
    ssn1 = f"SSN: ***-**-{client['client1_ssn_last_4']}" if client['client1_ssn_last_4'] else "SSN: N/A"
    c.drawString(48, 466, f"DOB: {dob1}   |   {age1}   |   {ssn1}")
    
    if client.get('client2_first_name'):
        c.setFillColor(colors.HexColor('#059669'))
        draw_shadow_rect(c, 416, 445, 340, 56, 8, 2, -2, 0.1)
        c.roundRect(416, 445, 340, 56, 8, fill=1, stroke=0)
        c.setFillColor(COLOR_WHITE)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(428, 484, f"{client['client2_first_name']} {client['client2_last_name']}")
        c.setFont("Helvetica", 9)
        dob2 = client['client2_dob'] or "N/A"
        age2 = f"Age: {client['client2_age']}" if client['client2_age'] else "Age: N/A"
        ssn2 = f"SSN: ***-**-{client['client2_ssn_last_4']}" if client['client2_ssn_last_4'] else "SSN: N/A"
        c.drawString(428, 466, f"DOB: {dob2}   |   {age2}   |   {ssn2}")
        
    # --- LAYOUT DESIGN FOR TCC ---
    # Center: Primary Residence / Trust Bubble
    cx_tr, cy_tr = 396, 260
    w_tr, h_tr = 200, 90
    draw_shadow_rect(c, cx_tr - w_tr/2, cy_tr - h_tr/2, w_tr, h_tr, 12, 3, -3, 0.15)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.roundRect(cx_tr - w_tr/2, cy_tr - h_tr/2, w_tr, h_tr, 12, fill=1, stroke=0)
    c.setFillColor(COLOR_WHITE)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(cx_tr, cy_tr + 26, "PRIMARY RESIDENCE TRUST")
    
    addr = client.get('trust_address', 'Address not specified')
    draw_wrapped_text(c, addr, cx_tr, cy_tr + 10, w_tr - 20, 11, font_size=8, align="center")
    
    c.setFillColor(colors.HexColor('#10B981')) # Emerald accent for value
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(cx_tr, cy_tr - 26, f"Zestimate: {format_currency(trust_value)}")
    
    # Connection line colors
    line_col = colors.HexColor('#94A3B8')
    
    # --- Top Left: Client 1 Retirement Box & Accounts ---
    c1_ret_box_x, c1_ret_box_y = 36, 370
    draw_shadow_rect(c, c1_ret_box_x, c1_ret_box_y, 170, 52, 8, 2, -2, 0.05)
    c.setFillColor(COLOR_WHITE)
    c.setStrokeColor(colors.HexColor('#E2E8F0'))
    c.roundRect(c1_ret_box_x, c1_ret_box_y, 170, 52, 8, fill=1, stroke=1)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(c1_ret_box_x + 12, c1_ret_box_y + 34, f"{client['client1_first_name']}'s Retirement")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(c1_ret_box_x + 12, c1_ret_box_y + 12, format_currency(c1_ret_total))
    
    count1 = len(c1_ret_accs)
    for idx, acc in enumerate(c1_ret_accs):
        if count1 <= 4:
            w, h = 170, 48
            px, py = c1_ret_box_x, c1_ret_box_y - 58 - (idx * 56)
        else:
            w, h = 120, 42
            col = idx % 2
            row = idx // 2
            px, py = c1_ret_box_x + (col * 130), c1_ret_box_y - 52 - (row * 50)
            
        draw_shadow_rect(c, px, py, w, h, 6, 2, -2, 0.05)
        c.setFillColor(COLOR_WHITE)
        c.setStrokeColor(colors.HexColor('#E2E8F0'))
        c.roundRect(px, py, w, h, 6, fill=1, stroke=1)
        
        # Color accent strip on the left
        c.setFillColor(colors.HexColor('#6366F1')) # Indigo
        c.path = c.beginPath()
        c.path.moveTo(px + 4, py)
        c.path.lineTo(px, py)
        c.path.lineTo(px, py + h)
        c.path.lineTo(px + 4, py + h)
        c.drawPath(c.path, stroke=0, fill=1)
        
        c.setFillColor(COLOR_PRIMARY_NAVY)
        c.setFont("Helvetica-Bold", 8 if count1 <= 4 else 7)
        c.drawString(px + 10, py + h - 14, f"{acc['institution']} {acc['subtype']}")
        c.setFont("Helvetica", 7.5 if count1 <= 4 else 6.5)
        c.setFillColor(COLOR_TEXT_MUTED)
        c.drawString(px + 10, py + h - 25, f"Account: *{acc['account_number_last_4']}")
        c.setFont("Helvetica-Bold", 9 if count1 <= 4 else 8)
        c.setFillColor(COLOR_PRIMARY_NAVY)
        val_str = format_currency(acc['balance'])
        if acc['cash_balance'] > 0:
            val_str += f" (Cash: {format_currency(acc['cash_balance'])})"
        c.drawString(px + 10, py + h - 38, val_str)
        
        if count1 <= 4:
            draw_elbow_line(c, px + 85, py + h, px + 85, py + h + (10 if idx==0 else 8), line_col)
        else:
            draw_elbow_line(c, px + w/2, py + h, px + w/2, py + h + 8, line_col)
            
    draw_elbow_line(c, c1_ret_box_x + 85, c1_ret_box_y + 52, cx_tr - w_tr/2 + 20, cy_tr + h_tr/2, line_col)

    # --- Top Right: Client 2 Retirement Box & Accounts ---
    if client.get('client2_first_name'):
        c2_ret_box_x, c2_ret_box_y = 586, 370
        draw_shadow_rect(c, c2_ret_box_x, c2_ret_box_y, 170, 52, 8, 2, -2, 0.05)
        c.setFillColor(COLOR_WHITE)
        c.setStrokeColor(colors.HexColor('#E2E8F0'))
        c.roundRect(c2_ret_box_x, c2_ret_box_y, 170, 52, 8, fill=1, stroke=1)
        c.setFillColor(COLOR_PRIMARY_NAVY)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(c2_ret_box_x + 12, c2_ret_box_y + 34, f"{client['client2_first_name']}'s Retirement")
        c.setFont("Helvetica-Bold", 14)
        c.drawString(c2_ret_box_x + 12, c2_ret_box_y + 12, format_currency(c2_ret_total))
        
        count2 = len(c2_ret_accs)
        for idx, acc in enumerate(c2_ret_accs):
            if count2 <= 4:
                w, h = 170, 48
                px, py = c2_ret_box_x, c2_ret_box_y - 58 - (idx * 56)
            else:
                w, h = 120, 42
                col = idx % 2
                row = idx // 2
                px, py = 502 + (col * 130), c2_ret_box_y - 52 - (row * 50)
                
            draw_shadow_rect(c, px, py, w, h, 6, 2, -2, 0.05)
            c.setFillColor(COLOR_WHITE)
            c.roundRect(px, py, w, h, 6, fill=1, stroke=1)
            
            c.setFillColor(colors.HexColor('#6366F1'))
            c.path = c.beginPath()
            c.path.moveTo(px + 4, py)
            c.path.lineTo(px, py)
            c.path.lineTo(px, py + h)
            c.path.lineTo(px + 4, py + h)
            c.drawPath(c.path, stroke=0, fill=1)
            
            c.setFillColor(COLOR_PRIMARY_NAVY)
            c.setFont("Helvetica-Bold", 8 if count2 <= 4 else 7)
            c.drawString(px + 10, py + h - 14, f"{acc['institution']} {acc['subtype']}")
            c.setFont("Helvetica", 7.5 if count2 <= 4 else 6.5)
            c.setFillColor(COLOR_TEXT_MUTED)
            c.drawString(px + 10, py + h - 25, f"Account: *{acc['account_number_last_4']}")
            c.setFont("Helvetica-Bold", 9 if count2 <= 4 else 8)
            c.setFillColor(COLOR_PRIMARY_NAVY)
            val_str = format_currency(acc['balance'])
            if acc['cash_balance'] > 0:
                val_str += f" (Cash: {format_currency(acc['cash_balance'])})"
            c.drawString(px + 10, py + h - 38, val_str)
            
            if count2 <= 4:
                draw_elbow_line(c, px + 85, py + h, px + 85, py + h + (10 if idx==0 else 8), line_col)
            else:
                draw_elbow_line(c, px + w/2, py + h, px + w/2, py + h + 8, line_col)
                
        draw_elbow_line(c, c2_ret_box_x + 85, c2_ret_box_y + 52, cx_tr + w_tr/2 - 20, cy_tr + h_tr/2, line_col)

    # --- Bottom: Non-Retirement Box & Accounts ---
    non_ret_box_x, non_ret_box_y = 311, 150
    draw_shadow_rect(c, non_ret_box_x, non_ret_box_y, 170, 52, 8, 2, -2, 0.05)
    c.setFillColor(COLOR_WHITE)
    c.setStrokeColor(colors.HexColor('#E2E8F0'))
    c.roundRect(non_ret_box_x, non_ret_box_y, 170, 52, 8, fill=1, stroke=1)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(non_ret_box_x + 12, non_ret_box_y + 34, "Non-Retirement Assets")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(non_ret_box_x + 12, non_ret_box_y + 12, format_currency(non_ret_total))
    
    count_non = len(non_ret_accs)
    for idx, acc in enumerate(non_ret_accs):
        w, h = 130, 46
        if count_non == 1:
            px = 396 - w/2
        else:
            spacing = (720 - w) / max(1, count_non - 1)
            px = 36 + (idx * spacing)
        py = non_ret_box_y - 65
        
        draw_shadow_rect(c, px, py, w, h, 6, 2, -2, 0.05)
        c.setFillColor(COLOR_WHITE)
        c.roundRect(px, py, w, h, 6, fill=1, stroke=1)
        
        c.setFillColor(colors.HexColor('#F59E0B')) # Amber accent
        c.path = c.beginPath()
        c.path.moveTo(px + 4, py)
        c.path.lineTo(px, py)
        c.path.lineTo(px, py + h)
        c.path.lineTo(px + 4, py + h)
        c.drawPath(c.path, stroke=0, fill=1)
        
        c.setFillColor(COLOR_PRIMARY_NAVY)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(px + 10, py + h - 14, f"{acc['institution']} {acc['subtype']}")
        c.setFont("Helvetica", 7.5)
        c.setFillColor(COLOR_TEXT_MUTED)
        c.drawString(px + 10, py + h - 25, f"Account: *{acc['account_number_last_4']}")
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(COLOR_PRIMARY_NAVY)
        val_str = format_currency(acc['balance'])
        if acc['cash_balance'] > 0:
            val_str += f" (Cash: {format_currency(acc['cash_balance'])})"
        c.drawString(px + 10, py + h - 38, val_str)
        
        draw_elbow_line(c, px + w/2, py + h, non_ret_box_x + 85, non_ret_box_y, line_col)
        
    draw_elbow_line(c, non_ret_box_x + 85, non_ret_box_y + 52, cx_tr, cy_tr - h_tr/2, line_col)
    
    # --- Bottom Left: Liabilities Summary Card ---
    lia_box_x, lia_box_y = 36, 40
    draw_shadow_rect(c, lia_box_x, lia_box_y, 250, 90, 10, 3, -3, 0.05)
    c.setFillColor(COLOR_WHITE)
    c.setStrokeColor(colors.HexColor('#FECACA')) # Soft red border
    c.roundRect(lia_box_x, lia_box_y, 250, 90, 10, fill=1, stroke=1)
    
    c.setFillColor(colors.HexColor('#EF4444')) # Red header banner
    c.path = c.beginPath()
    c.path.moveTo(lia_box_x + 10, lia_box_y + 90)
    c.path.lineTo(lia_box_x, lia_box_y + 90)
    c.path.lineTo(lia_box_x, lia_box_y + 70)
    c.path.lineTo(lia_box_x + 250, lia_box_y + 70)
    c.path.lineTo(lia_box_x + 250, lia_box_y + 90)
    c.path.lineTo(lia_box_x + 240, lia_box_y + 90)
    # Just draw a rect for simplicity over the top edge
    c.roundRect(lia_box_x, lia_box_y + 70, 250, 20, 4, fill=1, stroke=0)
    c.rect(lia_box_x, lia_box_y + 70, 250, 10, fill=1, stroke=0) # square off bottom corners
    
    c.setFillColor(COLOR_WHITE)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(lia_box_x + 12, lia_box_y + 76, "LIABILITIES & OUTSTANDING DEBTS")
    
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    for idx, acc in enumerate(liabilities_accs[:3]):
        lia_text = f"• {acc['institution']} {acc['subtype']} (*{acc['account_number_last_4']})"
        c.drawString(lia_box_x + 12, lia_box_y + 55 - (idx * 14), lia_text)
        c.drawRightString(lia_box_x + 238, lia_box_y + 55 - (idx * 14), format_currency(acc['balance']))
        
    c.setStrokeColor(colors.HexColor('#E2E8F0'))
    c.line(lia_box_x + 12, lia_box_y + 24, lia_box_x + 238, lia_box_y + 24)
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor('#DC2626')) # Red
    c.drawString(lia_box_x + 12, lia_box_y + 10, "Total Liabilities")
    c.drawRightString(lia_box_x + 238, lia_box_y + 10, format_currency(liabilities_total))
    
    # --- Bottom Right: Grand Total Net Worth Box ---
    gt_box_x, gt_box_y = 506, 40
    draw_shadow_rect(c, gt_box_x, gt_box_y, 250, 90, 10, 4, -4, 0.1)
    c.setFillColor(COLOR_WHITE)
    c.setStrokeColor(colors.HexColor('#A7F3D0')) # Soft green border
    c.roundRect(gt_box_x, gt_box_y, 250, 90, 10, fill=1, stroke=1)
    
    c.setFillColor(colors.HexColor('#10B981')) # Emerald green banner
    c.roundRect(gt_box_x, gt_box_y + 70, 250, 20, 4, fill=1, stroke=0)
    c.rect(gt_box_x, gt_box_y + 70, 250, 10, fill=1, stroke=0)
    
    c.setFillColor(COLOR_WHITE)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(gt_box_x + 12, gt_box_y + 76, "ESTIMATED CLIENT NET WORTH")
    
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_PRIMARY_NAVY)
    c.drawString(gt_box_x + 12, gt_box_y + 55, "Total Retirement Portfolio:")
    c.drawRightString(gt_box_x + 238, gt_box_y + 55, format_currency(c1_ret_total + c2_ret_total))
    
    c.drawString(gt_box_x + 12, gt_box_y + 41, "Total Non-Retirement Portfolio:")
    c.drawRightString(gt_box_x + 238, gt_box_y + 41, format_currency(non_ret_total))
    
    c.drawString(gt_box_x + 12, gt_box_y + 27, "Primary Residence Trust Value:")
    c.drawRightString(gt_box_x + 238, gt_box_y + 27, format_currency(trust_value))
    
    c.setStrokeColor(colors.HexColor('#E2E8F0'))
    c.line(gt_box_x + 12, gt_box_y + 22, gt_box_x + 238, gt_box_y + 22)
    
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor('#047857')) # Deep emerald
    c.drawString(gt_box_x + 12, gt_box_y + 6, "Grand Total")
    c.drawRightString(gt_box_x + 238, gt_box_y + 6, format_currency(grand_total_net_worth))
    
    # Landscape Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(36, 15, "Windbrook Solutions | Confidential Financial Assessment - TCC Chart")
    c.drawRightString(756, 15, "Page 1 of 1")
    
    c.save()
