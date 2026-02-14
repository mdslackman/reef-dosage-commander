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
        self.root.title("Aquarium Commander Pro v0.12.0")
        self.root.geometry("850x950")
        
        self.safety_limits = {"Alkalinity": 1.4, "Calcium": 20.0, "Magnesium": 100.0}
        self.load_settings()
        
        # Core Chemistry Data
        self.ranges = {
            "Alkalinity": {
                "units": ["dKH", "ppm"], "target": 8.5,
                "brands": {"Fritz RPM Liquid Alkalinity": 0.6, "ESV B-Ionic Alk (Part 1)": 1.9}
            },
            "Calcium": {"units": ["ppm"], "target": 420, "brands": {"Fritz RPM Liquid Calcium": 15.0}},
            "Magnesium": {"units": ["ppm"], "target": 1350, "brands": {"Fritz RPM Liquid Magnesium": 18.0}}
        }

        self.live_ph = tk.StringVar(value=str(self.settings.get("last_ph", 8.2)))
        self.vol_var = tk.StringVar(value="") 
        
        self.notebook = ttk.Notebook(root)
        self.calc_tab = ttk.Frame(self.notebook); self.maint_tab = ttk.Frame(self.notebook); self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.calc_tab, text=" Dosage "); self.notebook.add(self.maint_tab, text=" Maintenance "); self.notebook.add(self.log_tab, text=" History ")
        self.notebook.pack(expand=1, fill="both")
        
        self.build_calc_tab(); self.build_maint_tab(); self.build_log_tab()
        self.update_param_selection()

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, "r") as f: self.settings = json.load(f)
        except: self.settings = {"last_ph": 8.2}

    def build_calc_tab(self):
        f = ttk.Frame(self.calc_tab, padding="20"); f.pack(fill="both", expand=True)
        
        # --- TOP SECTION: MANDATORY VOLUME ---
        top_frame = tk.LabelFrame(f, text=" REQUIRED: TANK CONFIGURATION ", padx=10, pady=10, fg="red")
        top_frame.grid(row=0, columnspan=3, sticky="ew", pady=(0, 20))
        
        tk.Label(top_frame, text="Tank Volume (Gallons):", font=("Arial", 10, "bold")).grid(row=0, column=0)
        self.vol_ent = tk.Entry(top_frame, textvariable=self.vol_var, width=12, bg="#ffffcc", font=("Arial", 12, "bold"))
        self.vol_ent.grid(row=0, column=1, padx=5)
        
        tk.Label(top_frame, text="Current pH:", font=("Arial", 10)).grid(row=0, column=2, padx=(20, 5))
        tk.Label(top_frame, textvariable=self.live_ph, fg="#c0392b", font=("Arial", 14, "bold")).grid(row=0, column=3)

        # --- INPUTS ---
        self.p_var = tk.StringVar(value="Alkalinity"); self.u_var = tk.StringVar(); self.b_var = tk.StringVar()

        tk.Label(f, text="Select Parameter:").grid(row=2, column=0, sticky="w")
        self.p_menu = ttk.Combobox(f, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly")
        self.p_menu.grid(row=2, column=1, pady=5, sticky="ew")
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)

        tk.Label(f, text="Unit Type:").grid(row=3, column=0, sticky="w")
        self.u_menu = ttk.Combobox(f, textvariable=self.u_var, state="readonly")
        self.u_menu.grid(row=3, column=1, pady=5, sticky="ew")
        self.u_menu.bind("<<ComboboxSelected>>", self.sync_target_to_unit)

        tk.Label(f, text="Current Reading:").grid(row=4, column=0, sticky="w")
        self.curr_ent = tk.Entry(f); self.curr_ent.grid(row=4, column=1, pady=5, sticky="ew")
        
        tk.Label(f, text="Target Goal:").grid(row=5, column=0, sticky="w")
        self.targ_ent = tk.Entry(f); self.targ_ent.grid(row=5, column=1, pady=5, sticky="ew")

        tk.Label(f, text="Brand/Product:").grid(row=6, column=0, sticky="w")
        self.b_menu = ttk.Combobox(f, textvariable=self.b_var, state="readonly")
        self.b_menu.grid(row=6, column=1, pady=5, sticky="ew")

        tk.Button(f, text="CALCULATE DOSAGE", command=self.perform_calc, bg="#27ae60", fg="white", font=("Arial", 11, "bold")).grid(row=8, columnspan=3, pady=20, sticky="ew")
        
        self.res_lbl = tk.Label(f, text="--- SYSTEM READY ---", font=("Consolas", 11, "bold"), wraplength=450, justify="center")
        self.res_lbl.grid(row=9, columnspan=3)

    def build_maint_tab(self):
        f = ttk.Frame(self.maint_tab, padding="20"); f.pack(fill="both")
        tk.Label(f, text="LOG TEST RESULTS", font=("Arial", 12, "bold")).pack(pady=10)
        grid = ttk.Frame(f); grid.pack()
        params = [("Alkalinity", "m_alk"), ("Calcium", "m_cal"), ("Magnesium", "m_mag")]
        self.maint_inputs = {}
        for i, (label, attr) in enumerate(params):
            tk.Label(grid, text=f"{label}:").grid(row=i, column=0, pady=2)
            ent = tk.Entry(grid); ent.grid(row=i, column=1); self.maint_inputs[attr] = ent
        
        tk.Label(grid, text="pH Value:").grid(row=3, column=0, pady=2)
        tk.Entry(grid, textvariable=self.live_ph).grid(row=3, column=1)
        tk.Button(f, text="SAVE LOG (AUTO-TIMESTAMP)", command=self.save_maint, bg="#8e44ad", fg="white").pack(pady=15)

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        units = self.ranges[p]["units"]
        self.u_menu.config(values=units); self.u_menu.current(0)
        self.b_menu.config(values=list(self.ranges[p]["brands"].keys())); self.b_menu.current(0)
        self.sync_target_to_unit()

    def sync_target_to_unit(self, e=None):
        p, u = self.p_var.get(), self.u_var.get()
        base_targ = self.ranges[p]["target"]
        if p == "Alkalinity" and u == "ppm":
            base_targ = round(base_targ * 17.86, 1)
        self.targ_ent.delete(0, tk.END); self.targ_ent.insert(0, str(base_targ))

    def perform_calc(self):
        if not self.vol_var.get():
            messagebox.showerror("Safety Error", "Volume is REQUIRED for dosage calculation.")
            return
        try:
            p, u, vol = self.p_var.get(), self.u_var.get(), float(self.vol_var.get())
            curr, targ = float(self.curr_ent.get()), float(self.targ_ent.get())
            strength = self.ranges[p]["brands"][self.b_var.get()]
            
            # Internal conversion for math
            if p == "Alkalinity" and u == "ppm": strength *= 17.86
            
            diff = targ - curr
            if diff <= 0:
                self.res_lbl.config(text="STATUS: OPTIMAL. No dose required.", fg="green")
                return
            
            total_ml = (diff * vol) / strength
            limit = self.safety_limits[p]
            if p == "Alkalinity" and u == "ppm": limit *= 17.86
            
            days = max(1, int(diff / limit) + (1 if diff % limit > 0 else 0))
            ph_val = float(self.live_ph.get())
            if ph_val >= 8.45: days = max(days, 6)
            
            risk = "LOW" if days == 1 else "MEDIUM"
            if ph_val >= 8.5: risk = "HIGH (pH SPIKE)"
            
            msg = f"RISK LEVEL: {risk}\nTOTAL: {total_ml:.1f} mL\nDAILY: {total_ml/days:.1f} mL over {days} days"
            self.res_lbl.config(text=msg, fg="#c0392b" if risk != "LOW" else "#2980b9")
        except: messagebox.showerror("Error", "Check numeric inputs.")

    def save_maint(self):
        d = datetime.now().strftime("%Y-%m-%d %H:%M")
        logged = False
        for attr, ent in self.maint_inputs.items():
            if ent.get():
                self.save_to_csv(d, "Test", attr.split('_')[1].capitalize(), ent.get()); logged = True
        if logged:
            messagebox.showinfo("Success", "Logged."); [e.delete(0, tk.END) for e in self.maint_inputs.values()]

    def save_to_csv(self, date, type, param, val):
        with open(LOG_FILE, "a", newline='') as f: csv.writer(f).writerow([date, type, param, val])
        self.refresh_logs()

    def build_log_tab(self):
        f = ttk.Frame(self.log_tab, padding="20"); f.pack(fill="both", expand=True)
        self.txt = tk.Text(f, height=20, state="disabled", font=("Consolas", 10)); self.txt.pack(fill="both", expand=True)
        tk.Button(f, text="REFRESH", command=self.refresh_logs).pack(pady=5); self.refresh_logs()

    def refresh_logs(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                content = f.read(); self.txt.config(state="normal")
                self.txt.delete("1.0", tk.END); self.txt.insert(tk.END, content); self.txt.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
