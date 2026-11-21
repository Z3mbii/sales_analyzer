"""Własne dekoratory funkcji"""

import functools
import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

def measure_time(func: F) -> F:
    """Dekorator funkcji mierzacy czas wykonania"""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"[{func.__name__}] wykonano w {elapsed:.4f} s")
        print(f"[CZAS] {func.__name__} w {elapsed:.4f} s")
        return result

    return wrapper

def retry(attempts: int = 3, delay: float = 0.2, exceptions: tuple[type[Exception], ...] = (Exception,)) -> Callable[[F], F]:
    """Fabryka dekoratorów funckji"""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: Exception | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as err:
                    last_error = err
                    logger.warning(f"Próba {attempt}/{attempts} dla {func.__name__} nieudana: {err}")
                    if attempt < attempts:
                        time.sleep(delay)
            raise RuntimeError(f"Funckja {func.__name__} nieudana po {attempts} próbach") from last_error

        return wrapper

    return decorator

def require_validaed(method: F) -> F:
    """Dekorator metody sprawdzający czy obiekt przeszedl walidacje"""

    @functools.wraps(method)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if not getattr(self, "is_validated", False):
            raise PermissionError(
                f"Nie można wywołać metody '{method.__name__}' na niezweryfikowanym obiekcie {type(self).__name__}"
            )
        return method(self, *args, **kwargs)

    return wrapper