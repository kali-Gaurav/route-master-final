# Complete Startup Website Requirements Specification

## Executive Summary

This document outlines the complete technical and functional requirements for building an **Intelligent Route Optimization and Travel Planning Platform**. The platform combines advanced route generation algorithms, intelligent feature selection, comprehensive database management, and an AI agent system to provide users with optimized travel routes while maintaining data integrity and real-time accuracy.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Frontend Requirements](#frontend-requirements)
4. [Backend Requirements](#backend-requirements)
5. [Database Requirements](#database-requirements)
6. [AI Agent System](#ai-agent-system)
7. [Route Generation Engine](#route-generation-engine)
8. [Feature Selection Framework](#feature-selection-framework)
9. [Data Management Pipeline](#data-management-pipeline)
10. [Security & Compliance](#security--compliance)
11. [Implementation Roadmap](#implementation-roadmap)

---

## Project Overview

### Mission
Build a comprehensive web platform that intelligently generates optimal multi-transfer routes using advanced algorithms, manages transportation datasets, and provides real-time insights to users through an intuitive interface powered by an AI agent system.

### Core Features
- **Intelligent Route Generation**: Generate multiple route alternatives with varying transfer counts
- **Feature Selection**: Smart selection of relevant features based on user preferences
- **Real-time Data Management**: Upload, validate, and manage transportation datasets
- **AI Agent System**: Autonomous agent that assists with route optimization and user preferences
- **Multi-transfer Route Planning**: Support for 0, 1, 2, and 3+ transfer routes
- **Price & Schedule Integration**: Real-time fare and availability information
- **Advanced Search & Filtering**: Pareto-optimal route selection

### Target Users
- Business travelers seeking optimal routes
- Daily commuters
- Travel agencies
- Transportation logistics companies
- End-consumers planning trips

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Application                      │
│  (React/TypeScript + Vite + Tailwind CSS)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │  User Interface      │  │    AI Agent Chat Interface       │ │
│  │  - Route Search      │  │    - Smart Recommendations      │ │
│  │  - Advanced Filters  │  │    - Preference Learning        │ │
│  │  - Visualization     │  │    - Dynamic Suggestions        │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │ Admin Dashboard      │  │    Data Upload & Management      │ │
│  │ - Analytics          │  │    - Dataset Upload             │ │
│  │ - Reporting          │  │    - Schema Management          │ │
│  │ - User Management    │  │    - Data Validation            │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │ REST API / WebSocket
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend Services (Flask/FastAPI)             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            API Gateway & Request Handler               │   │
│  │  - Authentication & Authorization                      │   │
│  │  - Rate Limiting                                       │   │
│  │  - Request Validation                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │ Route Generation     │  │  Feature Selection Engine        │ │
│  │ Engine               │  │                                  │ │
│  │ - Pareto Optimizer   │  │ - Dynamic Feature Extraction    │ │
│  │ - Multi-transfer     │  │ - Relevance Scoring             │ │
│  │   Routing            │  │ - User Preference Mapping       │ │
│  │ - Graph Builder      │  │ - Recommendation Engine         │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │ AI Agent System      │  │  Data Validation & Pipeline     │ │
│  │                      │  │                                  │ │
│  │ - NLP Processing     │  │ - Dataset Validation            │ │
│  │ - Intent Recognition │  │ - Schema Mapping                │ │
│  │ - Learning Engine    │  │ - ETL Operations                │ │
│  │ - Decision Making    │  │ - Data Quality Checks           │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │ Cache Management     │  │  Real-time Data Integration      │ │
│  │                      │  │                                  │ │
│  │ - Route Cache        │  │ - Live API Wrappers             │ │
│  │ - Schedule Cache     │  │ - Seat Availability Updates     │ │
│  │ - Fare Cache         │  │ - Fare Updates                  │ │
│  │ - TTL Management     │  │ - Schedule Synchronization      │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │ Analytics Engine     │  │  Monitoring & Logging            │ │
│  │                      │  │                                  │ │
│  │ - Route Statistics   │  │ - Performance Monitoring         │ │
│  │ - Usage Analytics    │  │ - Error Logging & Alerting       │ │
│  │ - Performance Metrics│  │ - Audit Trails                  │ │
│  │ - Insights Generation│  │ - Health Checks                 │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │ SQL / ORM
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Database Layer (PostgreSQL)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                Core Data Schemas                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │ Transportation Data  │  │  User & Preference Data          │ │
│  │                      │  │                                  │ │
│  │ - Stations/Hubs      │  │ - User Profiles                 │ │
│  │ - Routes             │  │ - Search History                │ │
│  │ - Trains             │  │ - User Preferences              │ │
│  │ - Schedules          │  │ - Saved Routes                  │ │
│  │ - Fares              │  │ - Feedback                      │ │
│  │ - Availability       │  │ - Agent Interactions            │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │ Dataset Management   │  │  Cache & Indexes                │ │
│  │                      │  │                                  │ │
│  │ - Raw Datasets       │  │ - Redis Cache Layer             │ │
│  │ - Transformation     │  │ - Database Indexes              │ │
│  │ - Validation Results │  │ - Query Optimization            │ │
│  │ - Data Lineage       │  │ - Full-text Search              │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │ Analytics Tables     │  │  Audit & Logging                │ │
│  │                      │  │                                  │ │
│  │ - Route Statistics   │  │ - Activity Logs                 │ │
│  │ - Usage Metrics      │  │ - Data Change Logs              │ │
│  │ - Performance Data   │  │ - API Call Logs                 │ │
│  │ - User Behavior      │  │ - Agent Decision Logs           │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

#### Frontend
- **Framework**: React 18+ with TypeScript
- **Bundler**: Vite
- **Styling**: Tailwind CSS
- **UI Components**: Custom components + shadcn/ui
- **State Management**: TanStack Query + Zustand
- **Maps**: Leaflet/Mapbox for route visualization
- **Charts**: Recharts for analytics
- **Real-time**: WebSocket for live updates

#### Backend
- **Primary Framework**: Flask/FastAPI (Python)
- **Async Support**: AsyncIO, Aiohttp
- **Route Optimization**: Custom Pareto optimizer
- **Database ORM**: SQLAlchemy
- **Caching**: Redis
- **Message Queue**: Celery (for async tasks)
- **API Documentation**: Swagger/OpenAPI

#### Database
- **Primary**: PostgreSQL 13+
- **Cache Layer**: Redis 6+
- **Search**: Full-text search with PostgreSQL
- **Backup**: Automated backup pipeline

#### AI Agent System
- **NLP Library**: spaCy / NLTK
- **ML Framework**: scikit-learn / TensorFlow
- **Learning**: User preference learning with feedback
- **Intent Recognition**: Custom ML models

---

## Frontend Requirements

### 1. User Interface Components

#### 1.1 Route Search Interface
**Functionality:**
- Dual input fields for origin/destination stations
- Date & time picker
- Passenger count selector
- Class preference selector (First, Second, Third, etc.)
- Budget range slider
- Preferred transfer count toggle

**User Stories:**
- User can search for routes between any two stations
- System returns results sorted by Pareto-optimal criteria
- User can filter results by price, duration, transfers, time

**Non-functional Requirements:**
- Search response time < 2 seconds
- Support for autocomplete with 50,000+ stations
- Mobile-responsive design

#### 1.2 Route Display & Visualization
**Display Elements:**
- Route list with key metrics (price, duration, transfers, departure/arrival times)
- Timeline visualization for journey steps
- Station and train details for each leg
- Seat availability indicators
- Real-time price updates
- Interactive map showing route path

**Interactive Features:**
- Expand/collapse each route
- Compare multiple routes side-by-side
- Save routes for later
- Share routes with others
- Print route details

#### 1.3 Advanced Filtering Panel
**Filters:**
- Price range (min-max with slider)
- Duration (min-max hours)
- Number of transfers (0, 1, 2, 3+)
- Departure time window
- Arrival time window
- Train types (Express, Superfast, etc.)
- Class type
- Preferred stations
- Accessibility requirements

**Smart Filters:**
- "Most Economical" preset
- "Fastest Route" preset
- "Fewest Transfers" preset
- "Best Value" preset (combination)
- Custom saved filters

#### 1.4 AI Agent Chat Interface
**Features:**
- Chat window with conversational interface
- Natural language query processing
- Agent recommendations display
- Preference learning from interactions
- Quick suggestion buttons
- Agent personality & tone settings

**Example Interactions:**
- "Show me the cheapest way to reach Mumbai from Delhi"
- "I need to arrive by 2 PM, what's the best option?"
- "What routes avoid multiple transfers?"
- "Which train has the most available seats?"

#### 1.5 Admin Dashboard
**Components:**
- User management and analytics
- Dataset upload interface
- Data validation reports
- Database schema visualizer
- API usage analytics
- System health monitoring
- Error logs and alerts
- User feedback management

#### 1.6 User Account Management
**Features:**
- User registration and authentication
- Profile management
- Saved routes and favorites
- Search history
- Preference settings
- Notifications management
- Booking history
- Payment method management

### 2. Page Structure

```
/
├── /home
│   ├── Hero section with search
│   ├── Popular routes
│   ├── Quick filters
│   └── AI agent chatbot
├── /search
│   ├── Advanced search form
│   ├── Results page
│   ├── Route details modal
│   └── Filter sidebar
├── /route/:id
│   ├── Full route details
│   ├── Seat availability
│   ├── Pricing details
│   ├── Booking options
│   └── Reviews & ratings
├── /bookings
│   ├── Upcoming bookings
│   ├── Booking history
│   ├── Booking details
│   └── Cancellation/modification
├── /saved-routes
│   ├── Saved route list
│   ├── Collections/folders
│   └── Share options
├── /profile
│   ├── User information
│   ├── Preferences
│   ├── Address book
│   ├── Payment methods
│   └── Notifications
├── /admin
│   ├── Dashboard
│   ├── User management
│   ├── Dataset management
│   ├── Analytics
│   └── System settings
├── /agent
│   ├── Chat interface
│   ├── Agent settings
│   ├── Conversation history
│   └── Preferences
└── /help
    ├── FAQ
    ├── Tutorials
    ├── Support chat
    └── Documentation
```

### 3. Mobile Responsiveness
- Fully responsive design for mobile, tablet, desktop
- Touch-friendly interface elements
- Mobile-optimized search (single input with smart parsing)
- Progressive Web App (PWA) capability
- Offline route viewing capability

---

## Backend Requirements

### 1. API Endpoints Specification

#### 1.1 Route Search Endpoints

```
POST /api/v2/routes/search
Request:
{
  "origin": "NDLS",
  "destination": "MMCT",
  "date": "2026-02-01",
  "departure_time": "00:00",
  "passengers": 1,
  "class": "second",
  "budget_min": 0,
  "budget_max": 10000,
  "max_transfers": 3
}

Response:
{
  "search_id": "uuid",
  "timestamp": "2026-01-27T10:30:00Z",
  "results": {
    "direct": [...],
    "one_transfer": [...],
    "two_transfer": [...],
    "three_transfer": [...]
  },
  "metadata": {
    "total_results": 45,
    "search_time_ms": 1250,
    "filters_applied": {...}
  }
}
```

#### 1.2 Route Details Endpoint

```
GET /api/v2/routes/:route_id
Response:
{
  "route_id": "uuid",
  "segments": [
    {
      "train_number": "12015",
      "train_name": "Rajdhani Express",
      "origin": "NDLS",
      "destination": "MMCT",
      "departure": "2026-02-01T15:45:00",
      "arrival": "2026-02-02T06:30:00",
      "duration": 14.75,
      "available_seats": {
        "second": 24,
        "first": 8,
        "ac_first": 5
      },
      "fares": {
        "second": 550,
        "first": 1100,
        "ac_first": 2500
      },
      "stops": [...],
      "amenities": [...]
    }
  ],
  "total_price": 1100,
  "total_duration": 14.75,
  "transfers": 0,
  "environmental_impact": {...}
}
```

#### 1.3 AI Agent Endpoints

```
POST /api/v2/agent/chat
Request:
{
  "user_id": "uuid",
  "message": "Show me the cheapest routes",
  "context": {
    "last_search": {...},
    "preferences": {...}
  }
}

Response:
{
  "agent_response": "string",
  "recommendations": [
    {
      "type": "route",
      "route_id": "uuid",
      "reason": "Matches your budget preference"
    }
  ],
  "suggested_actions": [...]
}
```

#### 1.4 Feature Selection Endpoints

```
GET /api/v2/features/relevant?context=search_results
Response:
{
  "features": [
    {
      "name": "price",
      "relevance_score": 0.95,
      "display_priority": 1
    },
    {
      "name": "duration",
      "relevance_score": 0.87,
      "display_priority": 2
    },
    ...
  ]
}
```

#### 1.5 Dataset Management Endpoints

```
POST /api/v2/admin/datasets/upload
Request: multipart/form-data with CSV file

GET /api/v2/admin/datasets
GET /api/v2/admin/datasets/:dataset_id

POST /api/v2/admin/datasets/:dataset_id/validate
POST /api/v2/admin/datasets/:dataset_id/import
DELETE /api/v2/admin/datasets/:dataset_id
```

#### 1.6 Analytics Endpoints

```
GET /api/v2/analytics/search-trends
GET /api/v2/analytics/popular-routes
GET /api/v2/analytics/user-behavior
GET /api/v2/analytics/performance
```

### 2. Backend Services Architecture

#### 2.1 Route Generation Engine
**Responsibilities:**
- Accept search parameters from API
- Query database for available trains
- Build graph representation of network
- Run Pareto optimization algorithm
- Return sorted results by multiple criteria

**Key Functions:**
```python
def generate_routes(
    origin: str,
    destination: str,
    date: str,
    max_transfers: int,
    constraints: Dict
) -> List[Route]
```

**Algorithm Details:**
- Graph-based network representation
- Multi-objective optimization (price, time, transfers)
- Dynamic programming for path finding
- Constraint satisfaction for running days, availability

#### 2.2 Feature Selection Engine
**Responsibilities:**
- Analyze user context
- Extract relevant features from routes
- Score feature importance
- Rank features for display

**Scoring Criteria:**
- User preference history
- Current context relevance
- Statistical importance
- Display space constraints

**Example Logic:**
```python
def select_features(
    routes: List[Route],
    user_context: UserContext,
    available_space: int
) -> List[Feature]

# Return: [price, duration, transfers, departure_time, 
#          seat_availability, amenities]
# Based on user profile and route data
```

#### 2.3 AI Agent System
**Components:**

1. **Intent Recognizer**
   - NLP processing of user input
   - Intent classification (search, filter, compare, book)
   - Entity extraction (stations, dates, preferences)

2. **Learning Engine**
   - Track user interactions
   - Build preference profiles
   - Suggest based on patterns
   - Improve recommendations over time

3. **Decision Engine**
   - Rank route suggestions
   - Generate personalized recommendations
   - Handle multi-step conversations

4. **Response Generator**
   - Natural language response generation
   - Conversational tone
   - Actionable suggestions

**Example Flow:**
```
User: "I need to go from Delhi to Mumbai tomorrow, 
       but I'm on a tight budget"

Agent Processing:
1. Intent Recognition → "search" + "budget_conscious"
2. Entity Extraction → from: Delhi, to: Mumbai, 
                       date: tomorrow, preference: low_cost
3. Context Building → Retrieve user preferences,
                      past searches, budget patterns
4. Route Selection → Find cheapest options,
                     rank by value
5. Response → "I found 5 budget-friendly options..."
```

#### 2.4 Data Validation Pipeline
**Responsibilities:**
- Validate uploaded datasets
- Check data integrity
- Map columns to schema
- Identify missing values
- Run quality checks
- Generate validation reports

**Validation Steps:**
1. Schema validation (columns, types)
2. Referential integrity checks
3. Data range validation
4. Duplicate detection
5. Missing value handling
6. Consistency checks across tables

#### 2.5 Cache Management System
**Caching Strategy:**

| Data Type | TTL | Key Pattern | Priority |
|-----------|-----|-------------|----------|
| Route Results | 5 min | `routes:{origin}:{dest}:{date}` | High |
| Train Schedule | 1 hour | `schedule:{train_no}:{date}` | High |
| Fares | 30 min | `fare:{train}:{class}` | High |
| Station Info | 24 hours | `station:{code}` | Medium |
| User Preferences | 30 min | `user:{user_id}:prefs` | Medium |
| Search Trends | 1 hour | `trends:popular` | Low |

**Cache Invalidation:**
- Time-based expiration
- Event-based invalidation (price updates, schedule changes)
- Manual refresh for admin

### 3. Performance Requirements

| Metric | Target | Acceptable |
|--------|--------|------------|
| Search Response Time | < 1.5s | < 2.5s |
| Route Details Load | < 500ms | < 1s |
| Database Query Time | < 200ms | < 500ms |
| API Throughput | 1000 req/s | 500 req/s |
| Concurrent Users | 5000 | 2000 |
| Uptime | 99.9% | 99% |

### 4. Error Handling & Recovery

**Error Categories:**

1. **Validation Errors**
   - Invalid input parameters
   - Missing required fields
   - Out-of-range values

2. **Business Logic Errors**
   - No routes found
   - Insufficient seat availability
   - Schedule conflicts

3. **System Errors**
   - Database connection failures
   - Cache service unavailable
   - External API failures

4. **Authentication Errors**
   - Invalid credentials
   - Expired tokens
   - Insufficient permissions

**Error Response Format:**
```json
{
  "status": "error",
  "code": "VALIDATION_ERROR",
  "message": "Origin station not found",
  "details": {
    "field": "origin",
    "value": "UNKN",
    "reason": "Invalid station code"
  },
  "timestamp": "2026-01-27T10:30:00Z",
  "request_id": "uuid"
}
```

---

## Database Requirements

### 1. Core Data Schema

#### 1.1 Stations Table
```sql
CREATE TABLE stations (
  id UUID PRIMARY KEY,
  code VARCHAR(10) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  city_id UUID NOT NULL,
  region VARCHAR(100),
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  timezone VARCHAR(50),
  facilities JSONB,  -- {wifi: bool, parking: bool, etc}
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (city_id) REFERENCES cities(id)
);
```

#### 1.2 Trains Table
```sql
CREATE TABLE trains (
  id UUID PRIMARY KEY,
  number VARCHAR(10) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  train_type VARCHAR(50),  -- Express, Superfast, etc
  operator_id UUID,
  gauge VARCHAR(20),
  capacity INT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (operator_id) REFERENCES operators(id)
);
```

#### 1.3 Train Schedules Table
```sql
CREATE TABLE train_schedules (
  id UUID PRIMARY KEY,
  train_id UUID NOT NULL,
  date DATE NOT NULL,
  status VARCHAR(50),  -- Running, Cancelled, Delayed
  running_days JSONB,  -- {mon: true, tue: true, ...}
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (train_id) REFERENCES trains(id),
  UNIQUE(train_id, date)
);
```

#### 1.4 Train Routes Table
```sql
CREATE TABLE train_routes (
  id UUID PRIMARY KEY,
  train_id UUID NOT NULL,
  sequence INT NOT NULL,
  station_id UUID NOT NULL,
  arrival_time TIME,  -- Null for first station
  departure_time TIME,  -- Null for last station
  halt_duration INT,  -- Minutes
  distance INT,  -- KM from origin
  platform VARCHAR(10),
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (train_id) REFERENCES trains(id),
  FOREIGN KEY (station_id) REFERENCES stations(id),
  UNIQUE(train_id, station_id, sequence)
);
```

#### 1.5 Fares Table
```sql
CREATE TABLE fares (
  id UUID PRIMARY KEY,
  train_id UUID NOT NULL,
  origin_station_id UUID NOT NULL,
  destination_station_id UUID NOT NULL,
  class_type VARCHAR(50),  -- First, Second, AC, etc
  base_fare DECIMAL(10, 2),
  taxes DECIMAL(10, 2),
  total_fare DECIMAL(10, 2),
  currency VARCHAR(3) DEFAULT 'INR',
  valid_from DATE,
  valid_until DATE,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (train_id) REFERENCES trains(id),
  FOREIGN KEY (origin_station_id) REFERENCES stations(id),
  FOREIGN KEY (destination_station_id) REFERENCES stations(id)
);
```

#### 1.6 Seat Availability Table
```sql
CREATE TABLE seat_availability (
  id UUID PRIMARY KEY,
  train_schedule_id UUID NOT NULL,
  class_type VARCHAR(50),
  total_seats INT,
  available_seats INT,
  booked_seats INT,
  checked_at TIMESTAMP,
  expires_at TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (train_schedule_id) REFERENCES train_schedules(id)
);
```

#### 1.7 Routes Table (Multi-transfer Routes)
```sql
CREATE TABLE routes (
  id UUID PRIMARY KEY,
  origin_id UUID NOT NULL,
  destination_id UUID NOT NULL,
  journey_date DATE NOT NULL,
  total_price DECIMAL(10, 2),
  total_duration DECIMAL(8, 2),  -- Hours
  number_of_transfers INT,
  route_type VARCHAR(50),  -- Direct, OneTransfer, etc
  segments JSONB,  -- Array of segment details
  pareto_optimal BOOLEAN,
  created_at TIMESTAMP,
  FOREIGN KEY (origin_id) REFERENCES stations(id),
  FOREIGN KEY (destination_id) REFERENCES stations(id)
);
```

### 1.8 Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255),
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  phone VARCHAR(20),
  profile_picture_url VARCHAR(500),
  preferences JSONB,  -- User preferences for searches
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  last_login TIMESTAMP,
  is_active BOOLEAN DEFAULT true
);
```

#### 1.9 User Preferences Table
```sql
CREATE TABLE user_preferences (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL UNIQUE,
  preferred_class VARCHAR(50),
  budget_range JSONB,  -- {min: 0, max: 10000}
  max_transfers INT DEFAULT 2,
  preferred_departure_time_window JSONB,  -- {start: "06:00", end: "10:00"}
  preferred_stations JSONB,  -- Array of station codes
  accessibility_requirements JSONB,
  notification_preferences JSONB,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### 1.10 Search History Table
```sql
CREATE TABLE search_history (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  origin_id UUID NOT NULL,
  destination_id UUID NOT NULL,
  search_date DATE,
  search_time TIMESTAMP,
  filters_applied JSONB,
  results_count INT,
  selected_route_id UUID,
  created_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (origin_id) REFERENCES stations(id),
  FOREIGN KEY (destination_id) REFERENCES stations(id)
);
```

#### 1.11 Saved Routes Table
```sql
CREATE TABLE saved_routes (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  route_id UUID NOT NULL,
  collection_name VARCHAR(100),
  notes TEXT,
  saved_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (route_id) REFERENCES routes(id),
  UNIQUE(user_id, route_id)
);
```

### 1.12 Agent Interaction Log Table
```sql
CREATE TABLE agent_interactions (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  message TEXT NOT NULL,
  agent_response TEXT,
  intent VARCHAR(50),
  entities JSONB,
  recommended_routes JSONB,
  user_satisfaction INT,  -- 1-5 rating
  created_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### 1.13 Datasets Table
```sql
CREATE TABLE datasets (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  file_path VARCHAR(500),
  file_size BIGINT,
  row_count INT,
  columns JSONB,
  schema_mapping JSONB,
  data_type VARCHAR(50),  -- 'trains', 'stations', 'schedules', etc
  status VARCHAR(50),  -- 'pending', 'validated', 'imported', 'error'
  validation_report JSONB,
  imported_at TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  uploaded_by UUID,
  FOREIGN KEY (uploaded_by) REFERENCES users(id)
);
```

#### 1.14 Data Quality Metrics Table
```sql
CREATE TABLE data_quality_metrics (
  id UUID PRIMARY KEY,
  dataset_id UUID NOT NULL,
  metric_name VARCHAR(100),
  metric_value DECIMAL(10, 2),
  threshold_value DECIMAL(10, 2),
  status VARCHAR(50),  -- 'pass', 'warn', 'fail'
  checked_at TIMESTAMP,
  FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);
```

#### 1.15 Audit Log Table
```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  entity_type VARCHAR(100),
  entity_id UUID,
  action VARCHAR(50),  -- 'CREATE', 'UPDATE', 'DELETE'
  changes JSONB,
  performed_by UUID,
  ip_address INET,
  user_agent VARCHAR(500),
  created_at TIMESTAMP,
  FOREIGN KEY (performed_by) REFERENCES users(id)
);
```

### 2. Database Indexes

```sql
-- Performance critical indexes
CREATE INDEX idx_routes_origin_dest_date 
  ON routes(origin_id, destination_id, journey_date);

CREATE INDEX idx_train_routes_train_id 
  ON train_routes(train_id);

CREATE INDEX idx_search_history_user_id 
  ON search_history(user_id, created_at DESC);

CREATE INDEX idx_seat_availability_train_schedule 
  ON seat_availability(train_schedule_id);

CREATE INDEX idx_agents_interactions_user_date 
  ON agent_interactions(user_id, created_at DESC);

-- Full-text search indexes
CREATE INDEX idx_stations_name_search 
  ON stations USING GIN(name);

CREATE INDEX idx_trains_name_search 
  ON trains USING GIN(name);
```

### 3. Data Constraints & Validation

**Referential Integrity:**
- All foreign keys enforced
- Cascade delete policies defined
- No orphaned records

**Data Quality Rules:**
- Station codes must be 3-4 characters
- Fares must be > 0
- Distances must be >= 0
- Times must be valid 24-hour format
- Dates must be >= today

**Business Rules:**
- Train schedules must match running days
- Transfers must be at same/nearby stations
- Total journey time must be logical
- Fares must be consistent with distance

---

## AI Agent System

### 1. System Architecture

#### 1.1 Core Components

```
┌─────────────────────────────────────────────────┐
│              User Input (Text)                  │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│         Input Preprocessing & Cleaning          │
│     (Lowercase, spell check, tokenization)      │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│      Intent Recognition & Classification       │
│    (Search, Filter, Compare, Book, Help)       │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│      Named Entity Recognition (NER)             │
│  (Stations, Dates, Times, Numbers, Budget)     │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│      Context & Memory Retrieval                 │
│  (User preferences, search history, profile)    │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│     Route Generation & Ranking Engine           │
│   (Query database, apply filters, score)        │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│    Response Generation & Personalization        │
│   (Natural language, recommendations, actions)  │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│         User Output (Text + Routes)             │
└─────────────────────────────────────────────────┘
```

#### 1.2 Intent Classification

**Supported Intents:**

1. **Search Intent**
   - Trigger: "Show routes from X to Y"
   - Required entities: origin, destination, date
   - Optional: class, budget, transfers

2. **Filter Intent**
   - Trigger: "Show only cheap options"
   - Action: Apply additional constraints
   - Examples: Budget, time window, transfers

3. **Compare Intent**
   - Trigger: "Compare routes"
   - Action: Display side-by-side comparison
   - Criteria: Price, time, comfort, transfers

4. **Booking Intent**
   - Trigger: "Book this route"
   - Action: Initiate booking process
   - Confirmation required

5. **Help Intent**
   - Trigger: "How does this work?"
   - Action: Provide assistance/documentation
   - Contextual help

6. **Preference Intent**
   - Trigger: "I prefer cheapest options"
   - Action: Update user preferences
   - Personalization

**Example Intent Classification Model:**
```python
class IntentClassifier:
    def __init__(self):
        self.model = load_trained_classifier()  # ML model
        
    def classify(self, text: str) -> Intent:
        features = extract_features(text)
        intent_prob = self.model.predict_proba(features)
        intent = map_to_intent(argmax(intent_prob))
        confidence = max(intent_prob)
        return Intent(intent, confidence)
```

#### 1.3 Named Entity Recognition (NER)

**Entities to Extract:**

| Entity Type | Examples | Pattern |
|-------------|----------|---------|
| STATION | Delhi, Mumbai, NDLS | Station names/codes |
| DATE | Tomorrow, 2026-02-01 | Various date formats |
| TIME | 10 AM, 22:30 | Various time formats |
| BUDGET | 500-1000, Under 2000 | Price ranges |
| NUMBER | 1, 2, 5 passengers | Numbers with context |
| CLASS | First, Second, AC | Class types |
| TRANSFER | Direct, 1 stop, Multiple | Transfer count |
| PREFERENCE | Cheapest, Fastest | Preference keywords |

**NER Example:**
```
Input: "I want to go from Delhi to Mumbai tomorrow 
        with a budget of 1000 rupees"

Output:
{
  "STATION": ["Delhi", "Mumbai"],
  "DATE": ["tomorrow"],
  "BUDGET": [{"min": 0, "max": 1000}],
  "entities_confidence": {...}
}
```

### 2. Learning System

#### 2.1 User Preference Learning

**Learning Inputs:**
- Search history
- Selections made by user
- Ratings and feedback
- Time spent on different options
- Booking patterns

**Learning Algorithm:**
```python
def update_user_preferences(user_id: str, interaction: Interaction):
    """
    Update preferences based on user interaction
    """
    user_prefs = get_user_preferences(user_id)
    
    # Extract signals from interaction
    if interaction.selected_route:
        selected = interaction.selected_route
        # Increase weight of selected route's characteristics
        if selected.price < avg_price:
            user_prefs['price_weight'] += 0.1
        if selected.transfers < avg_transfers:
            user_prefs['transfer_weight'] += 0.1
            
    # Decay old preferences
    user_prefs = apply_decay(user_prefs, decay_rate=0.95)
    
    # Normalize
    user_prefs = normalize(user_prefs)
    
    save_user_preferences(user_id, user_prefs)
```

#### 2.2 Recommendation Engine

**Recommendation Scoring:**

For each route, calculate a personalized score:

```
score = w_price * (1 - normalized_price) +
        w_time * (1 - normalized_time) +
        w_transfers * (1 - normalized_transfers) +
        w_comfort * comfort_score +
        w_amenities * amenities_match

where:
- w_* are learned user weights
- normalized_* are 0-1 normalized metrics
- comfort_score based on class preference
- amenities_match based on user preferences
```

#### 2.3 Feedback Loop

**Explicit Feedback:**
- 5-star ratings on routes
- Thumbs up/down on recommendations
- Route helpfulness ratings

**Implicit Feedback:**
- Search patterns
- Dwell time on results
- Bookings made
- Cancellations/changes

**Feedback Integration:**
```python
def incorporate_feedback(
    user_id: str,
    route_id: str,
    rating: int,
    feedback_type: str  # 'explicit' or 'implicit'
):
    existing_rating = get_route_rating(user_id, route_id)
    
    # Exponential moving average
    alpha = 0.3 if feedback_type == 'explicit' else 0.1
    new_rating = (1-alpha) * existing_rating + alpha * rating
    
    save_route_rating(user_id, route_id, new_rating)
    
    # Update feature importance
    route = get_route(route_id)
    update_feature_weights(user_id, route, new_rating)
```

### 3. Conversational Flow Management

#### 3.1 Multi-turn Conversation Handling

**State Management:**
```python
class ConversationState:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.turns = []  # List of turns
        self.current_intent = None
        self.extracted_entities = {}
        self.context_routes = []  # Routes in current context
        self.clarifications_needed = []
        
    def add_turn(self, user_msg: str, agent_response: str):
        self.turns.append({
            'user': user_msg,
            'agent': agent_response,
            'timestamp': now()
        })
        
    def get_context_summary(self) -> str:
        """Summarize conversation context for agent"""
        return format_context(self.turns, max_turns=5)
```

#### 3.2 Clarification Handling

**When Information is Missing:**
```python
def handle_missing_entities(entities: Dict, intent: str) -> List[str]:
    """Generate clarification questions"""
    required = INTENT_REQUIREMENTS[intent]
    missing = required - set(entities.keys())
    
    clarifications = []
    for entity in missing:
        clarifications.append(CLARIFICATION_TEMPLATES[entity])
    
    return clarifications

# Example:
# Intent: Search
# Entities: {origin: 'Delhi'}
# Missing: destination, date
# Output: ["Where do you want to go?", "When do you want to travel?"]
```

### 4. Response Generation

#### 4.1 Natural Language Generation (NLG)

**Template-based Generation:**
```python
RESPONSE_TEMPLATES = {
    'search_found': (
        "I found {count} great options for you from {origin} "
        "to {destination} on {date}. "
        "The cheapest option is {cheapest_price} INR, "
        "and the fastest takes {fastest_time} hours."
    ),
    'search_not_found': (
        "I couldn't find direct routes for that date. "
        "Would you like me to show routes on {alternative_date} "
        "or with transfers?"
    ),
    'recommendation': (
        "Based on your preferences, I recommend {route_name} - "
        "it's {reason}."
    )
}

def generate_response(template_key: str, **kwargs) -> str:
    template = RESPONSE_TEMPLATES[template_key]
    return template.format(**kwargs)
```

#### 4.2 Personalization

**Tone & Style:**
```python
class AgentPersonality:
    FORMAL = "I recommend route..."
    CASUAL = "Hey! I found an awesome option..."
    TECHNICAL = "Route optimization resulted in..."
    
    def __init__(self, user_preference: str = "casual"):
        self.tone = user_preference
        
    def generate_greeting(self) -> str:
        greetings = {
            'formal': "How may I assist you?",
            'casual': "Hey there! Where to?",
            'technical': "Route optimization system ready."
        }
        return greetings[self.tone]
```

---

## Route Generation Engine

### 1. Algorithm Overview

#### 1.1 High-Level Flow

```
Input: {origin, destination, date, constraints}
         ▼
1. Query Database for all trains on date
         ▼
2. Filter trains by relevance (route coverage, type)
         ▼
3. Build Network Graph
   - Nodes: Stations
   - Edges: Train connections with weights (time, price)
         ▼
4. Find Paths (0, 1, 2, 3+ transfers)
   - Direct paths (0 transfers)
   - 1-hop paths (1 transfer)
   - 2-hop paths (2 transfers)
   - N-hop paths (3+ transfers)
         ▼
5. Filter Paths
   - Check schedule feasibility
   - Validate seat availability
   - Check running days
         ▼
6. Pareto Optimization
   - Multi-objective optimization
   - Non-dominated routes
         ▼
7. Score & Rank
   - User preference scoring
   - Personalization
         ▼
Output: Sorted list of routes
```

#### 1.2 Graph Construction

**Data Structure:**
```python
class TransportationGraph:
    def __init__(self):
        self.stations = {}  # code -> Station
        self.edges = []  # List of (from, to, train, time, fare)
        self.adj_list = {}  # Adjacency list
        
    def add_edge(self, from_station: str, to_station: str,
                 train: Train, departure: Time, arrival: Time,
                 fare: float):
        edge = Edge(
            source=from_station,
            dest=to_station,
            train=train,
            duration=arrival - departure,
            fare=fare,
            departure=departure,
            arrival=arrival
        )
        self.edges.append(edge)
        self.adj_list[from_station].append(edge)
        
    def get_outgoing_edges(self, station: str) -> List[Edge]:
        return self.adj_list.get(station, [])
```

**Graph Building Algorithm:**
```python
def build_graph_for_route(
    origin: str,
    destination: str,
    date: str,
    max_transfer_time: int = 120  # minutes
) -> TransportationGraph:
    """
    Build network graph for specific route search
    """
    graph = TransportationGraph()
    
    # Query all trains that stop at origin on this date
    trains = query_trains_for_date(date)
    
    for train in trains:
        schedule = get_train_schedule(train.id, date)
        if not schedule.is_running:
            continue
            
        stops = get_train_stops(train.id)
        
        # Add edges between consecutive stops
        for i, stop in enumerate(stops):
            for j in range(i + 1, len(stops)):
                next_stop = stops[j]
                fare = get_fare(
                    train.id, stop.station_id, 
                    next_stop.station_id
                )
                graph.add_edge(
                    from_station=stop.station_code,
                    to_station=next_stop.station_code,
                    train=train,
                    departure=stop.departure,
                    arrival=next_stop.arrival,
                    fare=fare
                )
    
    return graph
```

#### 1.3 Path Finding Algorithm

**Multi-transfer Route Finding:**
```python
def find_routes(
    graph: TransportationGraph,
    origin: str,
    destination: str,
    max_transfers: int = 3
) -> Dict[int, List[Route]]:
    """
    Find all routes from origin to destination
    Organized by number of transfers
    
    Returns: {
        0: [direct_routes],
        1: [1_transfer_routes],
        2: [2_transfer_routes],
        3: [3plus_transfer_routes]
    }
    """
    routes_by_transfers = {i: [] for i in range(max_transfers + 1)}
    
    # BFS-based search with path tracking
    queue = [(origin, [origin], [], 0)]  # (current_station, path, trains_taken, transfers)
    visited_states = set()
    
    while queue:
        current, path, trains, transfers = queue.pop(0)
        
        # Avoid infinite loops
        state = (current, len(trains), transfers)
        if state in visited_states:
            continue
        visited_states.add(state)
        
        if current == destination:
            route = construct_route(path, trains)
            routes_by_transfers[transfers].append(route)
            continue
            
        if transfers >= max_transfers:
            continue
            
        # Explore outgoing edges
        for edge in graph.get_outgoing_edges(current):
            # Check if we can take this edge from current departure
            current_time = trains[-1].arrival if trains else "00:00"
            
            # Allow transfer time
            if can_transfer(current_time, edge.departure):
                queue.append((
                    edge.dest,
                    path + [edge.dest],
                    trains + [edge.train],
                    transfers + (1 if trains else 0)
                ))
    
    return routes_by_transfers
```

### 2. Pareto Optimization

**Multi-objective Optimization:**

A route is **Pareto-optimal** if there's no other route that is better in all objectives.

**Objectives:**
1. **Price** (minimize)
2. **Time** (minimize)
3. **Transfers** (minimize)
4. **Comfort** (maximize) - based on class, amenities
5. **Departure Time** (user preference dependent)

**Algorithm:**
```python
def pareto_optimize_routes(
    routes: List[Route],
    user_preferences: Dict
) -> List[Route]:
    """
    Filter routes to Pareto frontier
    """
    # Normalize objectives to 0-1 range
    max_price = max(r.price for r in routes)
    max_time = max(r.duration for r in routes)
    max_transfers = max(r.transfers for r in routes)
    
    # Remove dominated routes
    pareto_routes = []
    for route in routes:
        dominated = False
        for other in routes:
            if route == other:
                continue
                
            # Check if other dominates route
            if (other.price <= route.price and
                other.duration <= route.duration and
                other.transfers <= route.transfers and
                (other.price < route.price or
                 other.duration < route.duration or
                 other.transfers < route.transfers)):
                dominated = True
                break
        
        if not dominated:
            pareto_routes.append(route)
    
    return pareto_routes
```

### 3. Validation & Feasibility Checks

**Checks Performed:**

1. **Schedule Validation**
   - Train is running on requested date
   - Connection is feasible (arrival < next departure)
   - Adequate transfer time

2. **Seat Availability**
   - Minimum required seats available
   - Availability updated in real-time

3. **Running Days**
   - Train runs on requested day of week
   - Special schedule handling

4. **Transfer Station Validity**
   - Stations are same or nearby
   - Transfer time is realistic

```python
def validate_route(route: Route, date: str) -> ValidationResult:
    """
    Validate route feasibility
    """
    issues = []
    
    # Check each segment
    for i, segment in enumerate(route.segments):
        # Check schedule
        if not is_train_running(segment.train_id, date):
            issues.append(f"Train {segment.train_id} not running on {date}")
            continue
            
        # Check seats
        available = get_seat_availability(
            segment.train_id, date, segment.class_type
        )
        if available < 1:
            issues.append(f"No seats available on train {segment.train_id}")
            
        # Check transfer time (if not last segment)
        if i < len(route.segments) - 1:
            next_segment = route.segments[i + 1]
            transfer_time = (next_segment.departure - segment.arrival).total_seconds() / 60
            
            if transfer_time < MIN_TRANSFER_TIME:
                issues.append(
                    f"Insufficient transfer time between segments "
                    f"({transfer_time} minutes available)"
                )
    
    is_valid = len(issues) == 0
    return ValidationResult(is_valid=is_valid, issues=issues)
```

---

## Feature Selection Framework

### 1. Feature Relevance Scoring

**Scoring Factors:**

| Factor | Weight | Description |
|--------|--------|-------------|
| User Frequency | 0.3 | How often user looks at this feature |
| Variance | 0.2 | Data variation (more variance = more relevant) |
| Correlation with Choice | 0.25 | Correlation with user's final selection |
| Context Relevance | 0.15 | Relevance to current search context |
| Screen Space | 0.1 | Available display space |

**Scoring Algorithm:**
```python
def score_feature_relevance(
    feature_name: str,
    user_id: str,
    context: SearchContext,
    available_space: int
) -> float:
    """
    Calculate relevance score for a feature
    Score range: 0-1 (higher = more relevant)
    """
    
    # Factor 1: User frequency (0-1)
    user_history = get_user_interaction_history(user_id)
    feature_views = count_feature_views(user_history, feature_name)
    user_frequency_score = min(feature_views / 100, 1.0)  # Normalize
    
    # Factor 2: Data variance in current results (0-1)
    current_routes = context.routes
    feature_values = [getattr(r, feature_name) for r in current_routes]
    variance = calculate_variance(feature_values)
    max_variance = calculate_max_possible_variance(feature_name)
    variance_score = variance / max_variance
    
    # Factor 3: Correlation with selection (0-1)
    selected_routes = get_user_selected_routes(user_id)
    correlation = calculate_correlation(
        feature_name, 
        selected_routes, 
        current_routes
    )
    correlation_score = abs(correlation)
    
    # Factor 4: Context relevance (0-1)
    context_keywords = extract_keywords(context.original_query)
    feature_context_score = calculate_relevance(
        feature_name, 
        context_keywords
    )
    
    # Factor 5: Screen space consideration
    space_score = 1.0 if available_space > FEATURE_MIN_SPACE else 0.5
    
    # Weighted combination
    relevance_score = (
        0.3 * user_frequency_score +
        0.2 * variance_score +
        0.25 * correlation_score +
        0.15 * feature_context_score +
        0.1 * space_score
    )
    
    return relevance_score
```

### 2. Feature Selection Process

**Available Features:**

| Feature | Type | Importance |
|---------|------|-----------|
| Price | Numeric | High |
| Duration | Numeric | High |
| Transfers | Numeric | High |
| Departure Time | Time | High |
| Arrival Time | Time | Medium |
| Train Name | Text | Medium |
| Class Type | Categorical | Medium |
| Seat Availability | Numeric | Medium |
| Amenities | Categorical | Low |
| Rating | Numeric | Low |
| Environmental Impact | Numeric | Low |

**Selection Algorithm:**
```python
def select_features_for_display(
    user_id: str,
    context: SearchContext,
    max_features: int = 6,
    min_relevance_threshold: float = 0.3
) -> List[SelectedFeature]:
    """
    Select most relevant features for display
    """
    
    # Score all available features
    all_features = AVAILABLE_FEATURES
    scored_features = []
    
    for feature in all_features:
        score = score_feature_relevance(
            feature.name, 
            user_id, 
            context,
            context.available_space
        )
        scored_features.append((feature, score))
    
    # Sort by score
    scored_features.sort(key=lambda x: x[1], reverse=True)
    
    # Select features above threshold
    selected = []
    for feature, score in scored_features:
        if score >= min_relevance_threshold and len(selected) < max_features:
            selected.append(SelectedFeature(
                name=feature.name,
                relevance_score=score,
                display_priority=len(selected) + 1
            ))
    
    return selected
```

### 3. Dynamic Feature Adjustment

**Adaptation Rules:**

```python
def adapt_feature_selection(
    user_interaction: UserInteraction,
    current_selection: List[Feature]
) -> List[Feature]:
    """
    Adjust feature selection based on user interaction
    """
    
    if interaction.type == 'expanded_feature':
        # User expanded a feature - increase its priority
        feature = interaction.feature
        update_user_feature_preference(
            user_id,
            feature.name,
            delta=+0.1
        )
    
    elif interaction.type == 'ignored_feature':
        # User ignored a feature - decrease its priority
        feature = interaction.feature
        update_user_feature_preference(
            user_id,
            feature.name,
            delta=-0.05
        )
    
    elif interaction.type == 'filtered_by_feature':
        # User used a feature to filter - increase relevance
        feature = interaction.feature
        update_feature_correlation(
            user_id,
            feature.name,
            delta=+0.15
        )
    
    # Recalculate and return updated selection
    return select_features_for_display(
        user_id,
        interaction.context,
        max_features=len(current_selection)
    )
```

---

## Data Management Pipeline

### 1. Dataset Upload & Validation

#### 1.1 Upload Process

```
User Upload
    ▼
1. File Validation
   - Check format (CSV, Excel, JSON)
   - Check file size (< 500MB)
   - Scan for malware
    ▼
2. Schema Detection
   - Auto-detect columns
   - Infer data types
   - Detect primary keys
    ▼
3. Preview & Mapping
   - Show sample rows
   - Allow user to map columns
   - Define data types
    ▼
4. Data Validation
   - Type validation
   - Range validation
   - Referential integrity
    ▼
5. Quality Assessment
   - Calculate quality metrics
   - Identify issues
   - Generate report
    ▼
6. Import Confirmation
   - Review validation results
   - Confirm import
    ▼
7. Database Import
   - Load to staging table
   - Validate constraints
   - Merge with existing data
    ▼
8. Post-import Processing
   - Create indexes
   - Update statistics
   - Clear cache
```

#### 1.2 Data Validation Checklist

```python
class DataValidationEngine:
    def validate_dataset(self, dataset: Dataset) -> ValidationReport:
        report = ValidationReport()
        
        # 1. Structure validation
        try:
            report.add_check(
                'column_count',
                self.validate_columns(dataset)
            )
            report.add_check(
                'data_types',
                self.validate_types(dataset)
            )
        except Exception as e:
            report.add_error('structure', str(e))
            return report
        
        # 2. Data quality validation
        report.add_check(
            'missing_values',
            self.check_missing_values(dataset)
        )
        report.add_check(
            'duplicates',
            self.check_duplicates(dataset)
        )
        report.add_check(
            'ranges',
            self.validate_ranges(dataset)
        )
        
        # 3. Referential integrity
        report.add_check(
            'foreign_keys',
            self.validate_foreign_keys(dataset)
        )
        
        # 4. Business logic validation
        report.add_check(
            'schedule_logic',
            self.validate_schedule_logic(dataset)
        )
        report.add_check(
            'fare_logic',
            self.validate_fare_logic(dataset)
        )
        
        # 5. Generate quality score
        report.quality_score = self.calculate_quality_score(report)
        
        return report
```

### 2. Data Transformation Pipeline

**ETL Stages:**

```
Extract
├─ Read from various sources
├─ Parse different formats
└─ Handle encoding issues
    ▼
Transform
├─ Data cleaning
├─ Schema mapping
├─ Normalization
├─ Enrichment
└─ Deduplication
    ▼
Load
├─ Validation
├─ Constraints enforcement
├─ Index creation
└─ Cache invalidation
```

**Transformation Example:**
```python
def transform_stations_dataset(raw_data: DataFrame) -> DataFrame:
    """
    Transform raw stations data to database schema
    """
    df = raw_data.copy()
    
    # Standardize column names
    df.columns = [normalize_column_name(c) for c in df.columns]
    
    # Clean data
    df['station_code'] = df['station_code'].str.upper().str.strip()
    df['station_name'] = df['station_name'].str.title().str.strip()
    
    # Validate codes
    df = df[df['station_code'].str.match(r'^[A-Z]{3,4}$')]
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['station_code'])
    
    # Add generated columns
    df['id'] = [generate_uuid() for _ in range(len(df))]
    df['created_at'] = pd.Timestamp.now()
    df['updated_at'] = pd.Timestamp.now()
    
    # Type conversion
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    return df
```

### 3. Data Quality Monitoring

**Continuous Monitoring:**

```python
class DataQualityMonitor:
    def __init__(self):
        self.checks = []
        
    def add_quality_check(self, check_name: str, check_func):
        self.checks.append((check_name, check_func))
        
    def run_quality_checks(self, dataset_id: str) -> QualityReport:
        report = QualityReport()
        data = query_dataset(dataset_id)
        
        for check_name, check_func in self.checks:
            try:
                result = check_func(data)
                report.add_result(check_name, result)
            except Exception as e:
                report.add_error(check_name, str(e))
        
        return report

# Example checks
monitor = DataQualityMonitor()

monitor.add_quality_check(
    'null_values',
    lambda df: {
        'total_nulls': df.isnull().sum().sum(),
        'percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
    }
)

monitor.add_quality_check(
    'duplicate_stations',
    lambda df: {
        'duplicates': df['station_code'].duplicated().sum(),
        'duplicate_codes': df[df['station_code'].duplicated()]['station_code'].unique().tolist()
    }
)

monitor.add_quality_check(
    'invalid_coordinates',
    lambda df: {
        'invalid_latitude': ((df['latitude'] < -90) | (df['latitude'] > 90)).sum(),
        'invalid_longitude': ((df['longitude'] < -180) | (df['longitude'] > 180)).sum()
    }
)
```

---

## Security & Compliance

### 1. Authentication & Authorization

**Authentication Methods:**
- Email/Password with bcrypt hashing
- JWT tokens for API authentication
- OAuth 2.0 for third-party integration
- Two-factor authentication (2FA) optional

**Authorization Levels:**
- **Guest**: Browse routes, search
- **User**: Booking, saved preferences, history
- **Premium**: Priority support, special routes
- **Admin**: Data management, user management
- **Superadmin**: System configuration

### 2. Data Security

**Encryption:**
- HTTPS/TLS for all data in transit
- AES-256 for sensitive data at rest
- API keys encrypted in database
- User passwords never stored as plaintext

**Privacy Measures:**
- GDPR compliance
- Data retention policies
- User consent for tracking
- Data anonymization for analytics
- Audit trails for data access

### 3. API Security

**Rate Limiting:**
- 1000 requests per minute per IP
- 100 requests per minute for unauthenticated
- Burst limit: 10 requests per second

**Input Validation:**
- SQL injection prevention
- XSS prevention
- CSRF token validation
- Input sanitization

---

## Implementation Roadmap

### Phase 1: Foundation (Months 1-2)
- [x] Database schema design and setup
- [x] Core API endpoints
- [ ] Frontend basic layout
- [ ] Basic route search functionality

### Phase 2: Core Features (Months 3-4)
- [ ] Multi-transfer route generation
- [ ] Feature selection framework
- [ ] Advanced filtering
- [ ] User authentication

### Phase 3: AI Agent (Months 5-6)
- [ ] Intent recognition model
- [ ] NER implementation
- [ ] Preference learning
- [ ] Chat interface

### Phase 4: Optimization (Months 7-8)
- [ ] Performance tuning
- [ ] Caching strategy
- [ ] Database optimization
- [ ] Frontend optimization

### Phase 5: Production Readiness (Months 9-10)
- [ ] Security hardening
- [ ] Testing (unit, integration, E2E)
- [ ] Documentation
- [ ] Deployment preparation

### Phase 6: Launch & Scale (Month 11+)
- [ ] Production deployment
- [ ] Monitoring setup
- [ ] Marketing launch
- [ ] Continuous improvement

---

## Success Metrics

### User Metrics
- **Search Success Rate**: > 95%
- **Average Response Time**: < 2 seconds
- **User Satisfaction**: > 4.5/5
- **Conversion Rate**: > 10%

### System Metrics
- **API Uptime**: > 99.9%
- **Database Query Time**: < 200ms
- **Page Load Time**: < 1.5 seconds
- **Error Rate**: < 0.1%

### Business Metrics
- **Monthly Active Users**: Target growth
- **Booking Volume**: X routes booked/month
- **Revenue**: Y INR/month
- **Customer Retention**: > 70%

---

## Conclusion

This comprehensive specification document outlines a complete startup platform for intelligent route optimization. The system combines advanced algorithms, real-time data management, AI-powered personalization, and a user-friendly interface to deliver an exceptional travel planning experience.

By following this specification, the team can build a scalable, maintainable, and feature-rich platform that meets user needs while maintaining high standards for data quality, security, and performance.

---

## Appendix: Technical Glossary

- **Pareto Optimal**: A solution where no objective can be improved without worsening another
- **ETL**: Extract, Transform, Load - data pipeline process
- **NER**: Named Entity Recognition - identifying entities in text
- **NLP**: Natural Language Processing - understanding human language
- **API**: Application Programming Interface - software communication protocol
- **JWT**: JSON Web Token - stateless authentication
- **GDPR**: General Data Protection Regulation - data privacy regulation
- **TTL**: Time To Live - cache expiration time
- **ORM**: Object-Relational Mapping - database abstraction layer

