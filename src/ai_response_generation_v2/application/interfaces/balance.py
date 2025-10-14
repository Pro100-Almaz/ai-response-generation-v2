from __future__ import annotations

from abc import ABC, abstractmethod


class BalanceControlProtocol(ABC):
    @abstractmethod
    async def check_points(self, *, minimum_points: int = 0) -> bool:
        """Return True if the user has at least ``minimum_points`` (defaults to a non-zero balance)."""

    @abstractmethod
    async def deduct_points(self, points: int = 20) -> bool:
        """Attempt to deduct ``points`` from the balance and return True on success."""
