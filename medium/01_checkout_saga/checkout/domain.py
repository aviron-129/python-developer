class OutOfStock(Exception):
    def __init__(self, sku: str, available: int, requested: int):
        self.sku = sku
        self.available = available
        self.requested = requested
        super().__init__(sku)


class UnknownSku(Exception):
    def __init__(self, sku: str):
        self.sku = sku
        super().__init__(sku)


class UnknownCheckout(Exception):
    def __init__(self, checkout_id: str):
        self.checkout_id = checkout_id
        super().__init__(checkout_id)


class PaymentDeclined(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)
