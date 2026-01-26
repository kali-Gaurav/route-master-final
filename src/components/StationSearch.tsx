import { useState, useRef, useEffect, useCallback } from "react";
import { Search, MapPin, Loader2 } from "lucide-react";
import { cn, getApiUrl } from "@/lib/utils";

interface Station {
  code: string;
  name: string;
  city?: string;
  state?: string;
  id?: number;
}

interface StationSearchProps {
  label: string;
  placeholder: string;
  value: Station | null;
  onChange: (station: Station | null) => void;
  icon?: "origin" | "destination";
}

export function StationSearch({
  label,
  placeholder,
  value,
  onChange,
  icon = "origin",
}: StationSearchProps) {
  const [query, setQuery] = useState(value ? `${value.name} (${value.code})` : "");
  const [isOpen, setIsOpen] = useState(false);
  const [results, setResults] = useState<Station[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout>();

  // Fetch stations from API with proper error handling
  const fetchStations = useCallback(async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setResults([]);
      setIsOpen(false);
      setSearchError(null);
      return;
    }

    try {
      setIsLoading(true);
      setSearchError(null);
      
      const apiUrl = getApiUrl(`/api/stations?query=${encodeURIComponent(searchQuery)}&limit=15`);
      console.log("[StationSearch] Fetching from:", apiUrl);
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("[StationSearch] Results:", data);
      
      // Handle both { total, stations: [...] } and array formats
      const stations = Array.isArray(data) ? data : (data.stations || []);
      
      // Ensure stations have all required fields
      const enrichedStations = stations.map((station: any) => ({
        code: station.code || station.station_code || '',
        name: station.name || station.station_name || '',
        city: station.city || '',
        state: station.state || '',
        id: station.id,
      }));

      setResults(enrichedStations);
      setIsOpen(enrichedStations.length > 0);
    } catch (error) {
      console.error("[StationSearch] Error fetching stations:", error);
      setSearchError(error instanceof Error ? error.message : "Failed to fetch stations");
      setResults([]);
      setIsOpen(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced search handler
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    onChange(null);

    // Clear previous debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Debounce the API call by 300ms
    debounceTimerRef.current = setTimeout(() => {
      fetchStations(val);
    }, 300);
  };

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const handleSelect = (station: Station) => {
    setQuery(`${station.name} (${station.code})`);
    onChange(station);
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className="relative flex-1">
      <label className="block text-sm font-medium text-muted-foreground mb-2">
        {label}
      </label>
      <div className="relative">
        <div className="absolute left-4 top-1/2 -translate-y-1/2 z-10">
          {icon === "origin" ? (
            <div className="w-3 h-3 rounded-full bg-green-500 ring-4 ring-green-500/20" />
          ) : (
            <MapPin className="w-5 h-5 text-primary" />
          )}
        </div>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => {
            if (query.length >= 2 && results.length > 0) {
              setIsOpen(true);
            }
          }}
          placeholder={placeholder}
          autoComplete="off"
          className={cn(
            "w-full pl-12 pr-12 py-4 rounded-xl",
            "bg-card border-2 border-border",
            "text-foreground placeholder:text-muted-foreground",
            "focus:border-primary focus:ring-4 focus:ring-primary/10",
            "transition-all duration-200 outline-none",
            "text-lg font-medium"
          )}
        />
        <div className="absolute right-4 top-1/2 -translate-y-1/2">
          {isLoading ? (
            <Loader2 className="w-5 h-5 text-muted-foreground animate-spin" />
          ) : (
            <Search className="w-5 h-5 text-muted-foreground" />
          )}
        </div>
      </div>

      {/* Error message display */}
      {searchError && (
        <div className="mt-2 p-2 bg-destructive/10 border border-destructive/20 rounded-lg">
          <p className="text-xs text-destructive">{searchError}</p>
        </div>
      )}

      {/* Results dropdown */}
      {isOpen && results.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-card border border-border rounded-xl shadow-card overflow-y-auto max-h-80 animate-fade-in custom-scrollbar">
          {results.map((station, idx) => (
            <button
              key={`${station.code}-${station.name}`}
              onClick={() => handleSelect(station)}
              className={cn(
                "w-full px-4 py-3 text-left",
                "hover:bg-primary/10 transition-colors",
                "flex items-center gap-3",
                idx !== results.length - 1 && "border-b border-border/50"
              )}
            >
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center font-mono text-sm font-bold text-primary">
                {station.code}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-foreground truncate">
                  {station.name}
                </div>
                {(station.city || station.state) && (
                  <div className="text-sm text-muted-foreground">
                    {[station.city, station.state].filter(Boolean).join(", ")}
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* No results message */}
      {isOpen && query.length >= 2 && results.length === 0 && !isLoading && !searchError && (
        <div className="absolute z-50 w-full mt-2 bg-card border border-border rounded-xl shadow-card p-4 text-center">
          <p className="text-sm text-muted-foreground">
            No stations found for "{query}"
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Try searching by station name, code, or city
          </p>
        </div>
      )}
    </div>
  );
}
