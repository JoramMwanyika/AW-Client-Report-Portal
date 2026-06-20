let clientsData = [];
let activeClientId = null;
let lastReportData = null; // Stored previous report balances for quick pre-fill reference
let canvaClientId = null;

// On Load
document.addEventListener("DOMContentLoaded", () => {
    loadClients();
    loadConfig();
});

async function loadConfig() {
    try {
        const res = await fetch('/api/config');
        const data = await res.json();
        canvaClientId = data.canva_client_id;
    } catch (err) {
        console.error("Failed to load Canva configuration:", err);
    }
}

// View Switching
function switchView(viewId) {
    document.querySelectorAll('.view-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const targetPanel = document.getElementById(`view-${viewId}`);
    if (targetPanel) {
        targetPanel.classList.add('active');
    }
    
    // Set sidebar item highlight
    if (viewId === 'client-list') {
        document.querySelector('.nav-item[onclick*="client-list"]').classList.add('active');
    } else if (viewId === 'client-setup' && !activeClientId) {
        document.querySelector('.nav-item[onclick*="openNewClientForm"]').classList.add('active');
    }
}

// FORMATTING HELPERS
function formatCurrency(value) {
    const number = parseFloat(value);
    if (isNaN(number)) return "$0";
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0
    }).format(number);
}

function formatPercent(value) {
    const number = parseFloat(value);
    if (isNaN(number)) return "0.0%";
    return number.toFixed(2) + "%";
}

