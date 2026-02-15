This README is designed to act as the official manual for Aquarium Commander Pro v0.15.7. It covers everything from basic chemical logging to the advanced biological tracking and predictive algorithms we've built.
🌊 Aquarium Commander Pro v0.15.7

Aquarium Commander Pro is a comprehensive desktop utility designed for saltwater reef hobbyists who prioritize stability. It combines chemical mathematics, biological export tracking, and predictive forecasting to help you maintain a thriving ecosystem.
🚀 Core Functionality
1. Action Plan (The Dosing Engine)

This tab calculates exactly how much of a specific supplement is needed to reach your target goals.

    Safety Thresholds: Automatically warns you if a dose is too large to perform in a single day, suggesting a multi-day schedule instead.

    pH & Fuge Logic: Dynamic input fields adjust based on the parameter. When correcting Alkalinity, it monitors pH to prevent precipitation. When correcting Nitrate, it monitors Refugium Light Hours.

    Silent Auto-Logging: Every calculation is automatically "Locked" into your history as a Dosing Event, allowing you to compare what you added vs. how the tank responded.

2. Maintenance (The Digital Logbook)

Centralized logging for all 7 major reef parameters:

    Core: Alkalinity (dKH/ppm), Calcium, Magnesium.

    Nutrients: Nitrate, Phosphate.

    Environment: Salinity (SG), Temperature (°F).

    Biological Export: A dedicated toggle to track when you harvest macroalgae, which appears as a marker on your trend graphs.

3. Trends (The Stability Map)

Visualizes your tank's health using a proprietary Tri-Zone color-coded graphing system:

    🟢 Green Zone: Your optimal target range.

    🟡 Yellow Zone: Cautionary drift.

    🔴 Red Zone: Danger—immediate correction required.

    Harvest Markers: Vertical orange lines indicate when nutrient export (algae trimming) occurred.

4. History (The Audit Trail)

A searchable, exportable database of every test result and dosing event. Entries can be deleted if a mistake is made or exported to .csv for sharing with professional reef consultants.
🛠 How to Use
Step 1: Configuration

Enter your Tank Volume in the Action Plan tab. The app saves this automatically, so you only have to do it once.
Step 2: Correcting a Parameter

    Select the Correction Category (e.g., Alkalinity).

    Choose your Brand Product or enter a Custom Strength.

    Enter your Current Reading and Target.

    Click Calculate Action Plan. The app will provide the total mL needed, a daily dose breakdown, and a Projected Target Date.

    Check the bottom of the window for the ✅ LOCKED TO HISTORY confirmation.

Step 3: Logging Maintenance

After performing your weekly water tests:

    Navigate to the Maintenance tab.

    Enter your results. For Alkalinity, the app will auto-detect if you are using ppm or dKH based on the value.

    Toggle the Harvested Macroalgae box if you pruned your refugium.

    Click Log Test Results (Silent).

Step 4: Analyzing Stability

Switch to the Trends tab. Scroll through the graphs to see if your parameter lines are staying within the Green Zone. If a line enters the Red Zone, go back to the Action Plan to calculate a correction.
💾 Technical Notes

    Data Storage: All data is saved locally in reef_logs.csv in the application folder.

    Units: The application handles both SG (Salinity) and dKH/ppm (Alkalinity) standardizations.

    Dependencies: Requires Python 3.x, tkinter, and matplotlib.
