import { useState, useMemo } from "react";
import { ArrowLeftRight, CalendarDays, Search, Sparkles, Users, MapPin, Filter } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { StationSearch } from "@/components/StationSearch";
import { RouteCard } from "@/components/RouteCard";
import { CategoryFilter } from "@/components/CategoryFilter";
import { FeaturesSection } from "@/components/FeaturesSection";
import { Station } from "@/data/stations";
import { sampleRoutes, Route, getCategoryBase, mapApiRouteToRoute } from "@/data/routes";
import { cn } from "@/lib/utils";
import { toast, Toast } from "@/hooks/use-toast";

const Index = () => {
  const [origin, setOrigin] = useState<Station | null>(null);
  const [destination, setDestination] = useState<Station | null>(null);
  const [travelDate, setTravelDate] = useState<string>("");
  const [isSearching, setIsSearching] = useState(false);
  const [optimalRoutes, setOptimalRoutes] = useState<Route[]>([]);
  const [allRoutes, setAllRoutes] = useState<Route[]>([]);
  const [viewMode, setViewMode] = useState<"optimal" | "all">("optimal");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isFromCache, setIsFromCache] = useState(false);

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
      } as Toast);
      return;
    }

    setIsSearching(true);
    setIsFromCache(false);
    
    try {
      const startTime = performance.now();
      const response = await fetch(`http://localhost:5000/api/routes?origin=${origin.code}&destination=${destination.code}`);
      const endTime = performance.now();
      const responseTime = endTime - startTime;
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to fetch routes");
      }

      const data = await response.json();
      
      // Check if routes were loaded from cache (very fast response < 500ms typically means cached)
      const wasCached = responseTime < 500;
      setIsFromCache(wasCached);
      
      const mappedOptimal = data.optimal_routes.map(mapApiRouteToRoute)
        .sort((a, b) => a.totalTime - b.totalTime);
      
      // Deduplicate and sort all routes by total time
      const allRoutesMap = new Map();
      data.all_generated_routes.forEach((apiRoute: any) => {
        const route = mapApiRouteToRoute(apiRoute);
        // Use train numbers as fingerprint for deduplication
        const fingerprint = route.segments.map(s => s.trainNumber).join("-");
        if (!allRoutesMap.has(fingerprint) || allRoutesMap.get(fingerprint).totalTime > route.totalTime) {
          allRoutesMap.set(fingerprint, route);
        }
      });

      const mappedAll = Array.from(allRoutesMap.values())
        .sort((a, b) => a.totalTime - b.totalTime);

      setOptimalRoutes(mappedOptimal);
      setAllRoutes(mappedAll);
      setViewMode("optimal");
      
      toast({
        title: wasCached ? "Routes Loaded from Cache! ⚡" : "Routes Found!",
        description: wasCached 
          ? `Instantly loaded ${mappedOptimal.length} optimal routes from saved data.`
          : `Found ${mappedOptimal.length} optimal and ${mappedAll.length} total routes.`,
      } as Toast);

      // Scroll to results
      setTimeout(() => {
        document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (error: any) {
      console.error("Search error:", error);
      toast({
        title: "Search Failed",
        description: error.message || "Could not connect to the route optimization server.",
        variant: "destructive",
      } as Toast);
    } finally {
      setIsSearching(false);
    }
  };

  const currentRoutes = viewMode === "optimal" ? optimalRoutes : allRoutes;

  const categories = useMemo(() => {
    const uniqueCategories = new Set<string>();
    currentRoutes.forEach((route) => {
      const base = getCategoryBase(route.category);
      if (base) uniqueCategories.add(base);
    });
    return Array.from(uniqueCategories);
  }, [currentRoutes]);

  const filteredRoutes = useMemo(() => {
    if (!selectedCategory) return currentRoutes;
    return currentRoutes.filter((route) => 
      getCategoryBase(route.category) === selectedCategory
    );
  }, [currentRoutes, selectedCategory]);

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
      {(optimalRoutes.length > 0 || allRoutes.length > 0) && (
        <section id="results" className="py-12 bg-secondary/30">
          <div className="container mx-auto px-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h2 className="text-2xl font-bold text-foreground">
                    {viewMode === "optimal" ? optimalRoutes.length : allRoutes.length} {viewMode === "optimal" ? "Optimal" : "Possible"} Routes Found
                  </h2>
                  {isFromCache && (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-green-500/10 text-green-600 dark:text-green-400 text-xs font-medium border border-green-500/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                      Loaded from Cache
                    </span>
                  )}
                </div>
                <p className="text-muted-foreground">
                  Showing {optimalRoutes.length} optimal and {allRoutes.length} total routes from {origin?.name} to {destination?.name}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-4">
                <div className="bg-card p-1 rounded-xl border border-border flex">
                  <button
                    onClick={() => setViewMode("optimal")}
                    className={cn(
                      "px-4 py-2 rounded-lg text-sm font-semibold transition-all",
                      viewMode === "optimal" 
                        ? "bg-primary text-white shadow-sm" 
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    Optimal Routes
                  </button>
                  <button
                    onClick={() => setViewMode("all")}
                    className={cn(
                      "px-4 py-2 rounded-lg text-sm font-semibold transition-all",
                      viewMode === "all" 
                        ? "bg-primary text-white shadow-sm" 
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    All Possible
                  </button>
                </div>

                <CategoryFilter
                  categories={categories}
                  selected={selectedCategory}
                  onChange={setSelectedCategory}
                />
              </div>
            </div>

            <div className="space-y-4">
              {filteredRoutes.length > 0 ? (
                filteredRoutes.map((route, idx) => (
                  <RouteCard
                    key={route.id}
                    route={route}
                    index={idx}
                    isRecommended={viewMode === "optimal" && idx === 0 && !selectedCategory}
                  />
                ))
              ) : (
                <div className="text-center py-12 bg-card rounded-2xl border-2 border-dashed border-border">
                  <Filter className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-20" />
                  <p className="text-muted-foreground">No routes match the selected filter.</p>
                </div>
              )}
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
