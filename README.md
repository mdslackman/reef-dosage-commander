🌊 Aquarium Commander Pro v0.20.3
Precision Reef Management & Bio-Safety Engine

Aquarium Commander Pro is a specialized Python-based toolkit designed for advanced reef aquarists. It bridges the gap between raw test kit data and actionable chemical dosing, with a hard focus on preventing livestock stress through automated safety caps.
🛠 Core Modules
1. Smart Action Plan (Dosing Calculator)

The engine calculates precise liquid additions based on your total system volume.

    Bio-Safety Speed Limits: Enforces a "Maximum Daily Rise" to prevent chemical shock.

        Alkalinity: 1.4 dKH / 25 ppm per day.

        Calcium: 25 ppm per day.

        Magnesium: 100 ppm per day.

    pH-Informed Dosing: Automatically extends dosing schedules if high pH (>8.35) is detected to avoid carbonate precipitation.

    Dynamic Target Snapping: Targets automatically reset to industry standards (Alk: 8.5, Ca: 420, Mg: 1350, PO4: 0.03) when switching parameters.

2. Unit-Aware Trends

Visualization logic that adapts to your preferred testing method.

    Hybrid Scaling: Supports both PPM and dKH on the same graph without breaking the Y-axis.

    Visual Goal Lines: Blue dashed lines indicate your specific target set-point.

    Safety Zones: Green (Optimal) and Red (Danger) shading provide immediate visual context for your tank’s health.

3. Integrated Testing Workflow

Specifically designed for Salifert and Hanna Instruments kits.

    Digital Timers: Built-in countdowns for reagents that require specific reaction times (e.g., Hanna Phosphorus 3-minute hold).

    Checklist Mode: Step-by-step instructions to ensure testing consistency—the key to successful reefing.

🚀 Installation & Requirements
Prerequisites

    Python 3.8+

    Required Libraries:
    Bash

    pip install pandas matplotlib

Running the App

    Save the code as aquarium_commander.py.

    Ensure you have write permissions in the folder (for reef_logs.csv and app_config.txt).

    Run via terminal:
    Bash

    python aquarium_commander.py

🛡 Safety Protocols (The "Reefer's Guardrail")

    The Custom Zero-Point: When using a "Custom" chemical, the strength defaults to 0.0. This is a intentional safety "break" requiring the user to verify the potency before the "Calculate" button will function.

    Automatic Multi-Day Spreading: If a correction is too large to be safe in 24 hours (e.g., a 152 ppm Alkalinity gap), the app will automatically generate a 3, 4, or 5-day dosing schedule.

📋 Version History

    v0.20.3: Initial Bio-Safety Audit release. Added dynamic target snapping and custom-strength zeroing.

    v0.20.2: Added Target Goal Lines and Y-axis unit labels.

    v0.19.0: Added Hanna Test Kit integration and digital timers.

🧪 Troubleshooting & Chemistry Anomalies
1. The "Precipitation" Loop (Alk/Ca Balancing)

If you find that dosing Alkalinity causes your Calcium to drop (or vice versa), you are likely experiencing Abiotic Precipitation.

    Symptoms: White "snow" in the water, white crust on heaters/pumps, or levels that won't rise despite dosing.

    The Fix: Check Magnesium first. Magnesium acts as a "buffer" that prevents Calcium and Carbonate from bonding prematurely. Ensure Magnesium is 1300–1400 ppm before making large corrections to Alk/Ca.

2. High pH & Alkalinity Dosing

Dosing high-pH additives (like Sodium Carbonate/Soda Ash) into a tank already at pH 8.4+ can cause localized precipitation.

    The App's Logic: This is why v0.20.3 automatically slows your dosing plan if you input a high pH.

    Action: Dose into a high-flow area (like a return pump chamber) to ensure rapid mixing.

3. Nitrate/Phosphate "Stall"

When using the "Generic Carbon" or "NoPox" settings:

    Redfield Ratio: Bacteria need both Nitrate and Phosphate to grow. If your Phosphate is 0.00, your Nitrate will often "stall" and refuse to drop because the bacteria are phosphate-limited.

    The Fix: If Nitrate isn't moving, check if your Phosphate has hit zero. You may need to feed more or dose a tiny amount of Phosphate to get the Nitrate moving again.

4. Reading Discrepancies (Hanna vs. Salifert)

It is common for different kits to vary by 5–10%.

    Stability > Specific Numbers: Pick one kit brand for your history logs and stick with it.

    The Fix: Consistency in how you perform the test (the user journey we built into the "Testing" tab) is more important than the brand of the kit itself.
