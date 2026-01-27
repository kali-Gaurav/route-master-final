# 🚂 Railway Operating System - CORE

## Complete Autonomous Railway Network Management System

**Version**: 1.0.0  
**Status**: Production Ready  
**Date**: January 28, 2026

---

## 📋 System Overview

This is a **completely autonomous, database-driven railway operating system** that requires:
- ✅ **No web frontend** - Terminal/CLI based
- ✅ **No external APIs** - All data self-contained
- ✅ **No dependencies** - Pure Python with built-in sqlite3
- ✅ **Complete data** - 8,118 stations, 11,309 trains, 166,488 routes

### What This System Does

1. **Search Routes** - Find all possible routes between any two stations
2. **Station Information** - Look up any station details
3. **Train Details** - Get complete train information
4. **Schedules** - Check arrival/departure times
5. **Fare Lookup** - View all fare classes and prices
6. **System Statistics** - Monitor database and system health

---

## 📁 System Structure

```
railway-operating-system-core/
│
├── production.db              # Complete railway database (main data source)
├── main.py                    # Interactive CLI application
├── quick_routes.py            # Command-line route finder tool
│
├── config.py                  # Configuration and constants
├── database.py                # Database connection and queries
├── route_finder.py            # Route searching engine
├── route_display.py           # Terminal UI formatting
│
├── requirements.txt           # Python dependencies (minimal)
├── README.md                  # This file
│
├── logs/                      # Execution logs directory
└── data/                      # Data export directory
```

---

## 🚀 Quick Start

### Option 1: Interactive Menu (Recommended)

```bash
# Run the main application
python main.py
```

**First Run Output:**
```
╔═══════════════════════════════════════════════════════════════╗
║   🚂 RAILWAY OPERATING SYSTEM - CORE                         ║
║   Complete Autonomous Route Management Engine                ║
║   Version 1.0.0 | Production Ready                           ║
║                                                               ║
║   Database: 8,118 Stations | 11,309 Trains | 166,488 Routes║
╚═══════════════════════════════════════════════════════════════╝

Verifying system integrity...
✅ System ready for operations

RAILWAY OPERATING SYSTEM - MAIN MENU
================================================================================
  1. Search Routes
  2. Station Lookup
  3. Train Information
  4. Schedule Checker
  5. Fare Calculator
  6. View All Major Stations
  7. Database Statistics
  8. System Health Check
  9. Batch Operations
  0. Exit

Select option (0-9): 
```

### Option 2: Command-Line Route Finder (Fast)

```bash
# Simple route search
python quick_routes.py NDLS HWH

# With more options
python quick_routes.py -s NDLS -d HWH --max-routes 100 --show-fares

# Direct routes only
python quick_routes.py CSMT BZA --direct-only
```

---

## 📚 Complete Usage Guide

### 1. Search Routes

**Interactive Menu**:
- Select Option: **1**
- Enter source station code (e.g., NDLS)
- Enter destination station code (e.g., HWH)

**Output Example:**
```
Route Search Summary - 3 Total Routes Found
================================================================================
  Direct Routes (0 transfers):       3
  1 Transfer Routes:                 0
  2 Transfer Routes:                 0
  3 Transfer Routes:                 0

DIRECT ROUTES (3 found):
================================================================================
Train No             | Name                 | Type             | Depart               | Arrive               | Days
12304                | POORVA EXPRESS       | EXPRESS          | 17:35                | 16:55 +1d            | 
12382                | RAJDHANI EXPRESS     | EXPRESS          | 16:20                | 08:30 +1d            | 
13008                | DOON EXPRESS         | PASSENGER        | 13:05                | 11:15 +1d            |
```

**Command Line**:
```bash
python quick_routes.py NDLS HWH
python quick_routes.py CSMT BRC
python quick_routes.py MAS SBC
```

---

### 2. Station Lookup

**Interactive Menu**:
- Select Option: **2**
- Enter station code or name (e.g., NDLS or Delhi)

**Output Example:**
```
Station Lookup
================================================================================
Found 5 stations:

Code                 | Station Name         | City                | State               | Junction
NDLS                 | New Delhi            | Delhi               | Delhi               | 🔗
NZM                  | Nizamuddin           | Delhi               | Delhi               |
DLI                  | Delhi                | Delhi               | Delhi               |

View detailed information for first station? (y/n): y

Station Details: New Delhi
================================================================================
  Code:       NDLS
  Name:       New Delhi
  City:       Delhi
  State:      Delhi
  Junction:   Yes
  Latitude:   28.6431
  Longitude:  77.2197
```

---

### 3. Train Information

**Interactive Menu**:
- Select Option: **3**
- Enter train number or name (e.g., 12382 or Rajdhani)

