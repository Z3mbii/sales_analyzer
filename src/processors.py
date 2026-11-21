"""Moduł równoległego przetwarzania danych"""

import math
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
from typing import Any

from src.decorators import measure_time
from src.models import SaleRecord

def analyze_batch(batch: list[SaleRecord]) -> dict[str, Any]:
    """Oblicza statystyki dla paczki rekordów"""
    total_revenue = 0.0
    total_items = 0
    revenue_by_region: dict[str, float] = defaultdict(float)
    revenue_by_category: dict[str, float] = defaultdict(float)
    amounts: list[float] = []

    for rec in batch:
        amount = rec.total_amount
        total_revenue += amount
        total_items += rec.quantity
        revenue_by_region[rec.region] += amount
        revenue_by_category[rec.category] += amount
        amounts.append(amount)

    count = len(amounts)
    mean = total_revenue / count if count else 0.0
    variance = sum((x - mean) ** 2 for x in amounts) / count if count else 0.0
    std_dev = math.sqrt(variance)

    threeshold = mean + 2 * std_dev
    high_value_txs = [rec.to_summart_dict() for rec in batch if rec.total_amount > threeshold]

    return {
        "count": count,
        "total_revenue": total_revenue,
        "total_items": total_items,
        "by_region": dict(revenue_by_region),
        "by_categoty": dict(revenue_by_category),
        "high_value_txs": high_value_txs,
    }

def merge_batch_results(partial_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Scala zwrócone wyniki"""
    final_count = 0
    final_revenue = 0.0
    final_items = 0
    merged_regions: dict[str, float] = defaultdict(float)
    merged_categories: dict[str, float] = defaultdict(float)
    all_anomalies: list[dict[str, Any]] = []

    for part in partial_results:
        final_count += part["count"]
        final_revenue += part["total_revenue"]
        final_items += part["total_items"]
        for reg, val in part["by_region"].items():
            merged_regions[reg] += val
        for cat, val in part["by_categoty"].items():
            merged_categories[cat] += val
        all_anomalies.extend(part["high_value_txs"])

    return {
        "processed_records": final_count,
        "total_revenue": round(final_revenue, 2),
        "total_items": final_items,
        "average_order_value": round(final_revenue / final_items, 2) if final_items else 0.0,
        "revenue_by_region": {k: round (v, 2) for k, v in sorted(merged_regions.items())},
        "revenue_by_category": {k: round(v, 2) for k, v in sorted(merged_categories.items())},
        "anomalies_count": len(all_anomalies),
        "top_anomalies": sorted(all_anomalies, key=lambda x: x["total_amount"], reverse=True)[:10],
    }

@measure_time
def process_batches_parallel(batches: list[list[SaleRecord]], workers: int | None = None) -> dict[str, Any]:
    """Rozdziela paczki danych miedzy procesy robocze"""
    max_workers = workers or cpu_count()
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        partial_results = list(pool.map(analyze_batch, batches))
    return merge_batch_results(partial_results)