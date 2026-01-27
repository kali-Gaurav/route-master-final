import sqlite3
import datetime
import pytest
from route_finder import RouteFinder
from config import DB_PATH


def test_calculate_transfer_waiting_same_day():
    waiting_minutes, day_offset, waiting_str, transfer_info, valid = RouteFinder.calculate_transfer_waiting('10:00:00', '11:00:00')
    assert waiting_minutes == 60
    assert day_offset == 0
    assert valid is True


def test_calculate_transfer_waiting_next_day():
    waiting_minutes, day_offset, waiting_str, transfer_info, valid = RouteFinder.calculate_transfer_waiting('23:30:00', '01:00:00')
    assert waiting_minutes == 90
    assert day_offset == 1
    assert valid is True


def test_calculate_transfer_waiting_insufficient():
    waiting_minutes, day_offset, waiting_str, transfer_info, valid = RouteFinder.calculate_transfer_waiting('10:00:00', '10:20:00')
    assert waiting_minutes == 20
    assert valid is False


@pytest.mark.skipif(not DB_PATH, reason="No DB_PATH configured")
def test_train_runs_on_matches_db():
    # Connect directly to DB to find a train that runs on Monday (MON=1)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("SELECT train_no FROM train_running_days WHERE mon = 1 LIMIT 1")
    row = cur.fetchone()
    if not row:
        pytest.skip("No train with MON=1 found in train_running_days")

    train_no = row[0]
    # Find a base_date that is a Monday
    today = datetime.date.today()
    days_ahead = (0 - today.weekday()) % 7
    base_monday = today + datetime.timedelta(days=days_ahead)

    finder = RouteFinder()
    runs = finder.train_runs_on(train_no, base_date=base_monday, day_offset=0)
    assert runs is True

    # Also verify a train that does NOT run on Monday (if exists)
    cur.execute("SELECT train_no FROM train_running_days WHERE mon = 0 LIMIT 1")
    row2 = cur.fetchone()
    if row2:
        train_no2 = row2[0]
        runs2 = finder.train_runs_on(train_no2, base_date=base_monday, day_offset=0)
        assert runs2 is False

    con.close()
