import os
import shutil
from datetime import datetime
from config import DB_PATH


def restore_db(src_path, dest_db=None, force=False, dry_run=False):
    """Restore a DB from `src_path` to the configured `DB_PATH` (or `dest_db`).

    If `dry_run` is True, perform validations only and return the would-be dest path.
    If `force` is False and dest exists, create a timestamped backup before overwrite.
    Returns the path restored to on success, None on failure.
    """
    try:
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"source backup not found: {src_path}")

        dest = dest_db or DB_PATH
        dest_dir = os.path.dirname(dest)
        if not os.path.isdir(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)

        if dry_run:
            # basic checks
            if not os.path.isfile(src_path):
                return None
            return dest

        # if destination exists and not forced, snapshot it
        if os.path.exists(dest) and not force:
            ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            backup_path = f"{dest}.pre_restore.{ts}.bak"
            shutil.copy2(dest, backup_path)

        shutil.copy2(src_path, dest)
        return dest
    except Exception:
        return None
