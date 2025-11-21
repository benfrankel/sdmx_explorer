from .init import init

init()

# `readline` is not available on Windows.
try:
    import readline
except ImportError:
    pass

import requests_cache
import sdmx

from datetime import timedelta

from .repl import Repl


def main():
    backend = requests_cache.SQLiteCache(
        db_path=__package__,
        use_cache_dir=True,
    )
    client = sdmx.Client(backend=backend, expire_after=timedelta(days=1))
    Repl(client).run()


if __name__ == "__main__":
    main()
