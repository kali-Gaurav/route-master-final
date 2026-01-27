# Development Prompt: Build Complete Route Optimization Platform Website

## Executive Directive

You are building a **complete, production-ready Intelligent Route Optimization and Travel Planning Platform** from scratch. This platform combines advanced route generation algorithms, AI-powered personalization, comprehensive data management, and real-time transportation data integration. Follow the requirements specification document (STARTUP_REQUIREMENTS_SPECIFICATION.md) and implement the system systematically.

---

## Part 1: Project Initialization & Setup

### 1.1 Repository & Environment Setup

**Create Project Structure:**
```
route-optimization-platform/
├── frontend/                    # React/TypeScript frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── services/           # API services
│   │   ├── hooks/              # Custom React hooks
│   │   ├── store/              # State management
│   │   ├── types/              # TypeScript types
│   │   ├── utils/              # Utility functions
│   │   ├── styles/             # CSS/Tailwind
│   │   └── App.tsx             # Main app component
│   ├── public/                 # Static assets
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.ts
│
├── backend/                     # Flask/FastAPI backend
│   ├── app/
│   │   ├── api/                # API routes
│   │   ├── services/           # Business logic
│   │   ├── models/             # Database models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── utils/              # Utility functions
│   │   ├── middleware/         # Custom middleware
│   │   └── __init__.py
│   ├── database/               # Database setup
│   ├── migrations/             # Database migrations
│   ├── config.py               # Configuration
│   ├── requirements.txt        # Python dependencies
│   └── run.py                  # Entry point
│
├── database/                    # Database setup & migrations
│   ├── schemas/                # SQL schema files
│   ├── migrations/             # Migration scripts
│   ├── seeds/                  # Seed data
│   └── init.sql                # Initial setup
│
├── docs/                        # Documentation
│   ├── API.md                  # API documentation
│   ├── ARCHITECTURE.md         # System architecture
│   └── SETUP.md                # Setup guide
│
├── docker-compose.yml          # Docker orchestration
├── .env.example                # Environment template
└── README.md                   # Project README
```

### 1.2 Technology Installation

**Backend Stack:**
```bash
# Python 3.10+
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install core dependencies
pip install flask==2.3.0
pip install flask-cors==4.0.0
pip install flask-sqlalchemy==3.0.0
pip install python-dotenv==1.0.0
pip install requests==2.31.0
pip install pandas==2.0.0
pip install numpy==1.24.0
pip install scikit-learn==1.3.0
pip install spacy==3.5.0
pip install redis==5.0.0
pip install celery==5.3.0
pip install pydantic==2.0.0
```

**Frontend Stack:**
```bash
# Node.js 18+
# Create React app with Vite
npm create vite@latest frontend -- --template react-ts

cd frontend
npm install

# Install UI libraries
npm install react-router-dom axios zustand @tanstack/react-query
npm install tailwindcss postcss autoprefixer
npm install recharts leaflet react-leaflet
npm install lucide-react shadcn-ui
```

**Database:**
```bash
# PostgreSQL 13+ required
# Create database
createdb route_optimization_db

# Install client
pip install psycopg2-binary==2.9.0
pip install sqlalchemy==2.0.0
```

---

## Part 2: Database Implementation

### 2.1 Database Schema Creation

**Step 1: Create Core Tables**

