
import os

ledger_content = """{% extends 'tracker/base.html' %}

{% block title %}Ledger - Sourcing Tracker{% endblock %}

{% block content %}
<div class="page-header d-flex justify-content-between align-items-center">
    <div>
        <h1><i class="bi bi-journal-text me-2"></i>Ledger</h1>
        <p class="mb-0">Track all money movements and transactions</p>
    </div>
    <button class="btn btn-gradient" data-bs-toggle="modal" data-bs-target="#addTransactionModal">
        <i class="bi bi-plus-circle me-1"></i>Add Transaction
    </button>
</div>

<!-- Filter -->
<div class="card mb-4">
    <div class="card-body py-3">
        <form method="get" class="row g-3 align-items-end">
            <div class="col-md-4">
                <label class="form-label">Filter by Partner</label>
                <select name="partner" class="form-select" onchange="this.form.submit()">
                    <option value="">All Partners</option>
                    {% for partner in partners %}
                        <option value="{{ partner.id }}" {% if selected_partner == partner.id|stringformat:'s' %}selected{% endif %}>
                            {{ partner.name }}
                        </option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-2">
                {% if selected_partner %}
                    <a href="{% url 'ledger' %}" class="btn btn-outline-light">Clear Filter</a>
                {% endif %}
            </div>
        </form>
    </div>
</div>

<!-- Transactions Table -->
<div class="card">
    <div class="card-body p-0">
        {% if transactions %}
        <div class="table-responsive">
            <table class="table table-hover mb-0">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Partner</th>
                        <th>Type</th>
                        <th class="text-end">Amount</th>
                        <th>Evidence</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
                    {% for txn in transactions %}
                    <tr class="animate-fade-in">
                        <td>{{ txn.date|date:"d M Y" }}</td>
                        <td>
                            <strong>{{ txn.partner.name }}</strong>
                            <br><small class="text-muted">{{ txn.partner.gst_number }}</small>
                        </td>
                        <td>
                            {% if txn.transaction_type == 'ADVANCE_RECEIVED' %}
                                <span class="badge bg-success bg-opacity-25 text-success">
                                    <i class="bi bi-arrow-down-circle me-1"></i>Advance Received
                                </span>
                            {% else %}
                                <span class="badge bg-danger bg-opacity-25 text-danger">
                                    <i class="bi bi-arrow-up-circle me-1"></i>Refund Given
                                </span>
                            {% endif %}
                        </td>
                        <td class="text-end">
                            <strong class="{% if txn.transaction_type == 'ADVANCE_RECEIVED' %}text-success{% else %}text-danger{% endif %}">
                                {% if txn.transaction_type == 'ADVANCE_RECEIVED' %}+{% else %}-{% endif %}₹{{ txn.amount|floatformat:2 }}
                            </strong>
                        </td>
                        <td>
                            {% if txn.evidence_file %}
                                <a href="{{ txn.evidence_file.url }}" target="_blank" class="btn btn-sm btn-outline-info">
                                    <i class="bi bi-file-earmark-image"></i> View
                                </a>
                            {% else %}
                                <span class="text-muted">—</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if txn.notes %}
                                <small>{{ txn.notes|truncatewords:10 }}</small>
                            {% else %}
                                <span class="text-muted">—</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
        <div class="empty-state">
            <i class="bi bi-journal"></i>
            <h5>No Transactions Yet</h5>
            <p>Record your first transaction to start tracking</p>
            <button class="btn btn-gradient" data-bs-toggle="modal" data-bs-target="#addTransactionModal">
                <i class="bi bi-plus-circle me-1"></i>Add Transaction
            </button>
        </div>
        {% endif %}
    </div>
</div>

<!-- Add Transaction Modal -->
<div class="modal fade" id="addTransactionModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content">
            <div class="modal-header border-0">
                <h5 class="modal-title"><i class="bi bi-plus-circle me-2"></i>Record Transaction</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="post" enctype="multipart/form-data">
                {% csrf_token %}
                <div class="modal-body">
                    <div class="row g-3">
                        <div class="col-md-6">
                            <label class="form-label">Partner</label>
                            {{ form.partner }}
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Transaction Type</label>
                            {{ form.transaction_type }}
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Amount (₹)</label>
                            {{ form.amount }}
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Date</label>
                            {{ form.date }}
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Evidence (Bank Screenshot)</label>
                            {{ form.evidence_file }}
                        </div>
                        <div class="col-12">
                            <label class="form-label">Notes</label>
                            {{ form.notes }}
                        </div>
                    </div>
                </div>
                <div class="modal-footer border-0">
                    <button type="button" class="btn btn-outline-light" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-gradient">
                        <i class="bi bi-check-circle me-1"></i>Record Transaction
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""

procurement_content = """{% extends 'tracker/base.html' %}

