// Popular Indian Railway Stations
export interface Station {
  code: string;
  name: string;
  city: string;
  state: string;
}

export const stations: Station[] = [
  { code: "PGT", name: "Palakkad Town", city: "Palakkad", state: "Kerala" },
  { code: "KOTA", name: "Kota Junction", city: "Kota", state: "Rajasthan" },
  { code: "BRC", name: "Vadodara Junction", city: "Vadodara", state: "Gujarat" },
  { code: "NDLS", name: "New Delhi", city: "Delhi", state: "Delhi" },
  { code: "CSTM", name: "Mumbai CST", city: "Mumbai", state: "Maharashtra" },
  { code: "BCT", name: "Mumbai Central", city: "Mumbai", state: "Maharashtra" },
  { code: "HWH", name: "Howrah Junction", city: "Kolkata", state: "West Bengal" },
  { code: "MAS", name: "Chennai Central", city: "Chennai", state: "Tamil Nadu" },
  { code: "SBC", name: "Bangalore City", city: "Bangalore", state: "Karnataka" },
  { code: "JP", name: "Jaipur Junction", city: "Jaipur", state: "Rajasthan" },
  { code: "ADI", name: "Ahmedabad Junction", city: "Ahmedabad", state: "Gujarat" },
  { code: "LKO", name: "Lucknow Junction", city: "Lucknow", state: "Uttar Pradesh" },
  { code: "PNBE", name: "Patna Junction", city: "Patna", state: "Bihar" },
  { code: "BZA", name: "Vijayawada Junction", city: "Vijayawada", state: "Andhra Pradesh" },
  { code: "SC", name: "Secunderabad Junction", city: "Hyderabad", state: "Telangana" },
  { code: "CBE", name: "Coimbatore Junction", city: "Coimbatore", state: "Tamil Nadu" },
  { code: "ERS", name: "Ernakulam Junction", city: "Kochi", state: "Kerala" },
  { code: "TVC", name: "Thiruvananthapuram Central", city: "Thiruvananthapuram", state: "Kerala" },
  { code: "QLN", name: "Kollam Junction", city: "Kollam", state: "Kerala" },
  { code: "AGC", name: "Agra Cantt", city: "Agra", state: "Uttar Pradesh" },
  { code: "CNB", name: "Kanpur Central", city: "Kanpur", state: "Uttar Pradesh" },
  { code: "BSB", name: "Varanasi Junction", city: "Varanasi", state: "Uttar Pradesh" },
  { code: "PUNE", name: "Pune Junction", city: "Pune", state: "Maharashtra" },
  { code: "NGP", name: "Nagpur Junction", city: "Nagpur", state: "Maharashtra" },
  { code: "RTM", name: "Ratlam Junction", city: "Ratlam", state: "Madhya Pradesh" },
  { code: "UJN", name: "Ujjain Junction", city: "Ujjain", state: "Madhya Pradesh" },
  { code: "ANND", name: "Anand Junction", city: "Anand", state: "Gujarat" },
  { code: "ED", name: "Erode Junction", city: "Erode", state: "Tamil Nadu" },
  { code: "MDU", name: "Madurai Junction", city: "Madurai", state: "Tamil Nadu" },
  { code: "TPJ", name: "Tiruchirappalli Junction", city: "Tiruchirappalli", state: "Tamil Nadu" },
];

export const getStationByCode = (code: string): Station | undefined => {
  return stations.find(s => s.code === code);
};

export const searchStations = (query: string): Station[] => {
  const lowerQuery = query.toLowerCase();
  return stations.filter(
    s => 
      s.code.toLowerCase().includes(lowerQuery) ||
      s.name.toLowerCase().includes(lowerQuery) ||
      s.city.toLowerCase().includes(lowerQuery)
  ).slice(0, 10);
};
