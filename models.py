# models.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Product:
    """Represents a scraped product."""
    title: str
    price: int
    in_stock: bool
    url: str
    seller: Optional[str] = None

    def __repr__(self) -> str:
        stock_status = "有貨" if self.in_stock else "缺貨"
        seller_info = f", seller='{self.seller}'" if self.seller else ""
        return f"Product(title='{self.title}', price={self.price}, stock='{stock_status}', url='{self.url}'{seller_info})"
