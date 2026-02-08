"""Load testing with Locust for Django Finance.

Run with:
    locust -f tests/performance/locustfile.py --host=http://localhost:8000

Headless mode (CI/CD):
    locust -f tests/performance/locustfile.py --headless -u 100 -r 10 -t 5m --host=http://localhost:8000

Options:
    -u: Number of users to simulate
    -r: Spawn rate (users per second)
    -t: Run time (e.g., 5m, 1h)
"""

import random
import string

from locust import HttpUser, between, task


class AuthenticatedAPIUser(HttpUser):
    """Simulates an authenticated user interacting with the finance API."""

    wait_time = between(1, 3)
    access_token: str = ""
    account_ids: list = []
    contact_ids: list = []

    def on_start(self):
        """Register and login on user start."""
        self._register_and_login()

    def _generate_email(self) -> str:
        """Generate a unique email for testing."""
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"loadtest_{suffix}@example.com"

    def _register_and_login(self):
        """Register a new user and get JWT token."""
        email = self._generate_email()
        password = "TestPassword123!"

        # Register
        response = self.client.post(
            "/api/v1/auth/register/",
            json={
                "email": email,
                "password": password,
                "password_confirm": password,
                "first_name": "Load",
                "last_name": "Test",
            },
            name="/api/v1/auth/register/",
        )

        if response.status_code == 201:
            data = response.json()
            self.access_token = data.get("access", "")
        else:
            # Try login if registration failed (user might exist)
            self._login(email, password)

    def _login(self, email: str, password: str):
        """Login with existing credentials."""
        response = self.client.post(
            "/api/v1/auth/login/",
            json={"email": email, "password": password},
            name="/api/v1/auth/login/",
        )
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access", "")

    @property
    def auth_headers(self) -> dict:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.access_token}"}

    # =========================================================================
    # Dashboard (highest priority - most accessed)
    # =========================================================================

    @task(20)
    def view_dashboard(self):
        """View the dashboard - most common action."""
        self.client.get(
            "/api/v1/dashboard/",
            headers=self.auth_headers,
            name="/api/v1/dashboard/",
        )

    # =========================================================================
    # Finance - Read Operations
    # =========================================================================

    @task(10)
    def list_accounts(self):
        """List all accounts."""
        response = self.client.get(
            "/api/v1/finance/accounts/",
            headers=self.auth_headers,
            name="/api/v1/finance/accounts/",
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            self.account_ids = [acc["id"] for acc in results]

    @task(5)
    def view_account_detail(self):
        """View a specific account."""
        if self.account_ids:
            account_id = random.choice(self.account_ids)
            self.client.get(
                f"/api/v1/finance/accounts/{account_id}/",
                headers=self.auth_headers,
                name="/api/v1/finance/accounts/[id]/",
            )

    @task(8)
    def list_transactions(self):
        """List transactions."""
        self.client.get(
            "/api/v1/finance/transactions/",
            headers=self.auth_headers,
            name="/api/v1/finance/transactions/",
        )

    @task(5)
    def view_net_worth(self):
        """View net worth report."""
        self.client.get(
            "/api/v1/finance/reports/net-worth/",
            headers=self.auth_headers,
            name="/api/v1/finance/reports/net-worth/",
        )

    @task(3)
    def list_categories(self):
        """List categories."""
        self.client.get(
            "/api/v1/finance/categories/",
            headers=self.auth_headers,
            name="/api/v1/finance/categories/",
        )

    # =========================================================================
    # Social - Read Operations
    # =========================================================================

    @task(5)
    def list_contacts(self):
        """List contacts."""
        response = self.client.get(
            "/api/v1/social/contacts/",
            headers=self.auth_headers,
            name="/api/v1/social/contacts/",
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            self.contact_ids = [c["id"] for c in results]

    @task(3)
    def list_debts(self):
        """List peer debts."""
        self.client.get(
            "/api/v1/social/peer-debts/",
            headers=self.auth_headers,
            name="/api/v1/social/peer-debts/",
        )

    @task(2)
    def view_balances(self):
        """View balance summary."""
        self.client.get(
            "/api/v1/social/balances/",
            headers=self.auth_headers,
            name="/api/v1/social/balances/",
        )

    # =========================================================================
    # Finance - Write Operations (less frequent)
    # =========================================================================

    @task(2)
    def create_account(self):
        """Create a new account."""
        account_types = ["checking", "savings", "credit_card", "cash"]
        self.client.post(
            "/api/v1/finance/accounts/",
            json={
                "name": f"Test Account {random.randint(1, 9999)}",
                "account_type": random.choice(account_types),
                "currency": "USD",
                "initial_balance": str(round(random.uniform(100, 10000), 2)),
            },
            headers=self.auth_headers,
            name="/api/v1/finance/accounts/ [POST]",
        )

    @task(3)
    def create_transaction(self):
        """Create a new transaction."""
        if not self.account_ids:
            return

        account_id = random.choice(self.account_ids)
        transaction_type = random.choice(["income", "expense"])
        amount = str(round(random.uniform(10, 500), 2))

        self.client.post(
            "/api/v1/finance/transactions/",
            json={
                "account": account_id,
                "transaction_type": transaction_type,
                "amount": amount,
                "description": f"Load test {transaction_type}",
                "transaction_date": "2026-02-08",
            },
            headers=self.auth_headers,
            name="/api/v1/finance/transactions/ [POST]",
        )

    # =========================================================================
    # Social - Write Operations (less frequent)
    # =========================================================================

    @task(1)
    def create_contact(self):
        """Create a new contact."""
        suffix = "".join(random.choices(string.ascii_lowercase, k=4))
        self.client.post(
            "/api/v1/social/contacts/",
            json={
                "name": f"Test Contact {suffix}",
                "email": f"contact_{suffix}@example.com",
            },
            headers=self.auth_headers,
            name="/api/v1/social/contacts/ [POST]",
        )


class WebUIUser(HttpUser):
    """Simulates a user browsing the web interface."""

    wait_time = between(2, 5)

    @task(10)
    def view_dashboard_page(self):
        """View the dashboard page."""
        self.client.get("/", name="/ (Dashboard)")

    @task(5)
    def view_login_page(self):
        """View the login page."""
        self.client.get("/accounts/login/", name="/accounts/login/")

    @task(3)
    def view_accounts_page(self):
        """View accounts list page."""
        self.client.get("/accounts/", name="/accounts/")

    @task(3)
    def view_transactions_page(self):
        """View transactions list page."""
        self.client.get("/transactions/", name="/transactions/")

    @task(2)
    def view_contacts_page(self):
        """View contacts page."""
        self.client.get("/contacts/", name="/contacts/")

    @task(1)
    def health_check(self):
        """Check health endpoints."""
        self.client.get("/health/", name="/health/")
        self.client.get("/health/ready/", name="/health/ready/")


class HealthCheckUser(HttpUser):
    """Lightweight user for health check monitoring."""

    wait_time = between(5, 10)

    @task
    def health_check(self):
        """Perform health check."""
        self.client.get("/health/", name="/health/")

    @task
    def readiness_check(self):
        """Perform readiness check."""
        self.client.get("/health/ready/", name="/health/ready/")
