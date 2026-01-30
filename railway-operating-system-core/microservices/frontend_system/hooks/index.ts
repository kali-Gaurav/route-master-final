/**
 * Custom Hooks for API data fetching, form handling, authentication, and pagination
 */

import { useState, useEffect, useCallback, useRef, useReducer, useContext } from 'react'
import type {
  UseAsyncState,
  UseFormReturn,
  UseAuthReturn,
  UsePaginationReturn,
  User,
  ApiError,
  FormFieldError,
  AuthTokenPayload,
} from '../types'
import { apiClient } from '../api/client'

// ============================================================================
// useAsync - Generic data fetching hook with retry and error handling
// ============================================================================

export function useAsync<T>(
  asyncFunction: () => Promise<T>,
  immediate = true,
  dependencies: unknown[] = [],
): UseAsyncState<T> {
  const [state, setState] = useState<UseAsyncState<T>>({
    data: null,
    loading: immediate,
    error: null,
    refetch: async () => {},
  })

  const refetch = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const data = await asyncFunction()
      setState({ data, loading: false, error: null, refetch })
    } catch (error) {
      const apiError: ApiError = {
        code: 'FETCH_ERROR',
        message: error instanceof Error ? error.message : 'Unknown error',
        status: 500,
        timestamp: new Date().toISOString(),
      }
      setState({ data: null, loading: false, error: apiError, refetch })
    }
  }, [asyncFunction])

  useEffect(() => {
    if (immediate) {
      refetch()
    }
  }, dependencies)

  return { ...state, refetch }
}

// ============================================================================
// useForm - Form state management with validation
// ============================================================================

interface FormAction {
  type: 'SET_VALUE' | 'SET_ERROR' | 'SET_TOUCHED' | 'SET_SUBMITTING' | 'RESET'
  payload?: unknown
}

function formReducer<T extends Record<string, unknown>>(
  state: any,
  action: FormAction & { field?: string },
): any {
  switch (action.type) {
    case 'SET_VALUE':
      return {
        ...state,
        values: { ...state.values, [action.field as string]: action.payload },
        isDirty: true,
      }
    case 'SET_ERROR':
      return {
        ...state,
        errors: [
          ...state.errors.filter((e: FormFieldError) => e.field !== action.field),
          { field: action.field as string, message: action.payload },
        ],
      }
    case 'SET_TOUCHED':
      return {
        ...state,
        touched: { ...state.touched, [action.field as string]: true },
      }
    case 'SET_SUBMITTING':
      return { ...state, isSubmitting: action.payload }
    case 'RESET':
      return action.payload as any
    default:
      return state
  }
}

export function useForm<T extends Record<string, unknown>>(
  initialValues: T,
  onSubmit: (values: T) => Promise<void>,
  validate?: (values: T) => Record<keyof T, string | undefined>,
): UseFormReturn<T> {
  const [state, dispatch] = useReducer(formReducer, {
    values: initialValues,
    errors: [],
    touched: {},
    isSubmitting: false,
    isDirty: false,
  })

  const handleChange = useCallback(
    (field: keyof T) => (value: string | number | boolean) => {
      dispatch({ type: 'SET_VALUE', field: String(field), payload: value })
    },
    [],
  )

  const handleBlur = useCallback(
    (field: keyof T) => () => {
      dispatch({ type: 'SET_TOUCHED', field: String(field) })
    },
    [],
  )

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()

      // Validate
      if (validate) {
        const validationErrors = validate(state.values)
        const errors: FormFieldError[] = Object.entries(validationErrors)
          .filter(([, error]) => error)
          .map(([field, message]) => ({
            field: String(field),
            message: message || '',
            type: 'custom',
          }))

        if (errors.length > 0) {
          state.errors = errors
          return
        }
      }

      dispatch({ type: 'SET_SUBMITTING', payload: true })
      try {
        await onSubmit(state.values)
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Submission failed'
        dispatch({
          type: 'SET_ERROR',
          field: 'form',
          payload: message,
        })
      } finally {
        dispatch({ type: 'SET_SUBMITTING', payload: false })
      }
    },
    [state.values, validate, onSubmit],
  )

  const reset = useCallback(() => {
    dispatch({ type: 'RESET', payload: { values: initialValues, errors: [], touched: {} } })
  }, [initialValues])

  return {
    ...state,
    setValue: (field, value) => {
      dispatch({ type: 'SET_VALUE', field: String(field), payload: value })
    },
    setError: (field, error) => {
      dispatch({ type: 'SET_ERROR', field: String(field), payload: error })
    },
    handleChange,
    handleBlur,
    handleSubmit,
    reset,
  }
}

