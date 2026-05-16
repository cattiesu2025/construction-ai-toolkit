from typing import Any
from core_tools import data_layer


def get_history_delays(task_type: str, city: str = "Sydney") -> dict[str, Any]:
    """Return historical delay statistics for a given task type and city.

    Args:
        task_type: Construction task type e.g. 'excavation', 'concrete', 'piling'
        city: Australian city name
    """
    df = data_layer.historical_delays()

    matches = df[(df["task_type"] == task_type) & (df["city"] == city)]
    if matches.empty:
        matches = df[df["task_type"] == task_type]

    if matches.empty:
        return {
            "task_type": task_type,
            "city": city,
            "found": False,
            "message": f"No historical data for task type '{task_type}'",
        }

    row = matches.iloc[0]
    return {
        "task_type": task_type,
        "city": city,
        "found": True,
        "avg_delay_days": int(row["avg_delay_days"]),
        "delay_frequency_pct": float(row["delay_frequency_pct"]),
        "p90_delay_days": int(row["p90_delay_days"]),
        "common_causes": row["common_causes"].split(";"),
        "sample_size": int(row["sample_size"]),
        "interpretation": (
            f"{row['delay_frequency_pct']:.0f}% of {task_type} tasks in {city} "
            f"experience delays averaging {row['avg_delay_days']} days "
            f"(90th percentile: {row['p90_delay_days']} days)."
        ),
    }
