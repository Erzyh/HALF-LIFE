"""Save a matplotlib figure with a few retries.

On this Windows machine the target PNG is sometimes still held open by a viewer or indexer for a
moment after it was last displayed, and open(path, "w+b") then fails with [Errno 22] Invalid
argument. Retrying after a short pause is enough.
"""
import time


def savefig(fig, path, tries=6, wait=2.0, **kw):
    last = None
    for _ in range(tries):
        try:
            fig.savefig(path, **kw)
            return path
        except OSError as e:
            last = e
            time.sleep(wait)
    raise last
