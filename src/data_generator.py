"""Moduł odpowiadający za generowanie danych sprzedażowych."""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

CATEGORIES = ["Elektronika", "Dom i Ogród", "Sport", "Odzież", "Gaming"]
REGIONS = ["Dolnośląskie", "Mazowieckie", "Małopolskie", "Wielkopolskie", "Śląskie", "Pomorskie"]
DOMAINS = ["gmail.com", "wp.pl", "onet.pl", "firma.pl", "sklep.edu.pl"]

def _generate_valid_row(tx_id: int, base_date: datetime) -> list[str]:
    """Tworzy poprawny pojedynczy wiersz danych"""
    date_str = (base_date + timedelta(minutes=random.randint(0, 500_000))).strftime("%Y%m%d %H:%M:%S")
    category = random.choice(CATEGORIES)
    region = random.choice(REGIONS)
    quantity = random.randint(1, 20)
    price = round(random.uniform(15.0, 4500.0), 2)

    # Poprawny NIP
    nip = f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}"
    # Poprawny kod pocztowy
    postal_code = f"{random.randint(10, 99)}-{random.randint(100, 999)}"
    # Poprawny email
    email = f"klient.{tx_id}@{random.choice(DOMAINS)}"

    return [
        f"TX-{tx_id:07d}",
        date_str,
        category,
        region,
        str(quantity),
        f"{price:.2f}",
        nip,
        postal_code,
        email,
    ]

def _corrupt_row(row: list[str]) -> list[str]:
    """Celowo psuje losowe pole w wierszu zeby przetestowac walidacje"""
    corrupted = row.copy()
    defect_type = random.choice(["bad_nip", "bad_postal_code", "bad_email", "negative_price", "zero_qty"])

    if defect_type == "bad_nip":
        corrupted[6] = "123-ABC-99"
    elif defect_type == "bad_postal_code":
        corrupted[7] = "50370"
    elif defect_type == "bad_email":
        corrupted[8] = "niepoprawny_email.pl"
    elif defect_type == "negative_price":
        corrupted[5] = f"-{corrupted[5]}"
    elif defect_type == "zero_qty":
        corrupted[4] = "0"

    return corrupted


def generate_sales_csv(output_path: str | Path, num_rows: int = 200_000, error_rate: float = 0.05) -> Path:
    """Tworzy plik CSV z danymi"""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    headers = ["transaction_id", "timestamp", "category", "region", "quantity", "unit_price", "nip", "postal_code", "email"]
    base_date = datetime(2026, 1, 1, 8, 0, 0)

    with path.open(mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(headers)

        for i in range(1, num_rows + 1):
            row = _generate_valid_row(i, base_date)
            if random.random() < error_rate:
                row = _corrupt_row(row)
            writer.writerow(row)

    return path

if __name__ == "__main__":
    # Test uruchomienia bezposrednio tego pliku
    generated = generate_sales_csv("../data/sales_sample.csv", num_rows=50_000)
    print(f"Wygenerowany plik testowy: {generated.resolve()}")