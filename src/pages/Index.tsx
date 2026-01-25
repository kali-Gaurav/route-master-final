import { useState, useMemo } from "react";
import { ArrowLeftRight, CalendarDays, Search, Sparkles, Users, MapPin, Filter } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { StationSearch } from "@/components/StationSearch";
import { RouteCard } from "@/components/RouteCard";
import { RouteSkeleton } from "@/components/RouteSkeleton";
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
  const [displayedAlternatives, setDisplayedAlternatives] = useState<number>(5);
  const [viewMode, setViewMode] = useState<"optimal" | "all">("optimal");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isFromCache, setIsFromCache] = useState(false);
  const [directOnly, setDirectOnly] = useState(false);

  const handleSwapStations = () => {
    const temp = origin;
    setOrigin(destination);
    setDestination(temp);
    // Trigger search if both stations are selected
    if (origin && destination) {
      handleSearch();
    }
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
      let url = `http://localhost:5000/api/routes?origin=${origin.code}&destination=${destination.code}`;
      if (travelDate) {
        url += `&date=${travelDate}`;
      }
      console.log("[Search] Calling API:", url);
      
      const startTime = performance.now();
      const response = await fetch(url);
      const endTime = performance.now();
      const responseTime = endTime - startTime;
      
      console.log("[Search] Response status:", response.status, "Time:", responseTime.toFixed(0), "ms");
      
      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch (e) {
          console.error("[Search] Could not parse error response as JSON:", e);
          errorData = { error: `HTTP ${response.status}: ${response.statusText}` };
        }
        console.error("[Search] API Error:", errorData);
        throw new Error(errorData.error || "Failed to fetch routes");
      }

      let data;
      try {
        data = await response.json();
      } catch (e) {
        console.error("[Search] Could not parse response as JSON:", e);
        throw new Error("Server returned invalid response format");
      }
      
      console.log("[Search] Response data:", data);
      
      // Check if routes were loaded from cache (very fast response < 500ms typically means cached)
      const wasCached = responseTime < 500;
      setIsFromCache(wasCached);
      
      const mappedOptimal = data.optimal_routes.map(mapApiRouteToRoute)
        .sort((a, b) => a.totalTime - b.totalTime);
      
      // Map all alternative routes
      const mappedAlternatives = (data.all_alternative_routes || [])
        .map(mapApiRouteToRoute)
        .sort((a, b) => a.totalTime - b.totalTime);
      
      // Combine optimal + alternatives for "all" view
      const allCombined = [...mappedOptimal, ...mappedAlternatives];

      setOptimalRoutes(mappedOptimal);
      setAllRoutes(allCombined);
      setViewMode("optimal");
      setDisplayedAlternatives(5); // Reset pagination on new search
      
      toast({
        title: wasCached ? "Routes Loaded from Cache! ⚡" : "Routes Found!",
        description: wasCached 
          ? `Instantly loaded ${mappedOptimal.length} optimal routes from saved data.`
          : `Found ${mappedOptimal.length} optimal routes and ${mappedAlternatives.length} alternatives.`,
      } as Toast);

      // Scroll to results
      setTimeout(() => {
        document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (error: any) {
      console.error("[Search] Error occurred:", error);
      console.error("[Search] Error type:", error.constructor.name);
      console.error("[Search] Error message:", error.message);
      
      let errorMessage = error.message || "Could not connect to the route optimization server.";
      
      // Check if it's a network error
      if (error instanceof TypeError && error.message.includes("fetch")) {
        errorMessage = "Cannot connect to server at localhost:5000. Make sure 'python api.py' is running.";
      }
      
      toast({
        title: "Search Failed",
        description: errorMessage,
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
    let routes = currentRoutes;
    
    // Apply direct only filter
    if (directOnly) {
      routes = routes.filter((route) => route.totalTransfers === 0);
    }
    
    // Apply category filter
    if (!selectedCategory) return routes;
    return routes.filter((route) => 
      getCategoryBase(route.category) === selectedCategory
    );
  }, [currentRoutes, selectedCategory, directOnly]);

  // Paginated routes: show optimal routes (no pagination) or alternative routes (paginated)
  const displayedRoutes = useMemo(() => {
    if (viewMode === "optimal") {
      return filteredRoutes; // Show all optimal routes
    } else {
      // For "all" view, show alternatives with pagination
      return filteredRoutes.slice(0, displayedAlternatives);
    }
  }, [filteredRoutes, viewMode, displayedAlternatives]);

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

              {/* Direct Only Toggle */}
              <div className="flex items-center gap-3 mb-6">
                <input
                  type="checkbox"
                  id="directOnly"
                  checked={directOnly}
                  onChange={(e) => setDirectOnly(e.target.checked)}
                  className="w-4 h-4 text-primary border-border rounded focus:ring-primary/20"
                />
                <label htmlFor="directOnly" className="text-sm font-medium text-muted-foreground cursor-pointer">
                  Direct routes only (no transfers)
                </label>
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
      {(optimalRoutes.length > 0 || allRoutes.length > 0 || isSearching) && (
        <section id="results" className="py-12 bg-secondary/30">
          <div className="container mx-auto px-4">
            {/* Show skeleton during search */}
            {isSearching ? (
              <>
                <div className="mb-8">
                  <div className="h-8 w-48 bg-secondary rounded-lg mb-2 animate-pulse" />
                  <div className="h-4 w-96 bg-secondary rounded animate-pulse" />
                </div>
                <RouteSkeleton count={3} />
              </>
            ) : (
            <>
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
              {displayedRoutes.length > 0 ? (
                <>
                  {displayedRoutes.map((route, idx) => (
                    <RouteCard
                      key={route.id}
                      route={route}
                      index={idx}
                      isRecommended={viewMode === "optimal" && idx === 0 && !selectedCategory}
                    />
                  ))}
                  
                  {/* Load More Button */}
                  {viewMode === "all" && displayedAlternatives < filteredRoutes.length && (
                    <div className="flex justify-center pt-4">
                      <button
                        onClick={() => setDisplayedAlternatives(prev => prev + 5)}
                        className={cn(
                          "px-6 py-3 rounded-lg font-semibold text-sm",
                          "border-2 border-primary text-primary",
                          "hover:bg-primary hover:text-white transition-all"
                        )}
                      >
                        Load More ({filteredRoutes.length - displayedAlternatives} remaining)
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-12 bg-card rounded-2xl border-2 border-dashed border-border">
                  <Filter className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-20" />
                  <p className="text-muted-foreground">No routes match the selected filter.</p>
                </div>
              )}
            </div>
            </>
            )}
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
