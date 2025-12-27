// Route data structure matching the API format
export interface RouteSegment {
  type: 'train' | 'flight'; // Added type to distinguish segments
  segment_id: string; // Changed from trainNumber
  name: string; // Changed from trainName
  from: string;
  to: string;
  departure: string;
  arrival: string;
  distance: number;
  duration_min: number; // Changed from duration
  wait_min: number; // Changed from waitBefore
  cost: number; // Added cost per segment
  seat_available: number; // Changed from seatAvailable (now a number for probability)
}

export interface RouteObjective {
  time: number;
  cost: number;
  transfers: number;
  seat_prob: number;
  safety_score: number;
  distance: number;
}

export interface Route {
  route_id: string; // Changed from id
  category: string;
  objectives: RouteObjective; // Encapsulated objectives
  segments: RouteSegment[];
}

export const categoryIcons: Record<string, string> = {
  "FASTEST": "⚡",
  "MOST DIRECT": "🚂",
  "BEST SEATS": "💺",
  "FAST": "⚡",
  "CHEAP": "💰",
  "BALANCED": "⚖️",
  "OPTIMAL ALTERNATIVE": "🎯", // Changed from ALTERNATIVE
};

export const categoryColors: Record<string, string> = {
  "FASTEST": "bg-amber-500",
  "MOST DIRECT": "bg-blue-500",
  "BEST SEATS": "bg-green-500",
  "FAST": "bg-orange-500",
  "CHEAP": "bg-emerald-500",
  "BALANCED": "bg-purple-500",
  "OPTIMAL ALTERNATIVE": "bg-slate-500", // Changed from ALTERNATIVE
};

export const formatDuration = (minutes: number): string => {
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  if (hours > 0) {
    return `${hours}h ${mins}m`;
  }
  return `${mins}m`;
};

export const formatCost = (cost: number): string => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(cost);
};

export const getCategoryBase = (category: string): string => {
  // Extract the base category name, handling potential numbers like "FAST #1"
  const match = category.match(/^([A-Z\s]+?)(?: #\d+)?(?: \S+)?$/);
  return match ? match[1].trim() : category;
};
