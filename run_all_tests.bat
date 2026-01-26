@echo off
REM Quick Test Runner for Windows - Executes all tests in proper sequence

echo ==========================================
echo Route Master - Vercel Deployment Test Suite
echo ==========================================
echo.

setlocal enabledelayedexpansion

REM Test counters
set PASSED=0
set FAILED=0

REM Function to run a test
:run_test
set test_name=%~1
set test_file=%~2
set description=%~3

echo.
echo [TEST !PASSED!] %test_name%
echo Description: %description%
echo ---

python "%test_file%" 2>&1 | tee /tmp/test_output.txt
if !errorlevel! equ 0 (
    echo.
    echo ^[PASS^] %test_name%
    set /a PASSED+=1
) else (
    echo.
    echo ^[FAIL^] %test_name%
    set /a FAILED+=1
    echo Check output above for details
)
goto :eof

REM Test 1: Deployment Validation
echo.
echo [TEST 1] Deployment Readiness Check
echo Description: Validates all requirements for Vercel deployment
echo ---
python vercel_deployment_validator.py
if !errorlevel! equ 0 (
    echo [PASS] Deployment Validation
    set /a PASSED+=1
) else (
    echo [FAIL] Deployment Validation
    set /a FAILED+=1
)

REM Test 2: Route Generation
echo.
echo [TEST 2] Route Generation Test
echo Description: Tests route generation with all three categories
echo ---
python test_route_generation_complete.py
if !errorlevel! equ 0 (
    echo [PASS] Route Generation
    set /a PASSED+=1
) else (
    echo [FAIL] Route Generation
    set /a FAILED+=1
)

REM Test 3: Comprehensive Suite
echo.
echo [TEST 3] Comprehensive Test Suite
echo Description: Full test coverage with 10 test categories
echo ---
python test_comprehensive_vercel.py
if !errorlevel! equ 0 (
    echo [PASS] Comprehensive Tests
    set /a PASSED+=1
) else (
    echo [FAIL] Comprehensive Tests
    set /a FAILED+=1
)

REM Final Summary
echo.
echo ==========================================
echo TEST EXECUTION SUMMARY
echo ==========================================
set /a TOTAL=PASSED+FAILED
echo Total Tests Run: !TOTAL!
echo Passed: !PASSED!
echo Failed: !FAILED!
echo ==========================================

if !FAILED! equ 0 (
    echo.
    echo ^^[SUCCESS^^] All tests passed - Ready for Vercel deployment
    exit /b 0
) else (
    echo.
    echo ^^[ERROR^^] Some tests failed - Review output above
    exit /b 1
)