// ----------------- CLIENT DIRECTORY -----------------
async function loadClients() {
    try {
        const response = await fetch('/api/clients');
        const clients = await response.json();
        clientsData = clients;
        
        const container = document.getElementById('clients-container');
        container.innerHTML = '';
        
        if (clients.length === 0) {
            container.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 40px; border: 2px dashed var(--color-border); border-radius: var(--radius-md);">
                    <p style="color: var(--color-text-muted); font-size: 1rem; margin-bottom: 16px;">No client records exist yet.</p>
                    <button class="btn btn-primary" onclick="openNewClientForm()">Add Your First Client</button>
                </div>
            `;
            return;
        }
        
        clients.forEach(client => {
            const card = document.createElement('div');
            card.className = 'client-card';
            card.onclick = () => viewClientReports(client.id);
            
            let name = `${client.client1_first_name} ${client.client1_last_name}`;
            if (client.client2_first_name) {
                name += ` & ${client.client2_first_name}`;
            }
            
            const lastReport = client.last_report_quarter ? `${client.last_report_quarter} (${client.last_report_date})` : 'Never';
            
            card.innerHTML = `
                <div class="client-card-name">${name}</div>
                <div class="client-card-meta">Primary Owner: ${client.client1_first_name} (${client.client1_age ? 'Age ' + client.client1_age : 'Age N/A'})</div>
                <div class="client-card-stats">
                    <div style="flex: 1">
                        <span class="client-card-stat-label">Last Report</span>
                        <span>${lastReport}</span>
                    </div>
                    <div style="flex: 1; text-align: right">
                        <span class="client-card-stat-label">Salary / Budget</span>
                        <span>${formatCurrency(client.monthly_salary)} / ${formatCurrency(client.agreed_expense_budget)}</span>
                    </div>
                </div>
                <div style="margin-top: 16px; display: flex; gap: 8px; justify-content: flex-end" onclick="event.stopPropagation()">
                    <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.8rem" onclick="openEditClientForm(${client.id})">Edit Profile</button>
                    <button class="btn btn-primary" style="padding: 6px 12px; font-size: 0.8rem" onclick="openReportEntryForm(${client.id})">New Report</button>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Error loading clients:", err);
    }
}

// ----------------- CLIENT SETUP VIEW -----------------
function openNewClientForm() {
    activeClientId = null;
    document.getElementById('setup-title').textContent = 'Create Client Record';
    document.getElementById('setup-client-id').value = '';
    document.getElementById('client-form').reset();
    document.getElementById('has-spouse').checked = false;
    toggleSpouseSection(false);
    document.getElementById('accounts-tbody').innerHTML = '';
    
    // Default account list (standard setup helper)
    addAccountRow({ owner: 'Client 1', type: 'Retirement', subtype: 'Roth IRA', institution: 'Charles Schwab', account_number_last_4: '', interest_rate: 0 });
    addAccountRow({ owner: 'Client 1', type: 'Retirement', subtype: 'Traditional IRA', institution: 'Charles Schwab', account_number_last_4: '', interest_rate: 0 });
    addAccountRow({ owner: 'Joint', type: 'Non-Retirement', subtype: 'Brokerage', institution: 'Charles Schwab', account_number_last_4: '', interest_rate: 0 });
    addAccountRow({ owner: 'Joint', type: 'Non-Retirement', subtype: 'Checking', institution: 'Pinnacle Bank', account_number_last_4: '', interest_rate: 0 });
    
    switchView('client-setup');
}

async function openEditClientForm(clientId) {
    activeClientId = clientId;
    document.getElementById('setup-title').textContent = 'Edit Client Profile';
    document.getElementById('setup-client-id').value = clientId;
    
    try {
        const cResponse = await fetch(`/api/clients/${clientId}`);
        const client = await cResponse.json();
        
        document.getElementById('c1-first').value = client.client1_first_name;
        document.getElementById('c1-last').value = client.client1_last_name;
        document.getElementById('c1-dob').value = client.client1_dob || '';
        document.getElementById('c1-ssn').value = client.client1_ssn_last_4 || '';
        
        if (client.client2_first_name) {
            document.getElementById('has-spouse').checked = true;
            toggleSpouseSection(true);
            document.getElementById('c2-first').value = client.client2_first_name;
            document.getElementById('c2-last').value = client.client2_last_name;
            document.getElementById('c2-dob').value = client.client2_dob || '';
            document.getElementById('c2-ssn').value = client.client2_ssn_last_4 || '';
        } else {
            document.getElementById('has-spouse').checked = false;
            toggleSpouseSection(false);
        }
        
        document.getElementById('monthly-salary').value = client.monthly_salary;
        document.getElementById('agreed-expense').value = client.agreed_expense_budget;
        document.getElementById('trust-address').value = client.trust_address || '';
        
        document.getElementById('ded-auto').value = client.deductible_auto;
        document.getElementById('ded-home').value = client.deductible_home;
        document.getElementById('ded-health').value = client.deductible_health;
        document.getElementById('ded-other').value = client.deductible_other;
        
        // Fetch accounts
        const aResponse = await fetch(`/api/clients/${clientId}/accounts`);
        const accounts = await aResponse.json();
        
        const tbody = document.getElementById('accounts-tbody');
        tbody.innerHTML = '';
        accounts.forEach(acc => addAccountRow(acc));
        
        switchView('client-setup');
    } catch (err) {
        console.error("Error loading client for edit:", err);
    }
}

function toggleSpouseSection(show) {
    document.getElementById('spouse-section').style.display = show ? 'block' : 'none';
}

function addAccountRow(acc = null) {
    const tbody = document.getElementById('accounts-tbody');
    const row = document.createElement('tr');
    
    const owner = acc ? acc.owner : 'Client 1';
    const type = acc ? acc.type : 'Retirement';
    const subtype = acc ? acc.subtype : 'Roth IRA';
    const institution = acc ? acc.institution : '';
    const last4 = acc ? acc.account_number_last_4 : '';
    const rate = acc ? acc.interest_rate : 0;
    
    row.innerHTML = `
        <td>
            <select class="form-control" onchange="handleAccountTypeChange(this)" name="type">
                <option value="Retirement" ${type === 'Retirement' ? 'selected' : ''}>Retirement</option>
                <option value="Non-Retirement" ${type === 'Non-Retirement' ? 'selected' : ''}>Non-Retirement</option>
                <option value="Trust" ${type === 'Trust' ? 'selected' : ''}>Trust Asset</option>
                <option value="Liability" ${type === 'Liability' ? 'selected' : ''}>Liability</option>
            </select>
        </td>
        <td>
            <select class="form-control" name="owner">
                <option value="Client 1" ${owner === 'Client 1' ? 'selected' : ''}>Client 1</option>
                <option value="Client 2" ${owner === 'Client 2' ? 'selected' : ''}>Client 2</option>
                <option value="Joint" ${owner === 'Joint' ? 'selected' : ''}>Joint / Trust</option>
            </select>
        </td>
        <td>
            <input class="form-control" type="text" name="subtype" value="${subtype}" placeholder="e.g. Roth IRA, Mortgage">
        </td>
        <td>
            <input class="form-control" type="text" name="institution" value="${institution}" placeholder="e.g. Charles Schwab">
        </td>
        <td>
            <input class="form-control" type="text" name="last4" value="${last4}" maxlength="4" placeholder="Last 4">
        </td>
        <td>
            <input class="form-control" type="number" name="rate" value="${rate}" step="any" min="0" ${type !== 'Liability' ? 'disabled' : ''}>
        </td>
        <td>
            <button type="button" class="btn btn-danger" style="padding: 4px 8px" onclick="deleteAccountRow(this)">Remove</button>
        </td>
    `;
    tbody.appendChild(row);
}

function deleteAccountRow(button) {
    button.closest('tr').remove();
}

function handleAccountTypeChange(select) {
    const row = select.closest('tr');
    const rateInput = row.querySelector('input[name="rate"]');
    if (select.value === 'Liability') {
        rateInput.removeAttribute('disabled');
    } else {
        rateInput.setAttribute('disabled', 'true');
        rateInput.value = '0';
    }
}

async function saveClientProfile(event) {
    event.preventDefault();
    
    const hasSpouse = document.getElementById('has-spouse').checked;
    
    const clientData = {
        client1_first_name: document.getElementById('c1-first').value,
        client1_last_name: document.getElementById('c1-last').value,
        client1_dob: document.getElementById('c1-dob').value || null,
        client1_ssn_last_4: document.getElementById('c1-ssn').value || null,
        client2_first_name: hasSpouse ? document.getElementById('c2-first').value : null,
        client2_last_name: hasSpouse ? document.getElementById('c2-last').value : null,
        client2_dob: hasSpouse ? document.getElementById('c2-dob').value : null,
        client2_ssn_last_4: hasSpouse ? document.getElementById('c2-ssn').value : null,
        monthly_salary: parseFloat(document.getElementById('monthly-salary').value) || 0,
        agreed_expense_budget: parseFloat(document.getElementById('agreed-expense').value) || 0,
        trust_address: document.getElementById('trust-address').value || null,
        deductible_auto: parseFloat(document.getElementById('ded-auto').value) || 0,
        deductible_home: parseFloat(document.getElementById('ded-home').value) || 0,
        deductible_health: parseFloat(document.getElementById('ded-health').value) || 0,
        deductible_other: parseFloat(document.getElementById('ded-other').value) || 0
    };
    
    const id = document.getElementById('setup-client-id').value;
    const url = id ? `/api/clients/${id}` : '/api/clients';
    const method = id ? 'PUT' : 'POST';
    
    try {
        const clientRes = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(clientData)
        });
        const clientResult = await clientRes.json();
        
        if (!clientRes.ok) {
            alert(clientResult.error || "Failed to save client profile");
            return;
        }
        
        const savedClientId = id || clientResult.id;
        
        // Compile accounts list
        const accounts = [];
        document.querySelectorAll('#accounts-tbody tr').forEach(row => {
            accounts.push({
                type: row.querySelector('select[name="type"]').value,
                owner: row.querySelector('select[name="owner"]').value,
                subtype: row.querySelector('input[name="subtype"]').value,
                institution: row.querySelector('input[name="institution"]').value,
                account_number_last_4: row.querySelector('input[name="last4"]').value,
                interest_rate: parseFloat(row.querySelector('input[name="rate"]').value) || 0
            });
        });
        
        // Save accounts
        const accountsRes = await fetch(`/api/clients/${savedClientId}/accounts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(accounts)
        });
        
        if (!accountsRes.ok) {
            alert("Client profile saved, but failed to save account structures.");
        }
        
        loadClients();
        switchView('client-list');
    } catch (err) {
        console.error("Error saving client profile:", err);
    }
}

// ----------------- QUARTERLY DATA ENTRY VIEW -----------------
let currentClientProfile = null;
let currentClientAccounts = [];

async function openReportEntryForm(clientId) {
    activeClientId = clientId;
    document.getElementById('report-client-id').value = clientId;
    document.getElementById('report-entry-form').reset();
    
    // Set current date
    const today = new Date().toISOString().substring(0, 10);
    document.getElementById('rep-date').value = today;
    
    // Determine Quarter auto-suggestion (e.g. Q1 2026)
    const month = new Date().getMonth();
    const year = new Date().getFullYear();
    let suggestedQ = `${year}-Q1`;
    if (month >= 3 && month < 6) suggestedQ = `${year}-Q2`;
    else if (month >= 6 && month < 9) suggestedQ = `${year}-Q3`;
    else if (month >= 9) suggestedQ = `${year}-Q4`;
    document.getElementById('rep-quarter').value = suggestedQ;
    
    try {
        // Load Client info
        const cRes = await fetch(`/api/clients/${clientId}`);
        currentClientProfile = await cRes.json();
        
        let clientName = `${currentClientProfile.client1_first_name} ${currentClientProfile.client1_last_name}`;
        if (currentClientProfile.client2_first_name) {
            clientName += ` & ${currentClientProfile.client2_first_name} ${currentClientProfile.client2_last_name}`;
        }
        document.getElementById('report-client-subtitle').textContent = `Quarterly Balances Checklist for ${clientName}`;
        
        // Load Accounts structure
        const aRes = await fetch(`/api/clients/${clientId}/accounts`);
        currentClientAccounts = await aRes.json();
        
        // Load Most Recent Report for quick reference
        const rRes = await fetch(`/api/clients/${clientId}/recent-report`);
        lastReportData = await rRes.json();
        
        // Reset Previous references overlays
        document.getElementById('last-rep-private-reserve-ref').textContent = lastReportData ? `Previous: ${formatCurrency(lastReportData.private_reserve_balance)}` : 'Previous: N/A';
        document.getElementById('last-rep-trust-value-ref').textContent = lastReportData ? `Previous: ${formatCurrency(lastReportData.trust_zillow_value)}` : 'Previous: N/A';
        
        // Build accounts table rows
        const tbody = document.getElementById('report-accounts-tbody');
        tbody.innerHTML = '';
        
        if (currentClientAccounts.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--color-text-muted)">No accounts configured for this client. Please configure accounts in the Edit Profile screen.</td></tr>`;
        }
        
        currentClientAccounts.forEach(acc => {
            const row = document.createElement('tr');
            
            // Find if there is a previous balance for this account
            let prevBal = null;
            let prevCash = null;
            if (lastReportData && lastReportData.balances) {
                const match = lastReportData.balances.find(b => b.account_id === acc.id);
                if (match) {
                    prevBal = match.balance;
                    prevCash = match.cash_balance;
                }
            }
            
            const prevBalLabel = prevBal !== null ? `Prev: ${formatCurrency(prevBal)}` : 'Prev: N/A';
            const prevCashLabel = prevCash !== null ? `Prev: ${formatCurrency(prevCash)}` : 'Prev: N/A';
            
            // Checking if cash field is needed (only for Retirement or Non-Retirement)
            const isCashNeeded = (acc.type === 'Retirement' || acc.type === 'Non-Retirement');
            
            row.innerHTML = `
                <td>
                    <span style="font-weight:600;display:block">${acc.institution} ${acc.subtype}</span>
                    <span style="font-size:0.75rem;color:var(--color-text-muted)">*${acc.account_number_last_4 || 'N/A'}</span>
                </td>
                <td>${acc.owner}</td>
                <td><span class="badge ${acc.type === 'Retirement' ? 'badge-blue' : acc.type === 'Liability' ? 'badge-red' : 'badge-green'}">${acc.type}</span></td>
                <td>
                    <div style="display:flex;gap:4px;flex-direction:column">
                        <input class="form-control balance-input" type="number" name="balance-${acc.id}" data-account-id="${acc.id}" data-type="${acc.type}" data-owner="${acc.owner}" min="0" step="any" placeholder="0" required oninput="triggerCalculations()">
                        <span style="font-size:0.7rem;color:var(--color-text-muted)">${prevBalLabel}</span>
                    </div>
                </td>
                <td>
                    ${isCashNeeded ? `
                    <div style="display:flex;gap:4px;flex-direction:column">
                        <input class="form-control cash-input" type="number" name="cash-${acc.id}" data-account-id="${acc.id}" min="0" step="any" placeholder="0" oninput="triggerCalculations()">
                        <span style="font-size:0.7rem;color:var(--color-text-muted)">${prevCashLabel}</span>
                    </div>` : `<span style="color:var(--color-text-muted);font-size:0.8rem">-</span>`}
                </td>
                <td>
                    <button type="button" class="btn btn-secondary" style="padding:4px 8px; font-size:0.75rem" onclick="useLastAccVal(${acc.id}, ${prevBal}, ${prevCash})">Use Last</button>
                </td>
            `;
            tbody.appendChild(row);
        });
        
        triggerCalculations();
        switchView('report-entry');
    } catch (err) {
        console.error("Error setting up report entry form:", err);
    }
}