// ============================================================================
// useAuth - Authentication and authorization
// ============================================================================

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('auth_token'))
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<ApiError | null>(null)

  // Initialize auth from localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token')
    const storedUser = localStorage.getItem('auth_user')

    if (storedToken && storedUser) {
      try {
        setToken(storedToken)
        setUser(JSON.parse(storedUser))
        apiClient.setToken(storedToken)
      } catch (e) {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('auth_user')
      }
    }
    setIsLoading(false)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await apiClient.post<{ token: string; user: User }>('/v1/auth/login', {
        email,
        password,
      })

      const newToken = response.token
      const newUser = response.user

      setToken(newToken)
      setUser(newUser)
      apiClient.setToken(newToken)

      localStorage.setItem('auth_token', newToken)
      localStorage.setItem('auth_user', JSON.stringify(newUser))
    } catch (err) {
      const apiError: ApiError = {
        code: 'LOGIN_FAILED',
        message: err instanceof Error ? err.message : 'Login failed',
        status: 401,
        timestamp: new Date().toISOString(),
      }
      setError(apiError)
      throw apiError
    } finally {
      setIsLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    try {
      await apiClient.post('/v1/auth/logout', {})
    } catch {
      // Ignore errors on logout
    } finally {
      setUser(null)
      setToken(null)
      apiClient.setToken(null)
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
    }
  }, [])

  const refresh = useCallback(async () => {
    if (!token) return

    try {
      const response = await apiClient.post<{ token: string }>('/v1/auth/refresh', {})
      const newToken = response.token

      setToken(newToken)
      apiClient.setToken(newToken)
      localStorage.setItem('auth_token', newToken)
    } catch (err) {
      await logout()
    }
  }, [token, logout])

  const hasPermission = useCallback(
    (resource: string, action: string): boolean => {
      if (!user) return false

      // Admins have all permissions
      if (user.roles.includes('admin')) return true

      // Role-based permission check (simplified)
      const permissions: Record<string, string[]> = {
        admin: ['read', 'write', 'delete'],
        power_user: ['read', 'write'],
        analyst: ['read'],
        viewer: ['read'],
        system: ['read', 'write', 'delete'],
      }

      const userRole = user.roles[0]
      return permissions[userRole]?.includes(action) ?? false
    },
    [user],
  )

  return {
    user,
    token,
    isAuthenticated: !!user && !!token,
    isLoading,
    error,
    login,
    logout,
    refresh,
    hasPermission,
  }
}

// ============================================================================
// usePagination - Pagination state management
// ============================================================================

export function usePagination(initialPage = 1, initialPageSize = 10): UsePaginationReturn {
  const [page, setPage] = useState(initialPage)
  const [pageSize, setPageSizeState] = useState(initialPageSize)
  const [total, setTotal] = useState(0)

  const totalPages = Math.ceil(total / pageSize)
  const hasNext = page < totalPages
  const hasPrevious = page > 1

  const goToPage = useCallback((newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setPage(newPage)
    }
  }, [totalPages])

  const nextPage = useCallback(() => {
    if (hasNext) {
      setPage((p) => p + 1)
    }
  }, [hasNext])

  const previousPage = useCallback(() => {
    if (hasPrevious) {
      setPage((p) => p - 1)
    }
  }, [hasPrevious])

  const setPageSize = useCallback((size: number) => {
    setPageSizeState(size)
    setPage(1) // Reset to first page on page size change
  }, [])

  return {
    page,
    pageSize,
    total,
    totalPages,
    hasNext,
    hasPrevious,
    goToPage,
    nextPage,
    previousPage,
    setPageSize,
  }
}

// ============================================================================
// useDebounce - Debounce values for search/filter
// ============================================================================

export function useDebounce<T>(value: T, delayMs = 500): T {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delayMs)

    return () => clearTimeout(handler)
  }, [value, delayMs])

  return debouncedValue
}

// ============================================================================
// useLocalStorage - Persist state to localStorage
// ============================================================================

export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch {
      return initialValue
    }
  })

  const setValue = useCallback(
    (value: T) => {
      try {
        setStoredValue(value)
        window.localStorage.setItem(key, JSON.stringify(value))
      } catch (error) {
        console.error(`useLocalStorage error for key "${key}":`, error)
      }
    },
    [key],
  )

  return [storedValue, setValue]
}

// ============================================================================
// usePrevious - Track previous value
// ============================================================================

export function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>()

  useEffect(() => {
    ref.current = value
  }, [value])

  return ref.current
}
