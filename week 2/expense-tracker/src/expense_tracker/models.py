from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date as _date

from .errors import InvalidExpenseError


@dataclass
class Expense:
    id: int
    amount: float
    category: str
    description: str = ""
    date: str = field(default_factory=lambda: _date.today().isoformat())

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise InvalidExpenseError(f"Amount must be positive, got {self.amount}")
        if not self.category.strip():
            raise InvalidExpenseError("Category cannot be empty")
        try:
            _date.fromisoformat(self.date)
        except ValueError:
            raise InvalidExpenseError(f"Invalid date '{self.date}' (use YYYY-MM-DD)")
        self.category = self.category.strip().lower()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Expense:
        try:
            return cls(**data)
        except TypeError as exc:
            raise InvalidExpenseError(f"Bad expense record: {exc}") from exc

    def __str__(self) -> str:
        return f"#{self.id:<3} {self.date}  {self.category:<12} {self.amount:>9.2f}  {self.description}"