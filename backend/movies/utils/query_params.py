class RequestParams:
    """Lightweight helper for typed query param extraction."""

    def __init__(self, query_params):
        self.query_params = query_params

    @staticmethod
    def to_int(value, default=1):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def to_float(value, default=None):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def page(self, key="page", default=1, max_page=500):
        page = self.to_int(self.query_params.get(key, default), default=default)
        if page is None or page < 1:
            return default
        return min(page, max_page)

    def text(self, key, default=""):
        return (self.query_params.get(key, default) or "").strip()

    def int_or_none(self, key):
        return self.to_int(self.query_params.get(key), default=None)

    def float_or_none(self, key):
        return self.to_float(self.query_params.get(key), default=None)
