"""Moduł walidacji danych"""

import re

NIP_PATTERN = re.compile(
    r"^(?P<tax_office>\d{3})-?(?P<core>\d{3})-?(?P<part1>\d{2})-?(?P<part2>\d{2})$"
)

POSTAL_CODE_PATTERN = re.compile(
    r"^(?P<zone>\d{2})-(?P<district>\d{3})$"
)

EMAIL_PATTERN = re.compile(
    r"^(?P<user>[\w.+-]+)@(?P<domain>[\w-]+(?:\.[\w-]+)*)$",
    re.IGNORECASE,
)

TX_ID_PATTERN = re.compile(
    r"^TX-(?P<number>\d{7})$"
)

def validate_and_extract_nip(nip: str) -> dict[str, str]:
    """Waliduje numer NIP"""
    match = NIP_PATTERN.fullmatch(nip.strip())
    if not match:
        raise ValueError(f"Nieprawidłowy format NIP: '{nip}'")
    return match.groupdict()

def validate_and_extract_postal_code(postal_code: str) -> dict[str, str]:
    """Waliduje numer postal code"""
    match = POSTAL_CODE_PATTERN.fullmatch(postal_code.strip())
    if not match:
        raise ValueError(f"Nieprawidłwy kod pocztowy: '{postal_code}'")
    return match.groupdict()

def validate_and_extract_email(email: str) -> dict[str, str]:
    """Waliduje adres email"""
    match = EMAIL_PATTERN.fullmatch(email.strip())
    if not match:
        raise ValueError(f"Nieprawidłwy adres e-mail: '{email}'")
    return match.groupdict()
