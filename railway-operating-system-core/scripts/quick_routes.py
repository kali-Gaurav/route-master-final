# ===============================================
# QUICK ROUTE FINDER - DIRECT TERMINAL TOOL
# ===============================================
# Fast command-line tool for searching routes

import sys
import argparse
from route_finder import RouteFinder
from route_display import TerminalDisplay
from database import get_fares

def main():
    parser = argparse.ArgumentParser(
        description='Railway Route Finder - Quick search from terminal',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python quick_routes.py NDLS HWH
  python quick_routes.py -s NDLS -d HWH --max-routes 20
  python quick_routes.py CSMT BZA --show-fares
        '''
    )
    
    parser.add_argument('source', nargs='?', help='Source station code')
    parser.add_argument('destination', nargs='?', help='Destination station code')
    parser.add_argument('-s', '--source', dest='src_alt', help='Alternative source specification')
    parser.add_argument('-d', '--dest', dest='dest_alt', help='Alternative destination specification')
    parser.add_argument('--max-routes', type=int, default=50, help='Maximum routes to display')
    parser.add_argument('--show-fares', action='store_true', help='Show fare details')
    parser.add_argument('--direct-only', action='store_true', help='Show only direct routes')
    parser.add_argument('--start-date', dest='start_date', help='Start date for journey (YYYY-MM-DD). Defaults to today')
    parser.add_argument('--verbose', action='store_true', help='Show verbose skip reasons for candidate connections')
    
    args = parser.parse_args()
    
    # Get source and destination
    source = args.src_alt or args.source
    destination = args.dest_alt or args.destination
    
    if not source or not destination:
        parser.print_help()
        return
    
    source = source.upper().strip()
    destination = destination.upper().strip()
    
    if source == destination:
        print("❌ Error: Source and destination cannot be the same")
        return
    
    # Search routes
    display = TerminalDisplay()
    finder = RouteFinder()
    
    print(f"\n🔍 Searching routes from {source} to {destination}...")
    
    if args.direct_only:
        routes = finder.find_direct_routes(source, destination)
        display.display_direct_routes(routes, source, destination)
    else:
        # parse optional start date for day-aware validation
        start_date = None
        if args.start_date:
            try:
                from datetime import datetime as _dt
                start_date = _dt.strptime(args.start_date, '%Y-%m-%d').date()
            except Exception:
                print(f"❌ Invalid start date format. Use YYYY-MM-DD")
                return
        routes = finder.find_all_routes(source, destination, start_date=start_date, max_transfers=3, max_results=args.max_routes, verbose=args.verbose)
        display.display_route_summary(routes)

        # If verbose, show skipped connection reasons
        if args.verbose and routes.get('skips'):
            display.print_warning(f"{len(routes.get('skips'))} candidate connections were skipped. Reasons:")
            for s in routes.get('skips')[:50]:
                display.print_info(str(s))
        
        # Display direct routes
        if routes.get('direct'):
            display.display_direct_routes(routes['direct'], source, destination)
            
            # Show fares if requested
            if args.show_fares and routes['direct']:
                first_train = routes['direct'][0]
                train_no = first_train[0]
                fares = get_fares(train_no, source, destination)
                display.display_fares(fares, train_no, source, destination)
        
        # Display 1-transfer routes
        if routes.get('one_transfer') and len(routes['one_transfer']) > 0:
            display.display_one_transfer_routes(routes['one_transfer'], source, destination)
        
        # Display 2-transfer routes
        if routes.get('two_transfer') and len(routes['two_transfer']) > 0:
            display.display_two_transfer_routes(routes['two_transfer'], source, destination)
        
        # Display 3-transfer routes
        if routes.get('three_transfer') and len(routes['three_transfer']) > 0:
            display.display_three_transfer_routes(routes['three_transfer'], source, destination)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
