"""Application entry point for the Banking Management System."""
from cli.app import BankingCLI
from database import Database
from services.auth_service import AuthService
from services.bank_service import BankService


def main() -> None:
    """Initialize persistent services and launch the interactive CLI."""
    database = Database("banking_system.db")
    database.initialize()
    bank_service = BankService(database)
    auth_service = AuthService(database, bank_service=bank_service)
    try:
        BankingCLI(auth_service).run()
    except (EOFError, KeyboardInterrupt):
        print("\nApplication closed. Thank you for using the Banking Management System.")


if __name__ == "__main__":
    main()
