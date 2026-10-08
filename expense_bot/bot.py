"""Telegram daily-expense tracker bot.

Run:  BOT_TOKEN=<token from @BotFather> python -m expense_bot.bot
"""
import csv
import io
import logging
import os
from datetime import date, timedelta

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from . import db
from .parsing import parse_expense

logging.basicConfig(level=logging.INFO)

HELP = (
    "💰 *Daily Expense Tracker*\n\n"
    "Just send a message like `5.50 coffee` or `lunch 12 with team`.\n\n"
    "/today – today's expenses\n"
    "/week – last 7 days by category\n"
    "/month – this month by category\n"
    "/undo – delete your last entry\n"
    "/budget 500 – set monthly budget\n"
    "/export – download this month as CSV\n"
    "/help – show this message"
)


def _money(x):
    return f"{x:,.2f}"


def _category_report(title, rows, grand):
    if not rows:
        return f"{title}\nNo expenses yet."
    lines = [title] + [f"• {r['category']}: {_money(r['total'])}" for r in rows]
    lines.append(f"\n*Total: {_money(grand)}*")
    return "\n".join(lines)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP, parse_mode="Markdown")


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    parsed = parse_expense(update.message.text)
    if not parsed:
        await update.message.reply_text("Couldn't read that. Try `5.50 coffee`.", parse_mode="Markdown")
        return
    amount, category, note = parsed
    uid = update.effective_user.id
    db.add_expense(uid, amount, category, note)
    reply = f"✅ Added {_money(amount)} to *{category}*"
    budget = db.get_budget(uid)
    if budget:
        start_, end_ = db.month_range()
        spent = db.total(uid, start_, end_)
        reply += f"\nMonth: {_money(spent)} / {_money(budget)}"
        if spent > budget:
            reply += "\n⚠️ You are over budget!"
        elif spent >= 0.8 * budget:
            reply += "\n⚠️ You've used over 80% of your budget."
    await update.message.reply_text(reply, parse_mode="Markdown")


async def today(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid, d = update.effective_user.id, date.today()
    rows = db.list_expenses(uid, d, d)
    if not rows:
        await update.message.reply_text("No expenses today.")
        return
    lines = [f"• {_money(r['amount'])} {r['category']} {r['note']}".rstrip() for r in rows]
    lines.append(f"\n*Total: {_money(sum(r['amount'] for r in rows))}*")
    await update.message.reply_text("📅 *Today*\n" + "\n".join(lines), parse_mode="Markdown")


async def week(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid, end_ = update.effective_user.id, date.today()
    start_ = end_ - timedelta(days=6)
    text = _category_report("📊 *Last 7 days*", db.totals_by_category(uid, start_, end_), db.total(uid, start_, end_))
    await update.message.reply_text(text, parse_mode="Markdown")


async def month(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    start_, end_ = db.month_range()
    text = _category_report("🗓 *This month*", db.totals_by_category(uid, start_, end_), db.total(uid, start_, end_))
    budget = db.get_budget(uid)
    if budget:
        text += f"\nBudget: {_money(budget)}"
    await update.message.reply_text(text, parse_mode="Markdown")


async def undo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    row = db.delete_last(update.effective_user.id)
    msg = f"🗑 Removed {_money(row['amount'])} {row['category']}" if row else "Nothing to undo."
    await update.message.reply_text(msg)


async def budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        amount = float(ctx.args[0])
        if amount <= 0:
            raise ValueError
    except (IndexError, ValueError):
        current = db.get_budget(uid)
        hint = f"Current budget: {_money(current)}\n" if current else ""
        await update.message.reply_text(hint + "Usage: /budget 500")
        return
    db.set_budget(uid, amount)
    await update.message.reply_text(f"Monthly budget set to {_money(amount)}")


async def export(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    start_, end_ = db.month_range()
    rows = db.list_expenses(update.effective_user.id, start_, end_)
    if not rows:
        await update.message.reply_text("Nothing to export this month.")
        return
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "amount", "category", "note"])
    w.writerows([r["day"], r["amount"], r["category"], r["note"]] for r in rows)
    data = io.BytesIO(buf.getvalue().encode())
    data.name = f"expenses_{start_:%Y-%m}.csv"
    await update.message.reply_document(data)


def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise SystemExit("Set BOT_TOKEN (get one from @BotFather on Telegram).")
    db.DB_PATH = os.environ.get("DB_PATH", db.DB_PATH)
    db.init_db()
    app = Application.builder().token(token).build()
    for name, fn in [("start", start), ("help", start), ("today", today), ("week", week),
                     ("month", month), ("undo", undo), ("budget", budget), ("export", export)]:
        app.add_handler(CommandHandler(name, fn))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling()


if __name__ == "__main__":
    main()