function cancelReportEntry() {
    viewClientReports(activeClientId);
}

function useLastReportVal(fieldId) {
    if (!lastReportData) return;
    if (fieldId === 'rep-private-reserve') {
        document.getElementById('rep-private-reserve').value = lastReportData.private_reserve_balance;
    } else if (fieldId === 'rep-trust-value') {
        document.getElementById('rep-trust-value').value = lastReportData.trust_zillow_value;
    }
    triggerCalculations();
}

function useLastAccVal(accId, prevBal, prevCash) {
    if (prevBal !== null) {
        const balInput = document.querySelector(`input[name="balance-${accId}"]`);
        if (balInput) balInput.value = prevBal;
    }
    if (prevCash !== null) {
        const cashInput = document.querySelector(`input[name="cash-${accId}"]`);
        if (cashInput) cashInput.value = prevCash;
    }
    triggerCalculations();
}

// REAL-TIME AUTO CALCULATIONS ENGINE
function triggerCalculations() {
    if (!currentClientProfile) return;
    
    // Inflow & Outflow
    const inflow = currentClientProfile.monthly_salary;
    const outflow = currentClientProfile.agreed_expense_budget;
    const excess = inflow - outflow;
    
    document.getElementById('preview-inflow').textContent = formatCurrency(inflow);
    document.getElementById('preview-outflow').textContent = formatCurrency(outflow);
    
    const excessEl = document.getElementById('preview-excess');
    excessEl.textContent = formatCurrency(excess);
    if (excess >= 0) {
        excessEl.className = 'calc-value-positive';
    } else {
        excessEl.className = 'calc-value-negative';
    }
    
    // Private Reserve Target Cushion
    const deductibles = currentClientProfile.deductible_auto + currentClientProfile.deductible_home + currentClientProfile.deductible_health + currentClientProfile.deductible_other;
    const targetPr = (outflow * 6) + deductibles;
    document.getElementById('preview-pr-target').textContent = formatCurrency(targetPr);
    
    // Actual entered Private Reserve
    const actualPr = parseFloat(document.getElementById('rep-private-reserve').value) || 0;
    document.getElementById('preview-pr-actual').textContent = formatCurrency(actualPr);
    
    const prSurplus = actualPr - targetPr;
    const surplusEl = document.getElementById('preview-pr-surplus');
    surplusEl.textContent = prSurplus >= 0 ? `+${formatCurrency(prSurplus)}` : `-${formatCurrency(Math.abs(prSurplus))}`;
    surplusEl.className = prSurplus >= 0 ? 'calc-value-positive' : 'calc-value-negative';
    
    // Portfolio Sums
    let c1Retirement = 0;
    let c2Retirement = 0;
    let nonRetirement = 0;
    let liabilities = 0;
    
    document.querySelectorAll('#report-accounts-tbody tr').forEach(row => {
        const balInput = row.querySelector('.balance-input');
        if (!balInput) return;
        
        const bal = parseFloat(balInput.value) || 0;
        const type = balInput.getAttribute('data-type');
        const owner = balInput.getAttribute('data-owner');
        
        if (type === 'Retirement') {
            if (owner === 'Client 1') {
                c1Retirement += bal;
            } else {
                c2Retirement += bal;
            }
        } else if (type === 'Non-Retirement') {
            nonRetirement += bal;
        } else if (type === 'Liability') {
            liabilities += bal;
        }
    });
    
    const trustVal = parseFloat(document.getElementById('rep-trust-value').value) || 0;
    
    // Grand Total Net Worth (liabilities NOT subtracted)
    const grandTotal = c1Retirement + c2Retirement + nonRetirement + trustVal;
    
    document.getElementById('preview-c1-retirement').textContent = formatCurrency(c1Retirement);
    document.getElementById('preview-c2-retirement').textContent = formatCurrency(c2Retirement);
    document.getElementById('preview-non-retirement').textContent = formatCurrency(nonRetirement);
    document.getElementById('preview-trust-val').textContent = formatCurrency(trustVal);
    document.getElementById('preview-liabilities').textContent = formatCurrency(liabilities);
    
    document.getElementById('preview-grand-total').textContent = formatCurrency(grandTotal);
}

