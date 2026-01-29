import os
import json
from datetime import datetime
from route_finder import RouteFinder

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'routes')
os.makedirs(os.path.abspath(OUT_DIR), exist_ok=True)


def run_generate_routes(payload):
    """Run generate-routes given a payload dict and return output path and summary."""
    source = payload.get('source')
    dest = payload.get('dest')
    date_str = payload.get('date')
    max_transfers = int(payload.get('max_transfers', 3))
    max_results = int(payload.get('max_results', 100))
    sort_by = payload.get('sort_by')

    if not source or not dest:
        raise ValueError('source and dest required')

    start_date = None
    if date_str:
        try:
            start_date = datetime.fromisoformat(date_str).date()
        except Exception as e:
            import logging
            logging.warning(f"Error parsing date: {e}")
            start_date = None

    finder = RouteFinder()
    results = finder.find_all_routes(source, dest, start_date=start_date, max_transfers=max_transfers, max_results=max_results, sort_by=sort_by)

    fname = f"{source}_{dest}_{date_str or 'any'}.json"
    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'routes', fname))
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    summary = {
        'source': source,
        'dest': dest,
        'date': date_str,
        'file': out_path,
        'counts': {k: len(v) for k, v in results.items() if isinstance(v, list)}
    }
    return out_path, summary
