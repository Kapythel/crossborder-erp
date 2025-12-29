// Cross-Border ERP - Frontend JavaScript

const API_BASE = '/api';
let currentCompanyId = null;
let currentOCRData = null;

// ==================== Utility Functions ====================

function showToast(message, duration = 3000) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), duration);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// ==================== Modal Functions ====================

function showModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

function showAddCompanyModal() {
    showModal('addCompanyModal');
}

// ==================== API Functions ====================

async function apiCall(endpoint, method = 'GET', body = null) {
    try {
        const options = {
            method,
            headers: {}
        };

        if (body && !(body instanceof FormData)) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        } else if (body) {
            options.body = body;
        }

        const response = await fetch(`${API_BASE}${endpoint}`, options);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API request failed');
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast(`Error: ${error.message}`);
        throw error;
    }
}

// ==================== Company Functions ====================

async function loadCompanies() {
    try {
        const companies = await apiCall('/companies/');
        const select = document.getElementById('companySelect');

        if (!select) return;

        select.innerHTML = '<option value="">Select Company...</option>';
        companies.forEach(company => {
            const option = document.createElement('option');
            option.value = company.id;
            option.textContent = `${company.name} (${company.ein})`;
            select.appendChild(option);
        });

        select.addEventListener('change', (e) => {
            currentCompanyId = e.target.value ? parseInt(e.target.value) : null;
            onCompanyChange();
        });

        // Auto-select first company if available
        if (companies.length > 0) {
            select.value = companies[0].id;
            currentCompanyId = companies[0].id;
            onCompanyChange();
        }
    } catch (error) {
        console.error('Error loading companies:', error);
    }
}

async function handleAddCompany(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    const companyData = {
        name: formData.get('name'),
        ein: formData.get('ein'),
        texas_sales_tax_id: formData.get('texas_sales_tax_id') || null,
        rfc: formData.get('rfc') || null
    };

    try {
        await apiCall('/companies/', 'POST', companyData);
        showToast('Company added successfully!');
        closeModal('addCompanyModal');
        form.reset();
        loadCompanies();
    } catch (error) {
        console.error('Error adding company:', error);
    }
}

function onCompanyChange() {
    // Reload data based on current page
    if (window.location.pathname.includes('expenses')) {
        loadExpenses();
    } else if (window.location.pathname.includes('reconciliation')) {
        loadReconciliation();
    } else {
        loadDashboardData();
    }
}

// ==================== Dashboard Functions ====================

