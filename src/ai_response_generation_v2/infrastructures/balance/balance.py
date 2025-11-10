from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import httpx
import structlog

from ai_response_generation_v2.application.interfaces.balance import BalanceControlProtocol


logger = structlog.get_logger(__name__)


class BalanceError(RuntimeError):
    """Generic balance service error."""


class InsufficientBalanceError(BalanceError):
    """Raised when the user does not have enough points."""


@dataclass(slots=True, frozen=True, kw_only=True)
class MonolithBalanceControl(BalanceControlProtocol):
    base_url: str
    timeout: float
    client: httpx.AsyncClient
    default_minimum_points: int = 1

    _CHECK_ENDPOINT: Final[str] = "/api/balance/"
    _DEDUCT_ENDPOINT: Final[str] = "/api/balance/deduct/"

    async def check_points(self, *, minimum_points: int = 0, auth_token: str = None) -> bool:
        if not auth_token:
            return False

        required_points = max(minimum_points, self.default_minimum_points)
        url = self._build_url(self._CHECK_ENDPOINT)
        logger.info(
            "Checking balance",
            url=url,
            required_points=required_points,
        )

        try:
            response = await self.client.get(
                url,
                timeout=self.timeout,
                headers={"Authorization": auth_token}
            )
        except httpx.RequestError as exc:
            logger.error("Balance check failed", error=str(exc))
            raise BalanceError("Unable to contact balance service") from exc

        if response.status_code == httpx.codes.FORBIDDEN:
            logger.info("Insufficient balance", status_code=response.status_code)
            return False

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Balance check unexpected status",
                status_code=exc.response.status_code,
                detail=exc.response.text,
            )
            raise BalanceError("Balance check request failed") from exc

        data = response.json()

        return True

        # return bool(data.get("balance", 0) >= required_points)

    async def deduct_points(self, points: int = 20) -> bool:
        url = self._build_url(self._DEDUCT_ENDPOINT)
        logger.debug(
            "Deducting points",
            url=url,
            points=points,
        )
        payload = {"points": points}

        try:
            response = await self.client.post(url, json=payload, timeout=self.timeout)
        except httpx.RequestError as exc:
            logger.error("Point deduction failed", error=str(exc))
            raise BalanceError("Unable to contact balance service") from exc

        if response.status_code == httpx.codes.FORBIDDEN:
            logger.info("Deduction rejected due to insufficient balance")
            return False

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Deduction unexpected status",
                status_code=exc.response.status_code,
                detail=exc.response.text,
            )
            raise BalanceError("Point deduction request failed") from exc

        data = response.json()
        return bool(data.get("deducted", False))

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url.rstrip('/')}{endpoint}" if self.base_url else endpoint

