import { useState, useRef, useEffect } from "react";
import { Search, MapPin } from "lucide-react";
import { cn } from "@/lib/utils";

// Simplified station type to match our new data source
export interface Station {
  code: string;
  name: string;
}

// Store stations in a module-level variable to fetch only once
let allStations: Station[] = [];
let isFetching = false;

const fetchStations = async () => {
  if (allStations.length > 0 || isFetching) return;
  isFetching = true;
  try {
    const response = await fetch('/city_mapping.json');
    const data = await response.json();
    // Assuming the JSON has a "cities" array: ["city1", "city2", ...]
    allStations = data.cities.map((city: string) => ({ code: city, name: city }));
    console.log(`Loaded ${allStations.length} stations.`);
  } catch (error) {
    console.error("Failed to load city_mapping.json", error);
    // Handle error, maybe set a state to show an error message
  } finally {
    isFetching = false;
  }
};


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
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Fetch station data when the component mounts
    fetchStations();

    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    
    // Only search if we have stations and query is long enough
    if (allStations.length > 0 && val.length >= 3) {
      const lowerQuery = val.toLowerCase();
      const found = allStations.filter(
        s => 
          s.code.toLowerCase().includes(lowerQuery) ||
          s.name.toLowerCase().includes(lowerQuery)
      ).slice(0, 10); // Limit results for performance
      setResults(found);
      setIsOpen(true);
    } else {
      setResults([]);
      setIsOpen(false);
    }
    // Clear selection if input changes
    if (value) onChange(null);
  };

  const handleSelect = (station: Station) => {
    setQuery(station.name);
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
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => query.length >= 3 && results.length > 0 && setIsOpen(true)}
          placeholder={placeholder}
          className={cn(
            "w-full pl-12 pr-12 py-4 rounded-xl",
            "bg-card border-2 border-border",
            "text-foreground placeholder:text-muted-foreground",
            "focus:border-primary focus:ring-4 focus:ring-primary/10",
            "transition-all duration-200 outline-none",
            "text-lg font-medium"
          )}
        />
        <Search className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
      </div>

      {isOpen && results.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-card border border-border rounded-xl shadow-card overflow-hidden animate-fade-in max-h-60 overflow-y-auto">
          {results.map((station, idx) => (
            <button
              key={station.code}
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
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
