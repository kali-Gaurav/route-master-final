# Frontend System Starter and Requirements

## Overview
The Frontend System is a React/TypeScript application providing a modern, accessible user interface for the Railway Operating System. It includes 100+ types, 7 custom hooks, 7 WCAG 2.1 AA compliant components, and a Redux-like state management system.

## Requirements

### System Requirements
- Node.js 18+ (LTS recommended)
- npm or yarn package manager
- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+)

### Dependencies
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "axios": "^1.4.0",
    "react-router-dom": "^6.14.0",
    "redux": "^4.2.1",
    "react-redux": "^8.1.1",
    "@reduxjs/toolkit": "^1.9.5"
  },
  "devDependencies": {
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint": "^8.45.0",
    "prettier": "^3.0.0",
    "vite": "^4.4.0",
    "@vitejs/plugin-react": "^4.0.0"
  }
}
```

## Techniques Used

### Architecture
- **Component Architecture**: Modular, reusable components with clear separation of concerns
- **Custom Hooks**: 7 specialized hooks for data fetching, authentication, routing, and state management
- **State Management**: Redux-like store with TypeScript support for predictable state updates
- **Type Safety**: 100+ TypeScript interfaces and types for API contracts and component props

### Accessibility
- **WCAG 2.1 AA Compliance**: All 7 components follow accessibility guidelines
- **Semantic HTML**: Proper ARIA labels, roles, and keyboard navigation
- **Color Contrast**: High contrast ratios for readability
- **Screen Reader Support**: Comprehensive screen reader compatibility

### Performance
- **Code Splitting**: Lazy loading of routes and components
- **Memoization**: React.memo, useMemo, and useCallback for optimization
- **Bundle Optimization**: Vite-based build with tree shaking and minification

## Data Requirements

### API Endpoints
The frontend communicates with the backend via REST API:

#### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Get current user info

#### Routes
- `GET /api/v1/routes/search` - Search routes
- `GET /api/v1/routes/{id}` - Get route details
- `POST /api/v1/routes` - Create route (admin)

#### Stations
- `GET /api/v1/stations` - List stations
- `GET /api/v1/stations/{id}` - Get station details

#### Jobs
- `GET /api/v1/jobs` - List user jobs
- `GET /api/v1/jobs/{id}` - Get job status
- `POST /api/v1/jobs` - Submit new job

### Data Models
```typescript
interface User {
  id: string;
  email: string;
  role: 'admin' | 'user' | 'operator';
  tenantId: string;
}

interface Route {
  id: string;
  origin: string;
  destination: string;
  distance: number;
  duration: number;
  stops: Station[];
}

interface Station {
  id: string;
  name: string;
  code: string;
  latitude: number;
  longitude: number;
}

interface Job {
  id: string;
  type: 'route_search' | 'data_import';
  status: 'pending' | 'running' | 'completed' | 'failed';
  createdAt: Date;
  completedAt?: Date;
}
```

## Setup and Installation

### 1. Install Dependencies
```bash
cd frontend_system
npm install
```

### 2. Environment Configuration
Create `.env.local`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=Railway Operating System
VITE_ENABLE_DEBUG=true
```

### 3. Development Server
```bash
npm run dev
```
The application will be available at `http://localhost:5173`

### 4. Build for Production
```bash
npm run build
npm run preview
```

### 5. Testing
```bash
npm run test
npm run test:e2e  # Requires backend running
```

## Integration Points

### With Backend
- REST API communication via Axios
- JWT token management for authentication
- Error handling with user-friendly messages

### With Database
- Indirect connection through backend APIs
- No direct database access required

### With Deployment
- Static build output for deployment
- Environment-specific configuration

## Development Workflow

1. **Component Development**: Use the DesignSystem components for consistency
2. **State Management**: Dispatch actions to the Redux store
3. **API Calls**: Use the provided API client utilities
4. **Testing**: Write unit tests for components and integration tests for features
5. **Accessibility**: Test with screen readers and keyboard navigation

## Key Files Structure
```
frontend_system/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── DesignSystem.tsx # Main design system
│   │   └── ErrorBoundary.tsx
│   ├── hooks/              # Custom React hooks
│   │   └── index.ts        # Hook exports
│   ├── store/              # State management
│   │   └── index.tsx       # Redux store setup
│   ├── types/              # TypeScript definitions
│   │   └── index.ts        # Type exports
│   ├── utils/              # Utility functions
│   └── api/                # API client
│       └── client.ts       # Axios configuration
├── public/                 # Static assets
├── package.json
├── tsconfig.json
├── vite.config.ts
└── index.html
```</content>
<parameter name="filePath">c:\Users\Gaurav Nagar\OneDrive\Documents\testingfolder_v3\railway-operating-system-microservices\frontend_starter.md