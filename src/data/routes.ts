// Route data structure matching the CSV format
export interface RouteSegment {
  routeId: string;
  category: string;
  segment: number;
  trainNumber: string;
  trainName: string;
  from: string;
  to: string;
  departure: string;
  arrival: string;
  distance: number;
  duration: number;
  waitBefore: number;
  seatAvailable: boolean;
}

export interface Route {
  id: string;
  category: string;
  segments: RouteSegment[];
  totalTime: number;
  totalCost: number;
  totalTransfers: number;
  seatProbability: number;
  safetyScore: number;
}

export const categoryIcons: Record<string, string> = {
  "FASTEST": "⚡",
  "MOST DIRECT": "🚂",
  "BEST SEATS": "💺",
  "FAST": "⚡",
  "CHEAP": "💰",
  "BALANCED": "⚖️",
  "ALTERNATIVE": "🔄",
};

export const categoryColors: Record<string, string> = {
  "FASTEST": "bg-amber-500",
  "MOST DIRECT": "bg-blue-500",
  "BEST SEATS": "bg-green-500",
  "FAST": "bg-orange-500",
  "CHEAP": "bg-emerald-500",
  "BALANCED": "bg-purple-500",
  "ALTERNATIVE": "bg-slate-500",
};

// Sample data from PGT to KOTA
export const sampleRoutes: Route[] = [
  {
    id: "ROUTE_01",
    category: "FASTEST ⚡",
    segments: [
      {
        routeId: "ROUTE_01",
        category: "FASTEST ⚡",
        segment: 1,
        trainNumber: "22476",
        trainName: "CBE BKN AC S",
        from: "PGT",
        to: "BRC",
        departure: "16:20",
        arrival: "19:31",
        distance: 1598,
        duration: 1598,
        waitBefore: 0,
        seatAvailable: false,
      },
      {
        routeId: "ROUTE_01",
        category: "FASTEST ⚡",
        segment: 2,
        trainNumber: "12907",
        trainName: "BDTS SMPRK K",
        from: "BRC",
        to: "KOTA",
        departure: "23:12",
        arrival: "06:20",
        distance: 527,
        duration: 575,
        waitBefore: 221,
        seatAvailable: false,
      },
    ],
    totalTime: 2394,
    totalCost: 2125,
    totalTransfers: 1,
    seatProbability: 0,
    safetyScore: 100,
  },
  {
    id: "ROUTE_02",
    category: "MOST DIRECT 🚂",
    segments: [
      {
        routeId: "ROUTE_02",
        category: "MOST DIRECT 🚂",
        segment: 1,
        trainNumber: "22476",
        trainName: "CBE BKN AC S",
        from: "PGT",
        to: "BRC",
        departure: "16:20",
        arrival: "19:31",
        distance: 1598,
        duration: 1598,
        waitBefore: 0,
        seatAvailable: false,
      },
      {
        routeId: "ROUTE_02",
        category: "MOST DIRECT 🚂",
        segment: 2,
        trainNumber: "12431",
        trainName: "TVC-NZM RAJD",
        from: "BRC",
        to: "KOTA",
        departure: "00:24",
        arrival: "06:45",
        distance: 528,
        duration: 576,
        waitBefore: 293,
        seatAvailable: true,
      },
    ],
    totalTime: 2467,
    totalCost: 2126,
    totalTransfers: 1,
    seatProbability: 50,
    safetyScore: 100,
  },
  {
    id: "ROUTE_03",
    category: "BEST SEATS 💺",
    segments: [
      {
        routeId: "ROUTE_03",
        category: "BEST SEATS 💺",
        segment: 1,
        trainNumber: "16791",
        trainName: "PUU-PGT PALA",
        from: "PGT",
        to: "KKZ",
        departure: "13:20",
        arrival: "03:41",
        distance: 328,
        duration: 394,
        waitBefore: 0,
        seatAvailable: true,
      },
      {
        routeId: "ROUTE_03",
        category: "BEST SEATS 💺",
        segment: 2,
        trainNumber: "12483",
        trainName: "KCVL EXPRESS",
        from: "QLN",
        to: "KOTA",
        departure: "10:25",
        arrival: "02:55",
        distance: 2329,
        duration: 2409,
        waitBefore: 350,
        seatAvailable: true,
      },
    ],
    totalTime: 3192,
    totalCost: 2682,
    totalTransfers: 5,
    seatProbability: 83.33,
    safetyScore: 80,
  },
  {
    id: "ROUTE_04",
    category: "CHEAP 💰",
    segments: [
      {
        routeId: "ROUTE_04",
        category: "CHEAP 💰",
        segment: 1,
        trainNumber: "22476",
        trainName: "CBE BKN AC S",
        from: "PGT",
        to: "BRC",
        departure: "16:20",
        arrival: "19:31",
        distance: 1598,
        duration: 1598,
        waitBefore: 0,
        seatAvailable: false,
      },
      {
        routeId: "ROUTE_04",
        category: "CHEAP 💰",
        segment: 2,
        trainNumber: "22413",
        trainName: "MAO-NZM RAJD",
        from: "BRC",
        to: "KOTA",
        departure: "00:24",
        arrival: "06:45",
        distance: 527,
        duration: 575,
        waitBefore: 293,
        seatAvailable: true,
      },
    ],
    totalTime: 2466,
    totalCost: 2125,
    totalTransfers: 1,
    seatProbability: 50,
    safetyScore: 95,
  },
  {
    id: "ROUTE_05",
    category: "BALANCED ⚖️",
    segments: [
      {
        routeId: "ROUTE_05",
        category: "BALANCED ⚖️",
        segment: 1,
        trainNumber: "22476",
        trainName: "CBE BKN AC S",
        from: "PGT",
        to: "BRC",
        departure: "16:20",
        arrival: "19:31",
        distance: 1598,
        duration: 1598,
        waitBefore: 0,
        seatAvailable: false,
      },
      {
        routeId: "ROUTE_05",
        category: "BALANCED ⚖️",
        segment: 2,
        trainNumber: "12247",
        trainName: "BDTS NZM YUV",
        from: "BRC",
        to: "RTM",
        departure: "21:46",
        arrival: "01:05",
        distance: 262,
        duration: 349,
        waitBefore: 135,
        seatAvailable: true,
      },
      {
        routeId: "ROUTE_05",
        category: "BALANCED ⚖️",
        segment: 3,
        trainNumber: "12247",
        trainName: "BDTS NZM YUV",
        from: "RTM",
        to: "KOTA",
        departure: "01:10",
        arrival: "03:40",
        distance: 265,
        duration: 353,
        waitBefore: 0,
        seatAvailable: true,
      },
    ],
    totalTime: 2436,
    totalCost: 2125,
    totalTransfers: 2,
    seatProbability: 66.67,
    safetyScore: 95,
  },
  {
    id: "ROUTE_06",
    category: "ALTERNATIVE 🔄",
    segments: [
      {
        routeId: "ROUTE_06",
        category: "ALTERNATIVE 🔄",
        segment: 1,
        trainNumber: "12258",
        trainName: "KCVL-YPR EXP",
        from: "PGT",
        to: "CBE",
        departure: "00:15",
        arrival: "01:37",
        distance: 55,
        duration: 87,
        waitBefore: 0,
        seatAvailable: false,
      },
      {
        routeId: "ROUTE_06",
        category: "ALTERNATIVE 🔄",
        segment: 2,
        trainNumber: "12969",
        trainName: "CBE JAIPUR E",
        from: "ED",
        to: "UJN",
        departure: "10:50",
        arrival: "21:25",
        distance: 2058,
        duration: 2129,
        waitBefore: 460,
        seatAvailable: true,
      },
      {
        routeId: "ROUTE_06",
        category: "ALTERNATIVE 🔄",
        segment: 3,
        trainNumber: "19021",
        trainName: "BDTS LJN EXP",
        from: "BWM",
        to: "KOTA",
        departure: "01:10",
        arrival: "02:40",
        distance: 100,
        duration: 158,
        waitBefore: 32,
        seatAvailable: true,
      },
    ],
    totalTime: 3301,
    totalCost: 2489,
    totalTransfers: 7,
    seatProbability: 75,
    safetyScore: 70,
  },
];

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
  const base = category.split(' ')[0].split('#')[0];
  return base.replace(/[^A-Z]/g, '');
};
