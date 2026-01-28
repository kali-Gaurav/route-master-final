/**
 * Multi-Transfer Route API Service
 * Updated to use the unified FastAPI backend
 */

import { railwayAPI, type Route, type Station, type RouteSearchResponse, type StationSearchResponse } from './api';

// Re-export types for backward compatibility
export interface TransferRoute {
  from: string;
  to: string;
  transfers: number;
  route: string[];
  hops?: number;
  segments?: string[];
}

export interface RouteSearchResult {
  origin: string;
  destination: string;
  date: string;
  direct: TransferRoute[];
  one_transfer: TransferRoute[];
  two_transfer: TransferRoute[];
  three_transfer: TransferRoute[];
  metadata?: {
    timestamp: string;
    search_time_ms: number;
    total_routes: number;
  };
}

export interface TrainSchedule {
  train_no: string;
  train_name: string;
  schedule: any[];
}

export interface PriceInfo {
  origin: string;
  destination: string;
  prices: {
    train_no: string;
    class: string;
    fare: number;
  }[];
  avg_fare: number;
}

export interface SeatAvailability {
  train_no: string;
  availability: {
    station: string;
    '1A': number;
    '2A': number;
    '3A': number;
    'SL': number;
  }[];
}

export interface StationInfo {
  code: string;
  name: string;
}

/**
 * Search for multi-transfer routes between two stations
 * Updated to use the new FastAPI backend
 */
export async function searchRoutes(
  origin: string,
  destination: string,
  day: string = 'Mon',
  maxTransfers: number = 3
): Promise<RouteSearchResult> {
  try {
    const response: RouteSearchResponse = await railwayAPI.searchRoutes(origin, destination, maxTransfers);

    if (!response.success) {
      throw new Error('Route search failed');
    }

    // Convert new API response format to legacy format for backward compatibility
    const routes = response.data;

    // Group routes by transfer count
    const direct: TransferRoute[] = [];
    const one_transfer: TransferRoute[] = [];
    const two_transfer: TransferRoute[] = [];
    const three_transfer: TransferRoute[] = [];

    routes.forEach(route => {
      const transferRoute: TransferRoute = {
        from: route.origin,
        to: route.destination,
        transfers: route.total_transfers,
        route: route.segments.map(seg => seg.from_station).concat(route.segments[route.segments.length - 1].to_station),
        segments: route.segments.map(seg => seg.train_no.toString()),
      };

      switch (route.total_transfers) {
        case 0:
          direct.push(transferRoute);
          break;
        case 1:
          one_transfer.push(transferRoute);
          break;
        case 2:
          two_transfer.push(transferRoute);
          break;
        case 3:
          three_transfer.push(transferRoute);
          break;
      }
    });

    return {
      origin,
      destination,
      date: new Date().toISOString().split('T')[0],
      direct,
      one_transfer,
      two_transfer,
      three_transfer,
      metadata: {
        timestamp: new Date().toISOString(),
        search_time_ms: 0, // Not provided by new API
        total_routes: routes.length,
      },
    };
  } catch (error) {
    console.error('Route search error:', error);
    throw error;
  }
}

/**
 * Get list of stations for autocomplete
 * Updated to use the new FastAPI backend
 */
export async function getStations(search?: string): Promise<StationInfo[]> {
  try {
    const response: StationSearchResponse = await railwayAPI.searchStations(search, 50);

    if (!response.success) {
      throw new Error('Station search failed');
    }

    return response.data.map(station => ({
      code: station.code,
      name: station.name,
    }));
  } catch (error) {
    console.error('Station search error:', error);
    throw error;
  }
}

/**
 * Get train schedule (all stations and timings)
 * Note: This endpoint may not be available in the new API
 */
export async function getTrainSchedule(trainNo: string): Promise<TrainSchedule> {
  try {
    const response = await railwayAPI.getTrain(parseInt(trainNo));

    if (!response.success) {
      throw new Error('Train schedule fetch failed');
    }

    // Convert to legacy format
    return {
      train_no: trainNo,
      train_name: response.data.name,
      schedule: [], // Schedule data not available in current API
    };
  } catch (error) {
    console.error('Train schedule error:', error);
    throw error;
  }
}

/**
 * Get pricing for a specific route
 * Note: Pricing may not be available in the new API
 */
export async function getPrices(
  origin: string,
  destination: string
): Promise<PriceInfo> {
  // Pricing not implemented in current API
  throw new Error('Pricing information not available');
}

/**
 * Get seat availability for a train
 * Note: Seat availability may not be available in the new API
 */
export async function getSeatAvailability(trainNo: string): Promise<SeatAvailability> {
  // Seat availability not implemented in current API
  throw new Error('Seat availability not available');
}

/**
 * Health check endpoint
 * Updated to use the new FastAPI backend
 */
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await railwayAPI.health();
    return response.status === 'healthy';
  } catch {
    return false;
  }
}

/**
 * Get system statistics
 * Updated to use the new FastAPI backend
 */
export async function getStats() {
  try {
    const response = await railwayAPI.getStats();

    if (!response.success) {
      throw new Error('Stats fetch failed');
    }

    return {
      stations: response.data.stations,
      trains: response.data.trains,
      routes: response.data.routes,
      last_updated: response.data.last_updated,
    };
  } catch (error) {
    console.error('Stats error:', error);
    throw error;
  }
}

/**
 * Format route data for display
 */
export function formatRoute(route: TransferRoute): {
  displayText: string;
  stationCount: number;
  transferCount: number;
} {
  const stationCount = route.route?.length || 0;
  const transferCount = route.transfers || 0;

  let displayText = route.route?.join(' → ') || 'Unknown route';
  if (displayText.length > 100) {
    displayText = route.route?.[0] + ' → ... → ' + route.route?.[stationCount - 1] || displayText;
  }

  return {
    displayText,
    stationCount,
    transferCount,
  };
}

/**
 * Get transfer route details
 */
export async function getTransferRouteDetails(
  routes: TransferRoute[],
  transferCount: number
): Promise<Map<string, any>> {
  const details = new Map();

  for (const route of routes.slice(0, 3)) {
    // Limit to first 3 for performance
    try {
      const trains = route.segments || [];
      for (const trainNo of trains) {
        if (trainNo && !details.has(trainNo)) {
          try {
            const schedule = await getTrainSchedule(trainNo);
            details.set(trainNo, schedule);
          } catch (error) {
            console.error(`Failed to fetch details for train ${trainNo}:`, error);
          }
        }
      }
    } catch (error) {
      console.error(`Failed to fetch details for route:`, error);
    }
  }

  return details;
}
