import tkinter as tk
from tkinter import messagebox, ttk
import csv
import json
import os
from datetime import datetime

# --- FILE PATHS ---
LOG_FILE = "aquarium_data.csv"
SETTINGS_FILE = "settings.json"

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.11.1")
        self.root.geometry("850x950")

        self.load_settings()
        
        # --- PARAMETER MASTER DATA ---
        self.ranges = {
            "Alkalinity": {
                "units": ["dKH", "ppm"], 
                "target": 8.5, 
                "range": [5, 6, 7, 11, 12, 14],
                "brands": {
                    "Custom (Manual)": 0.0,
                    "Fritz RPM Liquid Alkalinity": 0.6,
                    "ESV B-Ionic Alk (Part 1)": 1.9,
                    "Red Sea Foundation B (Alk)": 0.1,
                    "BRC Pharma Soda Ash": 0.5
                }
            },
            "Calcium": {
                "units": ["ppm"], 
                "target": 420, 
                "range": [300, 350, 380, 450, 500, 550],
                "brands": {
                    "Custom (Manual)": 0.0,
                    "Fritz RPM Liquid Calcium": 10.0,
                    "ESV B-Ionic Cal (Part 2)": 20.0,
                    "Red Sea Foundation A (Cal)": 2.0
                }
            },
            "Magnesium": {
                "units": ["ppm"], 
                "target": 1350, 
                "range": [1000, 1150, 1250, 1450, 1550, 1700],
                "brands": {
                    "Custom (Manual)": 0.0,
                    "Fritz RPM Liquid Magnesium": 5.0,
                    "Red Sea Foundation C (Mag)": 1.0
                }
            }
        }

        self.notebook = ttk.Notebook(root)
        self.calc_tab = ttk.Frame(self.notebook)
        self.maint_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.calc_tab, text=" Dosage ")
        self.notebook.add(self.maint_tab, text=" Maintenance/Logging ")
        self.notebook.add(self.log_tab, text=" History ")
        self.notebook.pack(expand=1, fill="both")

        self.build_calc_tab()
        self.build_maint_tab()
        self.build_log_tab()

        # Startup initialization
        self.update_param_selection()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f: self.settings = json.load(f)
            except: self.settings = {"tank_name": "My Reef", "volume": 220.0}
        else: self.settings = {"tank_name": "My Reef", "volume": 220.0}

    def build_calc_tab(self):
        f = ttk.Frame(self.calc_tab, padding="20"); f.pack(fill="both", expand=True)

        self.param_var = tk.StringVar(value="Alkalinity")
        self.unit_var = tk.StringVar(value="dKH")
        self.brand_var = tk.StringVar(value="Custom (Manual)")
        self.dynamic_unit_text = tk.StringVar(value="dKH")

        tk.Label(f, text=f"Tank: {self.settings['tank_name']} ({self.settings['volume']} Gal)", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=3)
        
        self.gauge_canvas = tk.Canvas(f, width=500, height=70, bg="#f0f0f0", highlightthickness=0)
        self.gauge_canvas.grid(row=1, column=0, columnspan=3, pady=10)

        # Parameter
        tk.Label(f, text="Select Parameter:").grid(row=2, column=0, sticky="w")
        self.p_menu = ttk.Combobox(f, textvariable=self.param_var, values=list(self.ranges.keys()), state="readonly")
        self.p_menu.grid(row=2, column=1, pady=5, sticky="ew")
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)

        # Preferred Unit
        tk.Label(f, text="Preferred Unit:").grid(row=3, column=0, sticky="w")
        self.u_menu = ttk.Combobox(f, textvariable=self.unit_var, state="readonly")
        self.u_menu.grid(row=3, column=1, pady=5, sticky="ew")
        self.u_menu.bind("<<ComboboxSelected>>", self.sync_all_labels)

        # Current Level
        tk.Label(f, text="Current Level:").grid(row=4, column=0, sticky="w")
        self.curr_ent = tk.Entry(f); self.curr_ent.grid(row=4, column=1, pady=5, sticky="ew")
        self.curr_ent.bind("<KeyRelease>", self.handle_input_change)
        tk.Label(f, textvariable=self.dynamic_unit_text).grid(row=4, column=2, sticky="w")

        # Target Level
        tk.Label(f, text="Target Level:").grid(row=5, column=0, sticky="w")
        self.targ_ent = tk.Entry(f); self.targ_ent.grid(row=5, column=1, pady=5, sticky="ew")
        tk.Label(f, textvariable=self.dynamic_unit_text).grid(row=5, column=2, sticky="w")

        # Product
        tk.Label(f, text="Dosing Product:").grid(row=6, column=0, sticky="w")
        self.b_menu = ttk.Combobox(f, textvariable=self.brand_var, state="readonly")
        self.b_menu.grid(row=6, column=1, pady=5, sticky="ew")
        self.b_menu.bind("<<ComboboxSelected>>", self.apply_brand_strength)

        # Strength (Rise per 1mL per 1Gal)
        tk.Label(f, text="Product Strength:").grid(row=7, column=0, sticky="w")
        self.strength_ent = tk.Entry(f); self.strength_ent.grid(row=7, column=1, pady=5, sticky="ew")
        tk.Label(f, text="rise/mL/gal").grid(row=7, column=2, sticky="w")

        self.calc_btn = tk.Button(f, text="CALCULATE ML DOSE", command=self.perform_calculation, bg="#2980b9", fg="white", font=("Arial", 10, "bold"))
        self.calc_btn.grid(row=8, column=0, columnspan=3, pady=20, sticky="ew")
        
        self.res_lbl = tk.Label(f, text="", font=("Consolas", 12, "bold"), wraplength=450, justify="center")
        self.res_lbl.grid(row=9, column=0, columnspan=3)

    def update_param_selection(self, event=None):
        p = self.param_var.get()
        self.u_menu.config(values=self.ranges[p]["units"])
        self.u_menu.set(self.ranges[p]["units"][0])
        self.b_menu.config(values=list(self.ranges[p]["brands"].keys()))
        self.b_menu.set("Custom (Manual)")
        self.strength_ent.delete(0, tk.END)
        self.sync_all_labels()

    def sync_all_labels(self, event=None):
        p = self.param_var.get()
        u = self.unit_var.get()
        self.dynamic_unit_text.set(u)
        
        # Adjust Target Number based on unit
        base_targ = self.ranges[p]["target"]
        if p == "Alkalinity" and u == "ppm":
            new_targ = round(base_targ * 17.86, 1)
        else:
            new_targ = base_targ
            
        self.targ_ent.delete(0, tk.END)
        self.targ_ent.insert(0, str(new_targ))

    def apply_brand_strength(self, event=None):
        p = self.param_var.get()
        b = self.brand_var.get()
        strength = self.ranges[p]["brands"].get(b, 0.0)
        self.strength_ent.delete(0, tk.END)
        if strength > 0: self.strength_ent.insert(0, str(strength))

    def handle_input_change(self, event=None):
        try:
            val = float(self.curr_ent.get())
            # Logic check: if Alk is > 25, user likely typing PPM
            if self.param_var.get() == "Alkalinity" and self.unit_var.get() == "dKH" and val > 25:
                self.unit_var.set("ppm")
                self.sync_all_labels()
            self.draw_gauge(val)
        except: pass

    def draw_gauge(self, value):
        self.gauge_canvas.delete("all")
        offset = 50
        colors = ["#e74c3c", "#f1c40f", "#2ecc71", "#f1c40f", "#e74c3c"]
        for i, color in enumerate(colors):
            self.gauge_canvas.create_rectangle(offset + (i*80), 10, offset + ((i+1)*80), 35, fill=color, outline="")
        p = self.param_var.get(); u = self.unit_var.get()
        adj_value = value / 17.86 if p == "Alkalinity" and u == "ppm" else value
        r = self.ranges[p]["range"]
        pos = (((adj_value - r[0]) / (r[5] - r[0])) * 400) if r[5] > r[0] else 0
        pos = max(0, min(400, pos)) + offset
        self.gauge_canvas.create_line(pos, 5, pos, 40, fill="black", width=4)

    def perform_calculation(self):
        try:
            p = self.param_var.get(); u = self.unit_var.get()
            curr = float(self.curr_ent.get()); targ = float(self.targ_ent.get())
            
            # Safety Threshold Check
            check_val = curr / 17.86 if p == "Alkalinity" and u == "ppm" else curr
            if check_val > self.ranges[p]["range"][3]:
                self.res_lbl.config(text=f"!!! HIGH {p.upper()} ALERT !!!\nReading: {curr}{u}\nDo not dose. Levels are already optimal/high.", fg="#c0392b")
                return

            diff = targ - curr
            if diff <= 0:
                self.res_lbl.config(text="Levels are Optimal.\nNo Dosage Required.", fg="#27ae60")
                return

            strength = float(self.strength_ent.get())
            vol = float(self.settings["volume"])
            total_ml = (diff * vol) / strength
            self.res_lbl.config(text=f"TOTAL DOSE: {total_ml:.1f} mL\n(To raise {p} by {diff:.2f} {u})", fg="#2980b9")
            
            if messagebox.askyesno("Log", "Log this dosage to history?"):
                self.save_to_csv("Dose", p, f"{total_ml}mL (+{diff}{u})")
        except: messagebox.showerror("Error", "Please check that all inputs are numbers.")

    def build_maint_tab(self):
        f = ttk.Frame(self.maint_tab, padding="20"); f.pack(fill="both")
        tk.Label(f, text="Quick-Log Test Results", font=("Arial", 12, "bold")).pack(pady=10)
        grid = ttk.Frame(f); grid.pack()
        tk.Label(grid, text="Alk:").grid(row=0, column=0); self.m_alk = tk.Entry(grid); self.m_alk.grid(row=0, column=1)
        tk.Label(grid, text="Cal:").grid(row=1, column=0); self.m_cal = tk.Entry(grid); self.m_cal.grid(row=1, column=1)
        tk.Label(grid, text="Mag:").grid(row=2, column=0); self.m_mag = tk.Entry(grid); self.m_mag.grid(row=2, column=1)
        tk.Button(f, text="SAVE MEASUREMENTS", command=self.save_maint, bg="#8e44ad", fg="white").pack(pady=20)

    def save_maint(self):
        try:
            d = datetime.now().strftime("%Y-%m-%d")
            if self.m_alk.get(): self.save_to_csv("Test", "Alkalinity", f"{self.m_alk.get()} dKH", d)
            if self.m_cal.get(): self.save_to_csv("Test", "Calcium", f"{self.m_cal.get()} ppm", d)
            if self.m_mag.get(): self.save_to_csv("Test", "Magnesium", f"{self.m_mag.get()} ppm", d)
            messagebox.showinfo("Success", "Parameters Logged.")
        except: pass

    def build_log_tab(self):
        f = ttk.Frame(self.log_tab, padding="20"); f.pack(fill="both")
        self.txt = tk.Text(f, height=25, state="disabled", font=("Consolas", 9)); self.txt.pack()
        tk.Button(f, text="REFRESH LOGS", command=self.refresh_logs).pack(pady=5)
        self.refresh_logs()

    def refresh_logs(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
                self.txt.config(state="normal"); self.txt.delete("1.0", tk.END)
                for line in lines[-25:]: self.txt.insert(tk.END, line)
                self.txt.config(state="disabled")

    def save_to_csv(self, entry_type, param, value, date_str=None):
        dt = date_str if date_str else datetime.now().strftime("%Y-%m-%d %H:%M")
        exists = os.path.isfile(LOG_FILE)
        with open(LOG_FILE, "a", newline='') as f:
            w = csv.writer(f)
            if not exists: w.writerow(["Timestamp", "Type", "Param", "Value"])
            w.writerow([dt, entry_type, param, value])
        self.refresh_logs()

if __name__ == "__main__":
    root = tk.Tk()
    app = AquariumCommanderPro(root)
    root.mainloop()
