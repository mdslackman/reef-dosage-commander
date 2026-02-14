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
        self.root.title("Aquarium Commander Pro v0.10.8")
        self.root.geometry("800x950")

        self.load_settings()
        
        # --- PARAMETER MASTER DATA ---
        self.ranges = {
            "Alkalinity": {
                "units": ["dKH", "ppm"], 
                "target": 8.5, 
                "range": [5, 6, 7, 11, 12, 14],
                "brands": {
                    "Custom (Manual)": 0.0,
                    "Fritz RPM Liquid Alk": 0.6,
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
                    "Fritz RPM Liquid Cal": 10.0,
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
                    "Fritz RPM Liquid Mag": 5.0,
                    "Red Sea Foundation C (Mag)": 1.0
                }
            }
        }

        self.notebook = ttk.Notebook(root)
        self.calc_tab = ttk.Frame(self.notebook)
        self.maint_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.calc_tab, text=" Dosage ")
        self.notebook.add(self.maint_tab, text=" Maintenance & Logging ")
        self.notebook.add(self.log_tab, text=" History ")
        self.notebook.add(self.settings_tab, text=" Settings ")
        self.notebook.pack(expand=1, fill="both")

        self.build_calc_tab()
        self.build_maint_tab()
        self.build_log_tab()
        self.build_settings_tab()

        # Startup initialization
        self.update_param_selection()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                self.settings = json.load(f)
        else:
            self.settings = {"tank_name": "New Reef Tank", "volume": 220.0}

    def build_calc_tab(self):
        self.calc_frame = ttk.Frame(self.calc_tab, padding="20")
        self.calc_frame.pack(fill="both", expand=True)

        self.param_var = tk.StringVar(value="Alkalinity")
        self.unit_var = tk.StringVar(value="dKH")
        self.brand_var = tk.StringVar(value="Custom (Manual)")
        self.targ_unit_label_var = tk.StringVar(value="dKH")

        self.header_lbl = tk.Label(self.calc_frame, text=f"Tank: {self.settings['tank_name']}", font=("Arial", 10, "italic"))
        self.header_lbl.grid(row=0, column=0, columnspan=3)
        
        self.gauge_canvas = tk.Canvas(self.calc_frame, width=500, height=70, bg="#f0f0f0", highlightthickness=0)
        self.gauge_canvas.grid(row=1, column=0, columnspan=3, pady=15)

        tk.Label(self.calc_frame, text="Parameter:").grid(row=2, column=0, sticky="w")
        self.param_menu = ttk.Combobox(self.calc_frame, textvariable=self.param_var, values=list(self.ranges.keys()), state="readonly")
        self.param_menu.grid(row=2, column=1, pady=5, sticky="ew")
        self.param_menu.bind("<<ComboboxSelected>>", self.update_param_selection)

        tk.Label(self.calc_frame, text="Current Level:").grid(row=3, column=0, sticky="w")
        self.curr_ent = tk.Entry(self.calc_frame)
        self.curr_ent.grid(row=3, column=1, pady=5, sticky="ew")
        self.curr_ent.bind("<KeyRelease>", self.handle_input_change)

        tk.Label(self.calc_frame, text="Unit:").grid(row=4, column=0, sticky="w")
        self.unit_menu = ttk.Combobox(self.calc_frame, textvariable=self.unit_var, state="readonly")
        self.unit_menu.grid(row=4, column=1, pady=5, sticky="ew")
        self.unit_menu.bind("<<ComboboxSelected>>", self.sync_target_unit)

        tk.Label(self.calc_frame, text="Target Level:").grid(row=5, column=0, sticky="w")
        self.targ_ent = tk.Entry(self.calc_frame)
        self.targ_ent.grid(row=5, column=1, pady=5, sticky="ew")
        tk.Label(self.calc_frame, textvariable=self.targ_unit_label_var, font=("Arial", 9, "bold")).grid(row=5, column=2, sticky="w", padx=5)

        tk.Label(self.calc_frame, text="Product:").grid(row=6, column=0, sticky="w")
        self.brand_menu = ttk.Combobox(self.calc_frame, textvariable=self.brand_var, state="readonly")
        self.brand_menu.grid(row=6, column=1, pady=5, sticky="ew")
        self.brand_menu.bind("<<ComboboxSelected>>", self.apply_brand_strength)

        tk.Label(self.calc_frame, text="Strength:").grid(row=7, column=0, sticky="w")
        self.strength_ent = tk.Entry(self.calc_frame)
        self.strength_ent.grid(row=7, column=1, pady=5, sticky="ew")

        self.calc_btn = tk.Button(self.calc_frame, text="CALCULATE DOSE", command=self.perform_calculation, bg="#2980b9", fg="white", font=("Arial", 10, "bold"))
        self.calc_btn.grid(row=8, column=0, columnspan=3, pady=20, sticky="ew")
        
        self.res_lbl = tk.Label(self.calc_frame, text="", font=("Consolas", 11, "bold"), wraplength=450)
        self.res_lbl.grid(row=9, column=0, columnspan=3)

    def update_param_selection(self, event=None):
        p = self.param_var.get()
        self.unit_menu.config(values=self.ranges[p]["units"])
        self.unit_menu.set(self.ranges[p]["units"][0])
        
        brand_list = list(self.ranges[p]["brands"].keys())
        self.brand_menu.config(values=brand_list)
        self.brand_menu.set("Custom (Manual)")
        
        self.strength_ent.delete(0, tk.END)
        self.sync_target_unit()

    def apply_brand_strength(self, event=None):
        p = self.param_var.get()
        b = self.brand_var.get()
        strength = self.ranges[p]["brands"].get(b, 0.0)
        self.strength_ent.delete(0, tk.END)
        if strength > 0:
            self.strength_ent.insert(0, str(strength))

    def handle_input_change(self, event=None):
        try:
            val = float(self.curr_ent.get())
            if self.param_var.get() == "Alkalinity" and self.unit_var.get() == "dKH" and val > 25:
                self.unit_var.set("ppm")
                self.sync_target_unit()
            self.draw_gauge(val)
        except: pass

    def draw_gauge(self, value):
        self.gauge_canvas.delete("all")
        offset = 50
        colors = ["#e74c3c", "#f1c40f", "#2ecc71", "#f1c40f", "#e74c3c"]
        for i, color in enumerate(colors):
            self.gauge_canvas.create_rectangle(offset + (i*80), 10, offset + ((i+1)*80), 35, fill=color, outline="")
        
        p = self.param_var.get()
        u = self.unit_var.get()
        adj_value = value / 17.86 if p == "Alkalinity" and u == "ppm" else value
        r_list = self.ranges[p]["range"]
        
        pos = (((adj_value - r_list[0]) / (r_list[5] - r_list[0])) * 400) if r_list[5] > r_list[0] else 0
        pos = max(0, min(400, pos)) + offset
        
        self.gauge_canvas.create_line(pos, 5, pos, 40, fill="black", width=4)
        self.gauge_canvas.create_text(pos, 55, text=f"{value} {u}", font=("Arial", 9, "bold"))

    def sync_target_unit(self, event=None):
        p = self.param_var.get()
        u = self.unit_var.get()
        self.targ_unit_label_var.set(u)
        base_targ = self.ranges[p]["target"]
        new_targ = round(base_targ * 17.86, 1) if p == "Alkalinity" and u == "ppm" else base_targ
        self.targ_ent.delete(0, tk.END)
        self.targ_ent.insert(0, str(new_targ))

    def perform_calculation(self):
        try:
            p = self.param_var.get()
            curr = float(self.curr_ent.get())
            targ = float(self.targ_ent.get())
            u = self.unit_var.get()
            
            check_val = curr / 17.86 if p == "Alkalinity" and u == "ppm" else curr
            if check_val > self.ranges[p]["range"][3]:
                self.res_lbl.config(text=f"STOP: {p} is too high ({curr} {u}).", fg="#c0392b")
                return

            diff = targ - curr
            if diff <= 0:
                self.res_lbl.config(text="Optimal. No dose needed.", fg="#27ae60")
                return

            strength = float(self.strength_ent.get())
            vol = float(self.settings["volume"])
            total_ml = (diff * vol) / strength
            self.res_lbl.config(text=f"DOSE: {total_ml:.1f} mL Total\nRise: +{diff:.2f}", fg="#2980b9")
            
            if messagebox.askyesno("Log", "Log this dose?"):
                self.save_to_csv("Dose", p, total_ml)
        except: messagebox.showerror("Error", "Check numeric inputs.")

    def build_maint_tab(self):
        for widget in self.maint_tab.winfo_children(): widget.destroy()
        f = ttk.Frame(self.maint_tab, padding="20"); f.pack(fill="both")
        desk = ttk.LabelFrame(f, text=" Bulk Test Results ", padding=10); desk.pack(fill="x")
        tk.Label(desk, text="Date:").grid(row=0, column=0)
        self.b_date = tk.Entry(desk); self.b_date.insert(0, datetime.now().strftime("%Y-%m-%d")); self.b_date.grid(row=0, column=1)
        tk.Label(desk, text="Alk:").grid(row=1, column=0); self.b_alk = tk.Entry(desk); self.b_alk.grid(row=1, column=1)
        tk.Label(desk, text="Cal:").grid(row=2, column=0); self.b_cal = tk.Entry(desk); self.b_cal.grid(row=2, column=1)
        tk.Label(desk, text="Mag:").grid(row=3, column=0); self.b_mag = tk.Entry(desk); self.b_mag.grid(row=3, column=1)
        tk.Button(desk, text="SAVE ALL TESTS", command=self.save_bulk, bg="#8e44ad", fg="white").grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")

    def save_bulk(self):
        d = self.b_date.get()
        try:
            if self.b_alk.get(): self.save_to_csv("Test", "Alkalinity", float(self.b_alk.get()), d)
            if self.b_cal.get(): self.save_to_csv("Test", "Calcium", float(self.b_cal.get()), d)
            if self.b_mag.get(): self.save_to_csv("Test", "Magnesium", float(self.b_mag.get()), d)
            messagebox.showinfo("Success", "Tests recorded.")
        except: messagebox.showerror("Error", "Numeric values only.")

    def build_log_tab(self):
        for widget in self.log_tab.winfo_children(): widget.destroy()
        f = ttk.Frame(self.log_tab, padding="20"); f.pack(fill="both")
        self.log_box = tk.Text(f, height=25, width=80, font=("Consolas", 9), state="disabled")
        self.log_box.pack(); self.refresh_logs()

    def refresh_logs(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                content = f.readlines()
                self.log_box.config(state="normal")
                self.log_box.delete("1.0", tk.END)
                self.log_box.insert(tk.END, "".join(content[-30:]))
                self.log_box.config(state="disabled")

    def build_settings_tab(self):
        f = ttk.Frame(self.settings_tab, padding="20"); f.pack(fill="both")
        tk.Label(f, text="Tank Name:").pack(); self.name_ent = tk.Entry(f); self.name_ent.insert(0, self.settings["tank_name"]); self.name_ent.pack()
        tk.Label(f, text="Volume (Gal):").pack(); self.vol_ent = tk.Entry(f); self.vol_ent.insert(0, str(self.settings["volume"])); self.vol_ent.pack()
        tk.Button(f, text="SAVE SETTINGS", command=self.save_config).pack(pady=10)

    def save_config(self):
        self.settings = {"tank_name": self.name_ent.get(), "volume": float(self.vol_ent.get())}
        with open(SETTINGS_FILE, "w") as f: json.dump(self.settings, f)
        self.header_lbl.config(text=f"Tank: {self.settings['tank_name']}")
        messagebox.showinfo("Saved", "Settings Updated.")

    def save_to_csv(self, type, param, val, custom_date=None):
        dt = f"{custom_date} 12:00" if custom_date else datetime.now().strftime("%Y-%m-%d %H:%M")
        exists = os.path.isfile(LOG_FILE)
        with open(LOG_FILE, "a", newline='') as f:
            writer = csv.writer(f)
            if not exists: writer.writerow(["Timestamp", "Tank", "Type", "Parameter", "Value"])
            writer.writerow([dt, self.settings["tank_name"], type, param, f"{val:.2f}"])
        self.refresh_logs()

if __name__ == "__main__":
    root = tk.Tk()
    app = AquariumCommanderPro(root)
    root.mainloop()
