import time
from typing import Any
import anthropic
from delay_agent import config  # must be first: triggers sys.path setup for workspace packages
from delay_agent import notifier
from delay_agent.prompts import SYSTEM_PROMPT
from core_tools import schedule, weather, history

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

TOOLS: list[dict] = [
    {
        "name": "get_schedule_data",
        "description": "Get planned vs actual progress for all tasks in a construction project",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID e.g. PRJ-001"}
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "analyze_progress_gap",
        "description": "Analyse the deviation between planned and actual progress for a specific task, returning delay estimate and downstream impact",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID e.g. T003"}
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "check_weather_impact",
        "description": "Fetch 7-day weather forecast for a location and assess construction risk (rain, wind, extreme temperature)",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_range": {"type": "string", "description": "Date range e.g. '2024-11-01 to 2024-11-07'"},
                "location": {"type": "string", "description": "Australian city e.g. Sydney, Melbourne, Brisbane, Perth"},
            },
            "required": ["date_range", "location"],
        },
    },
    {
        "name": "get_history_delays",
        "description": "Look up historical delay statistics for a task type and city to benchmark current deviation",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_type": {
                    "type": "string",
                    "description": "Task type: excavation, piling, concrete, structural_steel, tunnelling, mep, facade, fitout, demolition, civil, landscaping, roofing, survey, commissioning",
                },
                "city": {"type": "string", "description": "Australian city"},
            },
            "required": ["task_type"],
        },
    },
    {
        "name": "send_slack_alert",
        "description": "Send a delay risk alert to the Slack channel. Only call when severity >= MEDIUM.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Alert message in markdown"},
                "severity": {
                    "type": "string",
                    "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                    "description": "Risk severity level",
                },
            },
            "required": ["message", "severity"],
        },
    },
]

_TOOL_HANDLERS: dict[str, Any] = {
    "get_schedule_data": lambda **kw: schedule.get_schedule_data(**kw),
    "analyze_progress_gap": lambda **kw: schedule.analyze_progress_gap(**kw),
    "check_weather_impact": lambda **kw: weather.check_weather_impact(**kw),
    "get_history_delays": lambda **kw: history.get_history_delays(**kw),
    "send_slack_alert": lambda **kw: notifier.send_slack_alert(**kw),
}


def run_delay_agent(project_id: str, max_iterations: int | None = None) -> dict[str, Any]:
    """Run the delay detection agent for a project.

    Returns a dict with the final assessment and usage metrics.
    """
    max_iter = max_iterations or config.AGENT_MAX_ITERATIONS
    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                f"Analyse project {project_id} for schedule risks. "
                "If you find any tasks with significant delays (severity >= MEDIUM), send a Slack alert. "
                "End with a concise risk summary."
            ),
        }
    ]

    total_input_tokens = 0
    total_output_tokens = 0
    total_cache_read_tokens = 0
    iterations = 0
    start_time = time.time()

    for iteration in range(max_iter):
        iterations += 1

        response = _client.messages.create(
            model=config.AGENT_MODEL,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=TOOLS,
            messages=messages,
        )

        usage = response.usage
        total_input_tokens += usage.input_tokens
        total_output_tokens += usage.output_tokens
        total_cache_read_tokens += getattr(usage, "cache_read_input_tokens", 0)

        if response.stop_reason == "end_turn":
            final_text = next(
                (b.text for b in response.content if hasattr(b, "text")),
                "No summary produced.",
            )
            elapsed = time.time() - start_time
            return {
                "project_id": project_id,
                "summary": final_text,
                "iterations": iterations,
                "elapsed_seconds": round(elapsed, 2),
                "token_usage": {
                    "input": total_input_tokens,
                    "output": total_output_tokens,
                    "cache_read": total_cache_read_tokens,
                    "estimated_cost_usd": _estimate_cost(
                        total_input_tokens, total_output_tokens, total_cache_read_tokens
                    ),
                },
            }

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            seen_calls: dict[str, int] = {}

            for block in response.content:
                if block.type != "tool_use":
                    continue

                call_key = f"{block.name}:{str(block.input)}"
                seen_calls[call_key] = seen_calls.get(call_key, 0) + 1

                if seen_calls[call_key] > 2:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Error: repeated identical tool call — please proceed with available data",
                        "is_error": True,
                    })
                    continue

                try:
                    result = _TOOL_HANDLERS[block.name](**block.input)
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

    raise RuntimeError(f"Agent exceeded {max_iter} iterations for project {project_id}")


def _estimate_cost(input_tokens: int, output_tokens: int, cache_read_tokens: int) -> float:
    # claude-sonnet-4-6 pricing (per million tokens)
    input_cost = (input_tokens / 1_000_000) * 3.0
    output_cost = (output_tokens / 1_000_000) * 15.0
    cache_read_cost = (cache_read_tokens / 1_000_000) * 0.3
    return round(input_cost + output_cost + cache_read_cost, 5)
