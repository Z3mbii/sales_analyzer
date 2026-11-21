"""Benchmark porównujący wykonanie sekwencyjne, wielowątkowe oraz wieloprocesowe"""

import sys
import sysconfig
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import cpu_count
from pathlib import Path

import matplotlib.pyplot as plt

from src.models import SaleRecord
from src.processors import analyze_batch, merge_batch_results

def _run_sequential(batches: list[list[SaleRecord]]) -> float:
    start = time.perf_counter()
    results = [analyze_batch(batch) for batch in batches]
    merge_batch_results(results)
    return time.perf_counter() - start

def _run_threads(batches: list[list[SaleRecord]], workers: int) -> float:
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(analyze_batch, batches))
    merge_batch_results(results)
    return time.perf_counter() - start

def _run_processes(batches: list[list[SaleRecord]], workers: int) -> float:
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(analyze_batch, batches))
    merge_batch_results(results)
    return time.perf_counter() - start

def _save_chart(results: dict[str, float], output_path: Path) -> None:
    """Generuje i zapisuje wykres słupkowy"""
    labels = list(results.keys())
    times = list(results.values())
    colors = ["#6c757d", "#dc3545", "#198754"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, times, color=colors, width=0.5)
    ax.set_title("Wpływ GIL na obliczenia CPU-bound (analiza sprzedaży)")
    ax.set_ylabel("Czas wykonania")
    ax.grid(axis="y", linestyle="--", alpha=0.6)

    for bar, val in zip(bars, times):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + (max(times) * 0.02),
            f"{val:.3f} s",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

def run_gil_benchmark(batches: list[list[SaleRecord]], output_dir: str | Path = "data") -> dict[str, float]:
    """Przeprowadza bechmark i wyświetla wyniki"""
    workers = cpu_count()
    gil_disabled = bool(sysconfig.get_config_vars("Py_GIL_DISABLED"))
    is_gil_enabled_fn = getattr(sys, "_is_gil_enabled", None)
    gil_active = bool(is_gil_enabled_fn()) if callable(is_gil_enabled_fn) else not gil_disabled

    print("\n=== INFORMACJE O ŚRODOWISKU ===")
    print(f"Python: {sys.version.split()[0]} | Rdzenie CPU: {workers} | GIL aktywny: {gil_active}")
    print(f"Liczba paczek do przetworzenia: {len(batches)} (rekordów: {sum(len(b) for b in batches)})")

    seq_time = _run_sequential(batches)
    thr_time = _run_threads(batches, workers)
    proc_time = _run_processes(batches, workers)

    results = {
        "Sekwencyjne (1 wątek)": seq_time,
        f"Wątki ({workers} workers)": thr_time,
        f"Procesy ({workers} workers)": proc_time,
    }

    print("\n=== WYNIKI BENCHMARKU GIL ===")
    print(f"{'Tryb wykonania':<28} | {'Czas [s]':<10} | {'Przyspieszenie':<15}")
    print("-" * 60)
    for mode, elapsed in results.items():
        speedup = seq_time / elapsed if elapsed > 0 else 0.0
        print(f"{mode:<28} | {elapsed:<10.4} | {speedup:<14.2f}x")

    chart_path = Path(output_dir) / "gil_benchmark.png"
    chart_path.parent.mkdir(parents=True, exist_ok=True)
    _save_chart(results, chart_path)
    print(f"\nWykres zapisano w: {chart_path.resolve()}")

    return results
