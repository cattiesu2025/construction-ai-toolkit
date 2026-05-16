import json
import requests
from delay_agent import config

_SEVERITY_EMOJI = {
    "LOW": ":white_circle:",
    "MEDIUM": ":large_yellow_circle:",
    "HIGH": ":large_orange_circle:",
    "CRITICAL": ":red_circle:",
}


def send_slack_alert(message: str, severity: str = "MEDIUM") -> dict:
    """Send a delay alert to the configured Slack webhook.

    Args:
        message: The alert message content
        severity: One of LOW / MEDIUM / HIGH / CRITICAL
    """
    if not config.SLACK_WEBHOOK_URL or config.SLACK_WEBHOOK_URL.startswith("https://hooks.slack.com/services/..."):
        print(f"[SLACK MOCK] {severity}: {message[:120]}...")
        return {"ok": True, "mock": True}

    emoji = _SEVERITY_EMOJI.get(severity.upper(), ":white_circle:")
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Construction Delay Alert — {severity}",
                },
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message},
            },
        ]
    }

    try:
        resp = requests.post(
            config.SLACK_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        return {"ok": True, "status_code": resp.status_code}
    except requests.RequestException as exc:
        return {"ok": False, "error": str(exc)}
