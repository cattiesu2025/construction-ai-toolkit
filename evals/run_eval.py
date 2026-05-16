"""Eval runner for the delay detection agent using LLM-as-judge methodology."""
import json
import sys
import time
from pathlib import Path
import anthropic
from delay_agent.agent import run_delay_agent
from delay_agent.config import ANTHROPIC_API_KEY, AGENT_MODEL

_JUDGE_PROMPT = """You are evaluating an AI construction delay detection agent's output.

Agent output:
<output>
{output}
</output>

Expected severity: {expected_severity}
Should have sent alert: {should_alert}
Key signals that should appear: {key_signals}

Score each dimension 0 or 1:
1. correctness: Did the agent identify the correct severity level (or one level adjacent is ok)?
2. specificity: Does the output cite specific numbers, task IDs, dates, or percentages?
3. actionability: Does the output include concrete recommended actions with timeframes?

Respond ONLY with valid JSON:
{{"correctness": 0_or_1, "specificity": 0_or_1, "actionability": 0_or_1, "reasoning": "brief explanation"}}"""

_SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def llm_judge(agent_output: str, expected_severity: str, should_alert: bool, key_signals: list[str]) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = _JUDGE_PROMPT.format(
        output=agent_output[:3000],
        expected_severity=expected_severity,
        should_alert=should_alert,
        key_signals=", ".join(key_signals),
    )
    response = client.messages.create(
        model=AGENT_MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)
        result = json.loads(match.group()) if match else {"correctness": 0, "specificity": 0, "actionability": 0, "reasoning": "parse error"}
    return result


def run_eval(test_cases_path: str | None = None, max_cases: int | None = None) -> None:
    cases_file = Path(test_cases_path or Path(__file__).parent / "test_cases.json")
    cases = json.loads(cases_file.read_text())

    if max_cases:
        cases = cases[:max_cases]

    results = []
    total = len(cases)

    print(f"Running eval on {total} test cases...\n")

    for i, case in enumerate(cases, 1):
        print(f"[{i}/{total}] {case['id']} — {case['project_id']} ({case['expected_severity']})")

        try:
            agent_result = run_delay_agent(case["project_id"])
            output = agent_result["summary"]
            cost = agent_result["token_usage"]["estimated_cost_usd"]

            scores = llm_judge(output, case["expected_severity"], case["should_alert"], case["key_signals"])

            result = {
                "id": case["id"],
                "project_id": case["project_id"],
                "expected_severity": case["expected_severity"],
                "scores": scores,
                "agent_cost_usd": cost,
                "iterations": agent_result["iterations"],
            }
            results.append(result)
            print(f"  correctness={scores['correctness']} specificity={scores['specificity']} actionability={scores['actionability']} | ${cost:.4f}")

        except Exception as exc:
            print(f"  ERROR: {exc}")
            results.append({"id": case["id"], "error": str(exc)})

        if i < total:
            time.sleep(2)  # rate limiting

    _print_summary(results)
    output_path = Path(__file__).parent / "eval_results.json"
    output_path.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {output_path}")


def _print_summary(results: list[dict]) -> None:
    valid = [r for r in results if "scores" in r]
    if not valid:
        print("No valid results to summarize.")
        return

    n = len(valid)
    correctness = sum(r["scores"]["correctness"] for r in valid) / n
    specificity = sum(r["scores"]["specificity"] for r in valid) / n
    actionability = sum(r["scores"]["actionability"] for r in valid) / n
    total_cost = sum(r.get("agent_cost_usd", 0) for r in valid)
    avg_iterations = sum(r.get("iterations", 0) for r in valid) / n

    print("\n" + "=" * 60)
    print("EVAL SUMMARY")
    print("=" * 60)
    print(f"Cases evaluated: {n}/{len(results)}")
    print(f"Correctness:     {correctness:.0%}")
    print(f"Specificity:     {specificity:.0%}")
    print(f"Actionability:   {actionability:.0%}")
    print(f"Avg iterations:  {avg_iterations:.1f}")
    print(f"Total cost:      ${total_cost:.3f}")
    print(f"Avg cost/case:   ${total_cost/n:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    max_n = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_eval(max_cases=max_n)
