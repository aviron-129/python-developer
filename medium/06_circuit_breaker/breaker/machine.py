from breaker.domain import CircuitOpen, UpstreamDown


class Clock:
    def __init__(self):
        self.now = 0.0

    def advance(self, seconds: float) -> None:
        self.now += seconds


class Breaker:
    def __init__(self, clock: Clock, threshold: int = 3, reset_after: float = 30.0):
        self.clock = clock
        self.threshold = threshold
        self.reset_after = reset_after
        self.circuits: dict[str, dict] = {}

    def call(self, name: str, operation) -> dict:
        circuit = self.circuits.setdefault(
            name,
            {
                "state": "closed",
                "failures": 0,
                "opened_at": None,
                "cache": None,
            },
        )
        if circuit["state"] == "open":
            if self.clock.now - circuit["opened_at"] < self.reset_after:
                if circuit["cache"] is None:
                    raise CircuitOpen(name)
                return {"source": "cache", "body": circuit["cache"], "state": "open"}
            circuit["state"] = "half_open"

        try:
            body = operation()
        except UpstreamDown:
            circuit["failures"] += 1
            if circuit["state"] == "half_open" or circuit["failures"] >= self.threshold:
                circuit["state"] = "open"
                circuit["opened_at"] = self.clock.now
            raise
        circuit["failures"] = 0
        circuit["state"] = "closed"
        circuit["opened_at"] = None
        circuit["cache"] = body
        return {"source": "upstream", "body": body, "state": "closed"}

    def snapshot(self, name: str) -> dict:
        circuit = self.circuits.get(name)
        if circuit is None:
            return {"name": name, "state": "closed", "failures": 0, "has_cache": False}
        return {
            "name": name,
            "state": circuit["state"],
            "failures": circuit["failures"],
            "has_cache": circuit["cache"] is not None,
        }

    def reset(self, name: str) -> dict:
        self.circuits.pop(name, None)
        return self.snapshot(name)
