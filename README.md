# FaraYouTubeBot

## Railway deployment
1. Upload these files to the root of a GitHub repository.
2. Create a Railway service from the repository.
3. Add the environment variable `BOT_TOKEN` in Railway Variables.
4. Deploy. The `Procfile` starts the bot as a worker.

## Important
- Never commit a real Telegram bot token to GitHub.
- The bot must be an administrator in sponsor channels (or otherwise have permission to check membership) for membership checks to work reliably.
- The `/start` heart reaction is best-effort: if Telegram rejects it, the bot logs the issue and continues sending the normal welcome messages.
