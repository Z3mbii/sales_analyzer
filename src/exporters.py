"""Moduł eksportu raportów"""

import csv
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from multiprocessing import pool
from pathlib import Path
from typing import Any

from src.decorators import measure_time, retry

_AUDIT_LOCK = threading.Lock()

def _write_audit_entry(audit_file: Path, message: str) -> None:
    """dopisuje informacje o wygenerowanym raporcie"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with _AUDIT_LOCK:
        with audit_file.open(mode="a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{threading.current_thread().name}] [{message}]\n")

@retry(attempts=3, delay=0.1, exceptions=(OSError,))
def _export_json(report:dict[str, Any], output_dir: Path, audit_file: Path) -> Path:
    target = output_dir / "summary_report.json"
    with target.open(mode="w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    _write_audit_entry(audit_file, f"Zapisano raport JSON -> {target.name}")
    return target

@retry(attempts=3, delay=0.1, exceptions=(OSError,))
def _export_regional_csv(report:dict[str, Any], output_dir: Path, audit_file: Path) -> Path:
    target = output_dir / "regional_sales.csv"
    with target.open(mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerows(["Region", "Przychod_PLN"])
        for region, revenue in report["revenue_by_region"].items():
            writer.writerow([region, f"revenue:.2f"])
    _write_audit_entry(audit_file, f"Zapisano raport CSV -> {target.name}")
    return target

@retry(attempts=3, delay=0.1, exceptions=(OSError,))
def _export_text_summary(report: dict[str, Any], errors: list [str], output_dir: Path, audit_file: Path) -> Path:
    target = output_dir / "executive_summary.txt"
    lines = [
        "=== RAPORT PODSUMOWUJĄCY SPRZEDAŻ ===",
        f"Przetworzone poprawne transakcje: {report['processed_records']}",
        f"Odrzucone błędne rekordy: {len(errors)}",
        f"Łączny przychód: {report['total_revenue']:.2f} PLN",
        f"Średnia wartość koszyka: {report['average_order_value']:.2f} PLN",
        f"Wykryte anomalie cenowe: {report['anomalies_count']}",
    ]
    for cat, rev in report["revenue_by_category"].items():
        lines.append(f" * {cat}: {rev:.2f} PLN")

    with target.open(mode="w", encoding="utf-8") as f:
        f.write("\n".join(lines)+ "\n")
    _write_audit_entry(audit_file, f"Zapisano podsumowanie TXT -> {target.name}")
    return target

@measure_time
def export_all_reports(report: dict[str, Any], errors: list[str], output_dir: str | Path) -> list[Path]:
    """Urochamia zapis wszystkich raportów"""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    audit_file = out_path / "export_audit.log"

    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="Exporter") as pool:
        futures = [
        pool.submit(_export_json, report, out_path, audit_file),
        pool.submit(_export_regional_csv, report, out_path, audit_file),
        pool.submit(_export_text_summary, report, errors, out_path, audit_file),
    ]
    return [future.result() for future in futures]