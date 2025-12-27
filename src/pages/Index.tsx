import { useState, useMemo, useEffect } from "react"; // Added useEffect
import { ArrowLeftRight, CalendarDays, Search, Sparkles, Users, MapPin, ListFilter } from "lucide-react"; // Added ListFilter icon
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { StationSearch, Station } from "@/components/StationSearch";
import { RouteCard } from "@/components/RouteCard";
import { CategoryFilter } from "@/components/CategoryFilter";
import { FeaturesSection } from "@/components/FeaturesSection";
import { Route, getCategoryBase } from "@/data/routes";
import { cn } from "@/lib/utils";
import { toast, Toast } from "@/hooks/use-toast";

const Index = () => {
  const [origin, setOrigin] = useState<Station | null>(null);
  const [destination, setDestination] = useState<Station | null>(null);
  const [travelDate, setTravelDate] = useState<string>("");
  const [maxTransfers, setMaxTransfers] = useState<number>(3);
  const [isSearching, setIsSearching] = useState(false);
  const [optimalRoutes, setOptimalRoutes] = useState<Route[]>([]); // Renamed from routes
  const [allGeneratedRoutes, setAllGeneratedRoutes] = useState<Route[]>([]); // New state for all routes
  const [showAllRoutes, setShowAllRoutes] = useState(false); // New state to toggle view
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Determine which set of routes to display
  const currentRoutes = useMemo(() => {
    return showAllRoutes ? allGeneratedRoutes : optimalRoutes;
  }, [showAllRoutes, optimalRoutes, allGeneratedRoutes]);

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
    setOptimalRoutes([]);
    setAllGeneratedRoutes([]);
    setSelectedCategory(null); // Reset category filter on new search

    try {
      const apiUrl = `http://localhost:5000/api/routes?origin=${origin.code}&destination=${destination.code}&max_transfers=${maxTransfers}`;
      const response = await fetch(apiUrl);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to fetch routes.");
      }

      setOptimalRoutes(data.optimal_routes || []);
      setAllGeneratedRoutes(data.all_generated_routes || []);

      if ((data.optimal_routes && data.optimal_routes.length > 0) || (data.all_generated_routes && data.all_generated_routes.length > 0)) {
        toast({
          title: "Routes Found!",
          description: `Found ${data.optimal_routes?.length || 0} Pareto-optimal routes and ${data.all_generated_routes?.length || 0} total generated routes.`,
        } as Toast);
      } else {
        toast({
          title: "No Routes Found",
          description: "No routes were found for your selected criteria.",
          variant: "destructive",
        } as Toast);
      }
    } catch (error: any) {
      toast({
        title: "Error Searching Routes",
        description: error.message || "An unexpected error occurred.",
        variant: "destructive",
      } as Toast);
      setOptimalRoutes([]);
      setAllGeneratedRoutes([]);
    } finally {
      setIsSearching(false);
      document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Adjust categories and filtered routes based on `currentRoutes`
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

  // Update display based on data availability
  useEffect(() => {
    if (optimalRoutes.length === 0 && allGeneratedRoutes.length > 0) {
      setShowAllRoutes(true); // Automatically switch to all routes if no optimal ones
    } else if (optimalRoutes.length > 0 && allGeneratedRoutes.length > 0 && showAllRoutes) {
      // If optimal routes appear after showing all, reset to optimal if desired or keep as is.
      // For now, let's keep the user's choice.
    }
  }, [optimalRoutes, allGeneratedRoutes]);


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
              <span className="text-gradient">Multimodal Route</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Multi-objective Pareto optimization finds routes that balance time, cost, 
              transfers, and seat availability, combining trains and flights.
            </p>
          </div>

          {/* Search Card */}
          <div className="max-w-4xl mx-auto">
            <div className="bg-card rounded-3xl border-2 border-border p-6 md:p-8 shadow-card">
              <div className="grid md:grid-cols-2 gap-4 mb-6">
                <StationSearch
                  label="From"
                  placeholder="Enter origin station/airport code"
                  value={origin}
                  onChange={setOrigin}
                  icon="origin"
                />
                
                <div className="relative">
                  <StationSearch
                    label="To"
                    placeholder="Enter destination station/airport code"
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
                    Max Transfers
                  </label>
                  <div className="relative">
                    <ArrowLeftRight className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <select
                      value={maxTransfers}
                      onChange={(e) => setMaxTransfers(Number(e.target.value))}
                      className={cn(
                        "w-full pl-12 pr-4 py-4 rounded-xl appearance-none",
                        "bg-secondary border-2 border-transparent",
                        "text-foreground",
                        "focus:border-primary focus:ring-4 focus:ring-primary/10",
                        "transition-all duration-200 outline-none"
                      )}
                    >
                      <option value={0}>0 Transfers</option>
                      <option value={1}>1 Transfer</option>
                      <option value={2}>2 Transfers</option>
                      <option value={3}>3 Transfers</option>
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
                  <span>175,000+ Train Segments</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <MapPin className="w-4 h-4 text-primary" />
                  <span>11,000+ Locations</span>
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
      {currentRoutes.length > 0 && ( // Use currentRoutes here
        <section id="results" className="py-12 bg-secondary/30">
          <div className="container mx-auto px-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
              <div>
                <h2 className="text-2xl font-bold text-foreground mb-2">
                  {showAllRoutes ? `All ${currentRoutes.length} Generated Routes` : `${currentRoutes.length} Optimal Routes`} Found
                </h2>
                <p className="text-muted-foreground">
                  {showAllRoutes ? `Showing all generated routes from ${origin?.name} to ${destination?.name}` : `Showing Pareto-optimal routes from ${origin?.name} to ${destination?.name}`}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <CategoryFilter
                  categories={categories}
                  selected={selectedCategory}
                  onChange={setSelectedCategory}
                />
                <button
                  onClick={() => setShowAllRoutes(!showAllRoutes)}
                  className={cn(
                    "px-4 py-2 rounded-full text-sm font-medium transition-all duration-200",
                    "flex items-center gap-2",
                    showAllRoutes
                      ? "bg-primary text-primary-foreground shadow-soft"
                      : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                  )}
                >
                  <ListFilter className="w-4 h-4" />
                  {showAllRoutes ? "Show Optimal" : "Show All"}
                </button>
              </div>
            </div>

            <div className="space-y-4">
              {filteredRoutes.map((route, idx) => (
                <RouteCard
                  key={route.route_id}
                  route={route}
                  index={idx}
                  isRecommended={idx === 0 && !selectedCategory && !showAllRoutes} // Only recommend for optimal view
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
