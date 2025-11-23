from .init import init

init()

# `readline` is not available on Windows.
try:
    import readline
except ImportError:
    pass

import requests_cache

from datetime import timedelta

from . import auth
from .repl import Repl


def main():
    try:
        backend = requests_cache.SQLiteCache(
            db_path=__package__,
            use_cache_dir=True,
        )
        client = auth.client(backend=backend, expire_after=timedelta(days=1))
    except KeyboardInterrupt:
        print("Interrupted")
        return
    Repl(client).run()
