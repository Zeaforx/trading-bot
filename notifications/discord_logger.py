import requests
from datetime import datetime
from config.settings import settings


class DiscordLogger:
    def _send(self, webhook_url, title, description, color):
        if not webhook_url:
            return
        embed = {
            "embeds": [
                {
                    "title": title,
                    "description": description,
                    "color": color,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ]
        }
        try:
            requests.post(webhook_url, json=embed)
        except Exception as e:
            print(f"Discord Error: {e}")

    def log_stage(self, stage, message, symbol=None, details=None):
        """
        Sends detailed steps. If 'details' dict is provided,
        it formats them as a code block.
        """
        # 1. Prepare the Title
        title_text = f"⚙️ {stage}"
        if symbol:
            title_text += f" [{symbol}]"

        # 2. Prepare the Description
        description_text = message

        # If we have data, add the code block to the description
        if details:
            description_text += "\n```yaml\n"
            for key, value in details.items():
                description_text += f"{key:<12}: {value}\n"
            description_text += "```"

        # 3. Send with all 4 required arguments
        # Args: (URL, Title, Description, Color)
        self._send(
            settings.DISCORD_WEBHOOK_DEBUG, title_text, description_text, 9807270
        )

    def log_trade(self, action, symbol, qty, price):
        msg = f"**{action.upper()}**\nSymbol: {symbol}\nQty: {qty}\nPrice: ${price:.2f}"
        color = 3066993 if action.lower() == "buy" else 15158332
        self._send(settings.DISCORD_WEBHOOK_TRADES, "Trade Executed", msg, color)

    def log_signal(self, symbol, signal, score, reason):
        msg = f"**Signal**\nSymbol: {symbol}\nType: {signal}\nScore: {score}\nReason: {reason}"
        self._send(settings.DISCORD_WEBHOOK_TRADES, "Strategy Signal", msg, 10181046)

    def log_error(self, error):
        self._send(
            settings.DISCORD_WEBHOOK_ALERTS, "⚠️ System Error", str(error), 15105570
        )

    def log_system(self, msg):
        self._send(settings.DISCORD_WEBHOOK_ALERTS, "ℹ️ System Status", msg, 3447003)


discord_logger = DiscordLogger()
