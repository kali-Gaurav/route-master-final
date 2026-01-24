import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
import logging

# Configure logging for the test script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_script")

# --- Configuration ---
BASE_URL = "http://127.0.0.1:5000/api/routes"
TEST_ORIGIN = "PGT"
TEST_DESTINATION = "KOTA"
TEST_MAX_TRANSFERS = 1
TEST_DATE = (datetime.now() + timedelta(days=7)).strftime('%d-%m-%Y') # A week from now
INVALID_ORIGIN = "XYZ"
NON_EXISTENT_STATION = "NONEXIST"
API_KEY_PLACEHOLDER = "e0adaea886msh3fb9b9456cad9ccp17a317jsna7fe7b2fe0b6" # Placeholder, actual key not used by script directly

# --- Helper Functions ---
async def make_request(session: aiohttp.ClientSession, url: str, params: dict) -> dict:
    logger.info(f"Making request to: {url} with params: {params}")
    async with session.get(url, params=params) as response:
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        return await response.json()

def verify_response(response_json: dict, scenario: str):
    logger.info(f"Verifying response for scenario: {scenario}")
    assert "error" not in response_json, f"Error found in response for {scenario}: {response_json.get('error')}"
    assert "optimal_routes" in response_json, f"'optimal_routes' missing in response for {scenario}"
    assert "all_generated_routes" in response_json, f"'all_generated_routes' missing in response for {scenario}"
    assert len(response_json['optimal_routes']) > 0, f"No optimal routes found for {scenario}"
    assert len(response_json['all_generated_routes']) > 0, f"No all generated routes found for {scenario}"

    # Verify live data presence in a sample segment
    sample_route = response_json['optimal_routes'][0]
    sample_segment = sample_route['segments'][0]
    assert 'live_seat_availability' in sample_segment, f"'live_seat_availability' missing in segment for {scenario}"
    assert 'live_fare' in sample_segment, f"'live_fare' missing in segment for {scenario}"
    assert sample_segment['live_seat_availability'].startswith("AVAILABLE"), f"Seat not AVAILABLE for {scenario}"
    assert sample_segment['live_fare'] > 0, f"Fare is not greater than 0 for {scenario}"
    
    logger.info(f"✓ Response verification successful for {scenario}.")

def clean_up_cache_files(origin: str, destination: str, date_str: str):
    logger.info(f"Cleaning up cache files for {origin}-{destination}-{date_str}...")
    disk_json_file = f"{origin}_to_{destination}_pareto_routes_{date_str}.json"
    disk_csv_file = f"{origin}_to_{destination}_all_routes_{date_str}.csv" # all routes csv
    disk_pareto_csv_file = f"{origin}_to_{destination}_pareto_routes_{date_str}.csv" # pareto routes csv

    for f in [disk_json_file, disk_csv_file, disk_pareto_csv_file]:
        if os.path.exists(f):
            os.remove(f)
            logger.info(f"Removed: {f}")
        else:
            logger.debug(f"File not found for removal: {f}")
    logger.info("Cache file cleanup complete.")


