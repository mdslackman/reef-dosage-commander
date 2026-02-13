import math

def get_input(prompt, is_float=True):
    val = input(prompt)
    if not val: return None
    return float(val) if is_float else val

def main():
    print("==========================================")
    print("   UNIVERSAL REEF DOSAGE COMMANDER v1.0   ")
    print("==========================================\n")

    tank_name = input("Tank Name (e.g., Wraith): ") or "My Reef"
    gallons = get_input(f"Total Water Volume for {tank_name} (Gallons): ")
    
    if not gallons:
        print("Error: Tank volume is required.")
        return

    # Configuration for Safety Guardrails
    # Format: { Key: (Display Name, Unit, Max Daily Rise) }
    params = {
        "1": ("Alkalinity", "dKH", 1.0),
        "2": ("Calcium", "ppm", 20.0),
        "3": ("Magnesium", "ppm", 100.0)
    }

    while True:
        print("\nWhat would you like to calculate?")
        print("1. Alkalinity\n2. Calcium\n3. Magnesium\n4. Exit")
        choice = input("Select (1-4): ")

        if choice == "4": break
        if choice not in params: continue

        name, unit, max_rise = params[choice]
        print(f"\n--- {name} Adjustment ---")

        # Special handling for Alkalinity Units
        current = get_input(f"Current {name} level: ")
        if choice == "1":
            unit_choice = input("Is that (1) ppm or (2) dKH? ")
            if unit_choice == "1":
                current = current * 0.056 # Convert ppm to dKH
                print(f"  > Converted to {current:.2f} dKH")
        
        target = get_input(f"Target {name} ({unit}): ")
        
        if current is not None and target is not None:
            diff = target - current
            if diff <= 0:
                print(f"  Status: {name} is already at or above target.")
                continue

            print(f"\nFind the 'Product Strength' on your bottle.")
            strength = get_input(f"How many {unit} does 1mL add to 1 Gallon of water?: ")
            
            if strength:
                total_ml = (diff * gallons) / strength
                days = math.ceil(diff / max_rise)
                daily_dose = total_ml / days

                print("-" * 30)
                print(f"RESULTS FOR {tank_name.upper()}:")
                print(f"Total {name} to add: {total_ml:.1f} mL")
                print(f"Daily Safety Dose: {daily_dose:.1f} mL")
                print(f"Duration:          {days} Day(s)")
                print("-" * 30)

    print("\nHappy Reefing! Remember: Stability is key.")

if __name__ == "__main__":
    main()