```sql
-- Execute the following in PostgreSQL:

-- 1. Cities Table
CREATE TABLE cities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL UNIQUE,
  state VARCHAR(100),
  country VARCHAR(100) DEFAULT 'India',
  timezone VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Stations Table
CREATE TABLE stations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code VARCHAR(10) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  city_id UUID NOT NULL,
  region VARCHAR(100),
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  timezone VARCHAR(50),
  facilities JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (city_id) REFERENCES cities(id),
  INDEX idx_station_code (code),
  INDEX idx_station_city (city_id)
);

-- 3. Operators Table
CREATE TABLE operators (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL UNIQUE,
  code VARCHAR(20),
  country VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Trains Table
CREATE TABLE trains (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  number VARCHAR(10) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  train_type VARCHAR(50),
  operator_id UUID,
  gauge VARCHAR(20),
  capacity INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (operator_id) REFERENCES operators(id),
  INDEX idx_train_number (number)
);

-- 5. Train Schedules Table
CREATE TABLE train_schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  train_id UUID NOT NULL,
  date DATE NOT NULL,
  status VARCHAR(50) DEFAULT 'Running',
  running_days JSONB DEFAULT '{"mon":true,"tue":true,"wed":true,"thu":true,"fri":true,"sat":true,"sun":true}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (train_id) REFERENCES trains(id),
  UNIQUE(train_id, date),
  INDEX idx_schedule_train_date (train_id, date)
);

-- 6. Train Routes Table (stations on train route)
CREATE TABLE train_routes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  train_id UUID NOT NULL,
  sequence INT NOT NULL,
  station_id UUID NOT NULL,
  arrival_time TIME,
  departure_time TIME,
  halt_duration INT DEFAULT 0,
  distance INT DEFAULT 0,
  platform VARCHAR(10),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (train_id) REFERENCES trains(id),
  FOREIGN KEY (station_id) REFERENCES stations(id),
  UNIQUE(train_id, station_id, sequence),
  INDEX idx_train_route_train (train_id)
);

-- 7. Fares Table
CREATE TABLE fares (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  train_id UUID NOT NULL,
  origin_station_id UUID NOT NULL,
  destination_station_id UUID NOT NULL,
  class_type VARCHAR(50),
  base_fare DECIMAL(10, 2),
  taxes DECIMAL(10, 2) DEFAULT 0,
  total_fare DECIMAL(10, 2),
  currency VARCHAR(3) DEFAULT 'INR',
  valid_from DATE,
  valid_until DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (train_id) REFERENCES trains(id),
  FOREIGN KEY (origin_station_id) REFERENCES stations(id),
  FOREIGN KEY (destination_station_id) REFERENCES stations(id),
  INDEX idx_fare_train_stations (train_id, origin_station_id, destination_station_id)
);

-- 8. Seat Availability Table
CREATE TABLE seat_availability (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  train_schedule_id UUID NOT NULL,
  class_type VARCHAR(50),
  total_seats INT,
  available_seats INT,
  booked_seats INT DEFAULT 0,
  checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (train_schedule_id) REFERENCES train_schedules(id),
  INDEX idx_seat_avail_schedule (train_schedule_id)
);

-- 9. Routes Table (multi-transfer routes)
CREATE TABLE routes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  origin_id UUID NOT NULL,
  destination_id UUID NOT NULL,
  journey_date DATE NOT NULL,
  total_price DECIMAL(10, 2),
  total_duration DECIMAL(8, 2),
  number_of_transfers INT,
  route_type VARCHAR(50),
  segments JSONB,
  pareto_optimal BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (origin_id) REFERENCES stations(id),
  FOREIGN KEY (destination_id) REFERENCES stations(id),
  INDEX idx_route_origin_dest_date (origin_id, destination_id, journey_date)
);

-- 10. Users Table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255),
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  phone VARCHAR(20),
  profile_picture_url VARCHAR(500),
  is_email_verified BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP,
  INDEX idx_user_email (email)
);

-- 11. User Preferences Table
CREATE TABLE user_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE,
  preferred_class VARCHAR(50),
  budget_range JSONB DEFAULT '{"min":0,"max":10000}',
  max_transfers INT DEFAULT 2,
  preferred_departure_time_window JSONB,
  preferred_stations JSONB DEFAULT '[]',
  accessibility_requirements JSONB DEFAULT '{}',
  notification_preferences JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 12. Search History Table
CREATE TABLE search_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  origin_id UUID NOT NULL,
  destination_id UUID NOT NULL,
  search_date DATE,
  search_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  filters_applied JSONB DEFAULT '{}',
  results_count INT,
  selected_route_id UUID,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (origin_id) REFERENCES stations(id),
  FOREIGN KEY (destination_id) REFERENCES stations(id),
  INDEX idx_search_history_user (user_id, search_time DESC)
);

-- 13. Saved Routes Table
CREATE TABLE saved_routes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  route_id UUID NOT NULL,
  collection_name VARCHAR(100),
  notes TEXT,
  saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (route_id) REFERENCES routes(id),
  UNIQUE(user_id, route_id),
  INDEX idx_saved_routes_user (user_id)
);

-- 14. Agent Interactions Table
CREATE TABLE agent_interactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  message TEXT NOT NULL,
  agent_response TEXT,
  intent VARCHAR(50),
  entities JSONB DEFAULT '{}',
  recommended_routes JSONB DEFAULT '[]',
  user_satisfaction INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_agent_interactions_user (user_id, created_at DESC)
);

-- 15. Datasets Table
CREATE TABLE datasets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  file_path VARCHAR(500),
  file_size BIGINT,
  row_count INT,
  columns JSONB DEFAULT '[]',
  schema_mapping JSONB DEFAULT '{}',
  data_type VARCHAR(50),
  status VARCHAR(50) DEFAULT 'pending',
  validation_report JSONB DEFAULT '{}',
  imported_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  uploaded_by UUID,
  FOREIGN KEY (uploaded_by) REFERENCES users(id),
  INDEX idx_datasets_status (status)
);

-- 16. Data Quality Metrics Table
CREATE TABLE data_quality_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dataset_id UUID NOT NULL,
  metric_name VARCHAR(100),
  metric_value DECIMAL(10, 2),
  threshold_value DECIMAL(10, 2),
  status VARCHAR(50),
  checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (dataset_id) REFERENCES datasets(id),
  INDEX idx_quality_metrics_dataset (dataset_id)
);

-- 17. Audit Log Table
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type VARCHAR(100),
  entity_id UUID,
  action VARCHAR(50),
  changes JSONB DEFAULT '{}',
  performed_by UUID,
  ip_address INET,
  user_agent VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (performed_by) REFERENCES users(id),
  INDEX idx_audit_logs_entity (entity_type, entity_id)
);

-- Create indexes for performance
CREATE INDEX idx_cities_name ON cities(name);
CREATE INDEX idx_stations_search ON stations USING GIN(to_tsvector('english', name));
CREATE INDEX idx_trains_search ON trains USING GIN(to_tsvector('english', name));
CREATE INDEX idx_routes_pareto ON routes(pareto_optimal, journey_date);
```