{% block title %}Procurement - Sourcing Tracker{% endblock %}

{% block content %}
<div class="page-header d-flex justify-content-between align-items-center">
    <div>
        <h1><i class="bi bi-cart3 me-2"></i>Procurement</h1>
        <p class="mb-0">Manage active sourcing and booking deals</p>
    </div>
    <button class="btn btn-gradient" data-bs-toggle="modal" data-bs-target="#addDealModal">
        <i class="bi bi-plus-circle me-1"></i>New Deal
    </button>
</div>

<!-- Active Deals Table -->
<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0"><i class="bi bi-box me-2"></i>Active Deals</h5>
        <span class="badge bg-primary">{{ deals|length }} deals</span>
    </div>
    <div class="card-body p-0">
        {% if deals %}
        <div class="table-responsive">
            <table class="table table-hover mb-0">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Partner</th>
                        <th>Qty</th>
                        <th>Estimated</th>
                        <th>Actual</th>
                        <th>Status</th>
                        <th>Invoice</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for deal in deals %}
                    <tr class="animate-fade-in">
                        <td>
                            <strong>{{ deal.item_name }}</strong>
                            {% if deal.is_over_budget %}
                                <span class="warning-badge ms-2">
                                    <i class="bi bi-exclamation-triangle"></i> Over Budget
                                </span>
                            {% endif %}
                            {% if deal.client_name %}
                                <br><small class="text-muted">For: {{ deal.client_name }}</small>
                            {% endif %}
                        </td>
                        <td>{{ deal.partner.name }}</td>
                        <td>{{ deal.quantity }}</td>
                        <td>
                            {% if deal.estimated_cost %}
                                ₹{{ deal.estimated_cost|floatformat:2 }}
                            {% else %}
                                <span class="text-muted">—</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if deal.actual_cost %}
                                <strong class="{% if deal.is_over_budget %}text-danger{% else %}text-success{% endif %}">
                                    ₹{{ deal.actual_cost|floatformat:2 }}
                                </strong>
                            {% else %}
                                <span class="text-muted">Pending</span>
                            {% endif %}
                        </td>
                        <td>
                            <span class="badge-status badge-{% if deal.status == 'SOURCING' %}sourcing{% else %}booked{% endif %}">
                                {{ deal.get_status_display }}
                            </span>
                        </td>
                        <td>
                            {% if deal.vendor_invoice %}
                                <a href="{{ deal.vendor_invoice.url }}" target="_blank" class="btn btn-sm btn-outline-success">
                                    <i class="bi bi-file-earmark-check"></i>
                                </a>
                            {% else %}
                                <span class="text-warning"><i class="bi bi-exclamation-circle"></i> Required</span>
                            {% endif %}
                        </td>
                        <td>
                            <button class="btn btn-sm btn-outline-light" data-bs-toggle="modal" data-bs-target="#updateDealModal{{ deal.id }}">
                                <i class="bi bi-pencil"></i>
                            </button>
                            {% if deal.status == 'BOOKED' and deal.vendor_invoice %}
                                <form method="post" action="{% url 'move_to_warehouse' deal.id %}" class="d-inline">
                                    {% csrf_token %}
                                    <button type="submit" class="btn btn-sm btn-success-gradient btn-gradient" title="Move to Warehouse">
                                        <i class="bi bi-box-arrow-in-right"></i>
                                    </button>
                                </form>
                            {% endif %}
                        </td>
                    </tr>

                    <!-- Update Deal Modal -->
                    <div class="modal fade" id="updateDealModal{{ deal.id }}" tabindex="-1">
                        <div class="modal-dialog modal-dialog-centered">
                            <div class="modal-content">
                                <div class="modal-header border-0">
                                    <h5 class="modal-title"><i class="bi bi-pencil me-2"></i>Update Deal</h5>
                                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                                </div>
                                <form method="post" action="{% url 'update_deal' deal.id %}" enctype="multipart/form-data">
                                    {% csrf_token %}
                                    <div class="modal-body">
                                        <div class="mb-3">
                                            <label class="form-label">Item</label>
                                            <input type="text" class="form-control" value="{{ deal.item_name }}" disabled>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Actual Cost (₹)</label>
                                            <input type="number" step="0.01" name="actual_cost" class="form-control" value="{{ deal.actual_cost|default:'' }}" placeholder="Enter actual cost">
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Vendor Invoice {% if not deal.vendor_invoice %}<span class="text-warning">(Required)</span>{% endif %}</label>
                                            {% if deal.vendor_invoice %}
                                                <div class="mb-2">
                                                    <a href="{{ deal.vendor_invoice.url }}" target="_blank" class="btn btn-sm btn-outline-success">
                                                        <i class="bi bi-file-earmark"></i> Current Invoice
                                                    </a>
                                                </div>
                                            {% endif %}
                                            <input type="file" name="vendor_invoice" class="form-control">
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Status</label>
                                            <select name="status" class="form-select">
                                                <option value="SOURCING" {% if deal.status == 'SOURCING' %}selected{% endif %}>Sourcing</option>
                                                <option value="BOOKED" {% if deal.status == 'BOOKED' %}selected{% endif %}>Booked</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="modal-footer border-0">
                                        <button type="button" class="btn btn-outline-light" data-bs-dismiss="modal">Cancel</button>
                                        <button type="submit" class="btn btn-gradient">
                                            <i class="bi bi-check-circle me-1"></i>Update Deal
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
        <div class="empty-state">
            <i class="bi bi-cart"></i>
            <h5>No Active Procurement</h5>
            <p>All deals have moved to logistics or been completed</p>
            <button class="btn btn-gradient" data-bs-toggle="modal" data-bs-target="#addDealModal">
                <i class="bi bi-plus-circle me-1"></i>Create New Deal
            </button>
        </div>
        {% endif %}
    </div>
