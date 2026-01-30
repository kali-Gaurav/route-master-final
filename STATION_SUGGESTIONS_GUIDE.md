# Station Suggestion Feature - How It Works

## Overview
When you type in the **Origin** or **Destination** input fields, the system automatically shows relevant railway station suggestions that match your input.

---

## How Station Suggestions Are Triggered

### 1. **User Types in Input Field**
When you start typing in either the Origin or Destination field, the system listens for input changes:

```typescript
const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  const val = e.target.value;
  setQuery(val);
  
  // Only show suggestions if user has typed 2 or more characters
  if (val.length >= 2) {
    const found = searchStations(val);  // Search for matching stations
    setResults(found);                   // Store matching results
    setIsOpen(true);                     // Open dropdown to display results
  } else {
    setResults([]);
    setIsOpen(false);
  }
};
```

**Key Point:** Suggestions appear only after you type **2 or more characters** to avoid showing too many results.

---

## 2. **Search Algorithm**

The `searchStations()` function in [src/data/stations.ts](src/data/stations.ts) searches through all available stations and filters based on three criteria:

```typescript
const filtered = stations.filter(
  s => 
    s.code.toLowerCase().includes(lowerQuery) ||      // Match station code (e.g., "NDLS")
    s.name.toLowerCase().includes(lowerQuery) ||      // Match station name (e.g., "New Delhi")
    s.city.toLowerCase().includes(lowerQuery)         // Match city name (e.g., "Delhi")
);
```

**You can search by:**
- **Station Code:** Type "NDLS" to find New Delhi Junction
- **Station Name:** Type "New Delhi" to find the station
- **City Name:** Type "Delhi" to find all Delhi stations

---

## 3. **Intelligent Sorting**

Results are sorted with major railway junctions prioritized first:

```typescript
// Major junctions are identified by keywords: "JN", "JUNCTION", "TERMINUS", "CENTRAL"
const aIsMajor = aName.includes("JN") || aName.includes("JUNCTION") || 
                 aName.includes("TERMINUS") || aName.includes("CENTRAL");

// Major stations appear first, then sorted alphabetically
// Results are limited to top 50 matches
```

**Sorting Order:**
1. Major junctions (Junction, Central, Terminus stations)
2. Regular stations sorted alphabetically
3. Maximum 50 results shown (with scrolling)

---

## 4. **Dropdown Display**

Once results are available, a dropdown appears below the input field showing:

```
┌─────────────────────────────────┐
│ [CODE] Station Name             │
│        City, State              │
├─────────────────────────────────┤
│ [NDLS] New Delhi Junction       │
│        Delhi, Delhi             │
├─────────────────────────────────┤
│ [NZM]  Hazrat Nizamuddin       │
│        Delhi, Delhi             │
└─────────────────────────────────┘
```

**Features:**
- Station code displayed in a colored badge
- Station name in bold
- City and state information below
- Smooth fade-in animation
- Scrollable if more than 7-8 results
- Auto-closes when clicking outside or selecting a station

---

## 5. **Selection Process**

When you click on a suggestion:

```typescript
const handleSelect = (station: Station) => {
  setQuery(`${station.name} (${station.code})`);  // Display format: "New Delhi (NDLS)"
  onChange(station);                               // Pass selected station to parent
  setIsOpen(false);                                // Close dropdown
};
```

**What happens:**
- Input field displays: `Station Name (CODE)` format
- Selected station data is sent to the route search function
- Dropdown automatically closes

---

## 6. **Data Source**

Station data comes from [src/data/station_search_data.json](src/data/station_search_data.json), which contains:

```json
{
  "stations": [
    {
      "code": "NDLS",
      "name": "New Delhi Junction",
      "city": "Delhi",
      "state": "Delhi"
    },
    ...
  ]
}
```

---

## Component Architecture

### Component: [StationSearch.tsx](src/components/StationSearch.tsx)

**Props:**
- `label` - Display label (e.g., "Origin Station")
- `placeholder` - Input placeholder text
- `value` - Currently selected station
- `onChange` - Callback when station is selected
- `icon` - Visual indicator ("origin" = green dot, "destination" = map pin)

**State Management:**
- `query` - Current input text
- `isOpen` - Dropdown visibility
- `results` - Filtered station matches
- `inputRef` - Reference to input field
- `containerRef` - Reference to container (for detecting outside clicks)

---

## User Experience Flow

```
1. User types "del" in Origin field
   ↓
2. System checks if length >= 2 ✓
   ↓
3. searchStations("del") filters all stations
   ↓
4. Results: Delhi stations, Delhiville, etc.
   ↓
5. Results sorted (majors first, alphabetically)
   ↓
6. Dropdown opens showing top 50 matches
   ↓
7. User clicks on "New Delhi Junction (NDLS)"
   ↓
8. Input displays: "New Delhi Junction (NDLS)"
   ↓
9. Dropdown closes, station is selected
```

---

## Features Implemented

✅ **Real-time Filtering** - Results update as you type  
✅ **Multi-field Search** - Search by code, name, or city  
✅ **Smart Sorting** - Major junctions prioritized  
✅ **Scrollable Results** - Up to 50 stations with overflow scroll  
✅ **Keyboard Support** - Focus and navigate with keyboard  
✅ **Click Outside Detection** - Dropdown closes on outside clicks  
✅ **Visual Indicators** - Different icons for origin/destination  
✅ **Mobile Responsive** - Works on all screen sizes  

---

## Example Searches

| Query | Results |
|-------|---------|
| "del" | New Delhi, Delhi Cantt, Delhiville |
| "NDLS" | New Delhi Junction |
| "bombay" | Mumbai Central, Mumbai Terminus, etc. |
| "KOL" | Kolkata Central, Howrah Junction |
| "HWH" | Howrah Junction |
| "bangalore" | Bangalore City, Yeshwantpur, Krantiveera |

---

## Performance Optimization

- **Minimum 2 characters** before search starts (reduces unnecessary filtering)
- **Maximum 50 results** returned (prevents large dropdown renders)
- **In-memory filtering** (no API calls for station search)
- **Custom scrollbar** styling for better UX
- **Debounced state updates** through React's built-in optimization

---

## Technical Implementation Details

### Search Algorithm Complexity
- **Time:** O(n) - single pass through all stations
- **Space:** O(m) - where m is number of matching results (max 50)

### Rendering Optimization
- Uses React hooks for state management
- Conditional rendering of dropdown (only renders when open)
- Maps results efficiently with keys

### Accessibility Features
- Label associated with input
- Proper focus management
- Keyboard navigation support
- ARIA-friendly structure
