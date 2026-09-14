def distance(left: str, right: str) -> int:
    if abs(len(left) - len(right)) > 1:
        return 2
    previous = list(range(len(right) + 1))
    for i, char in enumerate(left, start=1):
        current = [i]
        for j, other in enumerate(right, start=1):
            cost = 0 if char == other else 1
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + cost))
        previous = current
    return previous[-1]


class Catalog:
    def __init__(self):
        self.items: list[dict] = []

    def add(self, name: str, synonyms: list[str]) -> dict:
        item = {"name": name, "terms": [name.lower(), *[word.lower() for word in synonyms]]}
        self.items.append(item)
        return {"name": name, "synonyms": synonyms}

    def search(self, query: str) -> list[str]:
        needle = query.strip().lower()
        if not needle:
            return []
        found = []
        for item in self.items:
            if any(self._hit(needle, term) for term in item["terms"]):
                found.append(item["name"])
        return found

    def _hit(self, needle: str, term: str) -> bool:
        if needle in term or term.startswith(needle):
            return True
        return len(needle) >= 4 and distance(needle, term) <= 1
