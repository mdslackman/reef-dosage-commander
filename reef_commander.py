import tkinter as tk
from tkinter import messagebox, ttk
import csv, json, os
from datetime import datetime

# --- FILE PATHS ---
LOG_FILE = "aquarium_data.csv"
SETTINGS_FILE = "settings.json"

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.11.3")
        self.root.geometry("850x950")
        
        # --- SAFETY LIMITS ---
        self.safety_limits = {"Alkalinity": 1.4, "Calcium": 20.0, "Magnesium": 100.0}

        self.load_settings()
        
        # --- PRODUCT DATA ---
        self.ranges = {
            "Alkalinity": {
                "units": ["dKH", "ppm"], "target": 8.5, "range": [5, 6, 7, 11, 12, 14],
                "brands": {
                    "Custom (Manual)": 0.0,
                    "Fritz RPM Liquid Alkalinity": 0.6,
                    "ESV B-Ionic Alk (Part 1)": 1.9,
                    "Red Sea Foundation B (Alk)": 0.1
                }
            },
            "Calcium": {
                "units": ["ppm"], "target": 420, "range": [300, 350, 380, 450, 500, 550],
                "brands": {
                    "Custom (Manual)": 0.0,
                    "Fritz RPM Liquid Calcium": 15.0,
                    "ESV B-Ionic Cal (Part 2)": 16.0,
                    "Red Sea Foundation A (Cal)": 2.0
                }
            },
            "Magnesium": {
                "units": ["ppm"], "target": 1350, "range": [1000, 1150, 1250, 1450, 1550, 1700],
                "brands": {
                    "Custom (Manual)": 0.0,
                    "Fritz RPM Liquid Magnesium": 18.0,
                    "Red Sea Foundation C (Mag)": 1.0
                }
            }
        }

        self.notebook = ttk.Notebook(root)
        self.calc_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.calc_tab, text=" Dosage ")
        self.notebook.add(self.log_tab, text=" History ")
        self.notebook.pack(expand=1, fill="both")
        
        self.build_calc_tab()
        self.build_log_tab()
        self.update_param_selection()

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, "r") as f: self.settings = json.load(f)
        except: self.settings = {"tank_name": "My Reef", "volume": 220.0}

    def build_calc_tab(self):
        # FIXED: Removed 'padding' from pack() and moved it to the Frame constructor
        f = ttk.Frame(self.calc_tab, padding="20")
        f.pack(fill="both", expand=True)
        
        self.p_var = tk.StringVar(value="Alkalinity")
        self.u_var = tk.StringVar(value="dKH")
        self.b_var = tk.StringVar(value="Custom (Manual)")
        self.dyn_u = tk.StringVar(value="dKH")

        tk.Label(f, text=f"Tank: {self.settings['tank_name']} ({self.settings['volume']} Gal)", font=("Arial", 10, "bold")).grid(row=0, columnspan=3, pady=10)
        
        tk.Label(f, text="Parameter:").grid(row=1, column=0, sticky="w")
        self.p_menu = ttk.Combobox(f, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly")
        self.p_menu.grid(row=1, column=1, pady=5, sticky="ew")
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)

        tk.Label(f, text="Unit:").grid(row=2, column=0, sticky="w")
        self.u_menu = ttk.Combobox(f, textvariable=self.u_var, state="readonly")
        self.u_menu.grid(row=2, column=1, pady=5, sticky="ew")
        self.u_menu.bind("<<ComboboxSelected>>", self.sync_all)

        tk.Label(f, text="Current Level:").grid(row=3, column=0, sticky="w")
        self.curr_ent = tk.Entry(f); self.curr_ent.grid(row=3, column=1, pady=5, sticky="ew")
        tk.Label(f, textvariable=self.dyn_u).grid(row=3, column=2, padx=5)

        tk.Label(f, text="Target Level:").grid(row=4, column=0, sticky="w")
        self.targ_ent = tk.Entry(f); self.targ_ent.grid(row=4, column=1, pady=5, sticky="ew")
        tk.Label(f, textvariable=self.dyn_u).grid(row=4, column=2, padx=5)

        tk.Label(f, text="Product:").grid(row=5, column=0, sticky="w")
        self.b_menu = ttk.Combobox(f, textvariable=self.b_var, state="readonly")
        self.b_menu.grid(row=5, column=1, pady=5, sticky="ew")
        self.b_menu.bind("<<ComboboxSelected>>", self.apply_strength)

        tk.Label(f, text="Strength:").grid(row=6, column=0, sticky="w")
        self.str_ent = tk.Entry(f); self.str_ent.grid(row=6, column=1, pady=5, sticky="ew")
        tk.Label(f, text="rise/mL/gal").grid(row=6, column=2, padx=5)

        self.calc_btn = tk.Button(f, text="CALCULATE DOSE", command=self.perform_calc, bg="#2980b9", fg="white", font=("Arial", 10, "bold"))
        self.calc_btn.grid(row=7, column=0, columnspan=3, pady=20, sticky="ew")
        self.res_lbl = tk.Label(f, text="", font=("Consolas", 11, "bold"), wraplength=450, justify="center"); self.res_lbl.grid(row=8, columnspan=3)

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu.config(values=self.ranges[p]["units"]); self.u_menu.set(self.ranges[p]["units"][0])
        self.b_menu.config(values=list(self.ranges[p]["brands"].keys())); self.b_menu.set("Custom (Manual)")
        self.str_ent.delete(0, tk.END); self.sync_all()

    def sync_all(self, e=None):
        p, u = self.p_var.get(), self.u_var.get(); self.dyn_u.set(u)
        t = self.ranges[p]["target"]
        if p == "Alkalinity" and u == "ppm": t = round(t * 17.86, 1)
        self.targ_ent.delete(0, tk.END); self.targ_ent.insert(0, str(t))

    def apply_strength(self, e=None):
        s = self.ranges[self.p_var.get()]["brands"].get(self.b_var.get(), 0.0)
        self.str_ent.delete(0, tk.END); self.str_ent.insert(0, str(s))

    def perform_calc(self):
        try:
            p, u = self.p_var.get(), self.u_var.get()
            curr, targ = float(self.curr_ent.get()), float(self.targ_ent.get())
            strength, vol = float(self.str_ent.get()), float(self.settings["volume"])
            
            if p == "Alkalinity" and u == "ppm" and strength < 2.0:
                strength = strength * 17.86
            
            diff = targ - curr
            if diff <= 0: self.res_lbl.config(text="Status: Level is already Optimal.", fg="green"); return
            
            total_ml = (diff * vol) / strength
            limit = self.safety_limits[p]
            if p == "Alkalinity" and u == "ppm": limit = limit * 17.86
            
            days = max(1, int(diff / limit) + (1 if diff % limit > 0 else 0))
            
            result = f"TOTAL DOSE: {total_ml:.1f} mL\nTarget Rise: +{diff:.2f} {u}\n"
            if days > 1:
                daily = total_ml / days
                result += f"\n!!! SAFETY NOTICE !!!\nSpread over {days} days.\nDose {daily:.1f} mL per day."
                self.res_lbl.config(text=result, fg="#c0392b")
            else:
                result += "\nSafe to dose in a single day."
                self.res_lbl.config(text=result, fg="#2980b9")
        except ValueError: messagebox.showerror("Input Error", "Please enter valid numbers.")

    def build_log_tab(self):
        # FIXED: Padding moved from pack() to the Frame constructor
        f = ttk.Frame(self.log_tab, padding="20")
        f.pack(fill="both", expand=True)
        self.txt = tk.Text(f, height=25, state="disabled", font=("Consolas", 10))
        self.txt.pack(padx=10, pady=10, fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = AquariumCommanderPro(root)
    root.mainloop()
