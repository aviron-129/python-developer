class UpstreamDown(Exception):
    pass


class CircuitOpen(Exception):
    def __init__(self, name: str):
        self.name = name
        super().__init__(name)
