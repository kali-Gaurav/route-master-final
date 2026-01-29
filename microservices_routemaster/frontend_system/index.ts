/**
 * Frontend System - Comprehensive Exports
 * Complete React/TypeScript frontend platform with production-grade features
 */

// ============================================================================
// Type Exports
// ============================================================================
export * from './types'

// ============================================================================
// API Client
// ============================================================================
export { apiClient, ApiClientError } from './api/client'
export type { IApiClient } from './types'

// ============================================================================
// Hooks
// ============================================================================
export {
  useAsync,
  useForm,
  useAuth,
  usePagination,
  useDebounce,
  useLocalStorage,
  usePrevious,
} from './hooks'
export type { UseAsyncState, UseFormReturn, UseAuthReturn, UsePaginationReturn } from './types'

// ============================================================================
// Components - Design System
// ============================================================================
export { Button, Input, Modal, Spinner, Alert, Tooltip, Badge } from './components/DesignSystem'
export type { ButtonProps, InputProps, ModalProps } from './types'

// ============================================================================
// Components - Error Handling
// ============================================================================
export { ErrorBoundary, ErrorFallback, withErrorBoundary } from './components/ErrorBoundary'
export type { ErrorReport } from './types'

// ============================================================================
// State Management
// ============================================================================
export {
  initialState,
  storeReducer,
  StoreProvider,
  useStore,
  useAuthStore,
  useUIStore,
  useDataStore,
  useToasts,
  selectIsAuthenticated,
  selectCurrentUser,
  selectHasPermission,
  selectCacheNeedsRefresh,
} from './store'
export type { StoreState, StoreAction } from './types'

// ============================================================================
// Utilities
// ============================================================================
export {
  // Error handling
  isApiError,
  getErrorMessage,
  isRetryableError,
  // Validation
  validateEmail,
  validatePassword,
  validatePhoneNumber,
  // Formatting
  formatCurrency,
  formatDate,
  formatTime,
  formatDuration,
  truncateString,
  // Array & Object utilities
  groupBy,
  sortBy,
  unique,
  paginate,
  // Railway domain
  getTrainStatusColor,
  getTrainStatusLabel,
  getBookingStatusColor,
  getStationTierLabel,
  calculateRouteDuration,
  getRouteStops,
  isUpcomingRoute,
  // Local Storage
  setLocalStorage,
  getLocalStorage,
  removeLocalStorage,
  // Analytics
  trackEvent,
  trackPageView,
  trackError,
  // Performance
  measurePerformance,
  measureAsyncPerformance,
} from './store/utils'

// ============================================================================
// Version & Metadata
// ============================================================================
export const FRONTEND_VERSION = '1.0.0'
export const API_VERSION = 'v1'

