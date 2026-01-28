/**
 * Railway API Service
 * Unified API client for the FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Station {
  code: string;
  name: string;
  state?: string;
  zone?: string;
}

export interface RouteSegment {
  train_no: number;
  train_name: string;
  from_station: string;
  to_station: string;
  departure_time: string;
  arrival_time: string;
  days_running: string;
}

export interface Route {
  route_id: string;
  origin: string;
  destination: string;
  segments: RouteSegment[];
  total_transfers: number;
  total_duration: string;
  fare: number;
}

export interface RouteSearchResponse {
  success: boolean;
  data: Route[];
  total: number;
  origin_info?: Station;
  destination_info?: Station;
}

export interface StationSearchResponse {
  success: boolean;
  data: Station[];
  total: number;
}

export interface Train {
  train_no: number;
  name: string;
  origin: string;
  destination: string;
}

export interface TrainResponse {
  success: boolean;
  data: Train;
}

export interface StatsResponse {
  success: boolean;
  data: {
    stations: number;
    trains: number;
    routes: number;
    last_updated: string;
  };
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  database: string;
  version: string;
}

/**
 * Railway API Service Class
 */
export class RailwayAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Network error' }));
        throw new Error(error.detail || error.error || `HTTP ${response.status}`);
      }

      return response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  /**
   * Health check
   */
  async health(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  /**
   * Search stations
   */
  async searchStations(query?: string, limit: number = 20): Promise<StationSearchResponse> {
    const params = new URLSearchParams();
    if (query) params.append('search', query);
    params.append('limit', limit.toString());

    return this.request<StationSearchResponse>(`/api/v1/stations?${params}`);
  }

  /**
   * Get station details
   */
  async getStation(code: string): Promise<Station> {
    const response = await this.request<{ success: boolean; data: Station }>(`/api/v1/stations/${code}`);
    return response.data;
  }

  /**
   * Search routes
   */
  async searchRoutes(
    origin: string,
    destination: string,
    maxTransfers: number = 3
  ): Promise<RouteSearchResponse> {
    return this.request<RouteSearchResponse>('/api/v1/routes/search', {
      method: 'POST',
      body: JSON.stringify({
        origin: origin.toUpperCase(),
        destination: destination.toUpperCase(),
        max_transfers: maxTransfers,
      }),
    });
  }

  /**
   * Search routes (GET version)
   */
  async searchRoutesGet(
    origin: string,
    destination: string,
    maxTransfers: number = 3
  ): Promise<RouteSearchResponse> {
    const params = new URLSearchParams({
      origin: origin.toUpperCase(),
      destination: destination.toUpperCase(),
      max_transfers: maxTransfers.toString(),
    });

    return this.request<RouteSearchResponse>(`/api/v1/routes?${params}`);
  }

  /**
   * Get all trains
   */
  async getTrains(limit: number = 50): Promise<{ success: boolean; data: Train[]; total: number }> {
    const params = new URLSearchParams({ limit: limit.toString() });
    return this.request(`/api/v1/trains?${params}`);
  }

  /**
   * Get train details
   */
  async getTrain(trainNo: number): Promise<TrainResponse> {
    return this.request<TrainResponse>(`/api/v1/trains/${trainNo}`);
  }

  /**
   * Get system statistics
   */
  async getStats(): Promise<StatsResponse> {
    return this.request<StatsResponse>('/api/v1/stats');
  }
}

// Export singleton instance
export const railwayAPI = new RailwayAPI();

// Export individual functions for convenience
export const searchStations = (query?: string, limit?: number) =>
  railwayAPI.searchStations(query, limit);

export const getStation = (code: string) =>
  railwayAPI.getStation(code);

export const searchRoutes = (origin: string, destination: string, maxTransfers?: number) =>
  railwayAPI.searchRoutes(origin, destination, maxTransfers);

export const getTrains = (limit?: number) =>
  railwayAPI.getTrains(limit);

export const getTrain = (trainNo: number) =>
  railwayAPI.getTrain(trainNo);

export const getStats = () =>
  railwayAPI.getStats();

export const healthCheck = () =>
  railwayAPI.health();