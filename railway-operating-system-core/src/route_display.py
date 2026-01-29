# ===============================================
# TERMINAL UI AND DISPLAY FORMATTING
# ===============================================
# Beautiful terminal output for all queries

from config import COLORS, FARE_CLASSES, TABLE_WIDTH
from datetime import datetime

class TerminalDisplay:
    """Handles all terminal output formatting"""
    
    @staticmethod
    def print_header(text):
        """Print formatted header"""
        print(f"\n{COLORS['BOLD']}{COLORS['CYAN']}")
        print("=" * 80)
        print(f"  {text}")
        print("=" * 80)
        print(COLORS['RESET'])
    
    @staticmethod
    def print_success(text):
        """Print success message"""
        print(f"{COLORS['GREEN']}✅ {text}{COLORS['RESET']}")
    
    @staticmethod
    def print_error(text):
        """Print error message"""
        print(f"{COLORS['RED']}❌ {text}{COLORS['RESET']}")
    
    @staticmethod
    def print_info(text):
        """Print info message"""
        print(f"{COLORS['BLUE']}ℹ️  {text}{COLORS['RESET']}")
    
    @staticmethod
    def print_warning(text):
        """Print warning message"""
        print(f"{COLORS['YELLOW']}⚠️  {text}{COLORS['RESET']}")
    
    @staticmethod
    def print_table_header(*columns):
        """Print formatted table header"""
        header = " | ".join(str(col).ljust(20) for col in columns)
        print(f"{COLORS['BOLD']}{COLORS['CYAN']}{header}{COLORS['RESET']}")
        print("-" * 100)
    
    @staticmethod
    def print_table_row(*values):
        """Print formatted table row"""
        row = " | ".join(str(val).ljust(20) for val in values)
        print(row)
    
    @staticmethod
    def display_stations(stations, show_details=False):
        """Display stations in formatted table"""
        if not stations:
            TerminalDisplay.print_error("No stations found")
            return
        
        TerminalDisplay.print_header(f"Stations Found: {len(stations)}")
        
        if show_details:
            TerminalDisplay.print_table_header("Code", "Name", "City", "State", "Junction")
            for station in stations:
                junction_symbol = "🔗" if station[4] == 1 else " "
                TerminalDisplay.print_table_row(
                    station[0],
                    station[1][:20],
                    station[2][:15],
                    station[3][:10],
                    junction_symbol
                )
        else:
            TerminalDisplay.print_table_header("Code", "Station Name", "City")
            for station in stations:
                TerminalDisplay.print_table_row(
                    station[0],
                    station[1][:30],
                    station[2][:20]
                )
    
    @staticmethod
    def display_direct_routes(routes, source, destination):
        """Display direct routes in formatted table"""
        if not routes:
            TerminalDisplay.print_error(f"No direct routes found from {source} to {destination}")
            return
        
        TerminalDisplay.print_header(f"Direct Routes: {source} → {destination} ({len(routes)} found)")
        
        for idx, route in enumerate(routes[:20], 1):
            train_no = route['train_no'] if isinstance(route, dict) else route[0]
            train_name = route['train_name'] if isinstance(route, dict) else route[1]
            train_type = route['train_type'] if isinstance(route, dict) else route[2]
            departure = route['departure'] if isinstance(route, dict) else route[5]
            arrival = route['arrival'] if isinstance(route, dict) else route[6]
            distance = route.get('distance', 0) if isinstance(route, dict) else 0
            time_str = route.get('time_str', 'N/A') if isinstance(route, dict) else 'N/A'
            day_diff = route.get('day_diff', 0) if isinstance(route, dict) else 0
            
            arrival_display = f"{arrival} +{int(day_diff)}d" if day_diff else arrival
            
            print(f"\n{idx}. {COLORS['BOLD']}{train_no} | {train_name[:20]:<20}{COLORS['RESET']}")
            print(f"   Type: {train_type:<15} | Distance: {distance} km | Duration: {time_str}")
            print(f"   Depart: {departure} → Arrive: {arrival_display}")
    
    @staticmethod
    def display_train_info(train_info):
        """Display detailed train information"""
        if not train_info:
            TerminalDisplay.print_error("Train not found")
            return
        
        TerminalDisplay.print_header(f"Train Information: {train_info[0]}")
        
        print(f"{COLORS['BOLD']}Train Details:{COLORS['RESET']}")
        print(f"  Number:          {train_info[0]}")
        print(f"  Name:            {train_info[1]}")
        print(f"  Type:            {train_info[2]}")
        print(f"  Source Station:  {train_info[3]}")
        print(f"  Destination:     {train_info[4]}")
    
    @staticmethod
    def display_schedule(schedule, train_no, station_code):
        """Display schedule for train at station"""
        if not schedule:
            TerminalDisplay.print_error(f"No schedule found for Train {train_no} at {station_code}")
            return
        
        TerminalDisplay.print_header(f"Schedule - Train {train_no} at {station_code}")
        
        for stop in schedule:
            arrival = stop[0] if stop[0] else "Starting Point"
            departure = stop[1] if stop[1] else "Final Stop"
            day_offset = stop[2] if len(stop) > 2 else 0
            stop_duration = stop[3] if len(stop) > 3 else 0
            
            print(f"  Arrival:      {arrival} (Day {day_offset})")
            print(f"  Departure:    {departure}")
            if stop_duration > 0:
                print(f"  Stop Duration: {stop_duration} minutes")
    
    @staticmethod
    def display_fares(fares, train_no, source, destination):
        """Display fare information"""
        if not fares:
            TerminalDisplay.print_error(f"No fares found for Train {train_no} ({source} → {destination})")
            return
        
        TerminalDisplay.print_header(f"Fares - Train {train_no}: {source} → {destination}")
        
        print(f"\n{COLORS['BOLD']}{'Class':<10} {'Class Name':<20} {'Fare (₹)':<12} {'Seats Available':<15}{COLORS['RESET']}")
        print("-" * 60)
        
        for fare in fares:
            class_code = fare[0]
            class_name = FARE_CLASSES.get(class_code, "Unknown")
            price = fare[1]
            seats = fare[2] if len(fare) > 2 else "N/A"
            
            print(f"{class_code:<10} {class_name:<20} ₹{price:<11} {seats:<15}")
    
    @staticmethod
    def display_running_days(running_days, train_no):
        """Display running days for train"""
        TerminalDisplay.print_header(f"Running Days - Train {train_no}")
        
        days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
        running = []
        not_running = []
        
        for i, day in enumerate(days):
            if i < len(running_days) and running_days[i] == 1:
                running.append(day)
            else:
                not_running.append(day)
        
        print(f"\n{COLORS['GREEN']}✓ Runs On: {', '.join(running)}{COLORS['RESET']}")
        if not_running:
            print(f"{COLORS['RED']}✗ Does Not Run: {', '.join(not_running)}{COLORS['RESET']}")
    
    @staticmethod
    def display_database_stats(stats):
        """Display database statistics"""
        TerminalDisplay.print_header("Database Statistics")
        
        print(f"\n{COLORS['BOLD']}System Overview:{COLORS['RESET']}")
        print(f"  Total Stations:     {stats.get('total_stations', 'N/A'):>10}")
        print(f"  Total Trains:       {stats.get('total_trains', 'N/A'):>10}")
        print(f"  Total Routes:       {stats.get('total_routes', 'N/A'):>10}")
        print(f"  Total Schedules:    {stats.get('total_schedules', 'N/A'):>10}")
        print(f"  Total Fare Classes: {stats.get('total_fares', 'N/A'):>10}")
        print(f"  Active Trains:      {stats.get('active_trains', 'N/A'):>10}")
        
        if 'train_types' in stats:
            print(f"\n{COLORS['BOLD']}Train Type Distribution:{COLORS['RESET']}")
            for train_type, count in sorted(stats['train_types'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {train_type:<15} {count:>6} trains")
    
    @staticmethod
    def display_route_summary(routes):
        """Display route search summary"""
        if not routes:
            TerminalDisplay.print_error("No routes found")
            return
        # Compute total across specific route categories only
        total = len(routes.get('direct', [])) + len(routes.get('one_transfer', [])) + len(routes.get('two_transfer', [])) + len(routes.get('three_transfer', []))

        TerminalDisplay.print_header(f"Route Search Summary - {total} Total Routes Found")
        
        print(f"\n{COLORS['BOLD']}Routes by Category:{COLORS['RESET']}")
        print(f"  {COLORS['GREEN']}Direct Routes (0 transfers):       {len(routes.get('direct', [])):>4}{COLORS['RESET']}")
        print(f"  {COLORS['BLUE']}1 Transfer Routes:                {len(routes.get('one_transfer', [])):>4}{COLORS['RESET']}")
        print(f"  {COLORS['CYAN']}2 Transfer Routes:                {len(routes.get('two_transfer', [])):>4}{COLORS['RESET']}")
        print(f"  {COLORS['YELLOW']}3 Transfer Routes:                {len(routes.get('three_transfer', [])):>4}{COLORS['RESET']}")
    
    @staticmethod
    def display_one_transfer_routes(routes, source, destination):
        """Display 1-transfer routes"""
        if not routes:
            return
        
        TerminalDisplay.print_header(f"1 Transfer Routes: {source} → {destination} ({len(routes)} found)")
        
        for idx, route in enumerate(routes[:20], 1):
            leg1 = route['leg1']
            leg2 = route['leg2']
            junction = route['junction']
            total_dist = route.get('total_distance', 0)
            total_time = route.get('total_time_str', 'N/A')
            waiting_time = route.get('waiting_time_str', '0h 0m')
            transfer_info = route.get('transfer_info', 'Transfer')
            leg2_day = leg2.get('day', 1)
            day_indicator = f"+{leg2_day}d" if leg2_day > 1 else ""
            
            print(f"\n{idx}. {COLORS['BOLD']}{source} → {junction} → {destination}{COLORS['RESET']}")
            print(f"   {'Total Distance: ' + str(total_dist) + ' km':40} | {'Total Time: ' + total_time} (Wait: {waiting_time})")
            
            print(f"   Leg 1: Train {leg1['train_no']} | {leg1['train_name'][:20]:<20} | {leg1['distance']} km | {leg1['time_str']}")
            print(f"          {leg1['departure']} → {leg1['arrival']}")
            
            print(f"   Transfer at {junction}: {transfer_info}")
            
            print(f"   Leg 2: Train {leg2['train_no']} | {leg2['train_name'][:20]:<20} | {leg2['distance']} km | {leg2['time_str']}")
            print(f"          {leg2['departure']} {day_indicator} → {leg2['arrival']}")

    
    @staticmethod
    def display_two_transfer_routes(routes, source, destination):
        """Display 2-transfer routes"""
        if not routes:
            return
        
        TerminalDisplay.print_header(f"2 Transfer Routes: {source} → {destination} ({len(routes)} found)")
        
        for idx, route in enumerate(routes[:15], 1):
            legs = route['legs']
            total_dist = route.get('total_distance', 0)
            total_time = route.get('total_time_str', 'N/A')
            waiting_times = route.get('waiting_times', ['0h 0m', '0h 0m'])
            
            print(f"\n{idx}. {COLORS['BOLD']}{legs[0]['from']} → {legs[1]['from']} → {legs[2]['from']} → {destination}{COLORS['RESET']}")
            print(f"   {'Total Distance: ' + str(total_dist) + ' km':40} | {'Total Time: ' + total_time} (Waits: {' + '.join(waiting_times)})")
            
            for leg_idx, leg in enumerate(legs, 1):
                day_indicator = f"+{leg.get('day', 1)}d" if leg.get('day', 1) > 1 else ""
                print(f"   Leg {leg_idx}: Train {leg['train_no']} | {leg['train_name'][:15]:<15} | {leg['distance']} km | {leg['time_str']}")
                print(f"          {leg['departure']} {day_indicator} → {leg['arrival']}")
    
    @staticmethod
    def display_three_transfer_routes(routes, source, destination):
        """Display 3-transfer routes"""
        if not routes:
            return
        
        TerminalDisplay.print_header(f"3 Transfer Routes: {source} → {destination} ({len(routes)} found)")
        
        for idx, route in enumerate(routes[:10], 1):
            legs = route['legs']
            total_dist = route.get('total_distance', 0)
            total_time = route.get('total_time_str', 'N/A')
            waiting_times = route.get('waiting_times', ['0h 0m', '0h 0m', '0h 0m'])
            
            print(f"\n{idx}. {COLORS['BOLD']}{legs[0]['from']} → {legs[1]['from']} → {legs[2]['from']} → {legs[3]['from']} → {destination}{COLORS['RESET']}")
            print(f"   {'Total Distance: ' + str(total_dist) + ' km':40} | {'Total Time: ' + total_time} (Waits: {' + '.join(waiting_times)})")
            
            for leg_idx, leg in enumerate(legs, 1):
                day_indicator = f"+{leg.get('day', 1)}d" if leg.get('day', 1) > 1 else ""
                print(f"   Leg {leg_idx}: Train {leg['train_no']} | {leg['train_name'][:15]:<15} | {leg['distance']} km | {leg['time_str']}")
                print(f"          {leg['departure']} {day_indicator} → {leg['arrival']}")
    
    @staticmethod
    def display_menu(title, options):
        """Display menu"""
        TerminalDisplay.print_header(title)
        for option in options:
            print(f"  {option}")
        print()

if __name__ == '__main__':
    print("Display Module Test")
    display = TerminalDisplay()
    
    # Test display methods
    display.print_header("Test Header")
    display.print_success("This is a success message")
    display.print_error("This is an error message")
    display.print_info("This is an info message")
    display.print_warning("This is a warning message")
    
    print("\nTable Example:")
    display.print_table_header("Code", "Name", "City", "State")
    display.print_table_row("NDLS", "New Delhi", "Delhi", "Delhi")
    display.print_table_row("HWH", "Howrah", "Kolkata", "West Bengal")
