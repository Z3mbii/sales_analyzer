"""Modele domenowe reprezentujące rekordy sprzedaży"""

from datetime import datetime
from typing import Self

from src.decorators import require_validaed
from src.validators import (
    TX_ID_PATTERN,
    validate_and_extract_nip,
    validate_and_extract_email,
    validate_and_extract_postal_code,
)

class SaleRecord:
    """Reprezentuje transkacje sprzedazowa"""

    def __init__(
            self,
            transaction_id: str,
            timestamp: datetime,
            category: str,
            region: str,
            quantity: int,
            unit_price: float,
            nip: str,
            postal_code: str,
            email: str,
    ) -> None:
        self.is_validated = False

        if not TX_ID_PATTERN.fullmatch(transaction_id):
            raise ValueError(f"Nieprawidłowe ID transakcji: '{transaction_id}'")

        self.transaction_id = transaction_id
        self.timestamp = timestamp
        self.category = category
        self.region = region

        # Wywolanie setterow @properrty
        self.quantity = quantity
        self.unit_price = unit_price

        # Walidacja regexami i ekstrakcja metadanych
        nip_parts = validate_and_extract_nip(nip)
        postal_parts = validate_and_extract_postal_code(postal_code)
        email_parts = validate_and_extract_email(email)

        self.nip = nip
        self.tax_office_code = nip_parts["tax_office"]
        self.postal_code = postal_code
        self.postal_zone = postal_parts["zone"]
        self.email = email
        self.email_domain = email_parts["domain"]

        #Obiekt przeszedł pęłną walidacje
        self.is_validated = True

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        if value <= 0:
            raise ValueError(f"Ilość musi być dodatnia, otrzymano: {value}")
        self._quantity = value

    @property
    def unit_price(self) -> float:
        return self._unit_price

    @unit_price.setter
    def unit_price(self, value: float) -> None:
        if value <= 0:
            raise ValueError(f"Cena jednostkowa musi być dodatnia, otrzymano: {value}")
        self._unit_price = value

    @property
    def total_amount(self) -> float:
        """Wylicza wartość brutto transakcji"""
        return round(self._quantity * self._unit_price, 2)

    @classmethod
    def from_csv_row(cls, row: list[str]) -> Self:
        """Alternatywny konstruktowac SaleRecord"""
        if len(row) != 9:
            raise  ValueError(f"Oczekiwano 9 kolumn, otrzymano {len(row)}: {row}")

        tx_id, date_str, category, region, qty_str, price_str, nip, postal, email = row
        return cls(
            transaction_id=tx_id.strip(),
            timestamp=datetime.strptime(date_str.strip(), "%Y%m%d %H:%M:%S"),
            category=category.strip(),
            region=region.strip(),
            quantity=int(qty_str),
            unit_price=float(price_str),
            nip=nip,
            postal_code=postal,
            email=email,
        )

    @require_validaed
    def to_summary_dict(self) -> dict[str, str | int | float]:
        """Zwraca gotowy słownik"""
        return {
            "transaction_id": self.transaction_id,
            "category": self.category,
            "region": self.region,
            "total_amount": self.total_amount,
            "tax_office": self.tax_office_code,
            "email_domain": self.email_domain,
        }
