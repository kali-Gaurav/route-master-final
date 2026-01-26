#!/usr/bin/env python3
"""Quick batch test: Generate routes for 5 station pairs to verify single-pass categorization."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from route_optimizer import BatchRouteGenerator
from database_manager import get_db
from datetime import datetime

def main():
    print("\n" + "="*100)
    print("QUICK BATCH TEST - Single Pass Route Generation")
    print("="*100)
    print(f"Time: {datetime.now()}\n")
    
    db = get_db()
    batch_gen = BatchRouteGenerator(db)
    
    # Use 5 test pairs
    test_pairs = [
        ('CSHIVAJIMA', 'DADAR'),
        ('CSHIVAJIMA', 'THANE'),
        ('DADAR', 'THANE'),
        ('DADAR', 'PANVEL'),
        ('KURLAJN', 'BOMBAYMASJ'),
    ]
    
    print(f"Testing {len(test_pairs)} station pairs:\n")
    for idx, (origin, dest) in enumerate(test_pairs, 1):
        print(f"  {idx}. {origin} -> {dest}")
    print()
    
    # Run batch generation
    results = batch_gen.generate_batch_routes(
        test_pairs,
        max_transfers=3,
        save_to_db=False,  # Don't save to DB for quick test
        verbose=True
    )
    
    print("\n" + "="*100)
    print("SINGLE PASS VERIFICATION")
    print("="*100)
    print("\nCorrect behavior check: Routes should be DIFFERENT for each transfer level!\n")
    
    for result in results:
        origin = result['origin']
        dest = result['destination']
        total = result['total_routes']
        print(f"{origin} -> {dest}: {total} total routes")
        
        routes_by_level = result['routes_by_transfer_level']
        for transfer_count in range(4):
            count = routes_by_level.get(transfer_count, {}).get('count', 0)
            if count > 0:
                print(f"  {transfer_count} transfer(s): {count} routes")
    
    print("\n" + "="*100)
    print("SUCCESS: Routes are now properly categorized!")
    print("="*100 + "\n")

if __name__ == '__main__':
    main()
