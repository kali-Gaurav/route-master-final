# ===============================================
# RAILWAY OPERATING SYSTEM - CORE CONFIGURATION
# ===============================================
# Complete standalone configuration for the entire system

import os
from datetime import datetime

# ========== DATABASE CONFIGURATION ==========
DB_PATH = os.path.join(os.path.dirname(__file__), 'production.db')
DB_TIMEOUT = 10.0
DB_CHECK_SAME_THREAD = False

# ========== SYSTEM PATHS ==========
LOG_PATH = os.path.join(os.path.dirname(__file__), 'logs')
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')

# Create directories if not exist
os.makedirs(LOG_PATH, exist_ok=True)
os.makedirs(DATA_PATH, exist_ok=True)

# ========== LOGGING CONFIGURATION ==========
LOG_FILE = os.path.join(LOG_PATH, 'railway_system.log')
DEBUG_MODE = False

# ========== RAILWAY SYSTEM CONSTANTS ==========

# Train types available
TRAIN_TYPES = ['GENERAL', 'PASSENGER', 'EXPRESS', 'MEMU', 'DEMU', 'OTHERS']

# Fare classes
FARE_CLASSES = {
    '1A': '1st AC',
    '2A': '2nd AC',
    '3A': '3rd AC',
    'SL': 'Sleeper',
    'CC': 'Chair Car',
    '2S': '2nd Seating'
}

# Days of week
DAYS_OF_WEEK = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

# ========== ROUTE SEARCH CONFIGURATION ==========
MAX_TRANSFERS = 3
DEFAULT_PAGE_SIZE = 10
MAX_ROUTE_RESULTS = 100

# ========== MAJOR STATIONS ==========
MAJOR_STATIONS = {
    'NDLS': 'New Delhi',
    'HWH': 'Howrah',
    'CSMT': 'Chhatrapati Shivaji (Mumbai)',
    'BZA': 'Vijayawada',
    'MAS': 'Chennai Central',
    'SBC': 'Bangalore City',
    'BRC': 'Vadodara',
    'LTT': 'Lokmanya Tilak (Mumbai)'
}

# ========== DISPLAY CONFIGURATION ==========
# Terminal colors and formatting
COLORS = {
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'RED': '\033[91m',
    'BLUE': '\033[94m',
    'CYAN': '\033[96m',
    'WHITE': '\033[97m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m',
    'RESET': '\033[0m'
}

TABLE_WIDTH = 150
MAX_ROUTE_DISPLAY = 20  # Max routes to show without pagination

# ========== PERFORMANCE CONFIGURATION ==========
QUERY_TIMEOUT = 30
ROUTE_SEARCH_TIMEOUT = 45
CACHE_ENABLED = False

# ========== VALIDATION RULES ==========
MIN_STATION_CODE_LENGTH = 3
MAX_STATION_CODE_LENGTH = 7
STATION_CODE_UPPERCASE = True

# ========== TRANSFER CONFIGURATION ==========
MIN_TRANSFER_TIME_MINUTES = 30  # Minimum time between connecting trains
PREFER_SAME_STATION_TRANSFER = True
TRANSFER_SEARCH_DEPTH = 3

# ========== OUTPUT FORMATTING ==========
DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# ========== APPLICATION TITLE ==========
APP_TITLE = """
╔═══════════════════════════════════════════════════════════════╗
║   🚂 RAILWAY OPERATING SYSTEM - CORE                         ║
║   Complete Autonomous Route Management Engine                ║
║   Version 1.0.0 | Production Ready                           ║
║                                                               ║
║   Database: 8,118 Stations | 11,309 Trains | 166,488 Routes║
╚═══════════════════════════════════════════════════════════════╝
"""

# ========== SYSTEM INFORMATION ==========
SYSTEM_VERSION = '1.0.0'
SYSTEM_AUTHOR = 'Railway Intelligence Division'
SYSTEM_DATE_CREATED = '2026-01-28'
SYSTEM_STATUS = 'PRODUCTION'

DATABASE_STATS = {
    'stations': 8118,
    'trains': 11309,
    'routes': 166488,
    'schedules': 186074,
    'fares': 297780,
    'active_trains': 9878,
    'running_trains': 9878
}

# ========== MENU OPTIONS ==========
MAIN_MENU_OPTIONS = [
    '1. Search Routes',
    '2. Station Lookup',
    '3. Train Information',
    '4. Schedule Checker',
    '5. Fare Calculator',
    '6. View All Major Stations',
    '7. Database Statistics',
    '8. System Health Check',
    '9. Batch Operations',
    '0. Exit'
]

# ========== MESSAGES ==========
MESSAGES = {
    'welcome': 'Welcome to Railway Operating System Core',
    'goodbye': 'Thank you for using Railway Operating System. Goodbye!',
    'invalid_choice': 'Invalid choice. Please try again.',
    'loading': 'Loading...',
    'processing': 'Processing your request...',
    'error': 'An error occurred',
    'success': 'Operation completed successfully'
}

# ========== SYSTEM CHECKS ==========
def verify_config():
    """Verify all configuration paths and settings"""
    checks = {
        'database_exists': os.path.exists(DB_PATH),
        'log_dir_writable': os.access(LOG_PATH, os.W_OK),
        'data_dir_writable': os.access(DATA_PATH, os.W_OK),
    }
    return all(checks.values()), checks

if __name__ == '__main__':
    print(APP_TITLE)
    is_valid, checks = verify_config()
    print(f"\nConfiguration Status: {'✅ VALID' if is_valid else '❌ INVALID'}")
    for check, status in checks.items():
        print(f"  {check}: {'✅' if status else '❌'}")
