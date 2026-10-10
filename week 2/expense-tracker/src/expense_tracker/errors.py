class ExpenseError(Exception):
    """Base class for all expense tracker errors."""


class InvalidExpenseError(ExpenseError):
    """Raised when an expense has bad data."""


class StorageError(ExpenseError):
    """Raised when the JSON file can't be read or written."""


class ExpenseNotFoundError(ExpenseError):
    """Raised when an expense id doesn't exist."""