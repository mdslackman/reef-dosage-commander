import tkinter as tk
from tkinter import messagebox, ttk
import csv
import json
import os
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime

# --- FILE PATHS ---
LOG_FILE = "aquarium_data.csv"
MAINT_FILE = "maintenance_log.csv"
SETTINGS_FILE = "settings.json"

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.10.1 (Pre-Alpha)")
        self.root.geometry("700x900")

        self.load_settings()
        
        # --- PARAMETER DEFINITIONS (Ranges for Gauge) ---
        # Format: {unit: [MinRed, MinYellow, GreenStart, GreenEnd, MaxYellow, MaxRed]}
        self.ranges = {
            "Alkalinity": {"dKH": [5, 6, 7, 11, 12, 14], "target": 8.5, "conv": 17.86},
            "Calcium": {"ppm": [300, 350, 380, 450, 500, 550], "target": 420, "conv": 1.0},
            "Magnesium": {"ppm": [1000, 1150, 1250, 1450, 1550, 1700], "target": 1350, "conv": 1.0}
        }
        
        self.brands = {
            "Custom (Manual)": 0,
            "ESV B-Ionic Alk (Part 1)": 1.9,
            "ESV B-Ionic Cal (Part 2)": 20.0,
            "Red Sea Foundation A (Cal)": 2.0,
            "Red Sea Foundation B (Alk)": 0.1,
            "BRC Pharma Soda Ash": 0.5
        }

        self.notebook = ttk.Notebook(root)
        self.calc_tab = ttk.Frame(self.notebook)
        self.maint_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.calc_tab, text=" Dosage ")
        self.notebook.add(self.maint_tab, text=" Maintenance ")
        self.notebook.add(self.log_tab, text=" History ")
        self.notebook.add(self.settings_tab, text=" Settings ")
        self.notebook.pack(expand=1, fill="both")

        self.build_calc_tab()
        self.build_maint_tab()
        self.build_log_tab()
        self.build_settings_tab()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                self.settings = json.load(f)
        else:
            self.settings = {"tank_name": "My Aquarium", "volume": 220}

    # --- TAB 1: CALCULATION & GAUGE ---
    def build_calc_tab(self):
        frame = ttk.Frame(self.calc_tab, padding="20")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=f"Tank: {self.settings['tank_name']}", font=("Arial", 12, "italic")).grid(row=0, column=0, columnspan=2)
        tk.Label(frame, text="Chemical Adjuster", font=("Arial", 16, "bold")).grid(row=1, column=0, columnspan=2, pady=10)

        # Gauge Canvas
        self.gauge_canvas = tk.Canvas(frame, width=400, height=40, bg="#ecf0f1", highlightthickness=0)
        self.gauge_canvas.grid(row=2, column=0, columnspan=2, pady=10)
        self.draw_gauge(0) # Initial empty gauge

        # Inputs
        tk.Label(frame, text="Parameter:").grid(row=3, column=0, sticky="w")
        self.param_var = tk.StringVar(value="Alkalinity")
        self.param_menu = ttk.Combobox(frame, textvariable=self.param_var, values=list(self.ranges.keys()), state="readonly")
        self.param_menu.grid(row=3, column=1, pady=5, sticky="ew")
        self.param_menu.bind("<<ComboboxSelected>>", self.update_units_and_presets)

        tk.Label(frame, text="Current Level:").grid(row=4, column=0, sticky="w")
        self.curr_ent = tk.Entry(frame)
        self.curr_ent.grid(row=4, column=1, pady=5, sticky="ew")
        self.curr_ent.bind("<KeyRelease>", self.update_gauge_live)

        tk.Label(frame, text="Unit:").grid(row=5, column=0, sticky="w")
        self.unit_var = tk.StringVar(value="dKH")
        self.unit_menu = ttk.Combobox(frame, textvariable=self.unit_var, state="readonly")
        self.unit_menu.grid(row=5, column=1, pady=5, sticky="ew")

        tk.Label(frame, text="Target Level:").grid(row=6, column=0, sticky="w")
        self.targ_ent = tk.Entry(frame)
        self.targ_ent.grid(row=6, column=1, pady=5, sticky="ew")

        tk.Label(frame, text="Product:").grid(row=7, column=0, sticky="w")
        self.brand_var = tk.StringVar(value="Custom (Manual)")
        self.brand_menu = ttk.Combobox(frame, textvariable=self.brand_var, values=list(self.brands.keys()), state="readonly")
        self.brand_menu.grid(row=7, column=1, pady=5, sticky="ew")
        self.brand_menu.bind("<<ComboboxSelected>>", self.apply_brand)

        tk.Label(frame, text="Strength:").grid(row=8, column=0, sticky="w")
        self.strength_ent = tk.Entry(frame)
        self.strength_ent.grid(row=8, column=1, pady=5, sticky="ew")

        tk.Button(frame, text="CALCULATE DOSE", command=self.perform_calculation, bg="#2980b9", fg="white", font=("Arial", 10, "bold")).grid(row=9, column=0, columnspan=2, pady=20, sticky="ew")
        
        self.res_lbl = tk.Label(frame, text="", font=("Consolas", 11, "bold"), wraplength=450)
        self.res_lbl.grid(row=10, column=0, columnspan=2)

    def draw_gauge(self, value):
        self.gauge_canvas.delete("all")
        # Draw background zones
        colors = ["#e74c3c", "#f1c40f", "#2ecc71", "#f1c40f", "#e74c3c"]
        widths = [80, 80, 80, 80, 80]
        x_start = 0
        for i, color in enumerate(colors):
            self.gauge_canvas.create_rectangle(x_start, 0, x_start + widths[i], 30, fill=color, outline="")
            x_start += widths[i]
        
        # Draw needle
        param = self.param_var.get()
        unit = self.unit_var.get()
        if param == "Alkalinity" and unit == "ppm": value /= 17.86 # Normalize to dKH for gauge
        
        # Calculate needle position (simple mapping)
        r = self.ranges[param].get("dKH" if param == "Alkalinity" else "ppm")
        min_v, max_v = r[0], r[5]
        
        pos = ((value - min_v) / (max_v - min_v)) * 400 if max_v != min_v else 0
        pos = max(0, min(400, pos))
        self.gauge_canvas.create_line(pos, 0, pos, 40, fill="black", width=4)
        self.gauge_canvas.create_polygon(pos-5, 40, pos+5, 40, pos, 30, fill="black")

    def update_gauge_live(self, event=None):
        try:
            val = float(self.curr_ent.get())
            self.draw_gauge(val)
        except: pass

    def update_units_and_presets(self, event=None):
        p = self.param_var.get()
        u_list = self.ranges[p].get("units", ["dKH", "ppm"] if p == "Alkalinity" else ["ppm"])
        self.unit_menu.config(values=u_list)
        self.unit_menu.set(u_list[0])
        self.targ_ent.delete(0, tk.END)
        self.targ_ent.insert(0, str(self.ranges[p]["target"]))

    def apply_brand(self, event=None):
        s = self.brands[self.brand_var.get()]
        if s > 0:
            self.strength_ent.delete(0, tk.END)
            self.strength_ent.insert(0, str(s))

    def perform_calculation(self):
        try:
            curr = float(self.curr_ent.get())
            targ = float(self.targ_ent.get())
            strength = float(self.strength_ent.get())
            vol = float(self.settings["volume"])
            
            diff = targ - curr
            if diff <= 0:
                self.res_lbl.config(text="Status: Optimal. No dose required.", fg="#27ae60")
                return

            total_ml = (diff * vol) / strength
            self.res_lbl.config(text=f"DOSE: {total_ml:.1f} mL Total\nTarget: {targ} | Rise: +{diff:.2f}", fg="#2980b9")
            
            if messagebox.askyesno("Log", "Log this dose?"):
                self.save_to_csv("Dose", self.param_var.get(), total_ml, "")
        except: messagebox.showerror("Error", "Check your inputs.")

    # --- OTHER TABS (Consolidated Logic) ---
    def build_maint_tab(self):
        frame = ttk.Frame(self.maint_tab, padding="20")
        frame.pack(fill="both")
        tk.Label(frame, text="Maintenance Log", font=("Arial", 14, "bold")).pack(pady=10)
        for task in ["Filter Socks", "RO/DI Carbon", "Skimmer Cup", "Wavemaker Soak"]:
            f = ttk.Frame(frame); f.pack(fill="x", pady=2)
            tk.Label(f, text=task, width=20).pack(side="left")
            tk.Button(f, text="Mark Done", command=lambda t=task: self.log_maint(t)).pack(side="right")

    def log_maint(self, t):
        with open(MAINT_FILE, "a", newline='') as f:
            csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d"), t])
        messagebox.showinfo("Done", f"Logged {t}")

    def build_log_tab(self):
        frame = ttk.Frame(self.log_tab, padding="20")
        frame.pack(fill="both", expand=True)
        tk.Button(frame, text="Refresh History", command=self.refresh_logs).pack()
        self.log_box = tk.Text(frame, height=20, width=60, font=("Consolas", 9))
        self.log_box.pack(pady=10)
        self.refresh_logs()

    def refresh_logs(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                self.log_box.delete("1.0", tk.END)
                self.log_box.insert(tk.END, "".join(f.readlines()[-20:]))

    def build_settings_tab(self):
        frame = ttk.Frame(self.settings_tab, padding="20")
        frame.pack(fill="both")
        tk.Label(frame, text="Config", font=("Arial", 14, "bold")).pack()
        self.name_ent = tk.Entry(frame); self.name_ent.insert(0, self.settings["tank_name"]); self.name_ent.pack()
        self.vol_ent = tk.Entry(frame); self.vol_ent.insert(0, str(self.settings["volume"])); self.vol_ent.pack()
        tk.Button(frame, text="Save", command=self.save_config).pack()

    def save_config(self):
        self.settings = {"tank_name": self.name_ent.get(), "volume": self.vol_ent.get()}
        with open(SETTINGS_FILE, "w") as f: json.dump(self.settings, f)
        messagebox.showinfo("Saved", "Settings Updated.")

    def save_to_csv(self, type, param, val, ph):
        exists = os.path.isfile(LOG_FILE)
        with open(LOG_FILE, "a", newline='') as f:
            writer = csv.writer(f)
            if not exists: writer.writerow(["Timestamp", "Tank", "Type", "Parameter", "Value", "pH"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), self.settings["tank_name"], type, param, f"{val:.2f}", ph])

if __name__ == "__main__":
    root = tk.Tk()
    app = AquariumCommanderPro(root)
    root.mainloop()
