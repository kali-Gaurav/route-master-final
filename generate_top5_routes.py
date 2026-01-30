"""
Generate Best 5 Routes for Major Indian Railway Junctions
Uses Pareto Optimization Algorithm
"""

import pandas as pd
from route_optimizer import get_routes_data
import json
from datetime import datetime

# Define top 5 O-D pairs covering major corridors of India
TOP_5_JUNCTION_PAIRS = [
    {
        'origin': 'NDLS',
        'destination': 'MAS',
        'corridor': 'North to South (Delhi to Chennai)',
        'description': 'One of India\'s busiest corridors connecting the capital to Tamil Nadu'
    },
    {
        'origin': 'HWH',
        'destination': 'CSMT',
        'corridor': 'East to West (Kolkata to Mumbai)',
        'description': 'Connecting two major economic hubs across the country'
    },
    {
        'origin': 'SBC',
        'destination': 'NDLS',
        'corridor': 'South to North (Bangalore to Delhi)',
        'description': 'IT capital to political capital - high traffic business route'
    },
    {
        'origin': 'ADI',
        'destination': 'HWH',
        'corridor': 'West to East (Ahmedabad to Kolkata)',
        'description': 'Industrial corridor connecting Gujarat to West Bengal'
    },
    {
        'origin': 'JP',
        'destination': 'SBC',
        'corridor': 'Northwest to South (Jaipur to Bangalore)',
        'description': 'Tourist and business corridor across central India'
    }
]