---

## Part 3: Backend Implementation

### 3.1 Backend Project Structure & Configuration

**Create Flask Application (`backend/app/__init__.py`):**

```python
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/route_optimization_db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=os.getenv('CORS_ORIGINS', ['http://localhost:3000']).split(','))
    
    # Register blueprints
    from app.api import auth_bp, routes_bp, users_bp, admin_bp, agent_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(routes_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(agent_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
```

### 3.2 Database Models

**Create SQLAlchemy Models (`backend/app/models/`):**

```python
# models/__init__.py
from .user import User, UserPreferences
from .station import Station, City
from .train import Train, TrainSchedule, TrainRoute, Operator
from .fare import Fare
from .seat import SeatAvailability
from .route import Route
from .search import SearchHistory, SavedRoute
from .agent import AgentInteraction
from .dataset import Dataset, DataQualityMetric
from .audit import AuditLog

__all__ = [
    'User', 'UserPreferences', 'Station', 'City', 'Train',
    'TrainSchedule', 'TrainRoute', 'Operator', 'Fare',
    'SeatAvailability', 'Route', 'SearchHistory', 'SavedRoute',
    'AgentInteraction', 'Dataset', 'DataQualityMetric', 'AuditLog'
]

# models/user.py
from app import db
from uuid import uuid4
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    profile_picture_url = db.Column(db.String(500))
    is_email_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    preferences = db.relationship('UserPreferences', backref='user', uselist=False, cascade='all, delete-orphan')
    search_history = db.relationship('SearchHistory', backref='user', cascade='all, delete-orphan')
    saved_routes = db.relationship('SavedRoute', backref='user', cascade='all, delete-orphan')
    agent_interactions = db.relationship('AgentInteraction', backref='user', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'profile_picture_url': self.profile_picture_url,
            'is_email_verified': self.is_email_verified,
            'created_at': self.created_at.isoformat(),
        }

class UserPreferences(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)
    preferred_class = db.Column(db.String(50))
    budget_range = db.Column(db.JSON, default={'min': 0, 'max': 10000})
    max_transfers = db.Column(db.Integer, default=2)
    preferred_departure_time_window = db.Column(db.JSON)
    preferred_stations = db.Column(db.JSON, default=[])
    accessibility_requirements = db.Column(db.JSON, default={})
    notification_preferences = db.Column(db.JSON, default={})
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 3.3 API Endpoints

**Create Route Search API (`backend/app/api/routes.py`):**

```python
from flask import Blueprint, request, jsonify
from app.services.route_service import RouteService
from app.models import Station, Route
from app import db
import logging

