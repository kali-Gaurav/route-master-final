from database import verify_database, DatabaseConnection


def run_db_check():
    """Run basic DB checks and an integrity check PRAGMA.

    Returns dict with checks and integrity output.
    """
    result = {}
    try:
        checks = verify_database()
        result['verify'] = checks

        with DatabaseConnection() as db:
            if not db.connect():
                result['integrity'] = 'unable to connect'
                return result
            rows = db.execute_query("PRAGMA integrity_check;")
            # pragma returns rows like [('ok',)] or multiple problems
            integrity = [r[0] for r in rows] if rows else []
            result['integrity'] = integrity
    except Exception as e:
        result['error'] = str(e)

    return result
