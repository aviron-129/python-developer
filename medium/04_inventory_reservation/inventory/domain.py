class UnknownSku(Exception):
    def __init__(self, sku: str):
        self.sku = sku
        super().__init__(sku)


class InsufficientStock(Exception):
    def __init__(self, sku: str, available: int, requested: int):
        self.sku = sku
        self.available = available
        self.requested = requested
        super().__init__(sku)


class VersionConflict(Exception):
    def __init__(self, sku: str):
        self.sku = sku
        super().__init__(sku)


class UnknownReservation(Exception):
    def __init__(self, reservation_id: str):
        self.reservation_id = reservation_id
        super().__init__(reservation_id)


class IllegalTransition(Exception):
    def __init__(self, status: str):
        self.status = status
        super().__init__(status)
