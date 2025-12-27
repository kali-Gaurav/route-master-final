import { useState } from "react";
import { ChevronDown, ChevronUp, Clock, ArrowRight, Check, X, AlertTriangle, Train, Plane } from "lucide-react"; // Added Train and Plane icons
import { Route, formatDuration, formatCost, categoryIcons, categoryColors } from "@/data/routes"; // Added categoryIcons and categoryColors
import { cn } from "@/lib/utils";

interface RouteCardProps {
  route: Route;
  index: number;
  isRecommended?: boolean;
}

export function RouteCard({ route, index, isRecommended }: RouteCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Use categoryColors from routes.ts for consistent styling
  const getCategoryStyle = (category: string) => {
    const baseCategory = category.split(' ')[0].split('#')[0].trim(); // Extract base category
    const color = categoryColors[baseCategory.toUpperCase()] || "from-slate-500 to-gray-500";
    return color.replace("bg-", "from-") + " to-" + color.replace("bg-", "").split("-")[0] + "-400"; // Convert bg- to from-to gradients
  };

  const firstSegment = route.segments[0];
  const lastSegment = route.segments[route.segments.length - 1];

  return (
    <div
      className={cn(
        "bg-card rounded-2xl border-2 overflow-hidden transition-all duration-300",
        "hover:shadow-card hover:border-primary/30",
        isRecommended ? "border-primary shadow-soft" : "border-border",
        "animate-slide-in opacity-0"
      )}
      style={{ animationDelay: `${index * 0.1}s`, animationFillMode: "forwards" }}
    >
      {/* Header */}
      <div className="p-5">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "px-3 py-1.5 rounded-full text-white text-sm font-semibold",
                "bg-gradient-to-r",
                getCategoryStyle(route.category)
              )}
            >
              {categoryIcons[route.category.split(' ')[0].split('#')[0].trim().toUpperCase()]}{route.category}
            </div>
            {isRecommended && (
              <span className="px-2 py-1 bg-primary/10 text-primary text-xs font-semibold rounded-full">
                RECOMMENDED
              </span>
            )}
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-foreground">
              {formatCost(route.objectives.cost)}
            </div>
            <div className="text-sm text-muted-foreground">Total fare</div>
          </div>
        </div>

        {/* Journey Overview */}
        <div className="flex items-center gap-4 mb-4">
          <div className="flex-1">
            <div className="text-xs text-muted-foreground mb-1">DEPART</div>
            <div className="text-xl font-bold">{firstSegment.departure}</div>
            <div className="text-sm font-medium text-foreground">
              {firstSegment.from}
            </div>
          </div>
          
          <div className="flex-1 flex flex-col items-center">
            <div className="text-sm font-semibold text-muted-foreground">
              {formatDuration(route.objectives.time)}
            </div>
            <div className="w-full flex items-center gap-2 my-2">
              <div className="h-0.5 flex-1 bg-gradient-to-r from-primary to-accent" />
              <ArrowRight className="w-4 h-4 text-primary" />
            </div>
            <div className="text-xs text-muted-foreground">
              {route.objectives.transfers} transfer{route.objectives.transfers !== 1 ? "s" : ""}
            </div>
          </div>

          <div className="flex-1 text-right">
            <div className="text-xs text-muted-foreground mb-1">ARRIVE</div>
            <div className="text-xl font-bold">{lastSegment.arrival}</div>
            <div className="text-sm font-medium text-foreground">
              {lastSegment.to}
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-secondary/50 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-1">
              {route.objectives.seat_prob >= 50 ? (
                <Check className="w-4 h-4 text-green-500" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-amber-500" />
              )}
              <span className="text-xs text-muted-foreground">Seat Chance</span>
            </div>
            <div className="text-lg font-bold">{route.objectives.seat_prob.toFixed(0)}%</div>
          </div>
          <div className="bg-secondary/50 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Duration</span>
            </div>
            <div className="text-lg font-bold">{formatDuration(route.objectives.time)}</div>
          </div>
          <div className="bg-secondary/50 rounded-xl p-3">
            <div className="text-xs text-muted-foreground mb-1">Safety Score</div>
            <div className="flex items-center gap-2">
              <div className="text-lg font-bold">{route.objectives.safety_score}</div>
              <div className="flex-1 h-2 bg-border rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full"
                  style={{ width: `${route.objectives.safety_score}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Expand Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "w-full px-5 py-3 flex items-center justify-center gap-2",
          "bg-secondary/30 hover:bg-secondary/50 transition-colors",
          "text-sm font-medium text-muted-foreground"
        )}
      >
        {isExpanded ? (
          <>
            Hide Details <ChevronUp className="w-4 h-4" />
          </>
        ) : (
          <>
            View {route.segments.length} Segment{route.segments.length > 1 ? "s" : ""} <ChevronDown className="w-4 h-4" />
          </>
        )}
      </button>

      {/* Segments Detail */}
      {isExpanded && (
        <div className="p-5 bg-secondary/20 border-t border-border animate-fade-in">
          <div className="relative pl-8">
            {/* Timeline line */}
            <div className="absolute left-3 top-3 bottom-3 w-0.5 bg-gradient-to-b from-primary via-accent to-primary" />
            
            {route.segments.map((segment, idx) => (
              <div key={idx} className="relative mb-6 last:mb-0">
                {/* Timeline dot */}
                <div className="absolute -left-5 top-1 w-4 h-4 rounded-full bg-primary border-4 border-background" />
                
                <div className="bg-card rounded-xl p-4 border border-border">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                        {segment.type === 'train' ? (
                            <Train className="w-5 h-5 text-primary" />
                        ) : (
                            <Plane className="w-5 h-5 text-primary" />
                        )}
                      <div>
                        <div className="font-mono text-sm text-primary font-semibold">
                          {segment.segment_id}
                        </div>
                        <div className="font-medium text-foreground">
                          {segment.name} ({segment.type.toUpperCase()})
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                        <div className="font-bold text-foreground">{formatCost(segment.cost)}</div>
                        <div className={cn(
                            "px-2 py-1 rounded text-xs font-medium",
                            segment.seat_available >= 50
                            ? "bg-green-500/10 text-green-600" 
                            : "bg-red-500/10 text-red-600"
                        )}>
                            {segment.seat_available >= 50 ? "Seats Available" : "Waitlist"}
                        </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4 text-sm">
                    <div>
                      <div className="font-semibold">{segment.departure}</div>
                      <div className="text-muted-foreground">{segment.from}</div>
                    </div>
                    <div className="flex-1 flex flex-col items-center justify-center">
                      <div className="h-px w-full bg-border" />
                      <span className="text-xs text-muted-foreground my-1">
                        {formatDuration(segment.duration_min)}
                      </span>
                      <div className="h-px w-full bg-border" />
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">{segment.arrival}</div>
                      <div className="text-muted-foreground">{segment.to}</div>
                    </div>
                  </div>

                  {segment.wait_min > 0 && (
                    <div className="mt-3 pt-3 border-t border-border text-sm text-muted-foreground flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      <span>Wait time at {segment.from}: {formatDuration(segment.wait_min)}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