</div>

<!-- Add Deal Modal -->
<div class="modal fade" id="addDealModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content">
            <div class="modal-header border-0">
                <h5 class="modal-title"><i class="bi bi-plus-circle me-2"></i>Create New Deal</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="post" enctype="multipart/form-data">
                {% csrf_token %}
                <div class="modal-body">
                    <div class="row g-3">
                        <div class="col-md-8">
                            <label class="form-label">Item Name</label>
                            {{ form.item_name }}
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Quantity</label>
                            {{ form.quantity }}
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Partner</label>
                            {{ form.partner }}
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">End Client Name</label>
                            {{ form.client_name }}
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Estimated Cost (₹)</label>
                            {{ form.estimated_cost }}
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Actual Cost (₹)</label>
                            {{ form.actual_cost }}
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Commission %</label>
                            {{ form.commission_percent }}
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Vendor Invoice</label>
                            {{ form.vendor_invoice }}
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Status</label>
                            {{ form.status }}
                        </div>
                    </div>
                </div>
                <div class="modal-footer border-0">
                    <button type="button" class="btn btn-outline-light" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-gradient">
                        <i class="bi bi-check-circle me-1"></i>Create Deal
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
"""

os.makedirs('tracker/templates/tracker', exist_ok=True)

with open('tracker/templates/tracker/ledger.html', 'w', encoding='utf-8') as f:
    f.write(ledger_content)
    print("ledger.html written successfully")

with open('tracker/templates/tracker/procurement.html', 'w', encoding='utf-8') as f:
    f.write(procurement_content)
    print("procurement.html written successfully")
