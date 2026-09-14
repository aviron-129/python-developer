class DuplicateOrder(Exception):
    pass


class UnknownOrder(Exception):
    def __init__(self, order_id: str):
        self.order_id = order_id
        super().__init__(order_id)
