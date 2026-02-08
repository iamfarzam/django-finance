"""URL configuration for web UI."""

from django.urls import path

from modules.web import views

app_name = "web"

urlpatterns = [
    # Dashboard
    path("", views.DashboardView.as_view(), name="dashboard"),
    # React Dashboard (Next.js static export)
    path("react/dashboard/", views.ReactDashboardView.as_view(), name="react_dashboard"),

    # Accounts
    path("accounts/", views.AccountListView.as_view(), name="accounts_list"),
    path("accounts/new/", views.AccountCreateView.as_view(), name="account_create"),
    path("accounts/<uuid:pk>/", views.AccountDetailView.as_view(), name="account_detail"),
    path("accounts/<uuid:pk>/edit/", views.AccountUpdateView.as_view(), name="account_update"),

    # Transactions
    path("transactions/", views.TransactionListView.as_view(), name="transactions_list"),
    path("transactions/new/", views.TransactionCreateView.as_view(), name="transaction_create"),
    path("transactions/<uuid:pk>/", views.TransactionDetailView.as_view(), name="transaction_detail"),

    # Net Worth
    path("net-worth/", views.NetWorthView.as_view(), name="net_worth"),

    # Contacts
    path("contacts/", views.ContactListView.as_view(), name="contacts_list"),
    path("contacts/new/", views.ContactCreateView.as_view(), name="contact_create"),
    path("contacts/<uuid:pk>/", views.ContactDetailView.as_view(), name="contact_detail"),
    path("contacts/<uuid:pk>/edit/", views.ContactUpdateView.as_view(), name="contact_update"),

    # Peer Debts
    path("debts/", views.DebtListView.as_view(), name="debts_list"),
    path("debts/new/", views.DebtCreateView.as_view(), name="debt_create"),
    path("debts/<uuid:pk>/", views.DebtDetailView.as_view(), name="debt_detail"),

    # Expense Groups
    path("groups/", views.GroupListView.as_view(), name="groups_list"),
    path("groups/new/", views.GroupCreateView.as_view(), name="group_create"),
    path("groups/<uuid:pk>/", views.GroupDetailView.as_view(), name="group_detail"),

    # Settlements
    path("settlements/", views.SettlementListView.as_view(), name="settlements_list"),
    path("settlements/new/", views.SettlementCreateView.as_view(), name="settlement_create"),

    # Balances
    path("balances/", views.BalancesSummaryView.as_view(), name="balances_summary"),

    # Profile & Settings
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
]
