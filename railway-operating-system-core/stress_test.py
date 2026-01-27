import json
import time
from datetime import date, timedelta
from route_finder import RouteFinder
from config import DB_PATH
import sqlite3

finder = RouteFinder()
report = {
    'run_at': str(date.today()),
    'results': []
}

def run_midnight_connection_test():
    case = {'name': 'Midnight Connection', 'desc': '23:50 arrival -> 00:15 departure check'}
    # Deterministic search: look up candidate arrival/departure pairs from DB
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        SELECT a.train_no, a.arrival_time, b.train_no, b.departure_time
        FROM train_routes a
        JOIN train_routes b ON a.station_code = b.station_code
        WHERE a.arrival_time BETWEEN '23:30:00' AND '23:59:59'
          AND b.departure_time BETWEEN '00:00:00' AND '02:59:59'
        LIMIT 1
    """)
    row = cur.fetchone()
    con.close()

    if not row:
        # fallback to previous heuristic run
        res = finder.find_one_transfer_routes('NDLS', 'HWH', start_date=date(2026,1,26), max_results=50, verbose=True)
        skips = res.get('skips', []) if isinstance(res, dict) else []
        found = any((s.get('wait_minutes') is not None and s.get('wait_minutes') < 30) for s in skips)
        case['status'] = 'PASS' if found else 'WARN'
        return case

    # If we found a candidate pair, ensure the engine marks it as invalid (insufficient wait)
    _, arr_time, _, dep_time = row
    # Run a localized search: pick the station from DB that had this pair
    # We'll attempt the find_one_transfer_routes and ensure the specific pair is reported as skipped
    res = finder.find_one_transfer_routes('NDLS', 'HWH', start_date=date(2026,1,26), max_results=200, verbose=True)
    skips = res.get('skips', []) if isinstance(res, dict) else []
    matched = None
    for s in skips:
        if s.get('train2_departure') == dep_time and s.get('train1_no') == row[0]:
            matched = s
            break
    case['status'] = 'PASS' if matched else 'WARN'
    case['detail'] = matched
    return case


def run_leap_year_month_end_test():
    case = {'name': 'Leap/Month-End', 'desc': 'Routes spanning Feb->Mar across leap and non-leap years'}
    # run for 2024-02-28 (leap) and 2026-02-28 (non-leap)
    results = {}
    for y in (2024, 2026):
        d = date(y,2,28)
        out = finder.find_two_transfer_routes('NDLS','HWH', start_date=d, max_results=20, verbose=False)
        # check whether any route has legs with day >=3 (spans to March 1+)
        spans = False
        for r in out:
            legs = r.get('legs')
            if legs:
                days = [leg.get('day',1) for leg in legs]
                if max(days) >= 3:
                    spans = True
                    break
        results[str(y)] = spans
    case['status'] = 'PASS' if results.get('2024') or results.get('2026') else 'WARN'
    case['detail'] = results
    return case


def run_weekly_gap_test():
    case = {'name': 'Weekly Gap', 'desc': 'Train runs only on Monday should not be used on other days'}
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT train_no FROM train_running_days WHERE mon=1 AND tue=0 AND wed=0 AND thu=0 AND fri=0 AND sat=0 AND sun=0 LIMIT 1")
    row = cur.fetchone()
    if not row:
        case['status'] = 'SKIP'
        case['detail'] = 'No strictly Monday-only train found in DB'
        return case
    train_no = row[0]
    # pick a Tuesday after a known Monday (find next Tuesday)
    today = date.today()
    tuesday = today + timedelta(days=(1 - today.weekday()) % 7 + 1)
    runs = finder.train_runs_on(train_no, base_date=tuesday, day_offset=0)
    case['status'] = 'PASS' if not runs else 'FAIL'
    case['detail'] = {'train_no': train_no, 'tuesday': str(tuesday), 'runs': runs}
    con.close()
    return case


def run_long_haul_accumulator():
    case = {'name': 'Long-Haul Accumulator', 'desc': 'Verify cumulative day offsets across legs'}
    out = finder.find_three_transfer_routes('SBC','SRE', start_date=date(2026,1,26), max_results=20, verbose=False)
    ok = False
    for r in out:
        legs = r.get('legs', [])
        days = [leg.get('day', 1) for leg in legs]
        if days == sorted(days) and len(days) > 1:
            ok = True
            case['sample'] = {'legs_days': days}
            break
    case['status'] = 'PASS' if ok else 'WARN'
    return case


def run_circular_routing_prevention():
    case = {'name': 'Circular Routing Prevention', 'desc': 'Ensure junctions do not equal source/destination'}
    res = finder.find_one_transfer_routes('NDLS','HWH', start_date=date(2026,1,26), max_results=50, verbose=False)
    ok = True
    for r in res:
        junction = r.get('junction')
        if junction in ('NDLS','HWH'):
            ok = False
            case['problem'] = r
            break
    case['status'] = 'PASS' if ok else 'FAIL'
    return case


def run_search_exhaustion_performance():
    case = {'name': 'Search Exhaustion Performance', 'desc': 'NDLS->CSMT with max_results=500 timing'}
    start = time.time()
    _ = finder.find_all_routes('NDLS','CSMT', start_date=date(2026,1,26), max_transfers=3, max_results=500, verbose=False)
    duration = time.time() - start
    case['duration_seconds'] = round(duration, 3)
    case['status'] = 'PASS' if duration < 3.0 else 'WARN'
    return case


def run_missing_data_test():
    case = {'name': 'Missing Data', 'desc': 'train in trains_master but missing running_days should safely return False'}
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT t.train_no FROM trains_master t LEFT JOIN train_running_days r ON t.train_no = r.train_no WHERE r.train_no IS NULL LIMIT 1")
    row = cur.fetchone()
    if not row:
        case['status'] = 'SKIP'
        case['detail'] = 'No missing running_days entry found'
        return case
    train_no = row[0]
    try:
        runs = finder.train_runs_on(train_no, base_date=date(2026,1,26), day_offset=0)
        case['status'] = 'PASS' if runs is False else 'WARN'
        case['detail'] = {'train_no': train_no, 'runs': runs}
    except Exception as e:
        case['status'] = 'FAIL'
        case['detail'] = str(e)
    con.close()
    return case


def run_station_typo_test():
    case = {'name': 'Station Typos', 'desc': 'Input sanitization check for casing/whitespace'}
    a = finder.find_all_routes(' ndls ', ' hwh ', start_date=date(2026,1,26), max_transfers=1, max_results=10, verbose=False)
    b = finder.find_all_routes('NDLS','HWH', start_date=date(2026,1,26), max_transfers=1, max_results=10, verbose=False)
    # compare counts
    def count_routes(allr):
        return sum(len(allr.get(k, [])) for k in ('direct','one_transfer','two_transfer','three_transfer'))
    ca = count_routes(a)
    cb = count_routes(b)
    case['status'] = 'PASS' if ca == cb else 'FAIL'
    case['counts'] = {'typo_count': ca, 'normal_count': cb}
    return case


tests = [
    run_midnight_connection_test,
    run_leap_year_month_end_test,
    run_weekly_gap_test,
    run_long_haul_accumulator,
    run_circular_routing_prevention,
    run_search_exhaustion_performance,
    run_missing_data_test,
    run_station_typo_test
]

if __name__ == '__main__':
    for t in tests:
        try:
            r = t()
        except Exception as e:
            r = {'name': t.__name__, 'status': 'ERROR', 'detail': str(e)}
        print(f"[{r['status']}] {r['name']}: {r.get('desc','')}")
        report['results'].append(r)

    with open('stress_report.json','w',encoding='utf-8') as fh:
        json.dump(report, fh, indent=2, default=str)
    print('\nStress test run complete. Report written to stress_report.json')
