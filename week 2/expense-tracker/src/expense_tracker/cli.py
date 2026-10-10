from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import ExpenseError
from .storage import ExpenseStore

DEFAULT_FILE = Path.home() / ".expenses.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="expense", description="Track expenses in a JSON file.")
    parser.add_argument("-f", "--file", type=Path, default=DEFAULT_FILE, help="JSON data file")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add an expense")
    add.add_argument("amount", type=float)
    add.add_argument("category")
    add.add_argument("-d", "--description", default="")
    add.add_argument("--date", help="YYYY-MM-DD (default: today)")

    ls = sub.add_parser("list", help="list expenses")
    ls.add_argument("-c", "--category")

    rm = sub.add_parser("delete", help="delete an expense by id")
    rm.add_argument("id", type=int)

    sub.add_parser("summary", help="totals per category")

    exp = sub.add_parser("export", help="export to CSV")
    exp.add_argument("dest", type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = ExpenseStore(args.file)

    try:
        if args.command == "add":
            e = store.add(args.amount, args.category, args.description, args.date)
            print(f"Added: {e}")
        elif args.command == "list":
            expenses = store.list(args.category)
            if not expenses:
                print("No expenses found.")
            for e in expenses:
                print(e)
            if expenses:
                print(f"{'-' * 50}\nTotal: {store.total(args.category):.2f}")
        elif args.command == "delete":
            print(f"Deleted: {store.delete(args.id)}")
        elif args.command == "summary":
            for cat, amt in store.by_category().items():
                print(f"{cat:<15} {amt:>10.2f}")
            print(f"{'TOTAL':<15} {store.total():>10.2f}")
        elif args.command == "export":
            count = store.export_csv(args.dest)
            print(f"Exported {count} expenses to {args.dest}")
    except ExpenseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())