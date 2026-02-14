import tkinter as tk
from tkinter import ttk, messagebox
import csv, json, os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.12.9")
        self.root.geometry("1200x1000")
        
        # Financial Data: Price per Gallon (approximate)
        self.prices = {
            "Fritz RPM Liquid Alkalinity": 23.99,
            "ESV B-Ionic Alk (Part 1)": 24.92,
            "Fritz RPM Liquid Calcium": 23.99,
            "Fritz RPM Liquid Magnesium": 38.49
        }
        
        self.zones = {"Alkalinity": [5, 14], "Calcium": [300, 600], "Magnesium": [1100, 1700], "pH": [7.5, 9.0]}
        self.targets = {"Alk": 8.5, "Cal": 420, "Mag": 1350, "pH": 8.2}
        self.safety_limits = {"Alkalinity": 1.4, "Calcium": 20.0, "Magnesium": 100.0}
        
        self.ranges = {
            "Alkalinity": {"units": ["dKH"], "target": 8.5, "brands": list(self.prices.keys()[:2])},
            "Calcium": {"units": ["ppm"], "target": 420, "brands": ["Fritz RPM Liquid Calcium"]},
            "Magnesium": {"units": ["ppm"], "target": 1350, "brands": ["Fritz RPM Liquid Magnesium"]}
        }

        self.vol_var = tk.StringVar(value="") 
        self.notebook = ttk.Notebook(root)
        self.calc_tab = ttk.Frame(self.notebook)
        self.cost_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.calc_tab, text=" Dosage ")
        self.notebook.add(self.cost_tab, text=" Cost Tracker ")
        self.notebook.add(self.log_tab, text=" History ")
        self.notebook.pack(expand=1, fill="both")
        
        self.build_calc_tab()
        self.build_cost_tab()
        self.build_log_tab()

    def build_cost_tab(self):
        f = ttk.Frame(self.cost_tab, padding="30"); f.pack(fill="both")
        
        tk.Label(f, text="--- ANNUAL DOSING PROJECTION ---", font=("Arial", 14, "bold")).pack(pady=10)
        
        self.cost_info = tk.Label(f, text="Calculate a maintenance dose in the 'Dosage' tab\nto see your cost breakdown here.", 
                                  font=("Courier", 11), justify="left", bg="#f0f0f0", padx=20, pady=20)
        self.cost_info.pack(fill="x", pady=20)
        
        tk.Button(f, text="REFRESH COST ANALYSIS", command=self.update_costs, bg="#27ae60", fg="white").pack()

    def update_costs(self):
        """Calculates costs based on the current maintenance dose."""
        try:
            # Placeholder for logic: In a real run, this pulls from the maintenance dose variable
            # For this demo, let's assume a 20mL/day dose for the selected product
            daily_ml = 20.0 
            product = "ESV B-Ionic Alk (Part 1)"
            price_per_gal = self.prices.get(product, 25.00)
            ml_per_gal = 3785.41
            
            daily_cost = (daily_ml / ml_per_gal) * price_per_gal
            monthly = daily_cost * 30.44
            yearly = daily_cost * 365
            
            report = (f"Product: {product}\n"
                      f"Daily Dose: {daily_ml} mL\n"
                      f"----------------------------------\n"
                      f"Daily Cost:   ${daily_cost:.4f}\n"
                      f"Monthly Cost: ${monthly:.2f}\n"
                      f"Yearly Cost:  ${yearly:.2f}\n"
                      f"----------------------------------\n"
                      f"Tip: Bulk powder can reduce yearly costs by ~60%.")
            self.cost_info.config(text=report)
        except:
            self.cost_info.config(text="Error: Ensure a dosage is calculated first.")

    # [Standard build methods for calc_tab and log_tab omitted for brevity...]
    def build_calc_tab(self): pass
    def build_log_tab(self): pass

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
