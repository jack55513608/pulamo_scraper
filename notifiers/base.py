# notifiers/base.py
from abc import ABC, abstractmethod
from models import Product

class BaseNotifier(ABC):
    """Abstract base class for all notifiers."""

    @abstractmethod
    async def notify(self, product: Product, params: dict):
        """
        Sends a notification about a found product.
        """
        pass
