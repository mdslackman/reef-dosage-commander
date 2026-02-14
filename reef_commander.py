import tkinter as tk
from tkinter import ttk, messagebox
import csv, os
from datetime import datetime

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.13.2")
        self.root.geometry("1000x900")
        
        # Product & Unit Data
        self.prices = {
            "Fritz RPM Liquid Alkalinity": 23.99,
            "ESV B-Ionic Alk (Part 1)": 24.92,
            "Fritz RPM Liquid Calcium": 23.99,
            "Fritz RPM Liquid Magnesium": 38.49
        }
        price_keys = list(self.prices.keys())
        
        # Safety Thresholds
        self.safety_ranges = {
            "Alkalinity": {"min": 5.0, "max": 13.0}, # in dKH
            "Calcium": {"min": 350.0, "max": 550.0},
            "Magnesium": {"min": 1100.0, "max": 1600.0}
        }
        
        self.ranges = {
            "Alkalinity": {"units": ["dKH", "ppm"], "target": 8.5, "brands": price_keys[:2]},
            "Calcium": {"units": ["ppm"], "target": 420, "brands": [price_keys[2]]},
            "Magnesium": {"units": ["ppm"], "target": 1350, "brands": [price_keys[3]]}
        }

        self.vol_var = tk.StringVar(value="")
        self.p_var = tk.StringVar(value="Alkalinity")
        self.u_var = tk.StringVar()
        
        self.notebook = ttk.Notebook(root)
        self.calc_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.calc_tab, text=" Dosage & Safety ")
        self.notebook.pack(expand=1, fill="both")
        
        self.build_calc_tab()
        self.update_param_selection()

    def build_calc_tab(self):
        f = ttk.Frame(self.calc_tab, padding="40"); f.pack(fill="both", expand=True)
        
        tk.Label(f, text="Volume (Gal):").grid(row=0, column=0, sticky="w")
        tk.Entry(f, textvariable=self.vol_var, width=15, bg="#ffffcc").grid(row=0, column=1, sticky="w", pady=5)

        tk.Label(f, text="Parameter:").grid(row=1, column=0, sticky="w")
        self.p_menu = ttk.Combobox(f, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly")
        self.p_menu.grid(row=1, column=1, sticky="ew", pady=5)
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)

        tk.Label(f, text="Unit:").grid(row=2, column=0, sticky="w")
        self.u_menu = ttk.Combobox(f, textvariable=self.u_var, state="readonly")
        self.u_menu.grid(row=2, column=1, sticky="ew", pady=5)

        tk.Label(f, text="Current Reading:").grid(row=3, column=0, sticky="w")
        self.curr_ent = tk.Entry(f); self.curr_ent.grid(row=3, column=1, sticky="ew", pady=5)

        tk.Label(f, text="Target Goal:").grid(row=4, column=0, sticky="w")
        self.targ_ent = tk.Entry(f); self.targ_ent.grid(row=4, column=1, sticky="ew", pady=5)

        tk.Button(f, text="RUN SAFETY & DOSAGE CALC", command=self.perform_calc, bg="#2980b9", fg="white", height=2).grid(row=5, columnspan=2, pady=20, sticky="ew")
        
        self.res_lbl = tk.Label(f, text="Enter readings to begin.", font=("Arial", 12, "bold"), wraplength=500)
        self.res_lbl.grid(row=6, columnspan=2)

    def perform_calc(self):
        try:
            p = self.p_var.get()
            vol = float(self.vol_var.get())
            unit = self.u_var.get()
            curr = float(self.curr_ent.get())
            targ = float(self.targ_ent.get())

            # 1. AUTO-UNIT CORRECTION (Alk only)
            if p == "Alkalinity" and unit == "dKH" and curr > 25:
                curr = curr / 17.86
                self.curr_ent.delete(0, tk.END)
                self.curr_ent.insert(0, f"{curr:.2f}")
                messagebox.showinfo("Unit Corrected", f"Detected high Alkalinity ({curr*17.86:.0f}). Converted ppm to {curr:.2f} dKH.")

            # 2. CONVERT EVERYTHING TO STANDARD UNITS FOR CALC
            std_curr = curr
            std_targ = targ
            if p == "Alkalinity" and unit == "ppm":
                std_curr = curr / 17.86
                std_targ = targ / 17.86

            # 3. SAFETY CHECKS
            safe = self.safety_ranges[p]
            if std_curr < safe['min']:
                msg = f"⚠️ CRITICAL LOW: Your {p} is dangerously low ({curr} {unit})!"
                self.res_lbl.config(text=msg, fg="red")
                return
            elif std_curr > safe['max']:
                msg = f"⚠️ CRITICAL HIGH: Your {p} is way over target ({curr} {unit})!"
                self.res_lbl.config(text=msg, fg="red")
                return

            # 4. CALC DOSAGE
            diff = std_targ - std_curr
            if diff <= 0:
                self.res_lbl.config(text="STATUS: OPTIMAL. No correction needed.", fg="green")
                return

            strength = 0.6 if p == "Alkalinity" else 1.0 # Simple baseline
            total_ml = (diff * vol) / strength
            self.res_lbl.config(text=f"CORRECTION: Dose {total_ml:.1f} mL total.", fg="blue")

        except ValueError:
            self.res_lbl.config(text="ERROR: Please enter valid numbers.", fg="red")

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu.config(values=self.ranges[p]["units"]); self.u_menu.current(0)
        self.targ_ent.delete(0, tk.END); self.targ_ent.insert(0, str(self.ranges[p]["target"]))

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
