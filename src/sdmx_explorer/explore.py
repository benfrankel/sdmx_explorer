import requests_cache
import sdmx

from datetime import timedelta

from .repl import SdmxRepl


def main():
    try:
        _main()
    except KeyboardInterrupt:
        print("Interrupted")
        return 130


def _main():
    SdmxRepl(
        client=sdmx.Client(
            backend=requests_cache.SQLiteCache(
                db_path=__package__,
                use_cache_dir=True,
            ),
            expire_after=timedelta(days=1),
        )
    ).run()
