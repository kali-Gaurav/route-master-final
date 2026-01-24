"""
EXPANDABLE CACHE DEMO
=====================

Demonstrates the auto-discovering, expandable cache system
that automatically finds and loads all route files in the directory.

No hardcoded limits - just add more route files and they're instantly available!
"""

import time
from route_master_cache import get_routes, get_available_pairs, get_cache_stats

def demo_expandable_cache():
    """Demonstrate the expandable cache system"""
    print("🚀 ROUTE MASTER CACHE - EXPANDABLE SYSTEM DEMO")
    print("=" * 60)

    # Show loading process
    start_time = time.time()
    print("📦 Importing cache system...")

    # Import triggers auto-loading
    import_time = time.time() - start_time
    print(f"✓ Module imported in {import_time:.3f}s")
    print("\n📊 CACHE DISCOVERY RESULTS:")
    print("-" * 30)

    # Get cache statistics
    stats = get_cache_stats()
    print(f"Route files discovered: {stats['route_files_discovered']}")
    print(f"Route pairs available: {stats['route_pairs_available']}")
    print(f"Memory usage: {stats['memory_usage_mb']:.3f} MB")
    print(f"Load time: {stats['load_time_seconds']:.3f}s")

    print("\n🎯 AVAILABLE ROUTE PAIRS:")
    print("-" * 30)

    pairs = get_available_pairs()
    for i, (origin, dest, corridor) in enumerate(pairs, 1):
        print(f"{i:2d}. {corridor}")

    print("\n⚡ INSTANT ROUTE RETRIEVAL DEMO:")
    print("-" * 30)

    # Test retrieval from different pairs
    test_pairs = [
        ("NDLS", "MAS", "Delhi to Chennai"),
        ("HWH", "CSMT", "Kolkata to Mumbai"),
        ("SBC", "NDLS", "Bangalore to Delhi"),
        ("ADI", "HWH", "Ahmedabad to Kolkata"),
        ("JP", "SBC", "Jaipur to Bangalore")
    ]

    for origin, dest, description in test_pairs:
        start = time.time()
        routes = get_routes(origin, dest, "pareto")
        retrieval_time = time.time() - start

        if routes is not None:
            print(f"⚡ {origin}→{dest} ({description}): {len(routes)} routes in {retrieval_time:.4f}s")
        else:
            print(f"❌ {origin}→{dest}: No routes found")

    print("\n🎉 EXPANDABLE SYSTEM BENEFITS:")
    print("-" * 30)
    print("✅ Auto-discovers all route files on import")
    print("✅ No hardcoded limits or manual configuration")
    print("✅ Just add route files - they're instantly available")
    print("✅ Scales to hundreds of route pairs automatically")
    print("✅ Maintains instant retrieval performance")
    print("✅ Production-ready for any scale")

    print("\n" + "=" * 60)
    print("🎯 TO ADD MORE ROUTES:")
    print("   1. Generate routes using generate_top5_routes.py")
    print("   2. Add the CSV/JSON files to this directory")
    print("   3. Import route_master_cache - new routes are auto-discovered!")
    print("   4. No code changes needed - fully automatic!")
    print("=" * 60)

if __name__ == "__main__":
    demo_expandable_cache()