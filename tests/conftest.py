"""
Общие фикстуры для всего проекта.

api_client имеет scope="session" — одна HTTP-сессия на весь прогон,
TCP-соединение переиспользуется. При запуске с -n (xdist) каждый воркер
получает свою копию, что правильно — воркеры не должны делить состояние.
"""

import json
import os

import pytest

from utils import config  # загружает .env.{ENV} сразу при импорте
from utils.api_client import CoinGeckoClient


@pytest.fixture(scope="session")
def env_name() -> str:
    """Текущее окружение. Можно использовать в тестах если нужно."""
    return os.environ.get("ENV", "dev").lower()


@pytest.fixture(scope="session")
def api_client() -> CoinGeckoClient:
    client = CoinGeckoClient()
    yield client
    client.close()


@pytest.fixture(scope="session")
def coin_id() -> str:
    """Монета по умолчанию для тестов, которым нужен конкретный id."""
    return "bitcoin"


def pytest_report_header(config_obj) -> str:
    """Показывает активное окружение в шапке каждого запуска."""
    env = os.environ.get("ENV", "dev").lower()
    return f"environment: {env} | {config.BASE_URL} | timeout={config.REQUEST_TIMEOUT}s"


@pytest.fixture(autouse=True)
def log_response_on_failure(request):
    """
    При падении теста печатает полный дамп запроса и ответа.

    Чтобы включить логирование в конкретном тесте, достаточно сохранить
    response на узле:
        request.node.last_response = response

    Тесты, которые этого не делают, не теряют ничего — фикстура просто
    не найдёт атрибут и промолчит.
    """
    yield

    if request.node.rep_call.failed if hasattr(request.node, "rep_call") else False:
        response = getattr(request.node, "last_response", None)
        if response is not None:
            _print_response(response)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Стандартный способ узнать внутри фикстуры, упал тест или нет.
    # Без этого хука rep_call недоступен в фазе teardown.
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def _print_response(response) -> None:
    req = response.request
    sep = "─" * 60

    print(f"\n{sep}")
    print("REQUEST")
    print(f"  {req.method} {req.url}")
    for k, v in req.headers.items():
        print(f"  {k}: {v}")

    print("\nRESPONSE")
    print(f"  Status : {response.status_code} {response.reason}")
    print(f"  Elapsed: {response.elapsed.total_seconds():.3f}s")
    for k, v in response.headers.items():
        print(f"  {k}: {v}")

    print("\nBODY")
    try:
        body = json.dumps(response.json(), indent=2, ensure_ascii=False)
        if len(body) > 2000:
            body = body[:2000] + "\n  … (обрезано)"
        print(body)
    except ValueError:
        print(response.text[:2000])

    print(sep)
