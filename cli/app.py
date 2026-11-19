"""Interactive terminal application for customer banking workflows."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from getpass import getpass
from typing import Callable

from exceptions import BankingError
from services.auth_service import AuthService
from cli.formatters import account_type_label, format_ngn


class BankingCLI:
    """Run the interactive customer-facing banking menus.

    Input, output, and password functions are injectable so the interface can
    be tested without a real terminal. Financial rules remain in the services
    and account models; this class only collects input and presents results.
    """

    def __init__(
        self,
        auth_service: AuthService,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
        password_fn: Callable[[str], str] = getpass,
    ) -> None:
        self.auth = auth_service
        self.input = input_fn
        self.output = output_fn
        self.password = password_fn
        self._session_token: str | None = None

    def run(self) -> None:
        """Start the welcome menu and keep running until the user exits."""
        self._banner()
        while True:
            self.output("\nWELCOME")
            self.output("1. Create an account")
            self.output("2. Log in")
            self.output("0. Exit")
            choice = self._read("Choose an option: ")
            if choice == "1":
                self._register()
            elif choice == "2":
                self._login()
            elif choice == "0":
                self.output("Thank you for using Banking Management System.")
                return
            else:
                self.output("Invalid option. Choose 1, 2, or 0.")

    def _banner(self) -> None:
        self.output("=" * 58)
        self.output("             BANKING MANAGEMENT SYSTEM")
        self.output("                    NGN | CLI")
        self.output("=" * 58)

    def _read(self, prompt: str) -> str:
        """Read terminal input and normalize surrounding whitespace."""
        return self.input(prompt).strip()

    def _read_password(self, prompt: str) -> str:
        """Read a password without echoing it to the terminal."""
        return self.password(prompt)

    @staticmethod
    def _money(raw: str) -> Decimal:
        """Parse user-entered money directly into Decimal."""
        try:
            amount = Decimal(raw.strip())
        except (InvalidOperation, AttributeError):
            raise ValueError("Enter a valid amount, for example 2500 or 2500.50.")
        if not amount.is_finite():
            raise ValueError("Amount must be a finite number.")
        return amount

    def _register(self) -> None:
        self.output("\n--- CUSTOMER REGISTRATION ---")
        full_name = self._read("Full name: ")
        email = self._read("Email address: ")
        phone = self._read("Phone number (optional): ")
        password = self._read_password("Create password: ")
        confirmation = self._read_password("Confirm password: ")
        if password != confirmation:
            self.output("The passwords do not match. Please try again.")
            return
        try:
            customer = self.auth.register(full_name, email, password, phone)
            self.output(f"Registration successful. Welcome, {customer.full_name}!")
            self.output("You can now log in with your email and password.")
        except BankingError as error:
            self.output(f"Registration failed: {error}")

    def _login(self) -> None:
        self.output("\n--- CUSTOMER LOGIN ---")
        email = self._read("Email address: ")
        password = self._read_password("Password: ")
        try:
            session = self.auth.login(email, password)
            self._session_token = session.token
            self.output(f"\nLogin successful. Welcome back, {session.customer.full_name}!")
            self._customer_menu()
        except BankingError as error:
            self.output(f"Login failed: {error}")

    def _customer_menu(self) -> None:
        """Display customer dashboard until logout or session invalidation."""
        while self._session_token:
            try:
                customer = self.auth.require_customer(self._session_token)
                self.output(f"\n--- CUSTOMER DASHBOARD: {customer.full_name} ---")
                self.output("1. View my accounts")
                self.output("2. Create savings account")
                self.output("3. Create current account")
                self.output("4. Manage an account")
                self.output("5. Change password")
                self.output("0. Log out")
                choice = self._read("Choose an option: ")
                if choice == "1":
                    self._list_accounts()
                elif choice == "2":
                    self._create_savings()
                elif choice == "3":
                    self._create_current()
                elif choice == "4":
                    self._select_account()
                elif choice == "5":
                    self._change_password()
                elif choice == "0":
                    self._logout()
                else:
                    self.output("Invalid option. Choose 1–5 or 0.")
            except BankingError as error:
                self.output(f"Session ended: {error}")
                self._session_token = None

    def _list_accounts(self) -> None:
        accounts = self.auth.get_customer_accounts(self._token())
        if not accounts:
            self.output("You do not have any accounts yet.")
            return
        self.output("\nYOUR ACCOUNTS")
        for index, account in enumerate(accounts, start=1):
            self.output(
                f"{index}. {account_type_label(account)} | "
                f"{account.account_number} | Balance: {format_ngn(account.balance)}"
            )

    def _create_savings(self) -> None:
        self.output("\n--- CREATE SAVINGS ACCOUNT ---")
        opening = self._ask_money("Opening balance (minimum NGN 1,000.00): ")
        if opening is None:
            return
        minimum = self._ask_money("Required minimum balance (default 1000): ", default=Decimal("1000.00"))
        if minimum is None:
            return
        try:
            customer = self.auth.require_customer(self._token())
            account = self.auth.bank_service.create_savings_account(
                customer.customer_id, opening_balance=opening, minimum_balance=minimum
            )
            self.output(f"Savings account created: {account.account_number}")
            self.output(f"Available balance: {format_ngn(account.balance)}")
        except BankingError as error:
            self.output(f"Could not create savings account: {error}")

    def _create_current(self) -> None:
        self.output("\n--- CREATE CURRENT ACCOUNT ---")
        opening = self._ask_money("Opening balance (default 0): ", default=Decimal("0.00"))
        if opening is None:
            return
        overdraft = self._ask_money("Overdraft limit (default 0): ", default=Decimal("0.00"))
        if overdraft is None:
            return
        try:
            customer = self.auth.require_customer(self._token())
            account = self.auth.bank_service.create_current_account(
                customer.customer_id, opening_balance=opening, overdraft_limit=overdraft
            )
            self.output(f"Current account created: {account.account_number}")
            self.output(f"Available balance: {format_ngn(account.balance)}")
        except BankingError as error:
            self.output(f"Could not create current account: {error}")

    def _select_account(self) -> None:
        accounts = self.auth.get_customer_accounts(self._token())
        if not accounts:
            self.output("You need to create an account first.")
            return
        self._list_accounts()
        number = self._read("Enter the account number to manage (or 0 to cancel): ")
        if number == "0":
            return
        try:
            account = self.auth.get_account(self._token(), number)
            self._account_menu(account.account_number)
        except BankingError as error:
            self.output(f"Account selection failed: {error}")

    def _account_menu(self, account_number: str) -> None:
        while self._session_token:
            try:
                account = self.auth.get_account(self._token(), account_number)
                self.output(f"\n--- {account_type_label(account).upper()} {account_number} ---")
                self.output(f"Available balance: {format_ngn(account.balance)}")
                self.output("1. Deposit")
                self.output("2. Withdraw")
                self.output("3. Transfer")
                self.output("4. Transaction history")
                self.output("5. Generate account statement")
                self.output("0. Back to dashboard")
                choice = self._read("Choose an option: ")
                if choice == "1":
                    self._deposit(account_number)
                elif choice == "2":
                    self._withdraw(account_number)
                elif choice == "3":
                    self._transfer(account_number)
                elif choice == "4":
                    self._history(account_number)
                elif choice == "5":
                    self._statement(account_number)
                elif choice == "0":
                    return
                else:
                    self.output("Invalid option. Choose 1–5 or 0.")
            except BankingError as error:
                self.output(f"Account operation failed: {error}")
                return

    def _deposit(self, account_number: str) -> None:
        amount = self._ask_money("Amount to deposit: ")
        if amount is None:
            return
        try:
            transaction = self.auth.deposit(self._token(), account_number, amount)
            self.output(f"Deposit successful: {format_ngn(transaction.amount)}")
            self._show_balance(account_number)
        except BankingError as error:
            self.output(f"Deposit failed: {error}")

    def _withdraw(self, account_number: str) -> None:
        amount = self._ask_money("Amount to withdraw: ")
        if amount is None:
            return
        try:
            transaction = self.auth.withdraw(self._token(), account_number, amount)
            self.output(f"Withdrawal successful: {format_ngn(transaction.amount)}")
            self._show_balance(account_number)
        except BankingError as error:
            self.output(f"Withdrawal failed: {error}")

    def _transfer(self, sender_account_number: str) -> None:
        recipient = self._read("Recipient account number: ")
        amount = self._ask_money("Amount to transfer: ")
        if amount is None:
            return
        try:
            self.auth.transfer(self._token(), sender_account_number, recipient, amount)
            self.output(f"Transfer of {format_ngn(amount)} completed successfully.")
            self._show_balance(sender_account_number)
        except BankingError as error:
            self.output(f"Transfer failed: {error}")

    def _history(self, account_number: str) -> None:
        transactions = self.auth.get_transaction_history(self._token(), account_number)
        if not transactions:
            self.output("No transactions recorded.")
            return
        self.output("\nTRANSACTION HISTORY")
        for item in transactions:
            timestamp = item.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            self.output(
                f"{timestamp} | {item.transaction_type.value:<12} | "
                f"{format_ngn(item.amount)} | Ref: {item.reference}"
            )

    def _statement(self, account_number: str) -> None:
        self.output(self.auth.generate_statement(self._token(), account_number))

    def _show_balance(self, account_number: str) -> None:
        account = self.auth.get_account(self._token(), account_number)
        self.output(f"Current balance: {format_ngn(account.balance)}")

    def _change_password(self) -> None:
        current = self._read_password("Current password: ")
        new = self._read_password("New password: ")
        confirm = self._read_password("Confirm new password: ")
        if new != confirm:
            self.output("The new passwords do not match.")
            return
        try:
            self.auth.change_password(self._token(), current, new)
            self.output("Password changed. Please log in again with your new password.")
            self._session_token = None
        except BankingError as error:
            self.output(f"Password change failed: {error}")

    def _logout(self) -> None:
        token = self._token()
        try:
            self.auth.logout(token)
            self.output("You have been logged out successfully.")
        except BankingError as error:
            self.output(f"Logout notice: {error}")
        finally:
            self._session_token = None

    def _ask_money(self, prompt: str, default: Decimal | None = None) -> Decimal | None:
        raw = self._read(prompt)
        if not raw and default is not None:
            return default
        try:
            return self._money(raw)
        except ValueError as error:
            self.output(str(error))
            return None

    def _token(self) -> str:
        if not self._session_token:
            raise RuntimeError("No active customer session.")
        return self._session_token
