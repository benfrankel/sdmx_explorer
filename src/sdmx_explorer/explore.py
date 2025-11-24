import requests_cache
import sdmx

from datetime import timedelta

from .repl import SdmxRepl


def main():
    try:
        repl = SdmxRepl(
            client=sdmx.Client(
                backend=requests_cache.SQLiteCache(
                    db_path=__package__,
                    use_cache_dir=True,
                ),
                expire_after=timedelta(days=1),
            )
        )
    except KeyboardInterrupt:
        print("Interrupted")
    else:
        repl.run()