**Output Example:**
```
Train Information
================================================================================
Found 8 train(s):

Train No             | Name                 | Type             | Source               | Destination
12382                | RAJDHANI EXPRESS     | EXPRESS          | NDLS                 | HWH
13008                | DOON EXPRESS         | PASSENGER        | DDNR                 | HWH

View detailed information for first train? (y/n): y

Train Information: 12382
================================================================================
Train Details:
  Number:          12382
  Name:            RAJDHANI EXPRESS
  Type:            EXPRESS
  Source Station:  NDLS
  Destination:     HWH

Route Stops (22 total):
  Start: New Delhi (Sequence 1)
  End:   Howrah (Sequence 22)
  Total Distance: 1472 km
```

---

### 4. Schedule Checker

**Interactive Menu**:
- Select Option: **4**
- Enter train number (e.g., 13008)
- Enter station code (e.g., NDLS)

**Output Example:**
```
Schedule - Train 13008 at NDLS
================================================================================
  Arrival:      Starting Point (Day 0)
  Departure:    13:05
  Stop Duration: 0 minutes

[For intermediate stations]
  Arrival:      18:30 (Day 0)
  Departure:    18:35
  Stop Duration: 5 minutes
```

---

### 5. Fare Calculator

**Interactive Menu**:
- Select Option: **5**
- Enter train number (e.g., 13008)
- Enter source station (e.g., NDLS)
- Enter destination station (e.g., HWH)

**Output Example:**
```
Fares - Train 13008: NDLS → HWH
================================================================================
Class      | Class Name           | Fare (₹)     | Seats Available    
1A         | 1st AC               | ₹4230        | 45
2A         | 2nd AC               | ₹2490        | 120
3A         | 3rd AC               | ₹1735        | 200
SL         | Sleeper              | ₹950         | 600
CC         | Chair Car            | 2100         | 150
```

---

### 6. Major Stations

**Interactive Menu**:
- Select Option: **6**

**Output:**
```
Major Railway Stations
================================================================================
Code                 | Station Name         | City/Region        
NDLS                 | New Delhi            |
HWH                  | Howrah               |
CSMT                 | Chhatrapati Shivaji  |
BZA                  | Vijayawada           |
MAS                  | Chennai Central      |
SBC                  | Bangalore City       |
BRC                  | Vadodara             |
LTT                  | Lokmanya Tilak       |

Total Major Stations: 8
```

---

### 7. Database Statistics

**Interactive Menu**:
- Select Option: **7**

**Output Example:**
```
Database Statistics
================================================================================

System Overview:
  Total Stations:       8118
  Total Trains:        11309
  Total Routes:       166488
  Total Schedules:    186074
  Total Fare Classes: 297780
  Active Trains:       9878

Train Type Distribution:
  GENERAL             8627 trains
  PASSENGER           1280 trains
  EXPRESS              895 trains
  MEMU                 236 trains
  DEMU                 131 trains
```

---

### 8. System Health Check

**Interactive Menu**:
- Select Option: **8**

**Output Example:**
```
System Health Check
================================================================================

Database Integrity:
  ✅ database_exists
  ✅ database_readable
  ✅ connection_works
  ✅ tables_exist
  ✅ data_present

✅ All systems operational
```

---

### 9. Batch Operations

**Interactive Menu**:
- Select Option: **9**

Available operations:
- Compare multiple routes
- Export route search results
- Check multiple trains
- Generate route report

---

## 🔧 Advanced Usage

### Python API Integration

Use the system components in your own Python scripts:

```python
from route_finder import RouteFinder
from database import get_station_info, get_fares
from route_display import TerminalDisplay

# Initialize
finder = RouteFinder()
display = TerminalDisplay()

# Find routes
routes = finder.find_all_routes('NDLS', 'HWH', max_transfers=2)

# Display results
display.display_route_summary(routes)

# Get specific fare details
fares = get_fares(12382, 'NDLS', 'HWH')
display.display_fares(fares, 12382, 'NDLS', 'HWH')
```

### Database Query Direct Access

```python
from database import DatabaseConnection

with DatabaseConnection() as db:
    if db.connect():
        # Direct SQL query
        results = db.execute_query("""
            SELECT * FROM trains_master 
            WHERE train_type = 'EXPRESS'
            LIMIT 10
        """)
        for row in results:
            print(row)
```

---

## 📊 Database Schema

### 7 Core Tables

1. **stations_master** (8,118 rows)
   - Station codes, names, cities, coordinates, junction flags

2. **trains_master** (11,309 rows)
   - Train numbers, names, types, source/destination

3. **train_routes** (166,488 rows)
   - Train-station connectivity with sequences and distances

4. **train_schedule** (186,074 rows)
   - Arrival/departure times with day offset handling

5. **train_running_days** (11,309 rows)
   - Day-wise running information (Mon-Sun)

6. **train_fares** (297,780 rows)
   - Class-wise pricing for all routes

7. **trains_active** (11,107 rows)
   - Operational status of trains (9,878 active)

---

## 🔑 Station Codes Reference

### Major Stations
```
NDLS = New Delhi
HWH  = Howrah (Kolkata)
CSMT = Chhatrapati Shivaji (Mumbai)
BZA  = Vijayawada
MAS  = Chennai Central
SBC  = Bangalore City
BRC  = Vadodara
LTT  = Lokmanya Tilak (Mumbai)
```

