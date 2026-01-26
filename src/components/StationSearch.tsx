import { useState, useRef, useEffect, useCallback } from "react";
import { Search, MapPin, Loader2, Landmark } from "lucide-react";
import React from "react";
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
  const [results, setResults] = useState<any[]>([]);
  const [groupedCity, setGroupedCity] = useState<string | null>(null);
  const [highlightedIdx, setHighlightedIdx] = useState<number>(-1);
  const [isLoading, setIsLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout>();
  const resultsCache = useRef<Map<string, any[]>>(new Map());

  // Scroll highlighted item into view
  useEffect(() => {
    if (highlightedIdx >= 0 && dropdownRef.current) {
      const highlightedElement = dropdownRef.current.querySelector(`[data-idx="${highlightedIdx}"]`) as HTMLElement;
      if (highlightedElement) {
        highlightedElement.scrollIntoView({
          block: 'nearest',
          behavior: 'smooth'
        });
      }
    }
  }, [highlightedIdx]);

  // Fetch stations from API with proper error handling and caching
  const fetchStations = useCallback(async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setResults([]);
      setGroupedCity(null);
      setIsOpen(false);
      setSearchError(null);
      return;
    }

    // Check cache first
    const cacheKey = searchQuery.toLowerCase();
    if (resultsCache.current.has(cacheKey)) {
      const cachedResults = resultsCache.current.get(cacheKey)!;
      // Detect city_hubs result: all stations have same city and type is STATION or present
      if (cachedResults.length > 0 && cachedResults.every((s: any) => s.city && s.city.toLowerCase() === searchQuery.toLowerCase())) {
        setGroupedCity(cachedResults[0].city);
      } else {
        setGroupedCity(null);
      }
      setResults(cachedResults);
      setIsOpen(cachedResults.length > 0);
      setHighlightedIdx(-1);
      return;
    }

    try {
      setIsLoading(true);
      setSearchError(null);
      setGroupedCity(null);
      const apiUrl = getApiUrl(`/api/stations?query=${encodeURIComponent(searchQuery)}&limit=15`);
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
      const stations = Array.isArray(data) ? data : (data.stations || []);
      // Cache the results
      resultsCache.current.set(cacheKey, stations);
      // Detect city_hubs result: all stations have same city and type is STATION or present
      if (stations.length > 0 && stations.every((s: any) => s.city && s.city.toLowerCase() === searchQuery.toLowerCase())) {
        setGroupedCity(stations[0].city);
      } else {
        setGroupedCity(null);
      }
      setResults(stations);
      setIsOpen(stations.length > 0);
      setHighlightedIdx(-1);
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : "Failed to fetch stations");
      setResults([]);
      setGroupedCity(null);
      setIsOpen(false);
      setHighlightedIdx(-1);
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
    setHighlightedIdx(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIdx(prev => 
          prev < results.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIdx(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIdx >= 0 && highlightedIdx < results.length) {
          handleSelect(results[highlightedIdx]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        setHighlightedIdx(-1);
        break;
    }
  };

  const handleBlur = () => {
    // Delay to allow click on dropdown
    setTimeout(() => {
      if (!value && query.trim()) {
        // If no station selected and query is not empty, clear it
        setQuery("");
        setSearchError("Please select a valid station from the list");
        setTimeout(() => setSearchError(null), 3000);
      }
      setIsOpen(false);
      setHighlightedIdx(-1);
    }, 150);
  };

  // Highlight matched text utility
  function highlightMatch(text: string, query: string) {
    if (!query) return text;
    const idx = text.toLowerCase().indexOf(query.toLowerCase());
    if (idx === -1) return text;
    return <>
      {text.slice(0, idx)}
      <span className="bg-primary/20 font-bold">{text.slice(idx, idx + query.length)}</span>
      {text.slice(idx + query.length)}
    </>;
  }

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
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
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

      {/* Results dropdown with city grouping and icons */}
      {isOpen && results.length > 0 && (
        <div ref={dropdownRef} className="absolute z-50 w-full mt-2 bg-card border border-border rounded-xl shadow-card overflow-y-auto max-h-80 animate-fade-in custom-scrollbar">
          {groupedCity ? (
            <>
              <div className="flex items-center gap-2 px-4 py-2 bg-muted/30 border-b border-border/50">
                <Landmark className="w-5 h-5 text-primary" />
                <span className="font-bold text-primary">{highlightMatch(groupedCity, query)}</span>
                <span className="ml-2 text-xs text-muted-foreground">(City)</span>
              </div>
              {results.map((station, idx) => (
                <button
                  key={`${station.code}-${station.name}`}
                  data-idx={idx}
                  onClick={() => handleSelect(station)}
                  className={cn(
                    "w-full px-4 py-3 text-left",
                    "hover:bg-primary/10 transition-colors",
                    "flex items-center gap-3",
                    idx !== results.length - 1 && "border-b border-border/50",
                    idx === highlightedIdx && "bg-primary/10"
                  )}
                >
                  <MapPin className="w-5 h-5 text-muted-foreground" />
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-foreground truncate">
                      {highlightMatch(station.name, query)}
                      <span className="ml-2 font-mono text-xs text-primary">{station.code}</span>
                    </div>
                    {(station.state) && (
                      <div className="text-xs text-muted-foreground">
                        {station.state}
                      </div>
                    )}
                  </div>
                </button>
              ))}
            </>
          ) : (
            results.map((station, idx) => (
              <button
                key={`${station.code}-${station.name}`}
                data-idx={idx}
                onClick={() => handleSelect(station)}
                className={cn(
                  "w-full px-4 py-3 text-left",
                  "hover:bg-primary/10 transition-colors",
                  "flex items-center gap-3",
                  idx !== results.length - 1 && "border-b border-border/50",
                  idx === highlightedIdx && "bg-primary/10"
                )}
              >
                <MapPin className="w-5 h-5 text-muted-foreground" />
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-foreground truncate">
                    {highlightMatch(station.name, query)}
                    <span className="ml-2 font-mono text-xs text-primary">{station.code}</span>
                  </div>
                  {(station.city || station.state) && (
                    <div className="text-xs text-muted-foreground">
                      {[station.city, station.state].filter(Boolean).join(", ")}
                    </div>
                  )}
                </div>
              </button>
            ))
          )}
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
