"""Thin read-only wrapper around the official SnapTrade Python SDK."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, TypeVar, cast

from src.integrations.snaptrade.models import SnapTradeAccount, SnapTradeCredentials

T = TypeVar("T")


class SnapTradeAPIError(RuntimeError):
    """Sanitized SnapTrade SDK failure safe to show in CLI output."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Create a sanitized API error."""
        super().__init__(message)
        self.status_code = status_code


class SnapTradeClientWrapper:
    """Read-only SDK wrapper that never logs credential values."""

    def __init__(
        self, credentials: SnapTradeCredentials, sdk_client: Any | None = None
    ):
        """Initialize the wrapper with credentials and optional test client."""
        self.credentials = credentials
        self._client = (
            sdk_client if sdk_client is not None else self._build_sdk_client()
        )

    @classmethod
    def from_env(cls) -> SnapTradeClientWrapper:
        """Create a wrapper from local environment variables."""
        return cls(SnapTradeCredentials.from_env())

    def list_accounts(self) -> list[SnapTradeAccount]:
        """List linked SnapTrade accounts for the configured user."""
        response = self._call(
            lambda: self._client.account_information.list_user_accounts(
                user_id=self.credentials.user_id_value,
                user_secret=self.credentials.user_secret_value,
            )
        )
        body = _response_body(response)
        if not isinstance(body, list):
            raise SnapTradeAPIError(
                "SnapTrade list_user_accounts returned non-list body"
            )
        return [_normalize_account(item) for item in body]

    def get_balances(self, account_id: str) -> list[dict[str, Any]]:
        """Return normalized cash / buying-power balances for an account."""
        response = self._call(
            lambda: self._client.account_information.get_user_account_balance(
                account_id=account_id,
                user_id=self.credentials.user_id_value,
                user_secret=self.credentials.user_secret_value,
            )
        )
        return [
            _summarize_balance(item) for item in _ensure_list(_response_body(response))
        ]

    def get_positions(self, account_id: str) -> list[dict[str, Any]]:
        """Return normalized symbol / quantity / cost-basis positions."""
        response = self._call(
            lambda: self._client.account_information.get_user_account_positions(
                account_id=account_id,
                user_id=self.credentials.user_id_value,
                user_secret=self.credentials.user_secret_value,
            )
        )
        return [
            _summarize_position(item) for item in _ensure_list(_response_body(response))
        ]

    def get_options(self, account_id: str) -> list[dict[str, Any]]:
        """Return normalized option holdings (per-share cost, Fidelity symbol).

        SnapTrade excludes options from get_user_account_positions; they come
        from this separate endpoint. Cost/price are reported per contract (x100),
        normalized here to per-share to match the Fidelity CSV convention.
        """
        response = self._call(
            lambda: self._client.options.list_option_holdings(
                account_id=account_id,
                user_id=self.credentials.user_id_value,
                user_secret=self.credentials.user_secret_value,
            )
        )
        return [
            _summarize_option(item) for item in _ensure_list(_response_body(response))
        ]

    def get_account_equity(self, account_id: str) -> float | None:
        """Return net account equity (total value) from account details."""
        response = self._call(
            lambda: self._client.account_information.get_user_account_details(
                account_id=account_id,
                user_id=self.credentials.user_id_value,
                user_secret=self.credentials.user_secret_value,
            )
        )
        body = _response_body(response)
        if isinstance(body, Mapping):
            return _to_float(_nested_first(body, ("balance", "total", "amount")))
        return None

    def probe_account(self, account_id: str) -> dict[str, Any]:
        """Return minimal balance/position diagnostics for Phase 0 proof-of-life."""
        balances = self.get_balances(account_id)
        positions = self.get_positions(account_id)
        spaxx_positions = [p for p in positions if p.get("symbol") == "SPAXX"]
        average_price_present = sum(
            1 for p in positions if p.get("average_purchase_price") is not None
        )
        return {
            "account_id": account_id,
            "balance_count": len(balances),
            "balances": balances,
            "position_count": len(positions),
            "spaxx_as_position": len(spaxx_positions) > 0,
            "spaxx_position_count": len(spaxx_positions),
            "average_purchase_price_present_count": average_price_present,
            "average_purchase_price_missing_count": len(positions)
            - average_price_present,
        }

    def _build_sdk_client(self) -> Any:
        try:
            from snaptrade_client import SnapTrade
        except ImportError as exc:  # pragma: no cover - dependency gate
            raise RuntimeError(
                "snaptrade-python-sdk is not installed. Run `uv sync`."
            ) from exc
        return SnapTrade(
            consumer_key=self.credentials.consumer_key_value,
            client_id=self.credentials.client_id_value,
        )

    def _call(self, fn: Callable[[], T]) -> T:
        try:
            return fn()
        except Exception as exc:
            raise _to_snaptrade_error(exc) from exc