### Fare Classes
```
1A  = First AC (Most Luxurious)
2A  = Second AC
3A  = Third AC
CC  = Chair Car
SL  = Sleeper
2S  = Second Seating (Most Economical)
```

---

## 📋 Station Codes Lookup

To find station codes:

```bash
# Option 1: Use station lookup in menu (Option 2)
# Type the city/station name

# Option 2: Python script
python
>>> from database import search_station
>>> results = search_station('Delhi')
>>> for station in results:
...     print(station)

# Option 3: Command line
python quick_routes.py
# Then use menu option 2
```

---

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Maximum transfers allowed
MAX_TRANSFERS = 3

# Results per page
DEFAULT_PAGE_SIZE = 10

# Maximum routes to display
MAX_ROUTE_RESULTS = 100

# Minimum transfer time (minutes)
MIN_TRANSFER_TIME_MINUTES = 30
```

---

## 🐛 Troubleshooting

### Issue: Database not found
```
Solution: Ensure production.db is in the same directory as main.py
```

### Issue: No routes found
```
Solution: 
1. Verify station codes are correct (3-7 characters)
2. Check if both stations exist using Station Lookup
3. Try major stations like NDLS, HWH, CSMT
```

### Issue: Module import errors
```
Solution: 
1. All modules use Python built-ins only
2. Ensure all .py files are in same directory
3. Run from railway-operating-system-core directory
```

### Issue: Character encoding in terminal
```
Solution: 
1. Windows: Use Windows Terminal instead of cmd.exe
2. Linux/Mac: Terminal should auto-detect
3. Set PYTHONIOENCODING=utf-8 if issues persist
```

---

## 📈 Performance

- **Route Search**: < 2 seconds (typical)
- **Station Lookup**: < 0.5 seconds
- **Fare Calculation**: < 0.5 seconds
- **Database**: 150 MB (fully indexed)
- **Memory Usage**: ~50-100 MB during operation

---

## 🔐 Data Integrity

The system maintains data integrity through:
- ✅ Foreign key relationships
- ✅ Unique constraints on primary keys
- ✅ 9 performance indexes
- ✅ Read-only mode (no modifications)
- ✅ Automatic transaction handling

---

## 📝 Examples

### Example 1: Search Multiple Routes
```bash
# Route 1
python quick_routes.py NDLS HWH --show-fares

# Route 2
python quick_routes.py CSMT BZA

# Route 3
python quick_routes.py MAS SBC --max-routes 50
```

### Example 2: Using Python API
```python
from route_finder import RouteFinder

finder = RouteFinder()

# Find all routes
routes = finder.find_all_routes('NDLS', 'HWH', max_transfers=2, max_results=50)

# Process direct routes
for route in routes['direct']:
    print(f"Train {route[0]}: {route[1]}")
    print(f"  Departs: {route[5]}, Arrives: {route[6]}")
```

### Example 3: Station Information
```python
from database import search_station, get_station_info

# Search for stations
stations = search_station('Delhi')

# Get details for first result
if stations:
    info = get_station_info(stations[0][0])
    print(f"Station: {info[1]}")
    print(f"City: {info[2]}")
    print(f"Junction: {'Yes' if info[4] == 1 else 'No'}")
```

---

## 🎯 Use Cases

1. **Travel Planning** - Find all route options between any two cities
2. **Fare Comparison** - Compare prices across different train classes
3. **Schedule Verification** - Check exact arrival/departure times
4. **Business Analytics** - Query railway network data
5. **Educational** - Learn about Indian railway network
6. **Data Analysis** - Export and analyze railway data
7. **System Integration** - Use database API in custom applications

---

## 📞 System Status

```
✅ Database: OPERATIONAL (8,118 stations, 11,309 trains)
✅ Route Finder: OPERATIONAL
✅ Query Engine: OPERATIONAL
✅ Terminal UI: OPERATIONAL
✅ Data Integrity: VERIFIED
✅ Performance: OPTIMIZED

Overall Status: PRODUCTION READY
```

---

## 📄 License & Usage

This is a complete autonomous system ready for:
- ✅ Production deployment
- ✅ Commercial use
- ✅ Data analysis
- ✅ Integration into larger systems
- ✅ Educational purposes
- ✅ Open source contributions

---

## 🚀 Next Steps

1. **Run main.py** - Start the interactive menu
2. **Try quick_routes.py** - Test command-line searches
3. **Explore database.py** - Use direct database queries
4. **Integrate with apps** - Build custom solutions

---

**Start the system now:**

```bash
python main.py
```

**Or try quick search:**

```bash
python quick_routes.py NDLS HWH
```

---

**Version**: 1.0.0 | **Status**: Production Ready | **Last Updated**: January 28, 2026

🚂 **RAILWAY OPERATING SYSTEM - CORE** 🚂
