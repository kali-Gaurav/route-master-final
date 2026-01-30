/**
 * API Client - Type-safe wrapper around fetch with retry, caching, and error handling
 */

import type {
  ApiResponse,
  ApiError,
  RequestOptions,
  IApiClient,
} from '../types'

class RailwayOSApiClient implements IApiClient {
  private baseUrl: string
  private token: string | null = null
  private cache: Map<string, { data: unknown; timestamp: number }> = new Map()
  private readonly cacheDefaultTtl = 5 * 60 * 1000 // 5 minutes

  constructor(baseUrl: string = 'http://localhost:8000/api') {
    this.baseUrl = baseUrl
  }

  setToken(token: string | null) {
    this.token = token
  }

  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('GET', endpoint, undefined, options)
  }

  async post<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('POST', endpoint, data, options)
  }

  async put<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('PUT', endpoint, data, options)
  }

  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('DELETE', endpoint, undefined, options)
  }

  private async request<T>(
    method: string,
    endpoint: string,
    data?: unknown,
    options?: RequestOptions,
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const cacheKey = `${method}:${url}`

    // Check cache for GET requests
    if (method === 'GET' && options?.cache !== false) {
      const cached = this.cache.get(cacheKey)
      if (cached && Date.now() - cached.timestamp < (options?.timeout || this.cacheDefaultTtl)) {
        return cached.data as T
      }
    }

    // Build request headers
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options?.headers,
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    // Add trace headers for observability
    headers['X-Request-ID'] = this.generateRequestId()
    headers['X-Client-Version'] = '1.0.0'

    // Build query parameters
    const queryParams = new URLSearchParams()
    if (options?.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        queryParams.append(key, String(value))
      })
    }

    const fullUrl = queryParams.toString() ? `${url}?${queryParams}` : url

    // Retry logic with exponential backoff
    let lastError: Error | null = null
    const maxRetries = options?.retry ?? 3

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), options?.timeout || 30000)
        
        const response = await fetch(fullUrl, {
          method,
          headers,
          body: data ? JSON.stringify(data) : undefined,
          signal: controller.signal,
        })
        
        clearTimeout(timeoutId)

        // Handle rate limiting
        if (response.status === 429) {
          const retryAfter = parseInt(response.headers.get('retry-after') || '1', 10)
          await this.delay(retryAfter * 1000)
          continue
        }

        // Parse response
        const contentType = response.headers.get('content-type')
        const isJson = contentType?.includes('application/json')

        if (!response.ok) {
          const errorData = isJson ? await response.json() : { message: response.statusText }
          const error: ApiError = {
            code: `HTTP_${response.status}`,
            message: errorData.message || response.statusText,
            details: errorData.details,
            status: response.status,
            timestamp: new Date().toISOString(),
          }

          // Don't retry client errors (4xx)
          if (response.status >= 400 && response.status < 500) {
            throw new ApiClientError(error)
          }

          // Retry server errors (5xx)
          lastError = new ApiClientError(error)
          if (attempt < maxRetries - 1) {
            await this.delay(this.getBackoffDelay(attempt))
            continue
          }
          throw lastError
        }

        const result = isJson ? (await response.json() as ApiResponse<T>) : (await response.text() as T)

        // Cache successful GET responses
        if (method === 'GET' && options?.cache !== false) {
          this.cache.set(cacheKey, { data: result, timestamp: Date.now() })
        }

        return result as T
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error))

        // Don't retry on network errors beyond max retries
        if (attempt === maxRetries - 1) {
          throw lastError
        }

        // Exponential backoff with jitter
        await this.delay(this.getBackoffDelay(attempt))
      }
    }

    throw lastError || new Error('Request failed')
  }

  private getBackoffDelay(attempt: number): number {
    const baseDelay = 1000 // 1 second
    const delay = baseDelay * Math.pow(2, attempt)
    const jitter = Math.random() * 0.1 * delay
    return delay + jitter
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  clearCache(pattern?: string) {
    if (pattern) {
      const regex = new RegExp(pattern)
      for (const key of this.cache.keys()) {
        if (regex.test(key)) {
          this.cache.delete(key)
        }
      }
    } else {
      this.cache.clear()
    }
  }
}

// Custom error class for API errors
export class ApiClientError extends Error {
  public readonly apiError: ApiError

  constructor(apiError: ApiError) {
    super(apiError.message)
    this.name = 'ApiClientError'
    this.apiError = apiError
  }
}

// Singleton instance
export const apiClient = new RailwayOSApiClient()

export default apiClient
