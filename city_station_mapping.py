"""
City to Railway Station Mapping for India
Maps city names to their major railway stations with codes
"""

CITY_STATION_MAP = {
    # Major Metro Cities
    "mumbai": {
        "stations": [
            {"code": "CSTM", "name": "Chhatrapati Shivaji Maharaj Terminus", "type": "major"},
            {"code": "MMCT", "name": "Mumbai Central", "type": "major"},
            {"code": "LTT", "name": "Lokmanya Tilak Terminus", "type": "major"},
            {"code": "BCT", "name": "Mumbai Bandra Terminus", "type": "major"},
            {"code": "BDTS", "name": "Bandra Terminus", "type": "junction"},
            {"code": "DR", "name": "Dadar", "type": "junction"},
        ],
        "airport": {"code": "BOM", "name": "Chhatrapati Shivaji Maharaj International Airport"}
    },
    
    "delhi": {
        "stations": [
            {"code": "NDLS", "name": "New Delhi Railway Station", "type": "major"},
            {"code": "DLI", "name": "Old Delhi Railway Station", "type": "major"},
            {"code": "NZM", "name": "Hazrat Nizamuddin", "type": "major"},
            {"code": "DSA", "name": "Delhi Sarai Rohilla", "type": "junction"},
            {"code": "ANVT", "name": "Anand Vihar Terminal", "type": "major"},
        ],
        "airport": {"code": "DEL", "name": "Indira Gandhi International Airport"}
    },
    
    "bangalore": {
        "stations": [
            {"code": "SBC", "name": "Krantivira Sangolli Rayanna (Bangalore City)", "type": "major"},
            {"code": "YPR", "name": "Yesvantpur Junction", "type": "major"},
            {"code": "BAND", "name": "Banaswadi", "type": "junction"},
            {"code": "KJM", "name": "Krishnarajapuram", "type": "junction"},
        ],
        "airport": {"code": "BLR", "name": "Kempegowda International Airport"}
    },
    
    "bengaluru": {  # Alias for Bangalore
        "stations": [
            {"code": "SBC", "name": "Krantivira Sangolli Rayanna (Bangalore City)", "type": "major"},
            {"code": "YPR", "name": "Yesvantpur Junction", "type": "major"},
        ],
        "airport": {"code": "BLR", "name": "Kempegowda International Airport"}
    },
    
    "kolkata": {
        "stations": [
            {"code": "HWH", "name": "Howrah Junction", "type": "major"},
            {"code": "KOAA", "name": "Kolkata (Chitpur)", "type": "major"},
            {"code": "SDAH", "name": "Sealdah", "type": "major"},
        ],
        "airport": {"code": "CCU", "name": "Netaji Subhas Chandra Bose International Airport"}
    },
    
    "chennai": {
        "stations": [
            {"code": "MAS", "name": "Chennai Central", "type": "major"},
            {"code": "MS", "name": "Chennai Egmore", "type": "major"},
            {"code": "TBM", "name": "Tambaram", "type": "junction"},
        ],
        "airport": {"code": "MAA", "name": "Chennai International Airport"}
    },
    
    "hyderabad": {
        "stations": [
            {"code": "HYB", "name": "Hyderabad Deccan (Nampally)", "type": "major"},
            {"code": "SC", "name": "Secunderabad Junction", "type": "major"},
            {"code": "KCG", "name": "Kacheguda", "type": "junction"},
        ],
        "airport": {"code": "HYD", "name": "Rajiv Gandhi International Airport"}
    },
    
    "pune": {
        "stations": [
            {"code": "PUNE", "name": "Pune Junction", "type": "major"},
            {"code": "CCH", "name": "Chinchvad", "type": "junction"},
        ],
        "airport": {"code": "PNQ", "name": "Pune Airport"}
    },
    
    "ahmedabad": {
        "stations": [
            {"code": "ADI", "name": "Ahmedabad Junction", "type": "major"},
            {"code": "SBIB", "name": "Sabarmati Junction", "type": "junction"},
        ],
        "airport": {"code": "AMD", "name": "Sardar Vallabhbhai Patel International Airport"}
    },
    
    "jaipur": {
        "stations": [
            {"code": "JP", "name": "Jaipur Junction", "type": "major"},
            {"code": "GADJ", "name": "Gandhinagar Jaipur", "type": "junction"},
        ],
        "airport": {"code": "JAI", "name": "Jaipur International Airport"}
    },
    
    "lucknow": {
        "stations": [
            {"code": "LKO", "name": "Lucknow Charbagh", "type": "major"},
            {"code": "LJN", "name": "Lucknow Junction", "type": "major"},
        ],
        "airport": {"code": "LKO", "name": "Chaudhary Charan Singh International Airport"}
    },
    
    "kanpur": {
        "stations": [
            {"code": "CNB", "name": "Kanpur Central", "type": "major"},
            {"code": "ANVT", "name": "Kanpur Anwarganj", "type": "junction"},
        ],
        "airport": {"code": "KNU", "name": "Kanpur Airport"}
    },
    
    "nagpur": {
        "stations": [
            {"code": "NGP", "name": "Nagpur Junction", "type": "major"},
        ],
        "airport": {"code": "NAG", "name": "Dr. Babasaheb Ambedkar International Airport"}
    },
    
    "indore": {
        "stations": [
            {"code": "INDB", "name": "Indore Junction", "type": "major"},
        ],
        "airport": {"code": "IDR", "name": "Devi Ahilyabai Holkar Airport"}
    },
    
    "bhopal": {
        "stations": [
            {"code": "BPL", "name": "Bhopal Junction", "type": "major"},
            {"code": "HBJ", "name": "Habibganj", "type": "major"},
        ],
        "airport": {"code": "BHO", "name": "Raja Bhoj Airport"}
    },
    
    "patna": {
        "stations": [
            {"code": "PNBE", "name": "Patna Junction", "type": "major"},
            {"code": "PNC", "name": "Patna Saheb", "type": "junction"},
        ],
        "airport": {"code": "PAT", "name": "Lok Nayak Jayaprakash Airport"}
    },
    
    "surat": {
        "stations": [
            {"code": "ST", "name": "Surat Railway Station", "type": "major"},
        ],
        "airport": {"code": "STV", "name": "Surat Airport"}
    },
    
    "vadodara": {
        "stations": [
            {"code": "BRC", "name": "Vadodara Junction", "type": "major"},
        ],
        "airport": {"code": "BDQ", "name": "Vadodara Airport"}
    },
    
    "agra": {
        "stations": [
            {"code": "AGC", "name": "Agra Cantt", "type": "major"},
            {"code": "AF", "name": "Agra Fort", "type": "junction"},
        ],
        "airport": {"code": "AGR", "name": "Agra Airport"}
    },
    
    "varanasi": {
        "stations": [
            {"code": "BSB", "name": "Varanasi Junction", "type": "major"},
            {"code": "BCY", "name": "Varanasi City", "type": "junction"},
        ],
        "airport": {"code": "VNS", "name": "Lal Bahadur Shastri International Airport"}
    },
    
    "kochi": {
        "stations": [
            {"code": "ERS", "name": "Ernakulam Junction", "type": "major"},
            {"code": "ERNM", "name": "Ernakulam Town", "type": "junction"},
        ],
        "airport": {"code": "COK", "name": "Cochin International Airport"}
    },
    
    "cochin": {  # Alias for Kochi
        "stations": [
            {"code": "ERS", "name": "Ernakulam Junction", "type": "major"},
        ],
        "airport": {"code": "COK", "name": "Cochin International Airport"}
    },
    
    "thiruvananthapuram": {
        "stations": [
            {"code": "TVC", "name": "Thiruvananthapuram Central", "type": "major"},
        ],
        "airport": {"code": "TRV", "name": "Trivandrum International Airport"}
    },
    
    "trivandrum": {  # Alias
        "stations": [
            {"code": "TVC", "name": "Thiruvananthapuram Central", "type": "major"},
        ],
        "airport": {"code": "TRV", "name": "Trivandrum International Airport"}
    },
    
    "coimbatore": {
        "stations": [
            {"code": "CBE", "name": "Coimbatore Junction", "type": "major"},
        ],
        "airport": {"code": "CJB", "name": "Coimbatore International Airport"}
    },
    
    "madurai": {
        "stations": [
            {"code": "MDU", "name": "Madurai Junction", "type": "major"},
        ],
        "airport": {"code": "IXM", "name": "Madurai Airport"}
    },
    
    "visakhapatnam": {
        "stations": [
            {"code": "VSKP", "name": "Visakhapatnam Junction", "type": "major"},
        ],
        "airport": {"code": "VTZ", "name": "Visakhapatnam Airport"}
    },
    
    "vijayawada": {
        "stations": [
            {"code": "BZA", "name": "Vijayawada Junction", "type": "major"},
        ],
        "airport": {"code": "VGA", "name": "Vijayawada Airport"}
    },
    
    "guwahati": {
        "stations": [
            {"code": "GHY", "name": "Guwahati Railway Station", "type": "major"},
        ],
        "airport": {"code": "GAU", "name": "Lokpriya Gopinath Bordoloi International Airport"}
    },
    
    "chandigarh": {
        "stations": [
            {"code": "CDG", "name": "Chandigarh Railway Station", "type": "major"},
        ],
        "airport": {"code": "IXC", "name": "Chandigarh International Airport"}
    },
    
    "amritsar": {
        "stations": [
            {"code": "ASR", "name": "Amritsar Junction", "type": "major"},
        ],
        "airport": {"code": "ATQ", "name": "Sri Guru Ram Dass Jee International Airport"}
    },
    
    "jalandhar": {
        "stations": [
            {"code": "JUC", "name": "Jalandhar City", "type": "major"},
        ],
        "airport": {"code": "JLR", "name": "Jalandhar Airport"}
    },
    
    "raipur": {
        "stations": [
            {"code": "R", "name": "Raipur Junction", "type": "major"},
        ],
        "airport": {"code": "RPR", "name": "Swami Vivekananda Airport"}
    },
    
    "ranchi": {
        "stations": [
            {"code": "RNC", "name": "Ranchi Junction", "type": "major"},
        ],
        "airport": {"code": "IXR", "name": "Birsa Munda Airport"}
    },
    
    "goa": {
        "stations": [
            {"code": "MAO", "name": "Madgaon Junction", "type": "major"},
            {"code": "KRMI", "name": "Karmali", "type": "junction"},
        ],
        "airport": {"code": "GOI", "name": "Goa International Airport"}
    },
    
    "jammu": {
        "stations": [
            {"code": "JAT", "name": "Jammu Tawi", "type": "major"},
        ],
        "airport": {"code": "IXJ", "name": "Jammu Airport"}
    },
    
    "dehradun": {
        "stations": [
            {"code": "DDN", "name": "Dehradun Railway Station", "type": "major"},
        ],
        "airport": {"code": "DED", "name": "Jolly Grant Airport"}
    },
}


def get_stations_for_city(city_name: str) -> dict:
    """
    Get railway stations and airport for a city
    
    Args:
        city_name: Name of the city (case-insensitive)
        
    Returns:
        Dictionary with stations and airport info, or None if city not found
    """
    city_name = city_name.lower().strip()
    return CITY_STATION_MAP.get(city_name)


def suggest_station(city_name: str) -> dict:
    """
    Suggest primary railway station for a city
    
    Returns:
        Dictionary with suggested station code and all available options
    """
    city_data = get_stations_for_city(city_name)
    
    if not city_data:
        return {
            "status": "not_found",
            "message": f"City '{city_name}' not found in database. Please use station code directly.",
            "suggestion": None
        }
    
    stations = city_data["stations"]
    primary_station = stations[0]  # First station is primary
    
    return {
        "status": "success",
        "city": city_name.title(),
        "suggested_code": primary_station["code"],
        "suggested_name": primary_station["name"],
        "all_stations": stations,
        "airport": city_data.get("airport"),
        "message": f"For {city_name.title()}, I suggest {primary_station['code']} ({primary_station['name']})"
    }


def get_all_city_names() -> list:
    """Get list of all supported city names"""
    return list(CITY_STATION_MAP.keys())
