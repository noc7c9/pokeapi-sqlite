import json

from .db import Row


# Custom JSON encoder that allows encoding the custom sqlite Row objects
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Row):
            return dict(obj)
        return super().default(obj)


def json_dumps(obj, **kwargs):
    return json.dumps(obj, cls=JSONEncoder, indent=4, ensure_ascii=False, **kwargs)
