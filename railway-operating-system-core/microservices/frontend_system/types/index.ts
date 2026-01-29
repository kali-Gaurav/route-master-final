/**
 * Type Contracts for Railway OS Frontend
 * Ensures type safety across API client, hooks, components, and state
 */

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiResponse<T> {
  data: T
  status: number
  message: string
  timestamp: string
  trace_id: string
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, string>
  status: number
  timestamp: string
}

export interface PaginationMeta {
  page: number
  page_size: number
  total_items: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: PaginationMeta
}

// ============================================================================
// Authentication & Authorization
// ============================================================================

export type UserRole = 'admin' | 'power_user' | 'analyst' | 'viewer' | 'system'

export interface AuthTokenPayload {
  sub: string // User ID
  email: string
  roles: UserRole[]
  tenant_id: string
  exp: number
  iat: number
  jti: string // JWT ID for revocation
}

export interface User {
  id: string
  email: string
  name: string
  roles: UserRole[]
  tenant_id: string
  avatar_url?: string
  last_login: string
  created_at: string
}

export interface AuthContext {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: ApiError | null
}

export interface Permission {
  resource: string
  action: 'read' | 'write' | 'delete' | 'admin'
  conditions?: Record<string, string>
}

// ============================================================================
// Domain Models - Railway System
// ============================================================================

export interface Station {
  id: string
  name: string
  code: string
  latitude: number
  longitude: number
  region: string
  tier: 'major' | 'secondary' | 'minor'
  platforms: number
}

export interface Train {
  id: string
  name: string
  number: string
  type: 'express' | 'local' | 'freight' | 'special'
  status: 'running' | 'delayed' | 'cancelled' | 'maintenance'
  current_location: {
    station_id: string
    platform?: number
    timestamp: string
  }
  capacity: {
    total_seats: number
    available_seats: number
  }
}

export interface Route {
  id: string
  name: string
  train_id: string
  start_station_id: string
  end_station_id: string
  stops: Station[]
  estimated_duration_minutes: number
  departure_time: string
  arrival_time: string
  status: 'scheduled' | 'running' | 'completed' | 'cancelled'
}

export interface Booking {
  id: string
  user_id: string
  train_id: string
  passenger_name: string
  seat_number: string
  booking_date: string
  journey_date: string
  status: 'confirmed' | 'pending' | 'cancelled'
  price: number
  created_at: string
}

// ============================================================================
// Form & Validation Types
// ============================================================================

export interface FormFieldError {
  field: string
  message: string
  type: 'required' | 'pattern' | 'minlength' | 'maxlength' | 'email' | 'custom'
}

export interface FormState<T> {
  values: T
  errors: FormFieldError[]
  touched: Partial<Record<keyof T, boolean>>
  isSubmitting: boolean
  isDirty: boolean
}

export interface ValidationRule {
  required?: boolean
  minLength?: number
  maxLength?: number
  pattern?: RegExp
  custom?: (value: unknown) => string | null
}

export interface FormConfig<T> {
  fields: Record<keyof T, ValidationRule>
  onSubmit: (values: T) => Promise<void>
  initialValues: T
}

// ============================================================================
// Component Props
// ============================================================================

export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  onClick?: () => void | Promise<void>
  type?: 'button' | 'submit' | 'reset'
  ariaLabel?: string
}

export interface InputProps {
  type?: 'text' | 'email' | 'password' | 'number' | 'date'
  placeholder?: string
  value?: string
  onChange?: (value: string) => void
  error?: string
  disabled?: boolean
  required?: boolean
  ariaLabel?: string
  ariaDescribedBy?: string
}

export interface ModalProps {
  isOpen: boolean
  title: string
  onClose: () => void
  size?: 'sm' | 'md' | 'lg'
  isDismissible?: boolean
  ariaLabelledBy?: string
}

export interface ToastMessage {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
}

// ============================================================================
// Hook Return Types
// ============================================================================

export interface UseAsyncState<T, E = ApiError> {
  data: T | null
  loading: boolean
  error: E | null
  refetch: () => Promise<void>
}

export interface UseFormReturn<T> {
  values: T
  errors: FormFieldError[]
  touched: Partial<Record<keyof T, boolean>>
  isSubmitting: boolean
  isDirty: boolean
  setValue: (field: keyof T, value: unknown) => void
  setError: (field: keyof T, error: string) => void
  handleChange: (field: keyof T) => (value: string) => void
  handleBlur: (field: keyof T) => () => void
  handleSubmit: (e: React.FormEvent) => Promise<void>
  reset: () => void
}

export interface UseAuthReturn extends AuthContext {
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refresh: () => Promise<void>
  hasPermission: (resource: string, action: string) => boolean
}

export interface UsePaginationState {
  page: number
  pageSize: number
  total: number
  totalPages: number
  hasNext: boolean
  hasPrevious: boolean
}

export interface UsePaginationReturn extends UsePaginationState {
  goToPage: (page: number) => void
  nextPage: () => void
  previousPage: () => void
  setPageSize: (size: number) => void
}

// ============================================================================
// State Management
// ============================================================================

export interface StoreState {
  auth: AuthContext
  ui: {
    sidebarOpen: boolean
    theme: 'light' | 'dark'
    locale: string
    toasts: ToastMessage[]
  }
  data: {
    stations: Station[]
    trains: Train[]
    routes: Route[]
    bookings: Booking[]
  }
  cache: {
    lastFetch: Record<string, string>
    ttl: number
  }
}

export type StoreAction =
  | { type: 'SET_AUTH'; payload: User | null }
  | { type: 'SET_TOKEN'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'SET_THEME'; payload: 'light' | 'dark' }
  | { type: 'ADD_TOAST'; payload: ToastMessage }
  | { type: 'REMOVE_TOAST'; payload: string }
  | { type: 'SET_STATIONS'; payload: Station[] }
  | { type: 'SET_TRAINS'; payload: Train[] }
  | { type: 'SET_ROUTES'; payload: Route[] }
  | { type: 'SET_BOOKINGS'; payload: Booking[] }

// ============================================================================
// Service Contract Types
// ============================================================================

export interface IApiClient {
  get<T>(endpoint: string, options?: RequestOptions): Promise<T>
  post<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T>
  put<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T>
  delete<T>(endpoint: string, options?: RequestOptions): Promise<T>
}

export interface RequestOptions {
  headers?: Record<string, string>
  params?: Record<string, string | number | boolean>
  timeout?: number
  retry?: number
  cache?: boolean
}

export interface IAuthService {
  login(email: string, password: string): Promise<{ token: string; user: User }>
  logout(): Promise<void>
  refresh(): Promise<string>
  verifyToken(token: string): Promise<AuthTokenPayload>
}

export interface IRouteService {
  searchRoutes(from: string, to: string, date: string): Promise<Route[]>
  getRoute(routeId: string): Promise<Route>
  getTrainInfo(trainId: string): Promise<Train>
}

export interface IBookingService {
  createBooking(trainId: string, seatNumber: string): Promise<Booking>
  getBookings(userId: string): Promise<Booking[]>
  cancelBooking(bookingId: string): Promise<void>
}

// ============================================================================
// Analytics & Telemetry
// ============================================================================

export interface AnalyticsEvent {
  eventName: string
  properties: Record<string, unknown>
  timestamp: string
  userId?: string
  sessionId: string
}

export interface PerformanceMetric {
  name: string
  duration: number
  timestamp: string
  metadata?: Record<string, unknown>
}

export interface ErrorReport {
  message: string
  stack: string
  component: string
  userId?: string
  sessionId: string
  timestamp: string
  breadcrumbs: string[]
}