routes_bp = Blueprint('routes', __name__, url_prefix='/api/v2/routes')
logger = logging.getLogger(__name__)

route_service = RouteService()

@routes_bp.route('/search', methods=['POST'])
def search_routes():
    """
    Search for routes between origin and destination
    
    Request JSON:
    {
        "origin": "NDLS",
        "destination": "MMCT",
        "date": "2026-02-01",
        "passengers": 1,
        "class": "second",
        "budget_min": 0,
        "budget_max": 10000,
        "max_transfers": 3
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['origin', 'destination', 'date']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Search routes
        routes = route_service.search_routes(
            origin=data['origin'],
            destination=data['destination'],
            date=data['date'],
            max_transfers=data.get('max_transfers', 3),
            budget_min=data.get('budget_min', 0),
            budget_max=data.get('budget_max', 100000),
            passengers=data.get('passengers', 1),
            class_type=data.get('class', 'second')
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'direct': [r.to_dict() for r in routes.get(0, [])],
                'one_transfer': [r.to_dict() for r in routes.get(1, [])],
                'two_transfer': [r.to_dict() for r in routes.get(2, [])],
                'three_transfer': [r.to_dict() for r in routes.get(3, [])]
            },
            'metadata': {
                'total_results': sum(len(r) for r in routes.values()),
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching routes: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@routes_bp.route('/<route_id>', methods=['GET'])
def get_route_details(route_id):
    """Get detailed information about a specific route"""
    try:
        route = Route.query.filter_by(id=route_id).first()
        if not route:
            return jsonify({'error': 'Route not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': route.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving route: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
```

---

## Part 4: Frontend Implementation

### 4.1 Frontend Project Setup

**Create Vite React App with TypeScript:**

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 4.2 Core Components

**Create Main Layout (`frontend/src/App.tsx`):**

```typescript
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import SearchPage from './pages/SearchPage';
import RouteDetailsPage from './pages/RouteDetailsPage';
import ProfilePage from './pages/ProfilePage';
import AdminDashboard from './pages/AdminDashboard';
import AgentPage from './pages/AgentPage';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="flex flex-col min-h-screen">
          <Navbar />
          <main className="flex-grow">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/route/:id" element={<RouteDetailsPage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/agent" element={<AgentPage />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
```

**Create Search Component (`frontend/src/components/RouteSearch.tsx`):**

```typescript
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { searchRoutes } from '@/services/api';

interface SearchParams {
  origin: string;
  destination: string;
  date: string;
  passengers: number;
  class: string;
  budget_min: number;
  budget_max: number;
  max_transfers: number;
}

export default function RouteSearch() {
  const [searchParams, setSearchParams] = useState<SearchParams>({
    origin: '',
    destination: '',
    date: '',
    passengers: 1,
    class: 'second',
    budget_min: 0,
    budget_max: 10000,
    max_transfers: 3
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['routes', searchParams],
    queryFn: () => searchRoutes(searchParams),
    enabled: !!searchParams.origin && !!searchParams.destination && !!searchParams.date
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Query is triggered automatically by useQuery
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <form onSubmit={handleSearch} className="bg-white rounded-lg shadow-lg p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">From</label>
            <input
              type="text"
              placeholder="Origin station"
              value={searchParams.origin}
              onChange={(e) => setSearchParams({...searchParams, origin: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 border p-2"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">To</label>
            <input
              type="text"
              placeholder="Destination station"
              value={searchParams.destination}
              onChange={(e) => setSearchParams({...searchParams, destination: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 border p-2"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Date</label>
            <input
              type="date"
              value={searchParams.date}
              onChange={(e) => setSearchParams({...searchParams, date: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 border p-2"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Class</label>
            <select
              value={searchParams.class}
              onChange={(e) => setSearchParams({...searchParams, class: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 border p-2"
            >
              <option value="second">Second</option>
              <option value="first">First</option>
              <option value="ac_first">AC First</option>
            </select>
          </div>
        </div>
        
        <button
          type="submit"
          className="mt-4 w-full bg-blue-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-blue-700"
        >
          Search Routes
        </button>
      </form>

      {isLoading && <div className="text-center">Loading routes...</div>}
      {error && <div className="text-red-600">Error: {error.message}</div>}
      
      {data && (
        <div className="grid gap-4">
          <h2 className="text-2xl font-bold">Results</h2>
          {/* Display routes */}
          {data.data.direct.length > 0 && (
            <div>
              <h3 className="text-xl font-semibold mb-2">Direct Routes</h3>
              {data.data.direct.map((route) => (
                <RouteCard key={route.id} route={route} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function RouteCard({ route }: { route: any }) {
  return (
    <div className="bg-white p-4 rounded-lg shadow border border-gray-200 mb-2">
      <div className="flex justify-between items-center">
        <div>
          <p className="font-bold">{route.number_of_transfers} Transfers</p>
          <p className="text-sm text-gray-600">Duration: {route.total_duration}h</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-blue-600">₹{route.total_price}</p>
          <button className="mt-2 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            View Details
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

## Part 5: AI Agent System Implementation

### 5.1 Intent Recognition

**Create Intent Classifier (`backend/app/services/intent_classifier.py`):**

```python
import spacy
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import os

class IntentClassifier:
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.classifier = MultinomialNB()
        self.intent_map = {
            0: 'search',
            1: 'filter',
            2: 'compare',
            3: 'booking',
            4: 'help',
            5: 'preference'
        }
        
        # Load trained model if exists
        if os.path.exists('models/intent_classifier.pkl'):
            self.load_model()
    
    def extract_entities(self, text: str) -> dict:
        """Extract named entities from text"""
        doc = self.nlp(text)
        
        entities = {
            'STATION': [],
            'DATE': [],
            'TIME': [],
            'BUDGET': [],
            'NUMBER': [],
            'CLASS': [],
            'TRANSFER': [],
            'PREFERENCE': []
        }
        
        # Custom entity extraction logic
        for token in doc:
            if token.ent_type_ == 'PERSON':  # Custom: station names might appear as PERSON
                entities['STATION'].append(token.text)
            elif token.ent_type_ == 'DATE':
                entities['DATE'].append(token.text)
        
        return entities
    
    def classify(self, text: str) -> dict:
        """Classify user intent"""
        # Vectorize input
        text_vector = self.vectorizer.transform([text])
        
        # Predict intent
        intent_code = self.classifier.predict(text_vector)[0]
        confidence = self.classifier.predict_proba(text_vector).max()
        
        # Extract entities
        entities = self.extract_entities(text)
        
        return {
            'intent': self.intent_map.get(intent_code, 'unknown'),
            'confidence': float(confidence),
            'entities': entities
        }
    
    def train(self, texts: list, labels: list):
        """Train the classifier"""
        # Vectorize texts
        text_vectors = self.vectorizer.fit_transform(texts)
        
        # Train classifier
        self.classifier.fit(text_vectors, labels)
        
        # Save model
        self.save_model()
    
    def save_model(self):
        """Save trained model"""
        os.makedirs('models', exist_ok=True)
        with open('models/intent_classifier.pkl', 'wb') as f:
            pickle.dump(self.classifier, f)
    
    def load_model(self):
        """Load trained model"""
        with open('models/intent_classifier.pkl', 'rb') as f:
            self.classifier = pickle.load(f)
```

### 5.2 Agent Response Service

**Create Agent Service (`backend/app/services/agent_service.py`):**

```python
from app.services.intent_classifier import IntentClassifier
from app.services.route_service import RouteService
from app.models import User, UserPreferences, AgentInteraction
from app import db
from datetime import datetime

class AgentService:
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.route_service = RouteService()
        
        # Response templates
        self.templates = {
            'search_found': (
                "I found {count} great options for you from {origin} "
                "to {destination} on {date}. The cheapest option is ₹{cheapest}, "
                "and the fastest takes {fastest_time} hours."
            ),
            'search_not_found': (
                "I couldn't find direct routes for that date. "
                "Would you like to see routes with transfers?"
            ),
            'recommendation': (
                "Based on your preferences, I recommend {route_name} - it's {reason}."
            )
        }
    
    def process_message(self, user_id: str, message: str) -> dict:
        """Process user message and generate response"""
        
        # Classify intent
        classification = self.intent_classifier.classify(message)
        intent = classification['intent']
        entities = classification['entities']
        
        # Get user preferences
        user = User.query.get(user_id)
        prefs = user.preferences if user else None
        
        # Process based on intent
        if intent == 'search':
            response = self._handle_search_intent(entities, prefs)
        elif intent == 'filter':
            response = self._handle_filter_intent(entities, prefs)
        elif intent == 'preference':
            response = self._handle_preference_intent(entities, user)
        else:
            response = self._handle_help_intent()
        
        # Save interaction
        interaction = AgentInteraction(
            user_id=user_id,
            message=message,
            agent_response=response['text'],
            intent=intent,
            entities=entities,
            recommended_routes=str(response.get('routes', []))
        )
        db.session.add(interaction)
        db.session.commit()
        
        return response
    
    def _handle_search_intent(self, entities: dict, prefs) -> dict:
        """Handle search intent"""
        origin = entities.get('STATION', [None])[0]
        destination = entities.get('STATION', [None])[1] if len(entities.get('STATION', [])) > 1 else None
        
        if not origin or not destination:
            return {
                'text': "I need to know your origin and destination. Where are you traveling from and to?",
                'routes': []
            }
        
        # Search routes
        routes = self.route_service.search_routes(
            origin=origin,
            destination=destination,
            date=entities.get('DATE', [None])[0],
            max_transfers=3
        )
        
        total = sum(len(r) for r in routes.values())
        cheapest = min(
            [r for route_list in routes.values() for r in route_list],
            key=lambda x: x.total_price,
            default=None
        )
        
        if total == 0:
            return {
                'text': self.templates['search_not_found'],
                'routes': []
            }
        
        response_text = self.templates['search_found'].format(
            count=total,
            origin=origin,
            destination=destination,
            date=entities.get('DATE', ['today'])[0],
            cheapest=cheapest.total_price if cheapest else 'N/A',
            fastest_time=min([r.total_duration for route_list in routes.values() for r in route_list], default=0)
        )
        
        return {
            'text': response_text,
            'routes': [r.id for route_list in routes.values() for r in route_list[:3]]
        }
    
    def _handle_filter_intent(self, entities: dict, prefs) -> dict:
        """Handle filter intent"""
        return {
            'text': "I'll apply those filters to your search results.",
            'routes': []
        }
    
    def _handle_preference_intent(self, entities: dict, user) -> dict:
        """Handle preference update"""
        if user and user.preferences:
            # Update preferences based on entities
            user.preferences.updated_at = datetime.utcnow()
            db.session.commit()
        
        return {
            'text': "I've updated your preferences!",
            'routes': []
        }
    
    def _handle_help_intent(self) -> dict:
        """Handle help intent"""
        return {
            'text': "How can I help you? I can search for routes, apply filters, compare options, or help with bookings.",
            'routes': []
        }
```

### 5.3 Agent API Endpoint

**Add Agent Endpoint (`backend/app/api/agent.py`):**

```python
from flask import Blueprint, request, jsonify
from app.services.agent_service import AgentService
from app.middleware.auth import require_auth
import logging

agent_bp = Blueprint('agent', __name__, url_prefix='/api/v2/agent')
logger = logging.getLogger(__name__)
agent_service = AgentService()

@agent_bp.route('/chat', methods=['POST'])
@require_auth
def chat(user_id):
    """
    Send message to AI agent
    
    Request JSON:
    {
        "message": "Show me cheap routes from Delhi to Mumbai"
    }
    """
    try:
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        response = agent_service.process_message(user_id, message)
        
        return jsonify({
            'status': 'success',
            'data': {
                'response': response['text'],
                'recommended_routes': response.get('routes', []),
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing agent message: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
```

---

## Part 6: Route Generation Algorithm

### 6.1 Route Optimizer Service

**Create Route Optimizer (`backend/app/services/route_optimizer.py`):**

```python
from typing import List, Dict
from datetime import datetime, timedelta
from app.models import Train, TrainSchedule, TrainRoute, Fare, Station
from app import db

class RouteOptimizer:
    
    def __init__(self):
        self.MIN_TRANSFER_TIME = 120  # minutes
        self.MAX_TRANSFER_TIME = 1440  # 24 hours
    
    def find_routes(
        self,
        origin_code: str,
        destination_code: str,
        date: str,
        max_transfers: int = 3
    ) -> Dict[int, List[dict]]:
        """
        Find all routes from origin to destination
        Returns routes grouped by number of transfers
        """
        
        # Get stations
        origin = Station.query.filter_by(code=origin_code).first()
        destination = Station.query.filter_by(code=destination_code).first()
        
        if not origin or not destination:
            return {}
        
        routes_by_transfers = {i: [] for i in range(max_transfers + 1)}
        
        # BFS-based path finding
        from collections import deque
        
        queue = deque([(origin.id, [origin.id], [], 0, None)])  # (station_id, path, trains, transfers, arrival_time)
        visited = set()
        
        while queue:
            current_id, path, trains, transfers, arrival_time = queue.popleft()
            
            # Check if we reached destination
            if current_id == destination.id:
                route = self._construct_route(path, trains)
                if route:
                    routes_by_transfers[transfers].append(route)
                continue
            
            # Limit search depth
            if transfers >= max_transfers:
                continue
            
            # Find outgoing trains from current station
            outgoing = self._find_outgoing_trains(current_id, date, arrival_time)
            
            for train_id, next_station_id, departure, arrival in outgoing:
                state = (next_station_id, len(trains) + 1)
                
                if state not in visited:
                    visited.add(state)
                    queue.append((
                        next_station_id,
                        path + [next_station_id],
                        trains + [train_id],
                        transfers + 1 if trains else 0,
                        arrival
                    ))
        
        return routes_by_transfers
    
    def _find_outgoing_trains(
        self,
        station_id: str,
        date: str,
        earliest_arrival: datetime = None
    ) -> List[tuple]:
        """Find trains departing from station"""
        
        trains = db.session.query(
            TrainRoute.train_id,
            TrainRoute.id.label('to_route_id'),
            TrainRoute.departure_time,
            TrainRoute.arrival_time
        ).filter(
            TrainRoute.station_id == station_id
        ).all()
        
        results = []
        
        for train_id, route_id, departure, arrival in trains:
            # Check if train is running
            schedule = TrainSchedule.query.filter_by(
                train_id=train_id,
                date=date
            ).first()
            
            if not schedule or schedule.status != 'Running':
                continue
            
            # Check transfer time if not first train
            if earliest_arrival:
                gap = (departure.hour * 60 + departure.minute) - (earliest_arrival.hour * 60 + earliest_arrival.minute)
                if gap < self.MIN_TRANSFER_TIME or gap > self.MAX_TRANSFER_TIME:
                    continue
            
            # Get next stops on this train
            next_routes = db.session.query(
                TrainRoute.station_id,
                TrainRoute.arrival_time
            ).filter(
                TrainRoute.train_id == train_id,
                TrainRoute.id > route_id
            ).order_by(TrainRoute.id).all()
            
            for next_station, arrival_time in next_routes:
                results.append((train_id, next_station, departure, arrival_time))
        
        return results
    
    def _construct_route(self, station_ids: List[str], train_ids: List[str]) -> dict:
        """Construct full route from station and train IDs"""
        
        if not train_ids:
            return None
        
        segments = []
        total_price = 0
        total_duration = 0
        
        for i, train_id in enumerate(train_ids):
            origin_id = station_ids[i]
            destination_id = station_ids[i + 1]
            
            # Get fare
            fare = Fare.query.filter_by(
                train_id=train_id,
                origin_station_id=origin_id,
                destination_station_id=destination_id
            ).first()
            
            if not fare:
                return None  # Invalid route
            
            segments.append({
                'train_id': train_id,
                'origin_id': origin_id,
                'destination_id': destination_id,
                'fare': fare.total_fare
            })
            
            total_price += fare.total_fare
        
        return {
            'segments': segments,
            'total_price': total_price,
            'number_of_transfers': len(train_ids) - 1
        }
    
    def pareto_optimize(self, routes: List[dict]) -> List[dict]:
        """Filter routes to Pareto frontier"""
        
        pareto_routes = []
        
        for route in routes:
            dominated = False
            
            for other in routes:
                if route == other:
                    continue
                
                # Check if other dominates route
                if (other['total_price'] <= route['total_price'] and
                    other['number_of_transfers'] <= route['number_of_transfers'] and
                    (other['total_price'] < route['total_price'] or
                     other['number_of_transfers'] < route['number_of_transfers'])):
                    dominated = True
                    break
            
            if not dominated:
                pareto_routes.append(route)
        
        return pareto_routes
```

---

## Part 7: Testing & Validation

### 7.1 Unit Tests

**Create Tests (`backend/tests/test_route_service.py`):**

```python
import pytest
from app import create_app, db
from app.models import Station, City, Train, Operator

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_route_search(client, app):
    """Test route search functionality"""
    
    with app.app_context():
        # Create test data
        delhi = City(name='Delhi', state='Delhi')
        mumbai = City(name='Mumbai', state='Maharashtra')
        db.session.add_all([delhi, mumbai])
        db.session.commit()
        
        ndls = Station(code='NDLS', name='New Delhi', city_id=delhi.id)
        mmct = Station(code='MMCT', name='Mumbai Central', city_id=mumbai.id)
        db.session.add_all([ndls, mmct])
        db.session.commit()
        
        # Test search
        response = client.post('/api/v2/routes/search', json={
            'origin': 'NDLS',
            'destination': 'MMCT',
            'date': '2026-02-01',
            'max_transfers': 3
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
```

---

## Part 8: Deployment & Production Setup

### 8.1 Docker Configuration

**Create Dockerfile for Backend:**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y postgresql-client

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "run.py"]
```

**Create docker-compose.yml:**

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: route_user
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: route_optimization_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://route_user:secure_password@db:5432/route_optimization_db
      REDIS_URL: redis://redis:6379/0
    ports:
      - "5000:5000"
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

---

## Part 9: Final Checklist

### Frontend
- [ ] Home page with hero section
- [ ] Route search interface
- [ ] Results page with filtering
- [ ] Route details modal
- [ ] User profile/account management
- [ ] Saved routes functionality
- [ ] AI agent chat interface
- [ ] Admin dashboard
- [ ] Mobile responsive design
- [ ] Error handling & loading states

### Backend
- [ ] User authentication (JWT)
- [ ] Route search API
- [ ] Route details API
- [ ] Agent chat API
- [ ] User management API
- [ ] Admin data management API
- [ ] Input validation & sanitization
- [ ] Error handling
- [ ] Logging & monitoring
- [ ] Rate limiting

### Database
- [ ] All 15+ tables created
- [ ] Indexes created for performance
- [ ] Foreign key constraints
- [ ] Sample data loaded
- [ ] Backup procedures

### AI Agent
- [ ] Intent classification
- [ ] Entity extraction
- [ ] Response generation
- [ ] Preference learning
- [ ] Chat history tracking

### DevOps & Deployment
- [ ] Docker configuration
- [ ] Environment variable setup
- [ ] Database migrations
- [ ] CI/CD pipeline
- [ ] Monitoring & alerting
- [ ] Backup & recovery

---

## Part 10: Quick Start Commands

```bash
# Setup Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py

# Setup Frontend
cd frontend
npm install
npm run dev

# Start with Docker
docker-compose up -d

# Run Tests
pytest backend/tests/

# Database Migrations
alembic upgrade head
```

---

## Success Criteria

✅ Complete, functional website
✅ All API endpoints working
✅ Route search functioning with multi-transfer support
✅ AI agent responding intelligently to user queries
✅ Data management system for dataset uploads
✅ User authentication & profile management
✅ Performance metrics met (< 2 second search response)
✅ Mobile responsive design
✅ Production-ready deployment setup
✅ Comprehensive error handling
✅ Security measures implemented

---

This prompt provides a complete roadmap for building your startup's website. Follow it systematically and you'll have a fully functional intelligent route optimization platform ready for production.
