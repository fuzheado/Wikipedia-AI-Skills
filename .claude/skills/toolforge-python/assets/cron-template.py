# Cron Script Template for Toolforge

Copy this file, customize the `run()` function, and schedule with:

```bash
become my-tool
toolforge jobs run \
    --image tool-my-tool/tool-my-tool:latest \
    --command "python3 /data/project/my-tool/cron/script.py" \
    --schedule "0 * * * *" \
    my-cron-job
```

For traditional (non-Build Service) backends:

```bash
become my-tool
toolforge-jobs run cron --command \
    '/data/project/my-tool/venv/bin/python3 /data/project/my-tool/cron/script.py' \
    --schedule "0 * * * *" \
    my-cron-job
```

```python
#!/usr/bin/env python3
"""Scheduled maintenance script for Toolforge.

Usage:
    python3 cron/script.py           # Run once (for testing)
    python3 cron/script.py --dry-run # Preview actions without changes
"""

import argparse
import logging
import os
import sys
import time
import traceback
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
LOG_LEVEL = logging.INFO

# NFS-safe: write temp files locally, then atomically move to NFS
TMP_DIR = os.environ.get("TMPDIR", "/tmp")

# Tool name for logging context
TOOL_NAME = os.environ.get("TOOL_NAME", os.path.basename(os.getcwd()))


def setup_logging() -> logging.Logger:
    """Configure stdout logging.

    Toolforge captures stdout/stderr into Kubernetes logs (Build Service) or
    keeps them in job output files (traditional). Always log to stdout.
    """
    logger = logging.getLogger(TOOL_NAME)
    logger.setLevel(LOG_LEVEL)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)

    return logger


# ── NFS-Safe Helpers ───────────────────────────────────────────────────────

def atomic_write(path: str, content: str) -> None:
    """Write content atomically: tmp file → rename.

    NFS can leave partial files visible if a write is interrupted.
    Writing to /tmp first, then os.rename() (atomic on same filesystem)
    prevents partial reads.
    """
    import tempfile

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file in same directory (ensures atomic rename works)
    with tempfile.NamedTemporaryFile(
        mode="w",
        dir=str(target.parent),
        prefix=f".tmp_{target.name}_",
        delete=False,
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    os.rename(tmp_path, path)


def with_retry(fn, *args, max_retries=3, backoff=2.0, **kwargs):
    """Call fn with exponential backoff on failure.

    Toolforge jobs may encounter transient NFS stalls or API rate limits.
    Retry with backoff before failing.
    """
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries:
                wait = backoff ** attempt
                logging.warning(
                    "Attempt %d/%d failed (%s). Retrying in %.1fs...",
                    attempt, max_retries, exc, wait,
                )
                time.sleep(wait)
            else:
                logging.error(
                    "All %d attempts failed. Last error: %s", max_retries, exc
                )

    raise last_exc  # type: ignore[misc]


# ── Core Logic ─────────────────────────────────────────────────────────────

def run(logger: logging.Logger, dry_run: bool = False) -> None:
    """Main logic — customize for your use case.

    Common Toolforge cron patterns:
        - Cache cleanup: remove stale cached files
        - Data sync: fetch fresh data from Wikimedia APIs, write to NFS
        - Batch processing: process a queue of pending items
        - Health check: ping external monitoring, log stats
        - Database maintenance: VACUUM, reindex, prune old rows
    """
    logger.info("Starting scheduled task (dry_run=%s, tool=%s)", dry_run, TOOL_NAME)

    # ── Example: cache cleanup ──
    cache_dir = Path(os.environ.get("CACHE_DIR", "/data/project/my-tool/cache"))
    if cache_dir.exists():
        cutoff = time.time() - (24 * 3600)  # 24 hours
        cleaned = 0
        for entry in cache_dir.iterdir():
            if entry.is_file() and entry.stat().st_mtime < cutoff:
                logger.info("Removing stale cache: %s", entry.name)
                if not dry_run:
                    entry.unlink()
                cleaned += 1
        logger.info("Cache cleanup: %d stale files %s",
                     cleaned, "(dry run)" if dry_run else "removed")
    else:
        logger.info("Cache dir %s does not exist — skipping", cache_dir)

    # ── Your custom logic here ─────────────────────────────────────────

    logger.info("Scheduled task complete.")


# ── Entry Point ────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"{TOOL_NAME} — scheduled maintenance script"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview actions without making changes",
    )
    args = parser.parse_args()

    logger = setup_logging()

    try:
        run(logger, dry_run=args.dry_run)
    except Exception:
        logger.critical("Fatal error:\n%s", traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
```
