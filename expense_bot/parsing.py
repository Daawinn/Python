"""Parse free-text expense messages like '5.50 coffee with Sam'."""
import re

_AMOUNT = re.compile(r"^\$?(\d+(?:[.,]\d{1,2})?)$")


def parse_expense(text):
    """Return (amount, category, note) or None if text isn't an expense.

    Accepts '<amount> <category> [note...]' or '<category> <amount> [note...]'.
    """
    parts = text.strip().split()
    if len(parts) < 2:
        return None
    m = _AMOUNT.match(parts[0])
    if m:
        category, rest = parts[1], parts[2:]
    else:
        m = _AMOUNT.match(parts[1])
        if not m:
            return None
        category, rest = parts[0], parts[2:]
    amount = float(m.group(1).replace(",", "."))
    if amount <= 0 or _AMOUNT.match(category):
        return None
    return amount, category.lower(), " ".join(rest)
