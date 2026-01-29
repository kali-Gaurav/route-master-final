import { useState } from "react";
import { ChevronDown, ChevronUp, Clock, ArrowRight, Check, AlertTriangle } from "lucide-react";
import { Route, formatDuration, formatCost, formatLiveFare, getAvailabilityBadgeClasses, summarizeAvailability, getSeatAvailabilityState } from "@/data/routes";
import { getStationByCode } from "@/data/stations";
import { cn } from "@/lib/utils";

interface RouteCardProps {
  route: Route;
  index: number;
  isRecommended?: boolean;
}

export function RouteCard({ route, index, isRecommended }: RouteCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getCategoryStyle = (category: string) => {
    if (category.includes("FASTEST") || category.includes("FAST")) {
      return "from-amber-500 to-orange-500";
    }
    if (category.includes("DIRECT")) {
      return "from-blue-500 to-cyan-500";
    }
    if (category.includes("SEAT")) {
      return "from-green-500 to-emerald-500";
    }
    if (category.includes("CHEAP")) {
      return "from-emerald-500 to-teal-500";
    }
    if (category.includes("BALANCED")) {
      return "from-purple-500 to-violet-500";
    }
    return "from-slate-500 to-gray-500";
  };

  const firstSegment = route.segments[0];
  const lastSegment = route.segments[route.segments.length - 1];
  const availabilitySummary = summarizeAvailability(route.segments);
  const availabilityBadgeClasses = getAvailabilityBadgeClasses(availabilitySummary.state);
  const liveFareDisplay = formatLiveFare(route.liveFareTotal ?? route.totalCost);

  return (
    <div className="bg-card rounded-2xl border-2 overflow-hidden transition-all duration-300 hover:shadow-card hover:border-primary/30 border-primary shadow-soft animate-slide-in opacity-0"
         style={{ animationDelay: `${index * 0.1}s`, animationFillMode: "forwards" }}>
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
              {route.category}
            </div>
            {isRecommended && (
              <span className="px-2 py-1 bg-green-500/10 text-green-600 dark:text-green-400 text-xs font-semibold rounded-full border border-green-500/20">
                🏆 Best
              </span>
            )}
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-foreground">
              {formatCost(route.totalCost)}
            </div>
            <div className="text-sm text-muted-foreground">Total fare</div>
          </div>
        </div>

        {/* Main Content */}
        <div className="px-5 pb-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-foreground">
                {getStationByCode(firstSegment.fromStation)?.name || firstSegment.fromStation}
              </span>
              <span className="text-muted-foreground">→</span>
              <span className="text-sm font-semibold text-foreground">
                {getStationByCode(lastSegment.toStation)?.name || lastSegment.toStation}
              </span>
            </div>
            <div className={cn("px-2 py-1 rounded-md text-xs font-semibold", availabilityBadgeClasses)}>
              {availabilitySummary.summary}
            </div>
          </div>
          
          <div className="flex items-center justify-between text-sm mb-3">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Clock size={16} />
              <span>{firstSegment.departure}</span>
              <span>→</span>
              <span>{lastSegment.arrival}</span>
            </div>
            <span className="font-semibold">{formatDuration(route.totalTime)}</span>
          </div>

          {route.totalTransfers > 0 && (
            <div className="text-xs text-muted-foreground mb-3">
              {route.totalTransfers} transfer{route.totalTransfers > 1 ? 's' : ''}
            </div>
          )}

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full flex items-center justify-between text-sm font-semibold text-primary hover:text-primary/80 transition-colors"
          >
            <span>{isExpanded ? 'Hide Details' : 'View Details'}</span>
            {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>
        </div>
      </div>

      {/* Segments Detail */}
      {isExpanded && (
        <div className="p-5 bg-secondary/20 border-t border-border space-y-4 animate-fade-in">
          {route.segments.map((segment, idx) => (
            <div key={idx} className="border border-border rounded-lg p-4 bg-card/50">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-sm">
                  Train {segment.trainNumber}
                </span>
                <span className={cn("text-xs font-semibold px-2 py-1 rounded", getAvailabilityBadgeClasses(getSeatAvailabilityState(segment.liveSeatAvailability)))}>
                  {segment.liveSeatAvailability} seats
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground mb-2">
                <div>
                  <div className="text-foreground font-semibold">{segment.departure}</div>
                  <div>{getStationByCode(segment.fromStation)?.name}</div>
                </div>
                <div className="text-right">
                  <div className="text-foreground font-semibold">{segment.arrival}</div>
                  <div>{getStationByCode(segment.toStation)?.name}</div>
                </div>
              </div>
              {segment.liveFare && (
                <div className="text-xs text-primary font-semibold">
                  {formatLiveFare(segment.liveFare)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
