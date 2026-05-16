import anthropic
import slack_bot.config as config  # must be first: triggers sys.path setup
from slack_bot import roles
from slack_bot.dispatcher import dispatch
from slack_bot.tool_defs import filter_tools

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

_SYSTEM_BASE = (
    "You are a construction project assistant integrated into Slack. "
    "Answer questions about project schedule, defects, and compliance using the available tools. "
    "Be concise — Slack messages should be short. Use bullet points where helpful. "
    "If data shows no issues, say so clearly."
)


def handle_mention(user_id: str, text: str) -> str:
    """Process a Slack @mention and return the reply text."""
    role = roles.get_role(user_id)
    if role is None:
        return "You don't have access to this bot. Contact your admin."

    crew = roles.get_crew(user_id)
    allowed_names = roles.get_allowed_tool_names(role)
    tools = filter_tools(allowed_names)

    system_prompt = _SYSTEM_BASE
    if crew:
        system_prompt += f" This user belongs to {crew}. Only show data relevant to {crew}."

    messages: list[dict] = [{"role": "user", "content": text}]

    for _ in range(10):
        response = _client.messages.create(
            model=config.BOT_MODEL,
            max_tokens=1024,
            system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
            tools=tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return next(
                (b.text for b in response.content if hasattr(b, "text")),
                "Done — no summary produced.",
            )

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                try:
                    result = dispatch(block.name, block.input, crew=crew)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    })
                except Exception as exc:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Error: {exc}",
                        "is_error": True,
                    })
            messages.append({"role": "user", "content": tool_results})

    return "Request timed out after too many tool calls. Please try a more specific question."
