"""
Тесты для GET /coins/{id}

fast — схема ответа, обработка ошибок для одной монеты
slow — параметризация по нескольким монетам,
       проверка что цены совпадают с /coins/markets
"""

import pytest


REQUIRED_TOP_LEVEL_FIELDS = {"id", "symbol", "name", "market_data", "description"}

# Устоявшиеся монеты из топ-100 — они точно есть в API и не делистятся
KNOWN_COINS = ["bitcoin", "ethereum", "litecoin", "cardano"]


def _get_coin_minimal(client, coin_id: str):
    """
    Запрашиваем только то что нужно — отключаем тикеры, локализацию и прочее.
    Ответ становится раз в 10 меньше, тест работает быстрее.
    """
    return client.get_coin(
        coin_id,
        localization=False,
        tickers=False,
        community_data=False,
        developer_data=False,
    )


# — FAST —


@pytest.mark.fast
def test_coin_status_200(api_client, coin_id, request):
    response = _get_coin_minimal(api_client, coin_id)
    request.node.last_response = response
    assert response.status_code == 200


@pytest.mark.fast
def test_coin_404_for_unknown_id(api_client, request):
    """Несуществующий id должен давать 404, а не 500 или пустой объект."""
    response = _get_coin_minimal(api_client, "this-coin-does-not-exist-xyz")
    request.node.last_response = response
    assert response.status_code == 404


@pytest.mark.fast
def test_coin_id_matches_request(api_client, coin_id, request):
    """Поле id в ответе должно совпадать с тем что мы запросили."""
    response = _get_coin_minimal(api_client, coin_id)
    request.node.last_response = response
    assert response.json()["id"] == coin_id


@pytest.mark.fast
def test_coin_has_required_fields(api_client, coin_id, request):
    response = _get_coin_minimal(api_client, coin_id)
    request.node.last_response = response
    missing = REQUIRED_TOP_LEVEL_FIELDS - set(response.json().keys())
    assert not missing, f"Пропущены поля: {missing}"


@pytest.mark.fast
def test_coin_market_data_has_current_price(api_client, coin_id, request):
    """current_price.usd — самое важное поле, проверяем отдельно."""
    response = _get_coin_minimal(api_client, coin_id)
    request.node.last_response = response
    current_price = response.json()["market_data"]["current_price"]
    assert "usd" in current_price, "Поле current_price.usd отсутствует"
    assert isinstance(current_price["usd"], (int, float))
    assert current_price["usd"] > 0


@pytest.mark.fast
def test_coin_symbol_is_lowercase_string(api_client, coin_id, request):
    """CoinGecko всегда отдаёт символ в нижнем регистре (btc, eth, ...)."""
    response = _get_coin_minimal(api_client, coin_id)
    request.node.last_response = response
    symbol = response.json().get("symbol", "")
    assert isinstance(symbol, str)
    assert symbol == symbol.lower(), f"Символ не в нижнем регистре: {symbol!r}"


# — SLOW —


@pytest.mark.slow
@pytest.mark.parametrize("cid", KNOWN_COINS)
def test_known_coins_return_200(api_client, request, cid):
    """
    Параметризуем — каждая монета отдельный тест-кейс.
    Если упадёт одна, остальные продолжат выполняться.
    """
    response = _get_coin_minimal(api_client, cid)
    request.node.last_response = response
    assert response.status_code == 200, f"Неожиданный статус для {cid!r}"


@pytest.mark.slow
@pytest.mark.parametrize("cid", KNOWN_COINS)
def test_known_coins_have_positive_usd_price(api_client, request, cid):
    response = _get_coin_minimal(api_client, cid)
    request.node.last_response = response
    price = response.json()["market_data"]["current_price"]["usd"]
    assert price > 0, f"Нулевая или отрицательная цена у {cid}: {price}"


@pytest.mark.slow
@pytest.mark.parametrize("currency", ["usd", "eur", "btc"])
def test_coin_price_in_multiple_currencies(api_client, coin_id, request, currency):
    """current_price должен содержать не только usd."""
    response = _get_coin_minimal(api_client, coin_id)
    request.node.last_response = response
    current_price = response.json()["market_data"]["current_price"]
    assert currency in current_price, f"Валюта {currency!r} отсутствует в current_price"
    assert isinstance(current_price[currency], (int, float))


@pytest.mark.slow
def test_coin_price_consistent_with_markets(api_client, coin_id):
    """
    Цена из /coins/{id} и /coins/markets должна совпадать в пределах 2%.
    Небольшое расхождение нормально — эндпоинты кешируются независимо.
    """
    detail_price = (
        _get_coin_minimal(api_client, coin_id)
        .json()["market_data"]["current_price"]["usd"]
    )

    markets_data = api_client.get_markets(
        vs_currency="usd", ids=coin_id, per_page=1
    ).json()
    assert len(markets_data) == 1
    markets_price = markets_data[0]["current_price"]

    ratio = abs(detail_price - markets_price) / markets_price
    assert ratio < 0.02, (
        f"Цены расходятся больше чем на 2% для {coin_id}: "
        f"/coins/{coin_id}={detail_price}, /markets={markets_price} "
        f"(diff={ratio:.2%})"
    )


@pytest.mark.slow
@pytest.mark.parametrize("cid", KNOWN_COINS)
def test_known_coins_market_cap_rank_is_set(api_client, request, cid):
    """Все монеты из KNOWN_COINS — топ-100, у них должен быть рейтинг."""
    response = _get_coin_minimal(api_client, cid)
    request.node.last_response = response
    rank = response.json()["market_data"].get("market_cap_rank")
    assert isinstance(rank, int) and rank > 0, (
        f"Ожидался положительный рейтинг у {cid}, получили {rank!r}"
    )
