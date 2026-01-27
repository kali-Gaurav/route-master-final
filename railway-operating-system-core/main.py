# ===============================================
# MAIN APPLICATION - INTERACTIVE CLI MENU SYSTEM
# ===============================================
# Complete autonomous railway system entry point

import os
import sys
from datetime import datetime
from config import (
    APP_TITLE, MAIN_MENU_OPTIONS, MESSAGES, COLORS,
    MAJOR_STATIONS, DATABASE_STATS
)
from database import (
    get_all_stations, search_station, get_station_info,
    get_all_trains, search_train, get_train_info,
    get_train_route, get_schedule, get_fares,
    is_train_running, is_train_active, get_database_stats,
    verify_database
)
from route_finder import RouteFinder, search_routes_interactive
from route_display import TerminalDisplay

class RailwayOperatingSystem:
    """Main application controller"""
    
    def __init__(self):
        self.display = TerminalDisplay()
        self.route_finder = RouteFinder()
        self.running = True
    
    def show_welcome(self):
        """Show welcome screen"""
        print(APP_TITLE)
        
        # Verify database
        print(f"\n{COLORS['BLUE']}Verifying system integrity...{COLORS['RESET']}")
        checks = verify_database()
        
        if not all(checks.values()):
            self.display.print_error("Database verification failed!")
            print("Status:")
            for check, status in checks.items():
                symbol = '✅' if status else '❌'
                print(f"  {symbol} {check}")
            sys.exit(1)
        
        self.display.print_success("System ready for operations")
        print()
    
    def show_main_menu(self):
        """Display main menu"""
        self.display.display_menu("RAILWAY OPERATING SYSTEM - MAIN MENU", MAIN_MENU_OPTIONS)
    
    def search_routes_menu(self):
        """Menu: Search Routes"""
        print()
        self.display.print_header("Route Search")
        
        print(f"{COLORS['BOLD']}Major Stations:{COLORS['RESET']}")
        for code, name in list(MAJOR_STATIONS.items())[:8]:
            print(f"  {code}: {name}")
        print()
        
        source = input(f"{COLORS['BOLD']}Enter source station code (e.g., NDLS): {COLORS['RESET']}").strip().upper()
        if not source:
            self.display.print_error("Source station cannot be empty")
            return
        
        destination = input(f"{COLORS['BOLD']}Enter destination station code (e.g., HWH): {COLORS['RESET']}").strip().upper()
        if not destination:
            self.display.print_error("Destination station cannot be empty")
            return
        
        if source == destination:
            self.display.print_warning("Source and destination cannot be the same")
            return
        
        # Search routes
        routes = self.route_finder.find_all_routes(source, destination, max_transfers=3, max_results=50)
        
        if not routes or not any(routes.values()):
            self.display.print_error(f"No routes found from {source} to {destination}")
            return
        
        self.display.display_route_summary(routes)
        
        # Show direct routes if available
        if routes.get('direct'):
            print(f"\n{COLORS['GREEN']}{'='*80}")
            print(f"DIRECT ROUTES ({len(routes['direct'])} found):")
            print(f"{'='*80}{COLORS['RESET']}")
            
            self.display.print_table_header(
                "Train No",
                "Name",
                "Type",
                "Depart",
                "Arrive",
                "Days"
            )
            
            for route in routes['direct'][:15]:
                train_no = route[0]
                self.display.print_table_row(
                    train_no,
                    route[1][:20],
                    route[2],
                    route[5] if route[5] else "N/A",
                    route[6] if route[6] else "N/A",
                    ""
                )
        
        # Ask to show details
        choice = input(f"\n{COLORS['BOLD']}View fare details for a train? (Enter train number or press Enter to skip): {COLORS['RESET']}").strip()
        if choice:
            try:
                train_no = int(choice)
                fares = get_fares(train_no, source, destination)
                if fares:
                    self.display.display_fares(fares, train_no, source, destination)
                else:
                    self.display.print_error(f"No fare information found for train {train_no}")
            except ValueError:
                self.display.print_error("Invalid train number")
    
    def station_lookup_menu(self):
        """Menu: Station Lookup"""
        print()
        self.display.print_header("Station Lookup")
        
        search_term = input(f"{COLORS['BOLD']}Enter station code or name (e.g., NDLS or Delhi): {COLORS['RESET']}").strip()
        if not search_term:
            self.display.print_error("Search term cannot be empty")
            return
        
        stations = search_station(search_term)
        self.display.display_stations(stations, show_details=True)
        
        # Show detailed info for first result
        if stations:
            choice = input(f"\n{COLORS['BOLD']}View detailed information for first station? (y/n): {COLORS['RESET']}").strip().lower()
            if choice == 'y':
                info = get_station_info(stations[0][0])
                if info:
                    self.display.print_header(f"Station Details: {info[1]}")
                    print(f"  Code:       {info[0]}")
                    print(f"  Name:       {info[1]}")
                    print(f"  City:       {info[2]}")
                    print(f"  State:      {info[3]}")
                    print(f"  Junction:   {'Yes' if info[4] == 1 else 'No'}")
                    if len(info) > 5:
                        print(f"  Latitude:   {info[5]}")
                        print(f"  Longitude:  {info[6]}")
    
    def train_information_menu(self):
        """Menu: Train Information"""
        print()
        self.display.print_header("Train Information")
        
        search_term = input(f"{COLORS['BOLD']}Enter train number or name (e.g., 13008 or Rajdhani): {COLORS['RESET']}").strip()
        if not search_term:
            self.display.print_error("Search term cannot be empty")
            return
        
        trains = search_train(search_term)
        
        if not trains:
            self.display.print_error(f"No trains found for '{search_term}'")
            return
        
        print(f"\n{COLORS['BOLD']}Found {len(trains)} train(s):{COLORS['RESET']}")
        self.display.print_table_header("Train No", "Name", "Type", "Source", "Destination")
        
        for train in trains[:10]:
            self.display.print_table_row(train[0], train[1][:20], train[2], train[3], train[4])
        
        # Show details for first train
        if trains:
            choice = input(f"\n{COLORS['BOLD']}View detailed information for first train? (y/n): {COLORS['RESET']}").strip().lower()
            if choice == 'y':
                train_info = get_train_info(trains[0][0])
                if train_info:
                    self.display.display_train_info(train_info)
                    
                    # Show route
                    route = get_train_route(trains[0][0])
                    if route:
                        print(f"\n{COLORS['BOLD']}Route Stops ({len(route)} total):{COLORS['RESET']}")
                        print(f"  Start: {route[0][1]} (Sequence {route[0][0]})")
                        print(f"  End:   {route[-1][1]} (Sequence {route[-1][0]})")
                        print(f"  Total Distance: {route[-1][2]} km" if route[-1][2] else "  Total Distance: N/A")
    
    def schedule_checker_menu(self):
        """Menu: Schedule Checker"""
        print()
        self.display.print_header("Schedule Checker")
        
        train_no = input(f"{COLORS['BOLD']}Enter train number: {COLORS['RESET']}").strip()
        if not train_no:
            self.display.print_error("Train number cannot be empty")
            return
        
        try:
            train_no = int(train_no)
        except ValueError:
            self.display.print_error("Invalid train number")
            return
        
        station_code = input(f"{COLORS['BOLD']}Enter station code: {COLORS['RESET']}").strip().upper()
        if not station_code:
            self.display.print_error("Station code cannot be empty")
            return
        
        schedule = get_schedule(train_no, station_code)
        self.display.display_schedule(schedule, train_no, station_code)
    
    def fare_calculator_menu(self):
        """Menu: Fare Calculator"""
        print()
        self.display.print_header("Fare Calculator")
        
        train_no = input(f"{COLORS['BOLD']}Enter train number: {COLORS['RESET']}").strip()
        source = input(f"{COLORS['BOLD']}Enter source station code: {COLORS['RESET']}").strip().upper()
        destination = input(f"{COLORS['BOLD']}Enter destination station code: {COLORS['RESET']}").strip().upper()
        
        if not all([train_no, source, destination]):
            self.display.print_error("All fields are required")
            return
        
        try:
            train_no = int(train_no)
        except ValueError:
            self.display.print_error("Invalid train number")
            return
        
        fares = get_fares(train_no, source, destination)
        self.display.display_fares(fares, train_no, source, destination)
    
    def major_stations_menu(self):
        """Menu: View All Major Stations"""
        print()
        self.display.print_header("Major Railway Stations")
        
        self.display.print_table_header("Code", "Station Name", "City/Region")
        for code, name in MAJOR_STATIONS.items():
            self.display.print_table_row(code, name, "")
        
        print(f"\n{COLORS['BLUE']}Total Major Stations: {len(MAJOR_STATIONS)}{COLORS['RESET']}")
    
    def database_stats_menu(self):
        """Menu: Database Statistics"""
        print()
        stats = get_database_stats()
        self.display.display_database_stats(stats)
    
    def health_check_menu(self):
        """Menu: System Health Check"""
        print()
        self.display.print_header("System Health Check")
        
        checks = verify_database()
        print(f"\n{COLORS['BOLD']}Database Integrity:{COLORS['RESET']}")
        
        for check, status in checks.items():
            symbol = f"{COLORS['GREEN']}✅{COLORS['RESET']}" if status else f"{COLORS['RED']}❌{COLORS['RESET']}"
            print(f"  {symbol} {check}")
        
        all_ok = all(checks.values())
        if all_ok:
            self.display.print_success("All systems operational")
        else:
            self.display.print_error("Some systems require attention")
    
    def batch_operations_menu(self):
        """Menu: Batch Operations"""
        print()
        self.display.print_header("Batch Operations")
        
        print(f"{COLORS['BOLD']}Available Operations:{COLORS['RESET']}")
        print("  1. Compare multiple routes")
        print("  2. Export route search results")
        print("  3. Check multiple trains")
        print("  4. Generate route report")
        print("  0. Back to main menu")
        print()
        
        choice = input(f"{COLORS['BOLD']}Select operation: {COLORS['RESET']}").strip()
        
        if choice == '1':
            self.compare_routes()
        elif choice == '2':
            self.export_routes()
        elif choice == '0':
            return
        else:
            self.display.print_error("Invalid choice")
    
    def compare_routes(self):
        """Compare multiple routes"""
        print()
        print(f"{COLORS['BOLD']}Comparing Routes...{COLORS['RESET']}")
        
        source = input("Enter source station: ").strip().upper()
        destination = input("Enter destination station: ").strip().upper()
        
        if source and destination and source != destination:
            routes = self.route_finder.find_all_routes(source, destination, max_transfers=3, max_results=20)
            
            total = sum(len(r) if isinstance(r, list) else 0 for r in routes.values())
            print(f"\n{COLORS['GREEN']}Comparison Results:{COLORS['RESET']}")
            print(f"  Total Routes Found: {total}")
            print(f"  - Direct: {len(routes.get('direct', []))}")
            print(f"  - 1 Transfer: {len(routes.get('one_transfer', []))}")
            
            if total > 0:
                self.display.print_success("Route comparison complete")
    
    def export_routes(self):
        """Export route search results"""
        self.display.print_info("Export functionality available for future implementation")
    
    def run(self):
        """Main application loop"""
        self.show_welcome()
        
        while self.running:
            self.show_main_menu()
            
            choice = input(f"{COLORS['BOLD']}Select option (0-9): {COLORS['RESET']}").strip()
            
            if choice == '1':
                self.search_routes_menu()
            elif choice == '2':
                self.station_lookup_menu()
            elif choice == '3':
                self.train_information_menu()
            elif choice == '4':
                self.schedule_checker_menu()
            elif choice == '5':
                self.fare_calculator_menu()
            elif choice == '6':
                self.major_stations_menu()
            elif choice == '7':
                self.database_stats_menu()
            elif choice == '8':
                self.health_check_menu()
            elif choice == '9':
                self.batch_operations_menu()
            elif choice == '0':
                print(f"\n{COLORS['GREEN']}{MESSAGES['goodbye']}{COLORS['RESET']}\n")
                self.running = False
            else:
                self.display.print_error(MESSAGES['invalid_choice'])
            
            if self.running:
                input(f"\n{COLORS['YELLOW']}Press Enter to continue...{COLORS['RESET']}")
                os.system('cls' if os.name == 'nt' else 'clear')

def main():
    """Application entry point"""
    try:
        app = RailwayOperatingSystem()
        app.run()
    except KeyboardInterrupt:
        print(f"\n\n{COLORS['YELLOW']}Application interrupted by user{COLORS['RESET']}")
        sys.exit(0)
    except Exception as e:
        print(f"{COLORS['RED']}Fatal error: {str(e)}{COLORS['RESET']}")
        sys.exit(1)

if __name__ == '__main__':
    main()