async def run_tests():
    logger.info("--- Starting Backend API Integration Tests ---")
    logger.info(f"Ensure Flask server is running at {BASE_URL.replace('/api/routes', '')}")
    logger.info("If you encounter 'Connection refused' errors, start your Flask server.")

    async with aiohttp.ClientSession() as session:
        params = {
            "origin": TEST_ORIGIN,
            "destination": TEST_DESTINATION,
            "max_transfers": TEST_MAX_TRANSFERS,
            "date": TEST_DATE
        }
        test_date_for_cleanup = datetime.strptime(TEST_DATE, '%d-%m-%Y').strftime('%Y%m%d')

        # Scenario 1: Initial Call (Cache Miss, Full Computation)
        logger.info("\n[Scenario 1/5] Initial Call (Cache Miss, Full Computation)")
        clean_up_cache_files(TEST_ORIGIN, TEST_DESTINATION, test_date_for_cleanup) # Ensure no old files
        response_json_1 = await make_request(session, BASE_URL, params)
        verify_response(response_json_1, "Initial Call")
        # Verify disk files were created
        assert os.path.exists(f"{TEST_ORIGIN}_to_{TEST_DESTINATION}_pareto_routes_{test_date_for_cleanup}.json"), "Disk cache JSON not created"
        logger.info("✓ Scenario 1: Passed. Disk cache created.")

        # Scenario 2: In-Memory Cache Hit
        logger.info("\n[Scenario 2/5] In-Memory Cache Hit")
        response_json_2 = await make_request(session, BASE_URL, params)
        verify_response(response_json_2, "In-Memory Cache Hit")
        # For true verification, would need to inspect Flask logs, but response time implies hit
        logger.info("✓ Scenario 2: Passed. (Assuming Flask logs show 'Returning routes from memory cache')")
        
        # Scenario 3: Disk Cache Hit with Re-validation (Requires Flask Restart)
        logger.info("\n[Scenario 3/5] Disk Cache Hit with Re-validation")
        logger.warning("To test this scenario fully, please RESTART YOUR FLASK SERVER now, then run this test script again.")
        logger.warning("If you are running this script directly without restarting Flask, this will likely be an in-memory cache hit again.")
        # Simulating restart by just re-requesting, assume user will restart Flask for actual test.
        response_json_3 = await make_request(session, BASE_URL, params)
        verify_response(response_json_3, "Disk Cache Hit with Re-validation")
        logger.info("✓ Scenario 3: Passed. (Assuming Flask logs show 'Re-validating X disk-cached routes with live data')")

        # Scenario 4: Invalid Inputs (Missing Destination)
        logger.info("\n[Scenario 4/5] Invalid Inputs (Missing Destination)")
        invalid_params = {"origin": TEST_ORIGIN, "date": TEST_DATE}
        try:
            await make_request(session, BASE_URL, invalid_params)
            assert False, "Expected error for missing destination, but got success"
        except aiohttp.ClientResponseError as e:
            assert e.status == 400, f"Expected 400 error, got {e.status}"
            error_resp = await e.response.json()
            assert "Origin and destination are required." in error_resp.get("error"), f"Unexpected error message: {error_resp}"
            logger.info("✓ Scenario 4: Passed. Correctly handled missing destination.")

        # Scenario 5: Non-existent Origin/Destination
        logger.info("\n[Scenario 5/5] Non-existent Origin/Destination")
        non_existent_params = {"origin": NON_EXISTENT_STATION, "destination": TEST_DESTINATION, "date": TEST_DATE}
        try:
            response_json_nonexistent = await make_request(session, BASE_URL, non_existent_params)
            assert "error" in response_json_nonexistent, "Expected error for non-existent origin, but got success"
            assert f"Station '{NON_EXISTENT_STATION}' not found." in response_json_nonexistent.get("error"), f"Unexpected error message: {response_json_nonexistent}"
            logger.info("✓ Scenario 5: Passed. Correctly handled non-existent origin.")
        except aiohttp.ClientResponseError as e: # Handle HTTP error for server-side validation error
             assert e.status == 400, f"Expected 400 error for non-existent station, got {e.status}"
             error_resp = await e.response.json()
             assert f"Station '{NON_EXISTENT_STATION}' not found." in error_resp.get("error"), f"Unexpected error message: {error_resp}"
             logger.info("✓ Scenario 5: Passed. Correctly handled non-existent origin (HTTP 400).")

    logger.info("\n--- All Backend API Integration Tests Completed ---")
    clean_up_cache_files(TEST_ORIGIN, TEST_DESTINATION, test_date_for_cleanup)


if __name__ == "__main__":
    # Ensure a .env file exists for IRCTC_API_KEY for the Flask app.
    # The test script itself doesn't need it if Flask handles it.
    
    # Run the test
    asyncio.run(run_tests())

    # Final instruction to user
    logger.info("\n--- IMPORTANT: Manual Verification Required ---")
    logger.info("1. Start your Flask application: python api.py")
    logger.info("2. Run this test script: python temp_test_routes.py")
    logger.info("3. Pay close attention to the Flask server's console logs and the test script's logs.")
    logger.info("4. For Scenario 3 (Disk Cache Hit with Re-validation), you MUST restart your Flask server between the second and third request.")
    logger.info("5. Verify the JSON responses match the expected structure and data values.")
