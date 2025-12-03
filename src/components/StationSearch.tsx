import { useState, useRef, useEffect } from "react";
import { Search, MapPin } from "lucide-react";
import { Station, searchStations } from "@/data/stations";
import { cn } from "@/lib/utils";

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
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

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
      const found = searchStations(val);
      setResults(found);
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
        <div className="absolute z-50 w-full mt-2 bg-card border border-border rounded-xl shadow-card overflow-hidden animate-fade-in">
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
