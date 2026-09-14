class UnknownRecipient(Exception):
    def __init__(self, recipient_id: str):
        self.recipient_id = recipient_id
        super().__init__(recipient_id)


class UnknownTemplate(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class MissingPlaceholder(Exception):
    def __init__(self, name: str):
        self.name = name
        super().__init__(name)


CHANNELS = ("email", "push", "telegram")
