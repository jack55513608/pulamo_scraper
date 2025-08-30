# models.py
from dataclasses import dataclass
from typing import Optional

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Product:
    """Represents a scraped product."""
    title: str
    price: int
    in_stock: bool
    url: str
    seller: Optional[str] = None
    payment_methods: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        stock_status = "有貨" if self.in_stock else "缺貨"
        seller_info = f", seller='{self.seller}'" if self.seller else ""
        payment_info = f", payment_methods={self.payment_methods}" if self.payment_methods else ""
        return f"Product(title='{self.title}', price={self.price}, stock='{stock_status}', url='{self.url}'{seller_info}{payment_info})"