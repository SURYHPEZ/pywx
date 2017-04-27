# coding: utf-8

from functools import partial

from requests.compat import json


json.dumps = partial(json.dumps, ensure_ascii=False)
