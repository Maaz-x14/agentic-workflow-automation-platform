import json


def to_json(obj):
    return json.loads(json.dumps(obj, default=str))
