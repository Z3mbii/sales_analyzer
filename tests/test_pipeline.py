"""Testy jednostkowe dla modeli, walidatorów, dekoratorów oraz potoku przetwarzania."""

from datetime import datetime
from pathlib import Path

import pytest

from src.data_generator import generate_sales_csv
from src.decorators import retry
from src.models import SaleRecord
from src.pipeline import BatchIterator, build_sales_pipeline
from src.validators import (
    validate_and_extract_email,
    validate_and_extract_nip,
    validate_and_extract_postal_code,
)


def test_regex_validators_valid() -> None:
    nip_data = validate_and_extract_nip("123-456-78-90")
    assert nip_data["tax_office"] == "123"

    postal_data = validate_and_extract_postal_code("50-370")
    assert postal_data["zone"] == "50"
    assert postal_data["district"] == "370"

    email_data = validate_and_extract_email("Jan.Kowalski@Firma.PL")
    assert email_data["user"] == "Jan.Kowalski"
    assert email_data["domain"] == "Firma.PL"


def test_regex_validators_invalid() -> None:
    with pytest.raises(ValueError):
        validate_and_extract_nip("123-ABC-78-90")

    with pytest.raises(ValueError):
        validate_and_extract_postal_code("50370")

    with pytest.raises(ValueError):
        validate_and_extract_email("brak-malpy.pl")


def test_sale_record_properties_and_method_decorator() -> None:
    record = SaleRecord(
        transaction_id="TX-0000001",
        timestamp=datetime(2026, 5, 10, 12, 0, 0),
        category="Elektronika",
        region="Dolnośląskie",
        quantity=3,
        unit_price=100.50,
        nip="123-456-78-90",
        postal_code="50-370",
        email="klient@example.com",
    )
    assert record.total_amount == 301.50
    assert record.to_summary_dict()["tax_office"] == "123"

    # Próba ustawienia ujemnej ceny powinna wywołać ValueError ze strony settera @property
    with pytest.raises(ValueError):
        record.unit_price = -10.0

    # Wyłączenie flagi walidacji powinno zablokować metodę chronioną przez @require_validated
    record.is_validated = False
    with pytest.raises(PermissionError):
        record.to_summary_dict()


def test_batch_iterator() -> None:
    data = list(range(10))
    iterator = BatchIterator(data, batch_size=4)
    batches = list(iterator)
    assert batches == [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]


def test_retry_decorator() -> None:
    attempts_counter = 0

    @retry(attempts=3, delay=0.01, exceptions=(ConnectionError,))
    def flaky_operation() -> str:
        nonlocal attempts_counter
        attempts_counter += 1
        if attempts_counter < 3:
            raise ConnectionError("Tymczasowy błąd")
        return "SUKCES"

    assert flaky_operation() == "SUKCES"
    assert attempts_counter == 3


def test_full_pipeline_on_generated_file(tmp_path: Path) -> None:
    csv_file = tmp_path / "test_sales.csv"
    generate_sales_csv(csv_file, num_rows=100, error_rate=0.1)

    errors: list[str] = []
    pipeline = build_sales_pipeline(csv_file, batch_size=25, error_collector=errors)
    batches = list(pipeline)

    total_valid = sum(len(b) for b in batches)
    assert total_valid + len(errors) == 100
    assert len(batches) > 0