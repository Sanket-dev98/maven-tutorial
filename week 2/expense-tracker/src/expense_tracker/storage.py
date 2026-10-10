from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from .errors import ExpenseNotFoundError, StorageError
from .models import Expense


class ExpenseStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    # ---------- file I/O ----------
    def load(self) -> list[Expense]:
        if not self.path.exists():
            return []
        try:
            with self.path.open(encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError as exc:
            raise StorageError(f"{self.path} is not valid JSON: {exc}") from exc
        except OSError as exc:
            raise StorageError(f"Cannot read {self.path}: {exc}") from exc
        return [Expense.from_dict(item) for item in raw]

    def save(self, expenses: list[Expense]) -> None:
        tmp = self.path.with_suffix(".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tmp.open("w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in expenses], f, indent=2)
            tmp.replace(self.path)
        except OSError as exc:
            raise StorageError(f"Cannot write {self.path}: {exc}") from exc

    # ---------- operations ----------
    def add(self, amount: float, category: str, description: str = "",
            date: str | None = None) -> Expense:
        expenses = self.load()
        next_id = max((e.id for e in expenses), default=0) + 1
        kwargs = {"date": date} if date else {}
        expense = Expense(next_id, amount, category, description, **kwargs)
        expenses.append(expense)
        self.save(expenses)
        return expense

    def delete(self, expense_id: int) -> Expense:
        expenses = self.load()
        match = next((e for e in expenses if e.id == expense_id), None)
        if match is None:
            raise ExpenseNotFoundError(f"No expense with id {expense_id}")
        self.save([e for e in expenses if e.id != expense_id])
        return match

    def list(self, category: str | None = None) -> list[Expense]:
        expenses = self.load()
        if category:
            expenses = [e for e in expenses if e.category == category.lower()]
        return sorted(expenses, key=lambda e: (e.date, e.id))

    def total(self, category: str | None = None) -> float:
        return round(sum(e.amount for e in self.list(category)), 2)

    def by_category(self) -> dict[str, float]:
        totals: dict[str, float] = defaultdict(float)
        for e in self.load():
            totals[e.category] += e.amount
        return {cat: round(amt, 2) for cat, amt in sorted(totals.items())}

    def export_csv(self, dest: str | Path) -> int:
        expenses = self.list()
        try:
            with Path(dest).open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["id", "date", "category", "amount", "description"]
                )
                writer.writeheader()
                writer.writerows(e.to_dict() for e in expenses)
        except OSError as exc:
            raise StorageError(f"Cannot write {dest}: {exc}") from exc
        return len(expenses)