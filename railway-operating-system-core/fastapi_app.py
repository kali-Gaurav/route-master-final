from fastapi import FastAPI, Query
from typing import Optional
from datetime import datetime
from route_finder import RouteFinder

app = FastAPI(title="Railway Route Finder API")
finder = RouteFinder()

@app.get("/routes")
def get_routes(
    source: str,
    destination: str,
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    max_transfers: int = 3,
    max_results: int = 50,
    verbose: bool = False,
    sort_by: Optional[str] = Query(None, description="Sort results. Supported: 'duration'")
):
    """Return search results as JSON. Example: /routes?source=NDLS&destination=HWH&start_date=2026-01-26"""
    # parse date
    sd = None
    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d").date()
        except Exception:
            sd = None

    results = finder.find_all_routes(source, destination, start_date=sd, max_transfers=max_transfers, max_results=max_results, verbose=verbose, sort_by=sort_by)
    # ensure JSON-serializable (dates converted already in code)
    return results

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
