import math
import os
import csv
from datetime import datetime

# --- FILE SETUP ---
LOG_FILE = "aquarium_data.csv"

def get_input(prompt, is_float=True):
    val = input(prompt)
    if not val or val.lower() == 'skip': return None
    try:
        return float(val) if is_float else val
    except ValueError:
        print("Invalid number. Press Enter to skip.")
        return get_input(prompt, is_float)

def get_last_test(param):
    if not os.path.exists(LOG_FILE): return None
    try:
        with open(LOG_FILE, "r") as f:
            reader = list(csv.reader(f))
            for row in reversed(reader):
                if row[2] == "Test" and row[3] == param:
                    return float(row[4])
    except: return None
    return None

def run_safety_suite(name, current, target, ph):
    print("\n--- SAFETY ANALYSIS ---")
    warnings = []
    
    if name == "Alkalinity" and ph and ph >= 8.35:
        warnings.append(f"[!] HIGH pH ALERT: Current pH {ph} is elevated. Dosing Alkalinity now may cause precipitation.")

    last_mag = get_last_test("Magnesium")
    if name in ["Alkalinity", "Calcium"] and (last_mag is None or last_mag < 1300):
        mag_str = f"{last_mag} ppm" if last_mag else "Unknown"
        warnings.append(f"[!] MAGNESIUM GUARD: Foundation is {mag_str}. If Mag is under 1300, Alk/Cal stability is at risk.")

    if name == "Alkalinity":
        last_cal = get_last_test("Calcium")
        if last_cal and last_cal > 480 and target > 10:
            warnings.append("[!] PRECIPITATION RISK: Calcium is very high. Adding high Alkalinity could cause a 'snowstorm'.")
    
    limits = {"Alkalinity": 1.0, "Calcium": 20.0, "Magnesium": 100.0}
    total_increase = target - current
    if name in limits and total_increase > limits[name]:
        min_days = math.ceil(total_increase / limits[name])
        warnings.append(f"[!] SPEED LIMIT: Spread this {total_increase:.1f} unit increase over {min_days} days.")

    if not warnings:
        print("[OK] No immediate chemical conflicts detected.")
    else:
        for w in warnings: print(w)
    
    confirm = input("\nDo you wish to proceed with these risks? (y/n): ").lower()
    return confirm == 'y'

def save_entry(tank, entry_type, param, value, ph=None):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Tank", "Type", "Parameter", "Value", "pH"])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        writer.writerow([timestamp, tank, entry_type, param, value, ph])

def main():
    print("==========================================")
    print("   AQUARIUM DOSAGE COMMANDER v7.5 (PRO)   ")
    print("==========================================\n")

    tank_name = input("Enter Aquarium Name: ") or "My Aquarium"
    gallons = get_input(f"Total Water Volume (Gallons): ")
    
    if not gallons:
        print("Volume required to calculate dosage.")
        return

    while True:
        print(f"\n[{tank_name.upper()}] 1. Record Test  2. Calculate Dose  3. Exit")
        mode = input("Select: ")
        if mode == "3": break

        if mode == "1":
            ph = get_input("Current pH: ")
            param_name = input("Parameter (Alk/Cal/Mag): ")
            val = get_input(f"Result Value: ")
            if param_name.lower().startswith("a") and val and val > 20: val *= 0.056
            save_entry(tank_name, "Test", param_name.capitalize(), val, ph)
            print("Data Logged.")

        elif mode == "2":
            params = {"1": ("Alkalinity", "dKH"), "2": ("Calcium", "ppm"), "3": ("Magnesium", "ppm")}
            print("\n" + "\n".join([f"{k}. {v[0]}" for k, v in params.items()]))
            choice = input("Select Parameter: ")
            if choice not in params: continue
            
            name, unit = params[choice]
            curr = get_input(f"Current {name}: ")
            if choice == "1" and curr and curr > 20: curr *= 0.056
            
            targ = get_input(f"Target {name}: ")
            ph = get_input("Current pH (Optional): ")
            
            if not run_safety_suite(name, curr, targ, ph): continue

            strength = get_input(f"Product Strength (1mL adds how many {unit} to 1 Gal?): ")
            if all([curr, targ, strength]):
                total_ml = ((targ - curr) * gallons) / strength
                print(f"\n--- DOSAGE: {total_ml:.1f} mL Total ---")
                print(f"Record this in your log if you dose today.")

    print("\nHappy Reefing!")

if __name__ == "__main__":
    main()
