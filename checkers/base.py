# checkers/base.py
from abc import ABC, abstractmethod
from typing import List, Optional
from models import Product

class BaseChecker(ABC):
    """Abstract base class for all checkers."""

    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def check(self, products: List[Product], params: dict) -> Optional[Product]:
        """
        Checks the list of products and returns the target product if found.
        """
        pass