async function saveQuarterlyBalances(event) {
    event.preventDefault();
    
    const clientId = document.getElementById('report-client-id').value;
    const reportData = {
        quarter: document.getElementById('rep-quarter').value,
        report_date: document.getElementById('rep-date').value,
        private_reserve_balance: parseFloat(document.getElementById('rep-private-reserve').value) || 0,
        trust_zillow_value: parseFloat(document.getElementById('rep-trust-value').value) || 0,
        balances: []
    };
    
    document.querySelectorAll('#report-accounts-tbody tr').forEach(row => {
        const balInput = row.querySelector('.balance-input');
        if (!balInput) return;
        
        const accountId = parseInt(balInput.getAttribute('data-account-id'));
        const cashInput = row.querySelector('.cash-input');
        const cashBal = cashInput ? (parseFloat(cashInput.value) || 0) : 0;
        
        reportData.balances.push({
            account_id: accountId,
            balance: parseFloat(balInput.value) || 0,
            cash_balance: cashBal
        });
    });
    
    try {
        const response = await fetch(`/api/clients/${clientId}/reports`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(reportData)
        });
        const result = await response.json();
        
        if (response.ok) {
            viewClientReports(clientId);
        } else {
            alert(result.error || "Failed to save quarterly balances");
        }
    } catch (err) {
        console.error("Error saving quarterly balances:", err);
    }
}

