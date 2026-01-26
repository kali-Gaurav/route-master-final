# Frontend Enhancements Plan: Real-time Data Display and Caching UX

This document outlines the necessary frontend (React/TypeScript) enhancements to fully leverage the backend's real-time data integration and caching capabilities, providing a seamless and dynamic user experience.

## 1. Displaying Real-time Data on the Website

The backend (`route_optimizer.py` via `api.py`) now provides enriched route data, including `live_seat_availability` and `live_fare` for each segment, based on (simulated) real-time API calls. The frontend's role is to consume and visually present this information.

**Key Changes Required:**

*   **Update Data Models/Interfaces:** Ensure your React application's data models (TypeScript interfaces) for route segments and routes accommodate the new `live_seat_availability` (e.g., "AVAILABLE-120", "WL/30", "NOT AVAILABLE") and `live_fare` (numeric) fields.
*   **Modify `RouteCard.tsx` (and similar components):**
    *   **Seat Availability:** Instead of displaying static or placeholder availability, use `segment.live_seat_availability`.
        *   Implement conditional rendering:
            *   Green text/icon for "AVAILABLE-XXX".
            *   Orange/Yellow text/icon for "WL/XXX".
            *   Red text/icon or a disabled look for "NOT AVAILABLE".
        *   Display the number of available seats or waiting list number where applicable.
    *   **Fare:** Display `segment.live_fare` clearly, prefixed with the currency symbol (e.g., "₹750.00"). Ensure the total route fare (if calculated on frontend) sums these live segment fares.
    *   **Default Class Indication:** Clearly communicate that the displayed availability and fare are for **"Sleeper (SL) Class"** by default, as per the backend's current implementation. This can be done via a small label or tooltip near the availability/fare display.
*   **Loading States:** Introduce loading spinners or skeleton loaders within UI components (`RouteCard`, main search results area) while data is being fetched from the backend. This improves perceived performance and user experience, especially since live API calls can introduce latency.

## 2. Caching and Refreshing User Experience (UX)

The backend now uses `cachetools` to cache live API responses for a set duration (e.g., 5 minutes). This optimizes performance and reduces redundant external API calls. The frontend should reflect and complement this caching mechanism.

**Key UX Principles and Implementations:**

*   **Dynamic Data Fetching on Input Change:**
    *   **Clearing Results:** Whenever the user changes key input parameters (Origin, Destination, or Date of Travel), immediately **clear any previously displayed route results**. This prevents the user from seeing stale data that doesn't match their current search criteria.
    *   **Trigger New Search:** Automatically trigger a new backend API call to `/routes` (or your relevant endpoint) as soon as these key input parameters are updated and a valid search can be performed.
    *   **Visual Feedback:** Display loading indicators during the new data fetch.
*   **"Refresh" Behavior (Input Data Persistence vs. Clearing):**
    *   **Preserve Input:** Generally, when a user "refreshes" or changes a search parameter, the *other* search parameters (e.g., if only origin changes, keep destination and date) should *persist* in their respective input fields. "Erasing" all input data upon any change would be a poor user experience.
    *   **Clarification for "erased":** If "erased" implies that *previous search results* should be removed from view, then the above point about "Clearing Results" covers it. If it implies that input fields themselves should be wiped clean, this is generally discouraged unless explicitly resetting the form.
    *   **Manual Refresh Button (Optional):** Consider adding a "Refresh Results" button. When clicked, this button would trigger a new backend API call using the *current* input parameters, effectively bypassing any client-side caching (if implemented) and prompting the backend to fetch fresh data (which might hit the `rappid.in` API if the backend cache for that specific query has expired).
*   **Client-Side Caching (Optional but Recommended):** For static data (like station lists, city mappings), consider client-side caching (e.g., in browser's local storage or session storage). For dynamic route results, rely primarily on the backend's caching and re-fetch as needed.

## 3. Overall Website Performance & Responsiveness

*   **Optimize API Calls:** Ensure the frontend makes efficient API calls. Debounce search inputs if auto-fetching on type, to prevent an excessive number of requests.
*   **Error Handling:** Display user-friendly messages if the backend API fails or returns an error (e.g., "Could not fetch routes. Please try again later.").
*   **Responsive Design:** Ensure the layout and display of route information are responsive across different device sizes.

By implementing these frontend enhancements, the Route-Master project will provide a dynamic, informative, and performant experience, showcasing the value of its real-time data integration to investors.