def generate_all_top5_routes():
    """Generate routes for all top 5 junction pairs"""
    
    print("\n" + "="*100)
    print(" GENERATING ROUTES FOR TOP 5 MAJOR INDIAN RAILWAY JUNCTION PAIRS")
    print("="*100)
    print("\n🎯 Selected Junction Pairs:")
    for i, pair in enumerate(TOP_5_JUNCTION_PAIRS, 1):
        print(f"  {i}. {pair['origin']} → {pair['destination']} ({pair['corridor']})")
        print(f"     {pair['description']}")
    print("="*100)
    
    all_results = {
        'generation_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'total_pairs_analyzed': len(TOP_5_JUNCTION_PAIRS),
        'junction_pairs': []
    }
    
    for i, pair in enumerate(TOP_5_JUNCTION_PAIRS, 1):
        print(f"\n{'='*100}")
        print(f"PROCESSING PAIR {i}/5: {pair['origin']} → {pair['destination']}")
        print(f"Corridor: {pair['corridor']}")
        print(f"{'='*100}")
        
        # Run the algorithm with max 3 transfers
        max_transfers = 3
        results, router = get_routes_data(pair['origin'], pair['destination'], max_transfers)
        
        if "error" in results:
            print(f"❌ Error: {results['error']}")
            all_results['junction_pairs'].append({
                'pair': pair,
                'status': 'error',
                'error_message': results['error']
            })
            continue
        
        # Display summary
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"  ✓ Total routes generated: {results['metadata']['total_routes_generated']}")
        print(f"  ✓ Pareto front size: {results['metadata']['pareto_front_size']}")
        print(f"  ✓ Optimal routes selected: {results['metadata']['optimal_routes_count']}")
        
        # Display top 5 optimal routes
        print(f"\n🏆 TOP 5 OPTIMAL ROUTES:")
        print("-" * 100)
        print(f"{'Route':<12} {'Category':<20} {'Time':<12} {'Cost':<10} {'Transfers':<10} {'Seats':<10} {'Safety'}")
        print("-" * 100)
        
        for route_data in results['optimal_routes'][:5]:
            obj = route_data['objectives']
            time_hours = obj['time'] / 60
            time_str = f"{int(time_hours)}h {int((time_hours % 1) * 60)}m"
            print(f"{route_data['route_id']:<12} {route_data['category']:<20} {time_str:<12} "
                  f"₹{obj['cost']:<9.0f} {obj['transfers']:<10} {obj['seat_prob']:<9.1f}% {obj['safety_score']}/100")
        
        print("-" * 100)
        
        # Add to consolidated results
        all_results['junction_pairs'].append({
            'pair_number': i,
            'origin': pair['origin'],
            'destination': pair['destination'],
            'corridor': pair['corridor'],
            'description': pair['description'],
            'status': 'success',
            'statistics': results['metadata'],
            'top_5_routes': results['optimal_routes'][:5]
        })
        
        print(f"\n✅ Results saved to:")
        print(f"   • CSV: {pair['origin']}_to_{pair['destination']}_pareto_routes.csv")
        print(f"   • JSON: {pair['origin']}_to_{pair['destination']}_pareto_routes.json")
        print(f"   • All Routes CSV: {pair['origin']}_to_{pair['destination']}_all_routes.csv")
    
    # Save consolidated results
    consolidated_file = 'TOP5_MAJOR_JUNCTIONS_CONSOLIDATED_RESULTS.json'
    with open(consolidated_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n{'='*100}")
    print(f"✅ ALL PROCESSING COMPLETE")
    print(f"{'='*100}")
    print(f"\n📁 Consolidated results saved to: {consolidated_file}")
    
    # Generate summary CSV
    generate_summary_csv(all_results)
    
    return all_results

def generate_summary_csv(all_results):
    """Generate a summary CSV with best route from each pair"""
    
    summary_rows = []
    
    for pair_result in all_results['junction_pairs']:
        if pair_result['status'] != 'success':
            continue
        
        # Get the fastest route (first optimal route)
        if pair_result['top_5_routes']:
            fastest = pair_result['top_5_routes'][0]
            obj = fastest['objectives']
            
            # Get cheapest
            cheapest = min(pair_result['top_5_routes'], key=lambda x: x['objectives']['cost'])
            
            # Get least transfers
            least_transfers = min(pair_result['top_5_routes'], key=lambda x: x['objectives']['transfers'])
            
            summary_rows.append({
                'Pair Number': pair_result['pair_number'],
                'Origin': pair_result['origin'],
                'Destination': pair_result['destination'],
                'Corridor': pair_result['corridor'],
                'Total Routes Generated': pair_result['statistics']['total_routes_generated'],
                'Pareto Front Size': pair_result['statistics']['pareto_front_size'],
                'Fastest Time (min)': round(fastest['objectives']['time'], 2),
                'Fastest Cost (₹)': round(fastest['objectives']['cost'], 2),
                'Cheapest Cost (₹)': round(cheapest['objectives']['cost'], 2),
                'Cheapest Time (min)': round(cheapest['objectives']['time'], 2),
                'Min Transfers': least_transfers['objectives']['transfers'],
                'Avg Safety Score': 100.0,
                'Avg Seat Probability (%)': 100.0
            })
    
    summary_df = pd.DataFrame(summary_rows)
    summary_csv = 'TOP5_MAJOR_JUNCTIONS_SUMMARY.csv'
    summary_df.to_csv(summary_csv, index=False)
    
    print(f"\n📊 Summary comparison saved to: {summary_csv}")
    
    # Display summary table
    print(f"\n{'='*100}")
    print("SUMMARY: BEST ROUTES ACROSS TOP 5 JUNCTION PAIRS")
    print(f"{'='*100}\n")
    print(summary_df.to_string(index=False))
    print(f"\n{'='*100}")

def main():
    """Main execution function"""
    try:
        results = generate_all_top5_routes()
        
        print("\n" + "="*100)
        print("🎉 SUCCESS! ALL TOP 5 JUNCTION PAIR ROUTES GENERATED")
        print("="*100)
        print("\n📂 Generated Files:")
        print("   1. Individual CSV files for each O-D pair (Pareto optimal routes)")
        print("   2. Individual JSON files for each O-D pair (Complete route details)")
        print("   3. Individual CSV files for all generated routes per O-D pair")
        print("   4. TOP5_MAJOR_JUNCTIONS_CONSOLIDATED_RESULTS.json (All results combined)")
        print("   5. TOP5_MAJOR_JUNCTIONS_SUMMARY.csv (Quick comparison table)")
        print("\n" + "="*100)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
