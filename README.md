🌿 Reefer Madness v0.20.7
Advanced Reef Stability & Consumption Analytics

Reefer Madness is a toolkit allowing you to test, log and track chemical consumption of reef saltwater aquarium - covering alkylinity, calcium, magnesium, nitrate, and phosphate. For chemicals reefers want to dose, there's a daily dosage calculator and "action plan" calculator (used to rapidly and safely adjust your levels during crises - i.e. all of your corals dying from low alkylinity). You can track measurements overtime with logging and graphs,

This is a solo project for my own use, but please flag issues or ideas if you find the app helpful. This code was made using Gemini - I am not a software engineer but needed a calculator like this, so here we are.

✨ New in v0.20.7

    Persistent Data Core: All logs, system configurations, and unit preferences are now saved to Documents/ReeferMadness/. Your data is now independent of the application file location.

    Consumption Tracker: A new maintenance module that calculates exactly how much your corals are "eating" over a multi-day period.

    Live Dosing Status: The header bar now displays your current required daily maintenance dose at all times.

    Smart Unit Normalization: Seamlessly handles PPM (Hanna) and dKH (Standard) inputs, normalizing them for precise dosing plan generation.

🚀 Core Modules
1. The Consumption Engine (Maintenance Tab)

Instead of guessing your daily dose, Reefer Madness calculates it based on real-world uptake.

    Input: Test results from two different days and the time elapsed.

    Output: Precise daily "Drop" rate and the exact mL per day required to maintain stability.

    Safety: Automatically pulls product strength from your active selection in the Action Plan.

2. The Bio-Safety Action Plan (Correction Tab)

When parameters swing, the Action Plan calculates a path back to the target without shocking the system.

    Automatic Multi-Day Stretching: If a correction exceeds the Maximum Daily Rise (e.g., 1.4 dKH for Alkalinity), the app automatically divides the dose over several days.

    Product Precision: Pre-configured for Fritz RPM, ESV B-Ionic, and Carbon Dosing (NoPox), with a "Custom" mode for DIY solutions.

3. Visual Stability Trends (Trends Tab)

Data is only useful if it's readable. The trends module provides high-fidelity graphing.

    Adaptive Y-Axis: Automatically switches scales if it detects PPM-range data for Alkalinity.

    Target Overlays: Every graph features a blue dashed "Goal Line" based on your specific system targets.

🛠 Installation & Technical Details
Folder Structure

Upon first run, the app creates the following in your Documents folder:

    reef_logs.csv: Your entire testing history.

    app_config.txt: Remembers your system volume (e.g., 220 Gallons).

    unit_config.txt: Remembers your preference for Gallons vs. Liters.

Requirements

    Python 3.8+

    Libraries: pandas, matplotlib, tkinter

🧪 Troubleshooting: The "Redfield" & "Precipitation" Guards

    Precipitation Alert: If Alkalinity and Calcium are both dropping despite dosing, check your Magnesium levels in the Trends tab. Magnesium must be >1250 ppm to prevent abiotic precipitation.

    Nitrate Stalling: If dosing Carbon (NoPox/Vinegar) and Nitrate isn't dropping, check Phosphate. Bacteria require a trace of Phosphate to process Nitrate.

📋 Version History

    v0.20.7: Renamed to Reefer Madness. Migrated data to Documents folder. Added persistent Header Status.

    v0.20.6: Integrated Consumption Tracker and automated Maintenance Dose logic.

    v0.20.0: Initial Bio-Safety engine release with Max-Daily-Rise caps.