// ----------------- REPORT HISTORY ARCHIVE -----------------
async function viewClientReports(clientId) {
    activeClientId = clientId;
    
    try {
        // Load Client info
        const cRes = await fetch(`/api/clients/${clientId}`);
        const client = await cRes.json();
        
        let clientName = `${client.client1_first_name} ${client.client1_last_name}`;
        if (client.client2_first_name) {
            clientName += ` & ${client.client2_first_name} ${client.client2_last_name}`;
        }
        
        document.getElementById('history-title').textContent = `Report Archive for ${clientName}`;
        document.getElementById('history-subtitle').textContent = `View historical quarterly filings or download SACS and TCC PDF reports.`;
        
        // Bind generate new report button
        document.getElementById('history-new-report-btn').onclick = () => openReportEntryForm(clientId);
        
        // Fetch historical reports
        const rRes = await fetch(`/api/clients/${clientId}/reports`);
        const reports = await rRes.json();
        
        const tbody = document.getElementById('reports-history-tbody');
        tbody.innerHTML = '';
        
        if (reports.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:32px;color:var(--color-text-muted)">No reports generated yet. Click "Generate New Report" to start.</td></tr>`;
            switchView('report-history');
            return;
        }
        
        tbody.innerHTML = '';
        for (const rep of reports) {
            const repDetRes = await fetch(`/api/reports/${rep.id}`);
            if (!repDetRes.ok) continue;
            const rDetails = await repDetRes.json();
            
            // Calculate NW
            let c1Ret = 0, c2Ret = 0, nonRet = 0, liabs = 0;
            rDetails.balances.forEach(b => {
                if (b.type === 'Retirement') {
                    if (b.owner === 'Client 1') c1Ret += b.balance;
                    else c2Ret += b.balance;
                } else if (b.type === 'Non-Retirement') {
                    nonRet += b.balance;
                } else if (b.type === 'Liability') {
                    liabs += b.balance;
                }
            });
            const nw = c1Ret + c2Ret + nonRet + rDetails.trust_zillow_value;
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${rep.quarter}</strong></td>
                <td>${rep.report_date}</td>
                <td>${formatCurrency(rep.private_reserve_balance)}</td>
                <td style="font-weight:600; color:var(--color-green-dark)">${formatCurrency(nw)}</td>
                <td style="color:var(--color-red-dark)">${formatCurrency(liabs)}</td>
                <td>
                    <div class="actions-cell" style="display: flex; gap: 6px; flex-wrap: wrap;">
                        <a href="/api/reports/${rep.id}/download/sacs" download="SACS_${rep.quarter}.pdf" class="btn btn-success" style="padding: 6px 10px; font-size: 0.75rem">SACS PDF</a>
                        <button onclick="exportToCanva(${rep.id}, 'sacs')" class="btn btn-secondary" style="padding: 6px 10px; font-size: 0.75rem">Canva SACS</button>
                        <a href="/api/reports/${rep.id}/download/tcc" download="TCC_${rep.quarter}.pdf" class="btn btn-primary" style="padding: 6px 10px; font-size: 0.75rem">TCC PDF</a>
                        <button onclick="exportToCanva(${rep.id}, 'tcc')" class="btn btn-secondary" style="padding: 6px 10px; font-size: 0.75rem">Canva TCC</button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        }
        
        switchView('report-history');
    } catch (err) {
        console.error("Error showing client reports:", err);
    }
}

