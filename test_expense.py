import os, tempfile
from datetime import date
from expense_bot import db
from expense_bot.parsing import parse_expense


def test_parse():
    assert parse_expense("5.50 coffee") == (5.5, "coffee", "")
    assert parse_expense("lunch 12 with team") == (12.0, "lunch", "with team")
    assert parse_expense("$3,5 tea") == (3.5, "tea", "")
    assert parse_expense("hello") is None
    assert parse_expense("-5 food") is None
    assert parse_expense("5 10") is None


def test_db():
    p = os.path.join(tempfile.mkdtemp(), "t.db")
    db.init_db(p)
    db.add_expense(1, 5, "Food", path=p)
    db.add_expense(1, 7, "food", path=p)
    db.add_expense(1, 3, "bus", path=p)
    s, e = db.month_range()
    assert db.total(1, s, e, path=p) == 15
    assert db.totals_by_category(1, s, e, path=p)[0]["category"] == "food"
    assert db.delete_last(1, path=p)["category"] == "bus"
    db.set_budget(1, 100, path=p); db.set_budget(1, 200, path=p)
    assert db.get_budget(1, path=p) == 200
    assert db.total(2, s, e, path=p) == 0
