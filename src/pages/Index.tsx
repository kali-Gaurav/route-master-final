import { useState, useMemo } from "react";
import { ArrowLeftRight, CalendarDays, Search, Sparkles, Users, MapPin } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { StationSearch } from "@/components/StationSearch";
import { RouteCard } from "@/components/RouteCard";
import { CategoryFilter } from "@/components/CategoryFilter";
import { FeaturesSection } from "@/components/FeaturesSection";
import { Station } from "@/data/stations";
import { sampleRoutes, Route, RouteSegment, getCategoryBase } from "@/data/routes";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

const Index = () => {
  const [origin, setOrigin] = useState<Station | null>(null);
  const [destination, setDestination] = useState<Station | null>(null);
  const [travelDate, setTravelDate] = useState<string>("");
  const [isSearching, setIsSearching] = useState(false);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const handleSwapStations = () => {
    const temp = origin;
    setOrigin(destination);
    setDestination(temp);
  };

  const handleSearch = async () => {
    if (!origin || !destination) {
      toast({
        title: "Missing Information",
        description: "Please select both origin and destination stations.",
        variant: "destructive",
      });
      return;
    }

    setIsSearching(true);
    setRoutes([]); // Clear previous routes

    try {
      const response = await fetch(`http://localhost:5000/api/routes?origin=${origin.code}&destination=${destination.code}&max_transfers=3`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to fetch routes.");
      }

      const data = await response.json();

      // Transform API data to frontend Route[] type
      const transformedRoutes: Route[] = data.routes.map((apiRoute: any) => ({
        id: apiRoute.route_id,
        category: apiRoute.category,
        totalTime: apiRoute.objectives.time,
        totalCost: apiRoute.objectives.cost,
        totalTransfers: apiRoute.objectives.transfers,
        seatProbability: apiRoute.objectives.seat_prob,
        safetyScore: apiRoute.objectives.safety_score,
        totalDistance: apiRoute.objectives.distance,
        segments: apiRoute.segments.map((apiSegment: any): RouteSegment => ({
          routeId: apiRoute.route_id,
          category: apiRoute.category,
          segment: apiSegment.segment, // Ensure this is provided by API or generate
          trainNumber: apiSegment.train_no,
          trainName: apiSegment.train_name,
          from: apiSegment.from,
          to: apiSegment.to,
          departure: apiSegment.departure,
          arrival: apiSegment.arrival,
          distance: apiSegment.distance,
          duration: apiSegment.duration_min,
          waitBefore: apiSegment.wait_min,
          seatAvailable: apiSegment.seat_available === 1, // Ensure this is provided by API
        })),
      }));

      setRoutes(transformedRoutes);
      
      toast({
        title: "Routes Found!",
        description: `Found ${transformedRoutes.length} optimal routes for your journey.`,
      });

      // Scroll to results
      document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });

    } catch (error) {
      const message = error instanceof Error ? error.message : "An unknown error occurred.";
      toast({
        title: "Search Failed",
        description: message,
        variant: "destructive",
      });
    } finally {
      setIsSearching(false);
    }
  };

  const categories = useMemo(() => {
    const uniqueCategories = new Set<string>();
    routes.forEach((route) => {
      const base = getCategoryBase(route.category);
      if (base) uniqueCategories.add(base);
    });
    return Array.from(uniqueCategories);
  }, [routes]);

  const filteredRoutes = useMemo(() => {
    if (!selectedCategory) return routes;
    return routes.filter((route) => 
      getCategoryBase(route.category) === selectedCategory
    );
  }, [routes, selectedCategory]);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      {/* Hero Section */}
      <section className="relative pt-24 pb-12 overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-primary/10 blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-accent/10 blur-3xl" />
        </div>

        <div className="container mx-auto px-4 relative">
          <div className="text-center max-w-4xl mx-auto mb-12">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary mb-6">
              <Sparkles className="w-4 h-4" />
              <span className="text-sm font-medium">AI-Powered Route Optimization</span>
            </div>
            <h1 className="text-4xl md:text-6xl font-bold text-foreground mb-6 leading-tight">
              Find Your Perfect
              <br />
              <span className="text-gradient">Train Route</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Multi-objective Pareto optimization finds routes that balance time, cost, 
              transfers, and seat availability. Book even a day before travel.
            </p>
          </div>

          {/* Search Card */}
          <div className="max-w-4xl mx-auto">
            <div className="bg-card rounded-3xl border-2 border-border p-6 md:p-8 shadow-card">
              <div className="grid md:grid-cols-2 gap-4 mb-6">
                <StationSearch
                  label="From"
                  placeholder="Enter origin station"
                  value={origin}
                  onChange={setOrigin}
                  icon="origin"
                />
                
                <div className="relative">
                  <StationSearch
                    label="To"
                    placeholder="Enter destination station"
                    value={destination}
                    onChange={setDestination}
                    icon="destination"
                  />
                  <button
                    onClick={handleSwapStations}
                    className={cn(
                      "absolute -left-6 top-1/2 z-20 hidden md:flex",
                      "w-12 h-12 rounded-full bg-card border-2 border-border",
                      "items-center justify-center shadow-soft",
                      "hover:border-primary hover:bg-primary/5 transition-all"
                    )}
                  >
                    <ArrowLeftRight className="w-5 h-5 text-muted-foreground" />
                  </button>
                </div>
              </div>

              <div className="grid md:grid-cols-3 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">
                    Travel Date
                  </label>
                  <div className="relative">
                    <CalendarDays className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <input
                      type="date"
                      value={travelDate}
                      onChange={(e) => setTravelDate(e.target.value)}
                      className={cn(
                        "w-full pl-12 pr-4 py-4 rounded-xl",
                        "bg-secondary border-2 border-transparent",
                        "text-foreground placeholder:text-muted-foreground",
                        "focus:border-primary focus:ring-4 focus:ring-primary/10",
                        "transition-all duration-200 outline-none"
                      )}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">
                    Travelers
                  </label>
                  <div className="relative">
                    <Users className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <select
                      className={cn(
                        "w-full pl-12 pr-4 py-4 rounded-xl appearance-none",
                        "bg-secondary border-2 border-transparent",
                        "text-foreground",
                        "focus:border-primary focus:ring-4 focus:ring-primary/10",
                        "transition-all duration-200 outline-none"
                      )}
                    >
                      <option>1 Adult</option>
                      <option>2 Adults</option>
                      <option>3 Adults</option>
                      <option>4 Adults</option>
                    </select>
                  </div>
                </div>
                <div className="flex items-end">
                  <button
                    onClick={handleSearch}
                    disabled={isSearching}
                    className={cn(
                      "w-full py-4 px-6 rounded-xl font-semibold text-lg",
                      "hero-gradient text-white",
                      "hover:opacity-90 active:scale-[0.98] transition-all",
                      "flex items-center justify-center gap-2",
                      "disabled:opacity-50 disabled:cursor-not-allowed",
                      "shadow-soft"
                    )}
                  >
                    {isSearching ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Searching...
                      </>
                    ) : (
                      <>
                        <Search className="w-5 h-5" />
                        Find Routes
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="flex flex-wrap items-center justify-center gap-6 pt-4 border-t border-border">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <MapPin className="w-4 h-4 text-primary" />
                  <span>11,000+ Trains</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <MapPin className="w-4 h-4 text-primary" />
                  <span>8,000+ Stations</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Sparkles className="w-4 h-4 text-primary" />
                  <span>Pareto-Optimal</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Results Section */}
      {routes.length > 0 && (
        <section id="results" className="py-12 bg-secondary/30">
          <div className="container mx-auto px-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
              <div>
                <h2 className="text-2xl font-bold text-foreground mb-2">
                  {filteredRoutes.length} Optimal Routes Found
                </h2>
                <p className="text-muted-foreground">
                  Showing Pareto-optimal routes from {origin?.name} to {destination?.name}
                </p>
              </div>
              <CategoryFilter
                categories={categories}
                selected={selectedCategory}
                onChange={setSelectedCategory}
              />
            </div>

            <div className="space-y-4">
              {filteredRoutes.map((route, idx) => (
                <RouteCard
                  key={route.id}
                  route={route}
                  index={idx}
                  isRecommended={idx === 0 && !selectedCategory}
                />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Features Section */}
      <FeaturesSection />

      <Footer />
    </div>
  );
};

export default Index;
