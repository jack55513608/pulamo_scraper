# models.py
from dataclasses import dataclass

@dataclass
class Product:
    """Represents a scraped product."""
    title: str
    price: int
    in_stock: bool
    url: str

    def __repr__(self) -> str:
        stock_status = "有貨" if self.in_stock else "缺貨"
        return f"Product(title='{self.title}', price={self.price}, stock='{stock_status}', url='{self.url}')"
