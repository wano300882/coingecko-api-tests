"""
Тесты для GET /coins/markets

fast — базовый контракт: статус, схема, обязательные поля
slow — параметризованные по валютам и размерам страниц,
       проверка сортировки и пагинации
"""

import pytest


REQUIRED_COIN_FIELDS = {
    "id",
    "symbol",
    "name",
    "current_price",
    "market_cap",
    "market_cap_rank",
    "total_volume",
    "price_change_percentage_24h",
}


# — FAST —


@pytest.mark.fast
def test_markets_status_200(api_client, request):
    response = api_client.get_markets(per_page=5)
    request.node.last_response = response
    assert response.status_code == 200


@pytest.mark.fast
def test_markets_returns_list(api_client, request):
    """Ответ должен быть массивом."""
    response = api_client.get_markets(per_page=5)
    request.node.last_response = response
    assert isinstance(response.json(), list)


@pytest.mark.fast
def test_markets_respects_per_page(api_client, request):
    """Параметр per_page должен реально работать."""
    response = api_client.get_markets(per_page=5)
    request.node.last_response = response
    assert len(response.json()) == 5


@pytest.mark.fast
def test_markets_coin_has_required_fields(api_client, request):
    """Проверяем только первый элемент — нам важна схема, не все данные."""
    response = api_client.get_markets(per_page=1)
    request.node.last_response = response
    coin = response.json()[0]
    missing = REQUIRED_COIN_FIELDS - set(coin.keys())
    assert not missing, f"Пропущены поля: {missing}"


@pytest.mark.fast
def test_markets_market_cap_rank_is_positive_int(api_client, request):
    """market_cap_rank — положительное целое, не null и не ноль."""
    response = api_client.get_markets(per_page=10)
    request.node.last_response = response
    for coin in response.json():
        rank = coin.get("market_cap_rank")
        if rank is not None:
            assert isinstance(rank, int) and rank > 0, (
                f"Неожиданный market_cap_rank={rank!r} у {coin.get('id')}"
            )


# — SLOW —


@pytest.mark.slow
@pytest.mark.parametrize("currency", ["usd", "eur", "gbp", "jpy"])
def test_markets_supports_multiple_currencies(api_client, request, currency):
    """
    Параметризуем по валютам — каждая даёт отдельный тест-кейс в отчёте.
    Так сразу видно какая конкретно валюта сломалась, если что-то пойдёт не так.
    """
    response = api_client.get_markets(vs_currency=currency, per_page=5)
    request.node.last_response = response
    assert response.status_code == 200
    assert len(response.json()) > 0, f"Пустой ответ для валюты {currency}"


@pytest.mark.slow
@pytest.mark.parametrize("per_page", [10, 50, 100])
def test_markets_pagination_sizes(api_client, request, per_page):
    """Проверяем что разные размеры страниц возвращают правильное количество."""
    response = api_client.get_markets(per_page=per_page)
    request.node.last_response = response
    assert response.status_code == 200
    assert len(response.json()) == per_page


@pytest.mark.slow
def test_markets_ordered_by_market_cap_desc(api_client, request):
    """По умолчанию CoinGecko сортирует по капитализации убыванию."""
    response = api_client.get_markets(per_page=20, order="market_cap_desc")
    request.node.last_response = response

    previous_cap = float("inf")
    for coin in response.json():
        cap = coin.get("market_cap")
        if cap is None:
            continue
        assert cap <= previous_cap, (
            f"Нарушение сортировки около {coin.get('id')}: {cap} > {previous_cap}"
        )
        previous_cap = cap


@pytest.mark.slow
def test_markets_page_two_differs_from_page_one(api_client):
    """Страницы не должны пересекаться — иначе параметр page ни на что не влияет."""
    ids_page_1 = {c["id"] for c in api_client.get_markets(per_page=10, page=1).json()}
    ids_page_2 = {c["id"] for c in api_client.get_markets(per_page=10, page=2).json()}
    overlap = ids_page_1 & ids_page_2
    assert not overlap, f"Монеты повторяются на двух страницах: {overlap}"


@pytest.mark.slow
def test_markets_price_change_is_float_or_none(api_client, request):
    """price_change_percentage_24h — float или null, ничего другого быть не должно."""
    response = api_client.get_markets(per_page=20)
    request.node.last_response = response
    for coin in response.json():
        value = coin.get("price_change_percentage_24h")
        assert value is None or isinstance(value, float), (
            f"Неожиданный тип у {coin.get('id')}: {type(value)}"
        )
