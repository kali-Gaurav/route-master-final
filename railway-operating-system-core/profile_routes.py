import cProfile
import pstats
from route_finder import RouteFinder


def profile_routes():
    finder = RouteFinder()
    # Debug: ensure RouteFinder has expected methods
    print('RouteFinder attrs:', [m for m in dir(finder) if not m.startswith('_')])
    print('has_find_all_routes:', hasattr(finder, 'find_all_routes'))
    profiler = cProfile.Profile()
    profiler.enable()

    # Run a heavy search
    finder.find_all_routes('NDLS', 'HWH', max_transfers=3, max_results=200)

    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(30)  # Print top 30 heaviest calls


if __name__ == "__main__":
    profile_routes()
