import csv
import json

import pytest

from expense_tracker.cli import main
from expense_tracker.errors import (
    ExpenseNotFoundError,
    InvalidExpenseError,
    StorageError,
)
from expense_tracker.models import Expense
from expense_tracker.storage import ExpenseStore


@pytest.fixture
def store(tmp_path):
    return ExpenseStore(tmp_path / "expenses.json")


# ---------- model ----------
def test_expense_normalizes_category():
    assert Expense(1, 5, "  Food ").category == "food"


@pytest.mark.parametrize("amount", [0, -3])
def test_expense_rejects_non_positive_amount(amount):
    with pytest.raises(InvalidExpenseError):
        Expense(1, amount, "food")


def test_expense_rejects_bad_date():
    with pytest.raises(InvalidExpenseError):
        Expense(1, 5, "food", date="31-12-2026")


def test_expense_rejects_empty_category():
    with pytest.raises(InvalidExpenseError):
        Expense(1, 5, "   ")


# ---------- storage ----------
def test_add_persists_to_json(store):
    store.add(12.5, "food", "lunch", "2026-10-01")
    data = json.loads(store.path.read_text())
    assert data == [{
        "id": 1, "amount": 12.5, "category": "food",
        "description": "lunch", "date": "2026-10-01",
    }]


def test_ids_increment_after_delete(store):
    store.add(1, "a")
    store.add(2, "b")
    store.delete(2)
    assert store.add(3, "c").id == 2


def test_delete_missing_raises(store):
    with pytest.raises(ExpenseNotFoundError):
        store.delete(99)


def test_corrupt_json_raises_storage_error(store):
    store.path.write_text("{not json")
    with pytest.raises(StorageError):
        store.load()


def test_list_filters_and_sorts(store):
    store.add(5, "food", date="2026-10-03")
    store.add(7, "travel", date="2026-10-01")
    store.add(3, "food", date="2026-10-02")
    assert [e.date for e in store.list()] == ["2026-10-01", "2026-10-02", "2026-10-03"]
    assert len(store.list("FOOD")) == 2


def test_totals(store):
    store.add(10.10, "food")
    store.add(5.20, "food")
    store.add(20, "travel")
    assert store.total() == 35.30
    assert store.total("food") == 15.30
    assert store.by_category() == {"food": 15.30, "travel": 20.0}


def test_export_csv(store, tmp_path):
    store.add(9.99, "food", "snack", "2026-10-01")
    dest = tmp_path / "out.csv"
    assert store.export_csv(dest) == 1
    with dest.open() as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["category"] == "food"
    assert rows[0]["amount"] == "9.99"


# ---------- CLI ----------
def test_cli_add_and_list(tmp_path, capsys):
    f = str(tmp_path / "e.json")
    assert main(["-f", f, "add", "20", "food", "-d", "pizza"]) == 0
    assert main(["-f", f, "list"]) == 0
    out = capsys.readouterr().out
    assert "pizza" in out and "Total: 20.00" in out


def test_cli_returns_error_code_on_bad_input(tmp_path, capsys):
    f = str(tmp_path / "e.json")
    assert main(["-f", f, "add", "-5", "food"]) == 1
    assert "Amount must be positive" in capsys.readouterr().err


def test_cli_delete_missing(tmp_path, capsys):
    f = str(tmp_path / "e.json")
    assert main(["-f", f, "delete", "3"]) == 1
    assert "No expense with id 3" in capsys.readouterr().err