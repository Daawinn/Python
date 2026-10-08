# Telegram Daily Expense Bot

1. Open Telegram, talk to **@BotFather**, send `/newbot`, copy the token.
2. `pip install -r requirements.txt`
3. `BOT_TOKEN=<your token> python -m expense_bot.bot`
4. Message your bot: `5.50 coffee`, `/today`, `/week`, `/month`, `/budget 500`, `/undo`, `/export`.

Data is stored in `expenses.db` (SQLite; override with `DB_PATH`).
