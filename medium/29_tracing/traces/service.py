import uuid


class TraceBook:
    def __init__(self):
        self.traces: dict[str, list[dict]] = {}

    def place_order(self, sku: str, qty: int, stock: int) -> dict:
        trace_id = uuid.uuid4().hex
        parent_id = uuid.uuid4().hex
        child_id = uuid.uuid4().hex
        parent = {"id": parent_id, "name": "orders.create", "parent_id": None, "status": "ok"}
        child = {"id": child_id, "name": "inventory.reserve", "parent_id": parent_id, "status": "ok"}
        if stock < qty:
            child["status"] = "error"
            parent["status"] = "error"
            reserved = False
        else:
            reserved = True
        self.traces[trace_id] = [parent, child]
        return {"trace_id": trace_id, "reserved": reserved, "sku": sku, "qty": qty}

    def read(self, trace_id: str) -> dict:
        spans = self.traces.get(trace_id, [])
        return {"trace_id": trace_id, "spans": spans}
