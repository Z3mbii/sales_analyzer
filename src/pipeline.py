"""Strumień wczytywania i paczkowania danych"""

import csv
import logging
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import TypeVar

from src.models import SaleRecord

logger=logging.getLogger(__name__)
T = TypeVar('T')

def read_raw_rows(csv_path: str | Path) -> Iterator[list[str]]:
    """czyta plik CSV linia po linii"""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku danych: {path}")

    with path.open(mode="r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file, delimiter=";")
        next(reader, None) # Pominiecie naglowka
        for row in reader:
            yield row

def parse_valid_records(rows: Iterable[list[str]], error_collector: list[str] | None = None) -> Iterator[SaleRecord]:
    """przekształca wiersze w obiekty SaleRecord"""
    for line_no, row in enumerate(rows, start=2):
        try:
            yield SaleRecord.from_csv_row(row)
        except (ValueError, KeyError) as err:
            if error_collector is not None:
                error_collector.append(f"Linia {line_no}: {err}")

class BatchIterator(Iterator[list[T]]):
    """Iterator grupujacy dowolny strumien elementów"""

    def __init__(self, source: Iterable[T], batch_size: int = 10_000) -> None:
        if batch_size <= 0:
            raise ValueError("Rozmiar paczki musi być liczbą dodatnią")
        self._iterator = iter(source)
        self._batch_size = batch_size

    def __iter__(self) -> "BatchIterator[T]":
        return self

    def __next__(self) -> list[T]:
        batch: list[T] = []
        for _ in range(self._batch_size):
            try:
                batch.append(next(self._iterator))
            except StopIteration:
                break

        if not batch:
            raise StopIteration

        return batch

def build_sales_pipeline(
    csv_path: str | Path,
    min_amount: float = 0.0,
    batch_size: int = 10_000,
    error_collector: list[str] | None = None,
) -> BatchIterator[SaleRecord]:
    raw_stream = read_raw_rows(csv_path)
    records_stream = parse_valid_records(raw_stream, error_collector=error_collector)

    filtered_stream = (rec for rec in records_stream if rec.total_amount >= min_amount)

    return BatchIterator(filtered_stream, batch_size=batch_size)