import { useState, useRef, useEffect } from "react";
import { Search, MapPin } from "lucide-react";
import { cn } from "@/lib/utils";

interface Station {
  code: string;
  name: string;
  city: string;
  state: string;
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
  const [allStations, setAllStations] = useState<Station[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Fetch all stations on component mount
  useEffect(() => {
    const fetchStations = async () => {
      try {
        setIsLoading(true);
        const response = await fetch('http://localhost:5000/api/stations?limit=5000');
        if (response.ok) {
          const data = await response.json();
          // API returns { total, stations: [...] }
          const stations = data.stations || data || [];
          setAllStations(stations);
        } else {
          console.error('Failed to fetch stations');
        }
      } catch (error) {
        console.error('Error fetching stations:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStations();
  }, []);

  useEffect(() => {
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
    if (val.length >= 2) {
      // Filter stations based on query
      const filtered = allStations.filter(station =>
        station.name.toLowerCase().includes(val.toLowerCase()) ||
        station.code.toLowerCase().includes(val.toLowerCase()) ||
        station.city.toLowerCase().includes(val.toLowerCase())
      ).slice(0, 10); // Limit to 10 results
      setResults(filtered);
      setIsOpen(true);
    } else {
      setResults([]);
      setIsOpen(false);
    }
    onChange(null);
  };

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
          onFocus={() => query.length >= 2 && setIsOpen(true)}
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
        <div className="absolute z-50 w-full mt-2 bg-card border border-border rounded-xl shadow-card overflow-y-auto max-h-80 animate-fade-in custom-scrollbar">
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
                <div className="text-sm text-muted-foreground">
                  {station.city}, {station.state}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