/**
 * Frontend System Documentation
 * 
 * This is a complete, production-ready React/TypeScript frontend platform
 * for the Railway Operating System. It provides:
 * 
 * 1. TYPE SAFETY
 *    - Comprehensive TypeScript types for all API contracts
 *    - Compile-time safety for Redux-like state management
 *    - Full type coverage for components, hooks, and utilities
 * 
 * 2. API INTEGRATION
 *    - Typed API client with retry logic and caching
 *    - Request/response interceptors
 *    - Automatic retry on transient failures
 *    - Circuit breaker pattern support
 * 
 * 3. AUTHENTICATION & AUTHORIZATION
 *    - JWT token management with localStorage persistence
 *    - Role-based access control (RBAC) with 5 roles
 *    - Permission checking at component level
 *    - Automatic token refresh
 * 
 * 4. STATE MANAGEMENT
 *    - Redux-like store with reducers and actions
 *    - Built-in async data caching with TTL
 *    - Selector pattern for memoized queries
 *    - StoreProvider + useStore hooks for global state
 * 
 * 5. DESIGN SYSTEM
 *    - 7 accessible components (Button, Input, Modal, Spinner, Alert, Tooltip, Badge)
 *    - WCAG 2.1 AA compliance with proper ARIA labels
 *    - Consistent styling with 4 button variants and 3 sizes
 *    - Dark mode support via theme store
 * 
 * 6. ERROR HANDLING
 *    - ErrorBoundary component for catching React errors
 *    - Error reporting to backend with trace IDs
 *    - Fallback UI with error details in development
 *    - Breadcrumb tracking for better diagnostics
 * 
 * 7. HOOKS
 *    - useAsync: Generic data fetching with retry
 *    - useForm: Form state with validation
 *    - useAuth: Authentication with auto-refresh
 *    - usePagination: Pagination state management
 *    - useDebounce: Debounced values for search
 *    - useLocalStorage: Persistent state
 *    - usePrevious: Track previous values
 * 
 * 8. ACCESSIBILITY
 *    - WCAG 2.1 AA compliance
 *    - Proper ARIA labels and descriptions
 *    - Keyboard navigation support
 *    - Focus management
 *    - Screen reader friendly
 * 
 * 9. UTILITIES
 *    - Email, password, phone validation
 *    - Currency, date, time, duration formatting
 *    - Array operations (groupBy, sortBy, unique, paginate)
 *    - Railway domain helpers (status colors, labels, calculations)
 *    - LocalStorage with expiration
 *    - Analytics event tracking
 *    - Performance measurement
 * 
 * 10. OBSERVABILITY
 *    - Error tracking integration (Sentry)
 *    - Analytics (Google Analytics, Mixpanel)
 *    - Performance monitoring
 *    - Request tracing via X-Request-ID headers
 *    - Session tracking
 * 
 * USAGE EXAMPLE:
 * 
 *   import {
 *     Button,
 *     useAuth,
 *     useForm,
 *     ErrorBoundary,
 *     StoreProvider,
 *     useToasts,
 *   } from '@railway-os/frontend'
 * 
 *   function App() {
 *     return (
 *       <ErrorBoundary>
 *         <StoreProvider>
 *           <LoginPage />
 *         </StoreProvider>
 *       </ErrorBoundary>
 *     )
 *   }
 * 
 *   function LoginPage() {
 *     const { login } = useAuth()
 *     const { addToast } = useToasts()
 *     const form = useForm(
 *       { email: '', password: '' },
 *       async (values) => {
 *         await login(values.email, values.password)
 *         addToast({ type: 'success', message: 'Logged in!' })
 *       },
 *     )
 * 
 *     return (
 *       <form onSubmit={form.handleSubmit}>
 *         <Input
 *           type="email"
 *           placeholder="Email"
 *           value={form.values.email}
 *           onChange={form.handleChange('email')}
 *           error={form.errors.find(e => e.field === 'email')?.message}
 *         />
 *         <Input
 *           type="password"
 *           placeholder="Password"
 *           value={form.values.password}
 *           onChange={form.handleChange('password')}
 *           error={form.errors.find(e => e.field === 'password')?.message}
 *         />
 *         <Button type="submit" loading={form.isSubmitting}>
 *           Login
 *         </Button>
 *       </form>
 *     )
 *   }
 * 
 * ARCHITECTURE:
 * 
 *   ┌─────────────────────────────────────────┐
 *   │         React Application               │
 *   └────────────────┬────────────────────────┘
 *                    │
 *        ┌───────────┴───────────┐
 *        ▼                       ▼
 *   ┌─────────────┐     ┌─────────────────┐
 *   │ Components  │     │ ErrorBoundary   │
 *   │ (Design     │     │ (Error          │
 *   │  System)    │     │  Tracking)      │
 *   └─────────────┘     └─────────────────┘
 *        │
 *        ▼
 *   ┌─────────────────────────────────────┐
 *   │         Hooks Layer                  │
 *   │ useAuth, useForm, useAsync, etc.     │
 *   └────────┬────────────────────────────┘
 *            │
 *   ┌────────┴──────────────────────────┐
 *   │                                   │
 *   ▼                                   ▼
 * ┌──────────┐                   ┌─────────────────┐
 * │StoreProvider               │ API Client       │
 * │(State Mgmt)                │ (Data Fetching)  │
 * └──────────┘                   └──────┬──────────┘
 *                                        │
 *                          ┌─────────────┴──────────┐
 *                          ▼                        ▼
 *                    ┌──────────┐         ┌──────────────┐
 *                    │Validation│         │ Backend API  │
 *                    │Utilities │         │ (v1/v2)      │
 *                    └──────────┘         └──────────────┘
 * 
 * INTEGRATION WITH BACKEND (System B):
 * 
 *   - API Client uses /api/v1 and /api/v2 endpoints
 *   - Bearer token authentication with JWT
 *   - Rate limiting respected via 429 responses
 *   - Circuit breaker patterns for resilience
 *   - Request tracing with X-Request-ID headers
 *   - Observability: error tracking, analytics, performance metrics
 * 
 * SECURITY:
 * 
 *   - JWT tokens stored in localStorage (consider secure cookie for production)
 *   - HTTPS enforcement (configured in environment)
 *   - CSRF protection (token in headers)
 *   - XSS prevention via React's built-in escaping
 *   - Role-based access control at component level
 *   - Secure password validation requirements
 * 
 * PERFORMANCE:
 * 
 *   - API response caching with 5-minute TTL
 *   - Request deduplication for parallel requests
 *   - Lazy loading of components via React.lazy
 *   - Code splitting strategy
 *   - Debounced search/filter operations
 *   - Memoized selectors to prevent unnecessary re-renders
 * 
 * TESTING PATTERNS:
 * 
 *   - Types enable compile-time correctness
 *   - Hooks testable with @testing-library/react-hooks
 *   - Components testable with @testing-library/react
 *   - Mock API client for integration tests
 *   - ErrorBoundary testable via Jest
 * 
 * DEPLOYMENT (via System C):
 * 
 *   - Built with Vite/Create React App
 *   - Docker image includes frontend build artifacts
 *   - CDN integration for static assets
 *   - Environment variables for API endpoint
 *   - Blue-green deployment support
 * 
 * MONITORING (Observability):
 * 
 *   - Error boundary reports to Sentry
 *   - Analytics tracked via Google Analytics
 *   - Performance metrics: page load, API latency
 *   - User session tracking
 *   - Request tracing with correlation IDs
 */
