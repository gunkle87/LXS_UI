class Clipboard:
    """Canonical clipboard shell for the LXS UI."""
    def __init__(self):
        self._payload = None

    def set_payload(self, payload: dict | None):
        self._payload = None if payload is None else self._clone_payload(payload)

    def get_payload(self) -> dict | None:
        if self._payload is None:
            return None
        return self._clone_payload(self._payload)

    def has_payload(self) -> bool:
        return self._payload is not None

    @staticmethod
    def _clone_payload(payload: dict) -> dict:
        import copy

        return copy.deepcopy(payload)