// CANVA EXPORT TRIGGER
async function exportToCanva(reportId, type) {
    const btn = event.target;
    const oldText = btn.textContent;
    btn.textContent = "Processing...";
    btn.disabled = true;

    // Open the window synchronously to bypass browser popup blockers
    const canvaWindow = window.open('about:blank', '_blank');

    try {
        // Fetch the PDF as a blob to force a local download (preventing the browser from opening it inline)
        const response = await fetch(`/api/reports/${reportId}/download/${type}`);
        if (!response.ok) throw new Error("Failed to download PDF");
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        const filename = `${type.toUpperCase()}_Report_${reportId}.pdf`;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        
        setTimeout(() => {
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }, 100);

        // Point the new window to Canva's dedicated PDF editor
        canvaWindow.location.href = 'https://www.canva.com/pdf-editor/';

        // Alert to instruct the user on the next step
        alert(`Your report has been downloaded as "${filename}".\n\nCanva has deprecated automated URL imports, so we have opened Canva's PDF Editor in a new tab.\n\nPlease switch to that tab and DRAG AND DROP the downloaded PDF file into the Canva window to edit your report.`);

    } catch (err) {
        console.error("Export error:", err);
        if (canvaWindow) canvaWindow.close();
        alert("An error occurred during export.");
    } finally {
        btn.textContent = oldText;
        btn.disabled = false;
    }
}
