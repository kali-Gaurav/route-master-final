import { cn } from "@/lib/utils";

interface RouteSkeletonProps {
  count?: number;
}

export function RouteSkeleton({ count = 3 }: RouteSkeletonProps) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, idx) => (
        <div
          key={idx}
          className="bg-card rounded-2xl border-2 border-border p-5 animate-pulse"
          style={{ animationDelay: `${idx * 0.1}s` }}
        >
          {/* Header */}
          <div className="flex items-start justify-between gap-4 mb-4">
            <div className="flex items-center gap-3">
              {/* Category badge */}
              <div className="h-8 w-32 bg-secondary rounded-full" />
              <div className="h-6 w-20 bg-secondary rounded-full" />
            </div>
            <div className="text-right">
              <div className="h-8 w-24 bg-secondary rounded-lg mb-1 ml-auto" />
              <div className="h-4 w-20 bg-secondary rounded" />
            </div>
          </div>

          {/* Journey Overview */}
          <div className="flex items-center gap-4 mb-4">
            <div className="flex-1">
              <div className="h-3 w-16 bg-secondary rounded mb-2" />
              <div className="h-6 w-20 bg-secondary rounded mb-1" />
              <div className="h-4 w-32 bg-secondary rounded" />
            </div>
            
            <div className="flex-1 flex flex-col items-center">
              <div className="h-4 w-20 bg-secondary rounded mb-2" />
              <div className="w-full h-1 bg-secondary rounded my-2" />
              <div className="h-3 w-40 bg-secondary rounded" />
            </div>

            <div className="flex-1 text-right">
              <div className="h-3 w-16 bg-secondary rounded mb-2 ml-auto" />
              <div className="h-6 w-20 bg-secondary rounded mb-1 ml-auto" />
              <div className="h-4 w-32 bg-secondary rounded ml-auto" />
            </div>
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-4 gap-3 pt-4 border-t border-border">
            {[1, 2, 3, 4].map((i) => (
              <div key={i}>
                <div className="h-3 w-12 bg-secondary rounded mb-1" />
                <div className="h-5 w-16 bg-secondary rounded" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
