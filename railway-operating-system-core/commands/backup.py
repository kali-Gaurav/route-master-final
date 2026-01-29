import os
import shutil
from datetime import datetime
from config import DB_PATH


def backup_db(dest_dir='backups', compress=False):
    """Create a timestamped backup copy of production DB in dest_dir.

    Returns backup path on success, None on failure.
    """
    try:
        os.makedirs(dest_dir, exist_ok=True)
        ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        base_name = f"production_{ts}.db"
        out_path = os.path.join(dest_dir, base_name)
        shutil.copy2(DB_PATH, out_path)

        if compress:
            import gzip
            gz_path = out_path + '.gz'
            with open(out_path, 'rb') as f_in, gzip.open(gz_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            try:
                os.remove(out_path)
            except Exception as e:
                import logging
                logging.warning(f"Could not remove uncompressed backup: {e}")
                pass
            return gz_path

        return out_path
    except Exception as e:
        return None
