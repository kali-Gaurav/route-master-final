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
  const lowerQuery = query.toLowerCase();
  
  const filtered = stations.filter(
    s => 
      s.code.toLowerCase().includes(lowerQuery) ||
      s.name.toLowerCase().includes(lowerQuery) ||
      s.city.toLowerCase().includes(lowerQuery)
  );

  // Sort: Major junctions first, then by name
  return filtered.sort((a, b) => {
    const aName = a.name.toUpperCase();
    const bName = b.name.toUpperCase();
    
    const aIsMajor = aName.includes("JN") || aName.includes("JUNCTION") || aName.includes("TERMINUS") || aName.includes("CENTRAL");
    const bIsMajor = bName.includes("JN") || bName.includes("JUNCTION") || bName.includes("TERMINUS") || bName.includes("CENTRAL");

    if (aIsMajor && !bIsMajor) return -1;
    if (!aIsMajor && bIsMajor) return 1;
    
    // If both are major or both are not, sort by name length (shorter usually more relevant) then alphabetically
    if (aName.length !== bName.length) return aName.length - bName.length;
    return aName.localeCompare(bName);
  }).slice(0, 50); // Increased limit to allow scrolling
};
