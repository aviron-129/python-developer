import uuid

from checkout.domain import PaymentDeclined, UnknownCheckout
from checkout.store import Store


class SandboxPayments:
    def capture(self, checkout_id: str, amount: int, card_token: str) -> str:
        if not card_token or card_token == "decline" or amount <= 0:
            raise PaymentDeclined("Платёж отклонён")
        return f"pay_{checkout_id[:8]}"


class CheckoutSaga:
    def __init__(self, store: Store, payments: SandboxPayments):
        self.store = store
        self.payments = payments

    def open_sku(self, sku: str, name: str, on_hand: int) -> dict:
        with self.store.transaction():
            self.store.put_sku(sku, name, on_hand)
            return dict(self.store.get_sku(sku))

    def start(self, sku: str, qty: int, amount: int, card_token: str) -> dict:
        checkout_id = uuid.uuid4().hex
        with self.store.transaction():
            self.store.insert_checkout(checkout_id, sku, qty, amount)
            self.store.add_step(checkout_id, "started")
            self.store.take(sku, qty)
            self.store.mark(checkout_id, "reserved")
            self.store.add_step(checkout_id, "stock_reserved")

        try:
            payment_id = self.payments.capture(checkout_id, amount, card_token)
        except PaymentDeclined as exc:
            with self.store.transaction():
                self.store.restore(sku, qty)
                self.store.mark(checkout_id, "compensated", reason=exc.reason)
                self.store.add_step(checkout_id, "stock_released")
            return self.get(checkout_id)

        with self.store.transaction():
            self.store.mark(checkout_id, "confirmed", payment_id=payment_id)
            self.store.add_step(checkout_id, "payment_captured")
        return self.get(checkout_id)

    def get(self, checkout_id: str) -> dict:
        row = self.store.read_checkout(checkout_id)
        if row is None:
            raise UnknownCheckout(checkout_id)
        return row