def _to_snaptrade_error(exc: Exception) -> SnapTradeAPIError:
    """Convert SDK exceptions into a sanitized CLI-safe error."""
    status = getattr(exc, "status", None) or getattr(exc, "status_code", None)
    response_body = getattr(exc, "response_body", None)
    detail = _message_from_body(response_body)
    if detail:
        return SnapTradeAPIError(detail, status)
    if status:
        return SnapTradeAPIError(f"SnapTrade API error (status {status})", status)
    return SnapTradeAPIError(str(exc) or "Unknown SnapTrade API error")


def _message_from_body(body: Any) -> str | None:
    plain = _to_plain(body)
    if not isinstance(plain, Mapping):
        return None
    for key in ("detail", "default_detail", "message", "error"):
        value = plain.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _response_body(response: Any) -> Any:
    if hasattr(response, "body"):
        return _to_plain(response.body)
    if hasattr(response, "data"):
        return _to_plain(response.data)
    return _to_plain(response)


def _to_plain(value: Any) -> Any:
    """Convert generated SDK models into dict/list primitives."""
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, list | tuple):
        return [_to_plain(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _to_plain(item) for key, item in value.items()}
    if hasattr(value, "to_dict"):
        return _to_plain(value.to_dict())
    if hasattr(value, "model_dump"):
        return _to_plain(value.model_dump())
    if hasattr(value, "__dict__"):
        return {
            key: _to_plain(item)
            for key, item in vars(value).items()
            if not key.startswith("_")
        }
    return str(value)


def _normalize_account(raw_account: Any) -> SnapTradeAccount:
    raw = _to_plain(raw_account)
    if not isinstance(raw, Mapping):
        raise SnapTradeAPIError("SnapTrade account payload was not an object")
    account_id = _first_present(raw, "id", "account_id", "accountId")
    if not account_id:
        raise SnapTradeAPIError("SnapTrade account payload is missing id")
    institution = _first_present(
        raw,
        "institution_name",
        "institutionName",
        "brokerage_name",
        "brokerageName",
    ) or _nested_first(raw, ("brokerage_authorization", "name"), ("brokerage", "name"))
    balance_total_raw = _first_present(
        raw, "balance_total", "balanceTotal", "total_value", "totalValue"
    ) or _nested_first(raw, ("balance", "total", "amount"))
    currency = _currency_code(_first_present(raw, "currency")) or _currency_code(
        _nested_first(raw, ("balance", "total"))
    )
    balance_total = _to_float(balance_total_raw)
    account_type = _first_present(
        raw, "type", "account_type", "accountType", "account_category", "raw_type"
    )
    number = _first_present(raw, "number", "account_number", "accountNumber")
    return SnapTradeAccount(
        id=str(account_id),
        name=str(_first_present(raw, "name") or ""),
        institution_name=str(institution or ""),
        type=str(account_type or ""),
        currency=currency,
        number_masked=_mask_account_number(number),
        balance_total=balance_total,
        raw=dict(raw),
    )


def _ensure_list(value: Any) -> list[Any]:
    plain = _to_plain(value)
    if isinstance(plain, list):
        return plain
    if isinstance(plain, Mapping) and isinstance(plain.get("data"), list):
        return cast(list[Any], plain["data"])
    return []


def _summarize_balance(raw_balance: Any) -> dict[str, Any]:
    raw = _to_plain(raw_balance)
    if not isinstance(raw, Mapping):
        return {}
    # The SnapTrade Balance model only carries currency, cash, buying_power.
    return {
        "currency": _currency_code(_first_present(raw, "currency")),
        "cash": _to_float(_first_present(raw, "cash")),
        "buying_power": _to_float(_first_present(raw, "buying_power", "buyingPower")),
    }


def _summarize_position(raw_position: Any) -> dict[str, Any]:
    raw = _to_plain(raw_position)
    if not isinstance(raw, Mapping):
        return {}
    return {
        "symbol": _position_symbol(raw),
        "quantity": _to_float(
            _first_present(raw, "units", "quantity", "fractional_units")
        ),
        "average_purchase_price": _to_float(
            _first_present(raw, "average_purchase_price", "averagePurchasePrice")
        ),
        "price": _to_float(_first_present(raw, "price", "last_price", "lastPrice")),
        "open_pnl": _to_float(_first_present(raw, "open_pnl", "openPnl")),
        "instrument": "equity",
    }


def _summarize_option(raw_option: Any) -> dict[str, Any]:
    raw = _to_plain(raw_option)
    if not isinstance(raw, Mapping):
        return {}
    occ = _option_occ_ticker(raw)
    avg_contract = _to_float(
        _first_present(raw, "average_purchase_price", "averagePurchasePrice")
    )
    return {
        "symbol": _occ_to_fidelity_symbol(occ),
        "occ_symbol": occ,
        "quantity": _to_float(_first_present(raw, "units", "quantity")),
        # SnapTrade reports cost per contract (x100); normalize to per-share.
        "average_purchase_price": (avg_contract / 100)
        if avg_contract is not None
        else None,
        "price": _to_float(_first_present(raw, "price", "last_price")),
        "instrument": "option",
    }


def _option_occ_ticker(raw: Mapping[str, Any]) -> str | None:
    sym = raw.get("symbol")
    if isinstance(sym, Mapping):
        option_symbol = sym.get("option_symbol")
        if isinstance(option_symbol, Mapping):
            ticker = option_symbol.get("ticker")
            if isinstance(ticker, str):
                return ticker
    ticker = _first_present(raw, "ticker", "option_symbol")
    return ticker if isinstance(ticker, str) else None


def _occ_to_fidelity_symbol(occ: str | None) -> str | None:
    """Convert an OCC option ticker to Fidelity's CSV form.

    'SPY   260918P00620000' -> '-SPY260918P620' (6-char ticker, YYMMDD, C/P,
    8-digit strike x1000). Returns the input unchanged if it is not OCC-shaped.
    """
    if not occ or len(occ) < 21:
        return occ
    ticker = occ[:6].strip()
    yymmdd = occ[6:12]
    call_put = occ[12]
    try:
        strike = int(occ[13:21]) / 1000
    except ValueError:
        return occ
    strike_str = f"{strike:.0f}" if strike == int(strike) else f"{strike:g}"
    return f"-{ticker}{yymmdd}{call_put}{strike_str}"


def derive_margin_debt(
    stocks: list[dict[str, Any]],
    options: list[dict[str, Any]],
    equity: float | None,
) -> tuple[float | None, float]:
    """Derive margin debt and gross market value from holdings and net equity.

    SnapTrade does not expose the margin loan directly. Gross long market value
    (settled cash is carried in the SPAXX position, so it is already included)
    minus net account equity recovers it (validated within ~0.1% of the broker's
    reported net debit). Options use the x100 contract multiplier. margin_debt is
    a loan, so it is clamped to >= 0 (a net-cash account owes nothing). Returns
    (margin_debt, gross_market_value); margin_debt is None if equity is unknown.
    """
    stock_mv = sum((p.get("price") or 0) * (p.get("quantity") or 0) for p in stocks)
    option_mv = sum(
        (o.get("price") or 0) * (o.get("quantity") or 0) * 100 for o in options
    )
    gross_mv = round(stock_mv + option_mv, 2)
    if equity is None:
        return None, gross_mv
    return max(round(gross_mv - equity, 2), 0.0), gross_mv


def _position_symbol(raw_position: Any) -> str | None:
    raw = _to_plain(raw_position)
    if not isinstance(raw, Mapping):
        return None
    symbol = _first_present(raw, "symbol")
    if isinstance(symbol, str):
        return symbol.upper()
    if isinstance(symbol, Mapping):
        inner = symbol.get("symbol")
        if isinstance(inner, str):
            return inner.upper()
        if isinstance(inner, Mapping):
            ticker = inner.get("symbol")
            if isinstance(ticker, str):
                return ticker.upper()
    return None


def _first_present(raw: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in raw and raw[key] is not None:
            return raw[key]
    return None


def _nested_first(raw: Mapping[str, Any], *paths: tuple[str, ...]) -> Any:
    for path in paths:
        current: Any = raw
        for key in path:
            if not isinstance(current, Mapping) or key not in current:
                current = None
                break
            current = current[key]
        if current is not None:
            return current
    return None


def _currency_code(raw: Any) -> str | None:
    if isinstance(raw, str):
        return raw
    if isinstance(raw, Mapping):
        value = (
            raw.get("code")
            or raw.get("currency")
            or raw.get("currency_code")
            or raw.get("currencyCode")
        )
        return str(value) if value else None
    return None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mask_account_number(value: Any) -> str | None:
    if value is None:
        return None
    digits = "".join(char for char in str(value) if char.isdigit())
    if len(digits) <= 4:
        return "****" if digits else None
    return f"****{digits[-4:]}"
