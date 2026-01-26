"""
RAPPID Structured Data Generator

Transforms raw JSON responses into structured, queryable format.
Creates both structured JSON and CSV exports for different use cases.

Author: Route Master
Date: 2026-01-25
"""

import json
import csv
import gzip
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import os

try:
    from logger import LoggerFactory
except ImportError:
    import logging as LoggerFactory

class RappidStructuredGenerator:
    """
    Transform raw RAPPID API responses into structured format
    
    Input:  data/raw_rappid/TRAIN_NO.json (raw API response)
    Output: data/rappid_structured/TRAIN_NO.json (structured)
           dataset/trains_structured.csv (combined export)
    """
    
    def __init__(self):
        self.raw_path = Path("data/raw_rappid")
        self.structured_path = Path("data/rappid_structured")
        self.output_csv = Path("dataset/trains_structured.csv")
        self.logger = LoggerFactory.get_logger("rappid_structured") if hasattr(LoggerFactory, 'get_logger') else self._setup_logger()
        
        # Create directories if needed
        self.structured_path.mkdir(parents=True, exist_ok=True)
        self.output_csv.parent.mkdir(parents=True, exist_ok=True)
    
    def _setup_logger(self):
        """Simple logger setup if LoggerFactory not available"""
        logger = logging.getLogger("rappid_structured")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def transform_train(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw train data to structured format
        
        Args:
            raw_data: Raw JSON from RAPPID API
            
        Returns:
            Structured train data
        """
        if not raw_data:
            return None
        
        structured = {
            "train_no": str(raw_data.get("train_no", "")).strip(),
            "train_name": str(raw_data.get("train_name", "")).strip(),
            "train_type": raw_data.get("train_type", "").upper(),
            "classes": raw_data.get("classes", []),
            "frequency": raw_data.get("frequency", ""),
            "routes": self._extract_stations(raw_data.get("stations", [])),
            "meta": {
                "total_stations": len(raw_data.get("stations", [])),
                "distance_km": raw_data.get("total_distance", 0),
                "duration_hours": raw_data.get("duration_hours", 0),
                "source": raw_data.get("source_code", ""),
                "destination": raw_data.get("destination_code", ""),
                "transformed_at": datetime.now().isoformat()
            }
        }
        
        return structured
    
    def _extract_stations(self, stations: List[Dict]) -> List[Dict]:
        """
        Extract station information from raw stations list
        
        Args:
            stations: Raw stations list
            
        Returns:
            Structured station list with timing info
        """
        routes = []
        
        for idx, station in enumerate(stations):
            route_point = {
                "sequence": idx + 1,
                "station_code": str(station.get("code", "")).strip(),
                "station_name": str(station.get("name", "")).strip(),
                "state": station.get("state", ""),
                "zone": station.get("zone", ""),
                "distance_km": self._safe_int(station.get("distance")),
                "arrival_time": self._format_time(station.get("arrival")),
                "departure_time": self._format_time(station.get("departure")),
                "halt_minutes": self._safe_int(station.get("halt")),
                "platform": str(station.get("platform", "")).strip(),
                "is_source": idx == 0,
                "is_destination": idx == len(stations) - 1
            }
            routes.append(route_point)
        
        return routes
    
    def _format_time(self, time_str: Any) -> Optional[str]:
        """
        Ensure time is in HH:MM format
        
        Args:
            time_str: Time value from raw data
            
        Returns:
            Formatted time string or None
        """
        if not time_str:
            return None
        
        time_str = str(time_str).strip()
        if len(time_str) == 5 and ':' in time_str:  # HH:MM format
            return time_str
        
        # Try to parse and reformat
        try:
            if time_str.isdigit() and len(time_str) == 4:  # HHMM format
                return f"{time_str[:2]}:{time_str[2:]}"
        except:
            pass
        
        return time_str if time_str else None
    
    def _safe_int(self, value: Any) -> int:
        """Safely convert value to int"""
        try:
            return int(value) if value else 0
        except:
            return 0
    
    def process_single_train(self, train_no: str) -> bool:
        """
        Process a single train from raw to structured
        
        Args:
            train_no: Train number (e.g., "16320")
            
        Returns:
            True if successful, False otherwise
        """
        raw_file = self.raw_path / f"{train_no}.json"
        
        if not raw_file.exists():
            self.logger.warning(f"Raw file not found: {raw_file}")
            return False
        
        try:
            # Read raw JSON
            with open(raw_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            # Transform
            structured = self.transform_train(raw_data)
            
            if not structured:
                self.logger.warning(f"Failed to transform train {train_no}")
                return False
            
            # Save structured JSON
            output_file = self.structured_path / f"{train_no}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(structured, f, indent=2, ensure_ascii=False)
            
            # Also save compressed version
            output_gz = self.structured_path / f"{train_no}.json.gz"
            with gzip.open(output_gz, 'wt', encoding='utf-8') as f:
                json.dump(structured, f, ensure_ascii=False)
            
            self.logger.info(f"✓ Processed train {train_no}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing {train_no}: {e}")
            return False
    
    def process_all_trains(self) -> Dict[str, int]:
        """
        Process all raw train files
        
        Returns:
            Statistics: {successful, failed, total}
        """
        stats = {"successful": 0, "failed": 0, "total": 0}
        
        if not self.raw_path.exists():
            self.logger.error(f"Raw data path not found: {self.raw_path}")
            return stats
        
        json_files = list(self.raw_path.glob("*.json"))
        self.logger.info(f"Found {len(json_files)} raw train files")
        
        for raw_file in json_files:
            train_no = raw_file.stem  # Filename without extension
            stats["total"] += 1
            
            if self.process_single_train(train_no):
                stats["successful"] += 1
            else:
                stats["failed"] += 1
        
        self.logger.info(f"Processing complete: {stats['successful']}/{stats['total']} successful")
        return stats
    
    def export_to_csv(self, output_file: Optional[Path] = None) -> int:
        """
        Export all structured trains to CSV
        
        Args:
            output_file: Output CSV path (default: dataset/trains_structured.csv)
            
        Returns:
            Number of rows written
        """
        output_file = output_file or self.output_csv
        
        if not self.structured_path.exists() or not list(self.structured_path.glob("*.json")):
            self.logger.warning("No structured data found")
            return 0
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'train_no', 'train_name', 'train_type', 'classes',
                    'sequence', 'station_code', 'station_name', 'state', 'zone',
                    'distance_km', 'arrival_time', 'departure_time',
                    'halt_minutes', 'platform', 'is_source', 'is_destination'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                row_count = 0
                for structured_file in sorted(self.structured_path.glob("*.json")):
                    try:
                        with open(structured_file, 'r', encoding='utf-8') as f:
                            structured = json.load(f)
                        
                        train_no = structured.get("train_no")
                        train_name = structured.get("train_name")
                        train_type = structured.get("train_type")
                        classes = ", ".join(structured.get("classes", []))
                        
                        for route in structured.get("routes", []):
                            row = {
                                'train_no': train_no,
                                'train_name': train_name,
                                'train_type': train_type,
                                'classes': classes,
                                'sequence': route.get('sequence'),
                                'station_code': route.get('station_code'),
                                'station_name': route.get('station_name'),
                                'state': route.get('state'),
                                'zone': route.get('zone'),
                                'distance_km': route.get('distance_km'),
                                'arrival_time': route.get('arrival_time'),
                                'departure_time': route.get('departure_time'),
                                'halt_minutes': route.get('halt_minutes'),
                                'platform': route.get('platform'),
                                'is_source': route.get('is_source'),
                                'is_destination': route.get('is_destination')
                            }
                            writer.writerow(row)
                            row_count += 1
                    
                    except Exception as e:
                        self.logger.warning(f"Error exporting {structured_file.name}: {e}")
                        continue
            
            self.logger.info(f"✓ Exported {row_count} route entries to {output_file}")
            return row_count
        
        except Exception as e:
            self.logger.error(f"CSV export failed: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics on structured data
        
        Returns:
            Statistics dictionary
        """
        if not self.structured_path.exists():
            return {"total_trains": 0, "total_files": 0}
        
        json_files = list(self.structured_path.glob("*.json"))
        gz_files = list(self.structured_path.glob("*.json.gz"))
        
        total_trains = len(set([f.stem for f in json_files]))
        total_size_mb = sum(f.stat().st_size for f in json_files + gz_files) / (1024 * 1024)
        
        stats = {
            "total_trains": total_trains,
            "json_files": len(json_files),
            "compressed_files": len(gz_files),
            "total_size_mb": round(total_size_mb, 2),
            "csv_exists": self.output_csv.exists(),
            "csv_size_mb": self.output_csv.stat().st_size / (1024 * 1024) if self.output_csv.exists() else 0
        }
        
        return stats
    
    def validate_structured_data(self) -> Dict[str, Any]:
        """
        Validate structured data quality
        
        Returns:
            Validation report
        """
        report = {
            "valid_trains": 0,
            "missing_fields": 0,
            "errors": []
        }
        
        for structured_file in self.structured_path.glob("*.json"):
            try:
                with open(structured_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check required fields
                required = ['train_no', 'train_name', 'routes']
                if all(field in data for field in required):
                    report["valid_trains"] += 1
                else:
                    report["missing_fields"] += 1
                    report["errors"].append(f"{structured_file.name}: missing fields")
            
            except Exception as e:
                report["errors"].append(f"{structured_file.name}: {str(e)}")
        
        return report


if __name__ == "__main__":
    # Initialize generator
    generator = RappidStructuredGenerator()
    
    # Process all trains
    print("Processing all raw trains to structured format...")
    stats = generator.process_all_trains()
    print(f"Result: {stats['successful']} successful, {stats['failed']} failed")
    
    # Export to CSV
    print("\nExporting to CSV...")
    csv_rows = generator.export_to_csv()
    print(f"Exported {csv_rows} route entries")
    
    # Get statistics
    print("\nStatistics:")
    gen_stats = generator.get_statistics()
    for key, value in gen_stats.items():
        print(f"  {key}: {value}")
    
    # Validate
    print("\nValidating structured data...")
    validation = generator.validate_structured_data()
    print(f"Valid trains: {validation['valid_trains']}")
    if validation['errors']:
        print("Errors found:")
        for error in validation['errors'][:5]:
            print(f"  - {error}")
