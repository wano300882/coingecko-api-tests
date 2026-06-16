import requests

from utils import config


class CoinGeckoClient:
    """
    Обёртка над requests.Session для CoinGecko API.

    Все скучные детали (base URL, таймаут, заголовки) живут здесь,
    чтобы в тестах не повторять одно и то же.
    """

    def __init__(self) -> None:
        self._base_url = config.BASE_URL
        self._timeout = config.REQUEST_TIMEOUT

        self._session = requests.Session()

        headers = {
            "Accept": "application/json",
            "User-Agent": "coingecko-pytest-demo/1.0",
        }
        # Если задан API ключ (Pro тариф) — добавляем в заголовки сразу,
        # чтобы не думать об этом в каждом тесте
        if config.API_KEY:
            headers["x-cg-pro-api-key"] = config.API_KEY

        self._session.headers.update(headers)

    def ping(self) -> requests.Response:
        """GET /ping — проверяем что API вообще живо."""
        return self._get("/ping")

    def get_markets(self, vs_currency: str = "usd", **kwargs) -> requests.Response:
        """GET /coins/markets — список монет с рыночными данными."""
        params = {"vs_currency": vs_currency, **kwargs}
        return self._get("/coins/markets", params=params)

    def get_coin(self, coin_id: str, **kwargs) -> requests.Response:
        """GET /coins/{id} — детали конкретной монеты."""
        return self._get(f"/coins/{coin_id}", params=kwargs)

    def _get(self, path: str, params: dict | None = None) -> requests.Response:
        url = f"{self._base_url}{path}"
        response = self._session.get(url, params=params, timeout=self._timeout)
        return response

    def close(self) -> None:
        self._session.close()
