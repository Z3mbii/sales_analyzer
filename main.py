"""Główny punkt wejścia aplikacji System Analizy Danych Sprzedażowych."""

import argparse
import logging
from pathlib import Path

from benchmarks.gil_benchmark import run_gil_benchmark
from src.data_generator import generate_sales_csv
from src.decorators import measure_time
from src.exporters import export_all_reports
from src.pipeline import build_sales_pipeline
from src.processors import process_batches_parallel


def setup_logging(verbose: bool = False) -> None:
    """Konfiguruje globalny system logowania aplikacji."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@measure_time
def load_batches(csv_path: Path, min_amount: float, batch_size: int) -> tuple[list, list[str]]:
    """Wczytuje i waliduje dane przy użyciu potoku generatorów i własnego iteratora."""
    errors: list[str] = []
    pipeline = build_sales_pipeline(
        csv_path=csv_path,
        min_amount=min_amount,
        batch_size=batch_size,
        error_collector=errors,
    )
    batches = list(pipeline)
    return batches, errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="System analizy danych sprzedażowych CSV (Python 3.12+)."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/sales.csv"),
        help="Ścieżka do pliku wejściowego CSV (domyślnie: data/sales.csv).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/reports"),
        help="Katalog docelowy na wygenerowane raporty (domyślnie: data/reports).",
    )
    parser.add_argument(
        "--generate",
        type=int,
        metavar="ROWS",
        help="Wygeneruj nowy plik testowy CSV o podanej liczbie wierszy przed analizą.",
    )
    parser.add_argument(
        "--min-amount",
        type=float,
        default=0.0,
        help="Minimalna kwota transakcji uwzględniana w analizie (domyślnie: 0.0).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=15_000,
        help="Rozmiar pojedynczej paczki dla iteratora (domyślnie: 15000).",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Uruchom benchmark porównawczy GIL (sekwencyjnie vs wątki vs procesy).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Włącz szczegółowe logowanie (DEBUG).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)

    if args.generate:
        logger.info(f"Generowanie {args.generate} wierszy testowych do {args.input}...")
        generate_sales_csv(args.input, num_rows=args.generate)

    if not args.input.exists():
        logger.warning(f"Plik {args.input} nie istnieje. Generuję domyślny zbiór 250 000 wierszy...")
        generate_sales_csv(args.input, num_rows=250_000)

    logger.info("Rozpoczynam strumieniowe wczytywanie i walidację danych...")
    batches, validation_errors = load_batches(
        csv_path=args.input,
        min_amount=args.min_amount,
        batch_size=args.batch_size,
    )
    logger.info(f"Wczytano {len(batches)} paczek poprawnych danych (odrzucono błędnych wierszy: {len(validation_errors)}).")

    if args.benchmark:
        run_gil_benchmark(batches, output_dir=args.output_dir)
    else:
        logger.info("Przetwarzanie równoległe na wielu procesach...")
        report = process_batches_parallel(batches)

        logger.info("Eksport raportów na wielu wątkach...")
        created_files = export_all_reports(report, validation_errors, output_dir=args.output_dir)

        print("\n=== ZAKOŃCZONO POMYŚLNIE ===")
        for file_path in created_files:
            print(f" -> Wygenerowano: {file_path}")


if __name__ == "__main__":
    main()