import stationData from "./station_search_data.json";

// Popular Indian Railway Stations
export interface Station {
  code: string;
  name: string;
  city: string;
  state: string;
}

export const stations: Station[] = stationData.stations;

export const getStationByCode = (code: string): Station | undefined => {
  return stations.find(s => s.code === code);
};

export const searchStations = (query: string): Station[] => {
  const upperQuery = query.toUpperCase();
  
  // Try exact city match first
  let filtered = stations.filter(
    s => s.city.toUpperCase() === upperQuery
  );
  
  // If no exact city match, search by station code (exact or prefix) then name
  if (filtered.length === 0) {
    filtered = stations.filter(
      s => 
        s.code.toUpperCase().startsWith(upperQuery) ||
        s.code.toUpperCase() === upperQuery ||
        s.name.toUpperCase().includes(upperQuery)
    );
  }

  // Sort with smart prioritization
  return filtered.sort((a, b) => {
    const aCode = a.code.toUpperCase();
    const bCode = b.code.toUpperCase();
    const aName = a.name.toUpperCase();
    const bName = b.name.toUpperCase();
    
    // Priority 1: Exact code match
    const aCodeExact = aCode === upperQuery ? 0 : 1;
    const bCodeExact = bCode === upperQuery ? 0 : 1;
    if (aCodeExact !== bCodeExact) return aCodeExact - bCodeExact;
    
    // Priority 2: Code starts with query
    const aCodeStarts = aCode.startsWith(upperQuery) ? 0 : 1;
    const bCodeStarts = bCode.startsWith(upperQuery) ? 0 : 1;
    if (aCodeStarts !== bCodeStarts) return aCodeStarts - bCodeStarts;
    
    // Priority 3: Major junctions first
    const aIsMajor = aName.includes("JN") || aName.includes("JUNCTION") || aName.includes("TERMINUS") || aName.includes("CENTRAL");
    const bIsMajor = bName.includes("JN") || bName.includes("JUNCTION") || bName.includes("TERMINUS") || bName.includes("CENTRAL");
    if (aIsMajor && !bIsMajor) return -1;
    if (!aIsMajor && bIsMajor) return 1;
    
    // Priority 4: Shorter names (more relevant)
    if (aName.length !== bName.length) return aName.length - bName.length;
    
    // Priority 5: Alphabetical
    return aName.localeCompare(bName);
  }).slice(0, 50);
};
