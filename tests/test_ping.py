"""
Тесты для GET /ping

Все быстрые — один запрос, маленький ответ. Хорошо подходят как
первая проверка что API вообще доступно перед запуском тяжёлых тестов.
"""

import pytest


@pytest.mark.fast
def test_ping_status_200(api_client):
    """Базовый smoke: эндпоинт отвечает 200."""
    response = api_client.ping()
    assert response.status_code == 200


@pytest.mark.fast
def test_ping_response_is_json(api_client):
    """Ответ должен быть валидным JSON."""
    response = api_client.ping()
    data = response.json()
    assert isinstance(data, dict)


@pytest.mark.fast
def test_ping_gecko_says_hello(api_client, request):
    """
    CoinGecko документирует конкретный текст ответа.
    Если вдруг поменяют — узнаем сразу.
    """
    response = api_client.ping()
    request.node.last_response = response
    data = response.json()
    assert "gecko_says" in data
    assert data["gecko_says"] == "(V3) To the Moon!"


@pytest.mark.fast
def test_ping_content_type(api_client, request):
    """Content-Type должен быть JSON."""
    response = api_client.ping()
    request.node.last_response = response
    assert "application/json" in response.headers.get("Content-Type", "")
