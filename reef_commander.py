import tkinter as tk
from tkinter import messagebox, ttk
import csv
import json
import os
from datetime import datetime

# --- FILE PATHS ---
LOG_FILE = "aquarium_data.csv"
MAINT_FILE = "maintenance_log.csv"
SETTINGS_FILE = "settings.json"

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.10.3 (Pre-Alpha)")
        self.root.geometry("750x900")

        self.load_settings()
        
        # --- PARAMETER DEFINITIONS ---
        self.ranges = {
            "Alkalinity": {"units": ["dKH", "ppm"], "target": 8.5, "range": [5, 6, 7, 11, 12, 14]},
            "Calcium": {"units": ["ppm"], "target": 420, "range": [300, 350, 380, 450, 500, 550]},
            "Magnesium": {"units": ["ppm"], "target": 1350, "range": [1000, 1150, 1250, 1450, 1550, 1700]}
        }
        
        self.brands = {
            "Custom (Manual)": 0,
            "ESV B-Ionic Alk (Part 1)": 1.9,
            "ESV B-Ionic Cal (Part 2)": 20.0,
            "Red Sea Foundation A (Cal)": 2.0,
            "Red Sea Foundation B (Alk)": 0.1,
            "Fritz RPM Liquid Alk": 0.6,
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
            self.settings = {"tank_name": "My Aquarium", "volume": 220.0}

    def build_calc_tab(self):
        frame = ttk.Frame(self.calc_tab, padding="20")
        frame.pack(fill="both", expand=True)

        self.param_var = tk.StringVar(value="Alkalinity")
        self.unit_var = tk.StringVar(value="dKH")
        self.brand_var = tk.StringVar(value="Custom (Manual)")

        tk.Label(frame, text=f"Tank: {self.settings['tank_name']}", font=("Arial", 10, "italic")).grid(row=0, column=0, columnspan=2)
        tk.Label(frame, text="Chemical Adjuster", font=("Arial", 16, "bold")).grid(row=1, column=0, columnspan=2, pady=10)

        # Gauge Canvas (Widened to 500 to prevent cutoff)
        self.gauge_canvas = tk.Canvas(frame, width=500, height=60, bg="#f0f0f0", highlightthickness=0)
        self.gauge_canvas.grid(row=2, column=0, columnspan=2, pady=15)

        tk.Label(frame, text="Parameter:").grid(row=3, column=0, sticky="w")
        self.param_menu = ttk.Combobox(frame, textvariable=self.param_var, values=list(self.ranges.keys()), state="readonly")
        self.param_menu.grid(row=3, column=1, pady=5, sticky="ew")
        self.param_menu.bind("<<ComboboxSelected>>", self.update_units_and_presets)

        tk.Label(frame, text="Current Level:").grid(row=4, column=0, sticky="w")
        self.curr_ent = tk.Entry(frame)
        self.curr_ent.grid(row=4, column=1, pady=5, sticky="ew")
        self.curr_ent.bind("<KeyRelease>", self.update_gauge_live)
        self.curr_ent.bind("<FocusOut>", self.smart_unit_check)

        tk.Label(frame, text="Unit:").grid(row=5, column=0, sticky="w")
        self.unit_menu = ttk.Combobox(frame, textvariable=self.unit_var, state="readonly")
        self.unit_menu.grid(row=5, column=1, pady=5, sticky="ew")
        self.unit_menu.bind("<<ComboboxSelected>>", self.sync_target_unit)

        tk.Label(frame, text="Target Level:").grid(row=6, column=0, sticky="w")
        self.targ_ent = tk.Entry(frame)
        self.targ_ent.grid(row=6, column=1, pady=5, sticky="ew")

        tk.Label(frame, text="Product:").grid(row=7, column=0, sticky="w")
        self.brand_menu = ttk.Combobox(frame, textvariable=self.brand_var, values=list(self.brands.keys()), state="readonly")
        self.brand_menu.grid(row=7, column=1, pady=5, sticky="ew")
        self.brand_menu.bind("<<ComboboxSelected>>", self.apply_brand)

        tk.Label(frame, text="Product Strength:").grid(row=8, column=0, sticky="w")
        self.strength_ent = tk.Entry(frame)
        self.strength_ent.grid(row=8, column=1, pady=5, sticky="ew")

        tk.Button(frame, text="CALCULATE DOSE", command=self.perform_calculation, bg="#2980b9", fg="white", font=("Arial", 10, "bold")).grid(row=9, column=0, columnspan=2, pady=20, sticky="ew")
        
        self.res_lbl = tk.Label(frame, text="", font=("Consolas", 11, "bold"), wraplength=450)
        self.res_lbl.grid(row=10, column=0, columnspan=2)

        self.update_units_and_presets()
        self.draw_gauge(0)

    def draw_gauge(self, value):
        self.gauge_canvas.delete("all")
        # Shift everything 50 pixels right to prevent cutoff
        offset = 50
        colors = ["#e74c3c", "#f1c40f", "#2ecc71", "#f1c40f", "#e74c3c"]
        x_start = offset
        for color in colors:
            self.gauge_canvas.create_rectangle(x_start, 10, x_start + 80, 35, fill=color, outline="")
            x_start += 80
        
        param = self.param_var.get()
        unit = self.unit_var.get()
        
        # Math for normalization
        adj_value = value / 17.86 if param == "Alkalinity" and unit == "ppm" else value
        r_list = self.ranges[param]["range"]
        min_v, max_v = r_list[0], r_list[5]
        
        # Scale to 400 pixels + offset
        if max_v > min_v:
            pos = ((adj_value - min_v) / (max_v - min_v)) * 400
        else:
            pos = 0
        pos = max(0, min(400, pos)) + offset
        
        self.gauge_canvas.create_line(pos, 5, pos, 40, fill="black", width=3)
        self.gauge_canvas.create_text(pos, 50, text=f"{value} {unit}", font=("Arial", 9, "bold"))

    def sync_target_unit(self, event=None):
        param = self.param_var.get()
        unit = self.unit_var.get()
        base_targ = self.ranges[param]["target"]
        
        # Link Target to Unit Selection
        if param == "Alkalinity" and unit == "ppm":
            new_targ = round(base_targ * 17.86, 1)
        else:
            new_targ = base_targ
            
        self.targ_ent.delete(0, tk.END)
        self.targ_ent.insert(0, str(new_targ))
        
        # Refresh gauge if value exists
        try:
            val = float(self.curr_ent.get())
            self.draw_gauge(val)
        except: pass

    def smart_unit_check(self, event=None):
        try:
            val = float(self.curr_ent.get())
            if self.param_var.get() == "Alkalinity" and self.unit_var.get() == "dKH" and val > 20:
                if messagebox.askyesno("Unit Suggestion", f"{val} looks like PPM. Switch units and targets?"):
                    self.unit_var.set("ppm")
                    self.sync_target_unit()
        except: pass

    def update_gauge_live(self, event=None):
        try:
            val = float(self.curr_ent.get())
            self.draw_gauge(val)
        except: pass

    def update_units_and_presets(self, event=None):
        p = self.param_var.get()
        u_list = self.ranges[p]["units"]
        self.unit_menu.config(values=u_list)
        self.unit_menu.set(u_list[0])
        self.sync_target_unit()

    def apply_brand(self, event=None):
        s = self.brands[self.brand_var.get()]
        if s > 0:
            self.strength_ent.delete(0, tk.END)
            self.strength_ent.insert(0, str(s))

    # --- [Calculations, Maintenance, History, Settings Tabs same as 0.10.2] ---
    def perform_calculation(self):
        try:
            curr = float(self.curr_ent.get())
            targ = float(self.targ_ent.get())
            strength = float(self.strength_ent.get())
            vol = float(self.settings["volume"])
            diff = targ - curr
            if diff <= 0:
                self.res_lbl.config(text="Optimal. No dose needed.", fg="#27ae60")
                return
            total_ml = (diff * vol) / strength
            self.res_lbl.config(text=f"DOSE: {total_ml:.1f} mL Total\nTarget: {targ} | Rise: +{diff:.2f}", fg="#2980b9")
            if messagebox.askyesno("Log", "Log this dose?"):
                self.save_to_csv("Dose", self.param_var.get(), total_ml)
        except: messagebox.showerror("Error", "Check numeric inputs.")

    def build_maint_tab(self):
        frame = ttk.Frame(self.maint_tab, padding="20")
        frame.pack(fill="both")
        tk.Label(frame, text="Maintenance Log", font=("Arial", 14, "bold")).pack(pady=10)
        for t in ["Filter Socks", "RO/DI Carbon", "Skimmer Cup", "Wavemaker Soak"]:
            f = ttk.Frame(frame); f.pack(fill="x", pady=5)
            tk.Label(f, text=t, width=20, anchor="w").pack(side="left")
            tk.Button(f, text="Mark Done", command=lambda x=t: self.log_maint(x)).pack(side="right")

    def log_maint(self, t):
        with open(MAINT_FILE, "a", newline='') as f:
            csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d"), t])
        messagebox.showinfo("Done", f"Logged {t}")

    def build_log_tab(self):
        frame = ttk.Frame(self.log_tab, padding="20")
        frame.pack(fill="both", expand=True)
        tk.Button(frame, text="Refresh History", command=self.refresh_logs).pack(pady=5)
        self.log_box = tk.Text(frame, height=20, width=70, font=("Consolas", 9), state="disabled")
        self.log_box.pack(pady=10); self.refresh_logs()

    def refresh_logs(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                content = f.readlines()
                self.log_box.config(state="normal")
                self.log_box.delete("1.0", tk.END)
                self.log_box.insert(tk.END, "".join(content[-25:]))
                self.log_box.config(state="disabled")

    def build_settings_tab(self):
        frame = ttk.Frame(self.settings_tab, padding="20")
        frame.pack(fill="both")
        tk.Label(frame, text="System Configuration", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(frame, text="Tank Name:").pack()
        self.name_ent = tk.Entry(frame); self.name_ent.insert(0, self.settings["tank_name"]); self.name_ent.pack(pady=5)
        tk.Label(frame, text="Total Volume (Gallons):").pack()
        self.vol_ent = tk.Entry(frame); self.vol_ent.insert(0, str(self.settings["volume"])); self.vol_ent.pack(pady=5)
        tk.Button(frame, text="SAVE CONFIGURATION", command=self.save_config, bg="#27ae60", fg="white").pack(pady=20)

    def save_config(self):
        try:
            self.settings = {"tank_name": self.name_ent.get(), "volume": float(self.vol_ent.get())}
            with open(SETTINGS_FILE, "w") as f: json.dump(self.settings, f)
            messagebox.showinfo("Saved", "Settings Updated.")
        except: messagebox.showerror("Error", "Volume must be a number.")

    def save_to_csv(self, type, param, val):
        exists = os.path.isfile(LOG_FILE)
        with open(LOG_FILE, "a", newline='') as f:
            writer = csv.writer(f)
            if not exists: writer.writerow(["Timestamp", "Tank", "Type", "Parameter", "Value"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), self.settings["tank_name"], type, param, f"{val:.2f}"])
        self.refresh_logs()

if __name__ == "__main__":
    root = tk.Tk()
    app = AquariumCommanderPro(root)
    root.mainloop()
