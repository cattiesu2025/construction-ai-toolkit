import logging
import slack_bot.config as config  # must be first
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bot.handler import handle_mention

logging.basicConfig(level=logging.INFO)

app = App(token=config.SLACK_BOT_TOKEN)


@app.event("app_mention")
def on_mention(event, say):
    user_id = event.get("user", "")
    text = event.get("text", "")
    reply = handle_mention(user_id=user_id, text=text)
    say(reply)


def main():
    handler = SocketModeHandler(app, config.SLACK_APP_TOKEN)
    handler.start()


if __name__ == "__main__":
    main()
