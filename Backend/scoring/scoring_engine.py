from typing import Dict

def score_country(metrics: Dict[str, float], weights: Dict[str, float]) -> float:
    score = 0.0

    for metric_name, metric_value in metrics.items():
        weight = weights.get(metric_name, 0.0)
        score += metric_value * weight

    return round(score * 100, 2)
