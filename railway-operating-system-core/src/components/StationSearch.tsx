import { useState, useRef, useEffect, useCallback } from "react";
import { Search, MapPin, Loader2, Landmark, X } from "lucide-react";
import React from "react";
import { cn } from "@/lib/utils";
import { searchStations as searchStationsLocal, Station as StationType, getStationByCode } from "@/data/stations";

interface StationSearchProps {
  label: string;
  placeholder: string;
  value: StationType | null;
  onChange: (station: StationType | null) => void;
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

  // Search stations locally with instant results and smart caching
  const searchStations = useCallback((searchQuery: string) => {
    if (searchQuery.length < 2) {
      setResults([]);
      setGroupedCity(null);
      setIsOpen(false);
      setSearchError(null);
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setSearchError(null);
      
      // Check cache first (instant)
      const cacheKey = searchQuery.toLowerCase();
      if (resultsCache.current.has(cacheKey)) {
        const cachedResults = resultsCache.current.get(cacheKey)!;
        setResults(cachedResults);
        // Detect city grouping: all results from same city
        if (cachedResults.length > 0 && cachedResults.every((s: any) => s.city && s.city.toLowerCase() === searchQuery.toLowerCase())) {
          setGroupedCity(cachedResults[0].city);
        } else {
          setGroupedCity(null);
        }
        setIsOpen(cachedResults.length > 0);
        setHighlightedIdx(-1);
        setIsLoading(false);
        return;
      }

      // Local search (fast - no API call)
      const results = searchStationsLocal(searchQuery);
      
      // Cache the results
      resultsCache.current.set(cacheKey, results);
      
      // Detect city grouping: if all results from same city, show city header
      if (results.length > 0 && results.every((s: any) => s.city && s.city.toLowerCase() === searchQuery.toLowerCase())) {
        setGroupedCity(results[0].city);
      } else {
        setGroupedCity(null);
      }
      
      setResults(results);
      setIsOpen(results.length > 0);
      setHighlightedIdx(-1);
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : "Search failed");
      setResults([]);
      setGroupedCity(null);
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

  // Debounced search handler - uses local search (no API call needed)
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    onChange(null);

    // Clear previous debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Local search is fast, but still debounce for better UX (100ms instead of 300ms)
    debounceTimerRef.current = setTimeout(() => {
      searchStations(val);
    }, 100);
  };

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const handleSelect = (station: StationType) => {
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
    // Delay to allow click on dropdown items (150ms is enough for button click to register)
    setTimeout(() => {
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
            "w-full pl-10 pr-10 py-2 rounded-xl",
            "bg-card border-2 border-border",
            "text-foreground placeholder:text-muted-foreground",
            "focus:border-primary focus:ring-4 focus:ring-primary/10",
            "transition-all duration-200 outline-none",
            "text-base font-medium"
          )}
        />
        <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
          {query && (
            <button
              type="button"
              onMouseDown={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setQuery("");
                setResults([]);
                setIsOpen(false);
                onChange(null);
              }}
              className="text-muted-foreground hover:text-foreground transition-colors"
              title="Clear"
            >
              <X className="w-5 h-5" />
            </button>
          )}
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
                  type="button"
                  key={`${station.code}-${station.name}`}
                  data-idx={idx}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleSelect(station);
                  }}
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
                type="button"
                key={`${station.code}-${station.name}`}
                data-idx={idx}
                onMouseDown={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handleSelect(station);
                }}
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