async function loadDashboardData() {
    if (!currentCompanyId) return;

    try {
        // Load invoices
        const invoices = await apiCall(`/invoices/?company_id=${currentCompanyId}`);
        document.getElementById('totalInvoices').textContent = invoices.length;

        // Calculate total tax
        const totalTax = invoices.reduce((sum, inv) => sum + inv.tax_amount, 0);
        document.getElementById('totalTax').textContent = formatCurrency(totalTax);

        // Load expenses
        const expenses = await apiCall(`/expenses/?company_id=${currentCompanyId}`);
        document.getElementById('totalExpenses').textContent = expenses.length;

        // Load customs
        const customs = await apiCall(`/customs/?company_id=${currentCompanyId}`);
        document.getElementById('totalCustoms').textContent = customs.length;

        // Display recent invoices
        displayRecentInvoices(invoices.slice(0, 5));

        // Display recent expenses
        displayRecentExpenses(expenses.slice(0, 5));
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function displayRecentInvoices(invoices) {
    const container = document.getElementById('recentInvoices');
    if (!container) return;

    if (invoices.length === 0) {
        container.innerHTML = '<p class="text-gray-400 text-center py-8">No invoices yet</p>';
        return;
    }

    container.innerHTML = invoices.map(invoice => `
        <div class="flex justify-between items-center p-3 rounded-lg bg-white/5 hover:bg-white/10 transition">
            <div>
                <p class="font-semibold">${invoice.invoice_number}</p>
                <p class="text-sm text-gray-400">${formatDate(invoice.date)}</p>
            </div>
            <div class="text-right">
                <p class="font-bold">${formatCurrency(invoice.total, invoice.currency)}</p>
                <p class="text-xs text-gray-400">Tax: ${formatCurrency(invoice.tax_amount, invoice.currency)}</p>
            </div>
        </div>
    `).join('');
}

function displayRecentExpenses(expenses) {
    const container = document.getElementById('recentExpenses');
    if (!container) return;

    if (expenses.length === 0) {
        container.innerHTML = '<p class="text-gray-400 text-center py-8">No expenses yet</p>';
        return;
    }

    container.innerHTML = expenses.map(expense => `
        <div class="flex justify-between items-center p-3 rounded-lg bg-white/5 hover:bg-white/10 transition">
            <div>
                <p class="font-semibold">${expense.description || expense.vendor || 'Expense'}</p>
                <p class="text-sm text-gray-400">${formatDate(expense.date)}</p>
            </div>
            <div class="text-right">
                <p class="font-bold">${formatCurrency(expense.amount, expense.currency)}</p>
                <span class="text-xs badge bg-purple-500/20 text-purple-400">${expense.status}</span>
            </div>
        </div>
    `).join('');
}

// ==================== OCR & Expense Functions ====================

async function processReceipt(file) {
    if (!currentCompanyId) {
        showToast('Please select a company first');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('company_id', currentCompanyId);

    // Show loading
    document.getElementById('uploadZone').classList.add('hidden');
    document.getElementById('loadingSpinner').classList.remove('hidden');
    document.getElementById('ocrResults').classList.add('hidden');

    try {
        const result = await apiCall('/expenses/upload', 'POST', formData);
        currentOCRData = result;

        // Hide loading, show results
        document.getElementById('loadingSpinner').classList.add('hidden');
        document.getElementById('ocrResults').classList.remove('hidden');

        // Populate form with extracted data
        populateExpenseForm(result);

        showToast('Receipt processed successfully!');
    } catch (error) {
        console.error('Error processing receipt:', error);
        document.getElementById('loadingSpinner').classList.add('hidden');
        document.getElementById('uploadZone').classList.remove('hidden');
    }
}

function populateExpenseForm(ocrResult) {
    const fields = ocrResult.extracted_fields;

    document.getElementById('vendor').value = fields.vendor || '';
    document.getElementById('date').value = fields.date ? new Date(fields.date).toISOString().split('T')[0] : new Date().toISOString().split('T')[0];
    document.getElementById('currency').value = ocrResult.detected_currency;
    document.getElementById('total').value = fields.total || '';
    document.getElementById('tax').value = fields.tax || '';
    document.getElementById('tip').value = fields.tip || '';

    // Set confidence badge
    const badge = document.getElementById('confidenceBadge');
    const confidence = ocrResult.confidence;

    badge.className = 'badge ';
    if (confidence === 'high') {
        badge.className += 'bg-green-500/20 text-green-400';
        badge.textContent = '✓ High Confidence';
    } else if (confidence === 'medium') {
        badge.className += 'bg-yellow-500/20 text-yellow-400';
        badge.textContent = '~ Medium Confidence';
    } else {
        badge.className += 'bg-red-500/20 text-red-400';
        badge.textContent = '⚠ Low Confidence';
    }

    // Handle form submission
    const form = document.getElementById('expenseForm');
    form.onsubmit = handleExpenseSubmit;
}

async function handleExpenseSubmit(event) {
    event.preventDefault();

    if (!currentCompanyId) {
        showToast('Please select a company');
        return;
    }

    const total = parseFloat(document.getElementById('total').value) || 0;
    const tax = parseFloat(document.getElementById('tax').value) || 0;
    const tip = parseFloat(document.getElementById('tip').value) || 0;

    const expenseData = {
        company_id: currentCompanyId,
        description: document.getElementById('description').value || document.getElementById('vendor').value,
        vendor: document.getElementById('vendor').value,
        date: document.getElementById('date').value,
        currency: document.getElementById('currency').value,
        amount: total,
        tax_amount: tax,
        tip_amount: tip,
        category: document.getElementById('category').value,
        ocr_data: currentOCRData
    };

    try {
        await apiCall('/expenses/', 'POST', expenseData);
        showToast('Expense saved successfully!');
        cancelExpense();
        loadExpenses();
    } catch (error) {
        console.error('Error saving expense:', error);
    }
}

function cancelExpense() {
    document.getElementById('ocrResults').classList.add('hidden');
    document.getElementById('uploadZone').classList.remove('hidden');
    document.getElementById('expenseForm').reset();
    currentOCRData = null;
}

async function loadExpenses() {
    if (!currentCompanyId) return;

    try {
        const expenses = await apiCall(`/expenses/?company_id=${currentCompanyId}&limit=50`);
        const container = document.getElementById('expensesList');

        if (!container) return;

        if (expenses.length === 0) {
            container.innerHTML = '<p class="text-gray-400 text-center py-8">No expenses yet</p>';
            return;
        }

        container.innerHTML = `
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead>
                        <tr class="border-b border-white/10">
                            <th class="text-left py-3 px-4">Date</th>
                            <th class="text-left py-3 px-4">Vendor</th>
                            <th class="text-left py-3 px-4">Description</th>
                            <th class="text-right py-3 px-4">Amount</th>
                            <th class="text-center py-3 px-4">Category</th>
                            <th class="text-center py-3 px-4">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${expenses.map(expense => `
                            <tr class="border-b border-white/5 hover:bg-white/5 transition">
                                <td class="py-3 px-4">${formatDate(expense.date)}</td>
                                <td class="py-3 px-4">${expense.vendor || '-'}</td>
                                <td class="py-3 px-4">${expense.description}</td>
                                <td class="py-3 px-4 text-right font-semibold">${formatCurrency(expense.amount, expense.currency)}</td>
                                <td class="py-3 px-4 text-center">
                                    <span class="badge bg-purple-500/20 text-purple-400">${expense.category || 'Other'}</span>
                                </td>
                                <td class="py-3 px-4 text-center">
                                    <span class="badge bg-blue-500/20 text-blue-400">${expense.status}</span>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (error) {
        console.error('Error loading expenses:', error);
    }
}

// ==================== Reconciliation Functions ====================

async function loadReconciliation() {
    if (!currentCompanyId) {
        const container = document.getElementById('reconciliationList');
        if (container) {
            container.innerHTML = '<p class="text-gray-400 text-center py-8">Select a company to view reconciliation</p>';
        }
        return;
    }

    try {
        const items = await apiCall(`/reconciliation/?company_id=${currentCompanyId}`);
        allReconciliationItems = items;
        renderReconciliation(items);
    } catch (error) {
        console.error('Error loading reconciliation:', error);
    }
}
