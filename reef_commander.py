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
        self.root.title("Aquarium Commander Pro v0.11.7")
        self.root.geometry("850x950")
        
        self.safety_limits = {"Alkalinity": 1.4, "Calcium": 20.0, "Magnesium": 100.0}
        self.load_settings()
        
        self.ranges = {
            "Alkalinity": {
                "units": ["dKH", "ppm"], "target": 8.5,
                "brands": {"Fritz RPM Liquid Alkalinity": 0.6, "ESV B-Ionic Alk (Part 1)": 1.9}
            },
            "Calcium": {"units": ["ppm"], "target": 420, "brands": {"Fritz RPM Liquid Calcium": 15.0}},
            "Magnesium": {"units": ["ppm"], "target": 1350, "brands": {"Fritz RPM Liquid Magnesium": 18.0}}
        }

        self.live_ph = tk.StringVar(value=str(self.settings.get("last_ph", 8.2)))
        
        self.notebook = ttk.Notebook(root)
        self.calc_tab = ttk.Frame(self.notebook)
        self.maint_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.calc_tab, text=" Dosage ")
        self.notebook.add(self.maint_tab, text=" Maintenance ")
        self.notebook.add(self.log_tab, text=" History ")
        self.notebook.pack(expand=1, fill="both")
        
        self.build_calc_tab()
        self.build_maint_tab()
        self.build_log_tab()
        self.update_param_selection()

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, "r") as f: self.settings = json.load(f)
        except: self.settings = {"tank_name": "My Reef", "volume": 220.0, "last_ph": 8.2}

    def build_calc_tab(self):
        f = ttk.Frame(self.calc_tab, padding="20"); f.pack(fill="both", expand=True)
        
        ph_frame = tk.Frame(f, bg="#2c3e50", pady=10)
        ph_frame.grid(row=0, columnspan=3, sticky="ew", pady=(0, 20))
        tk.Label(ph_frame, text="LIVE SYSTEM pH", fg="white", bg="#2c3e50", font=("Arial", 10)).pack()
        tk.Label(ph_frame, textvariable=self.live_ph, fg="#f1c40f", bg="#2c3e50", font=("Arial", 28, "bold")).pack()

        self.p_var = tk.StringVar(value="Alkalinity")
        self.b_var = tk.StringVar()

        tk.Label(f, text="Parameter:").grid(row=2, column=0, sticky="w")
        self.p_menu = ttk.Combobox(f, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly")
        self.p_menu.grid(row=2, column=1, pady=5, sticky="ew")
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)

        tk.Label(f, text="Current Level:").grid(row=3, column=0, sticky="w")
        self.curr_ent = tk.Entry(f); self.curr_ent.grid(row=3, column=1, pady=5, sticky="ew")
        
        tk.Label(f, text="Target Level:").grid(row=4, column=0, sticky="w")
        self.targ_ent = tk.Entry(f); self.targ_ent.grid(row=4, column=1, pady=5, sticky="ew")

        tk.Label(f, text="Current pH:").grid(row=5, column=0, sticky="w")
        self.ph_ent = tk.Entry(f, textvariable=self.live_ph); self.ph_ent.grid(row=5, column=1, pady=5, sticky="ew")

        tk.Label(f, text="Product:").grid(row=6, column=0, sticky="w")
        self.b_menu = ttk.Combobox(f, textvariable=self.b_var, state="readonly")
        self.b_menu.grid(row=6, column=1, pady=5, sticky="ew")

        tk.Button(f, text="CALCULATE", command=self.perform_calc, bg="#2980b9", fg="white", font=("Arial", 10, "bold")).grid(row=7, columnspan=3, pady=20, sticky="ew")
        self.res_lbl = tk.Label(f, text="", font=("Consolas", 11, "bold"), wraplength=450, justify="center"); self.res_lbl.grid(row=8, columnspan=3)

    def build_maint_tab(self):
        f = ttk.Frame(self.maint_tab, padding="20"); f.pack(fill="both")
        tk.Label(f, text="LOG TEST RESULTS", font=("Arial", 12, "bold")).pack(pady=10)
        
        grid = ttk.Frame(f); grid.pack()
        tk.Label(grid, text="Alkalinity:").grid(row=0, column=0, pady=2)
        self.m_alk = tk.Entry(grid); self.m_alk.grid(row=0, column=1)
        tk.Label(grid, text="Calcium:").grid(row=1, column=0, pady=2)
        self.m_cal = tk.Entry(grid); self.m_cal.grid(row=1, column=1)
        tk.Label(grid, text="Magnesium:").grid(row=2, column=0, pady=2)
        self.m_mag = tk.Entry(grid); self.m_mag.grid(row=2, column=1)
        tk.Label(grid, text="pH Value:").grid(row=3, column=0, pady=2)
        self.m_ph_log = tk.Entry(grid, textvariable=self.live_ph); self.m_ph_log.grid(row=3, column=1)
        
        tk.Button(f, text="SAVE TO HISTORY", command=self.save_maint, bg="#8e44ad", fg="white", font=("Arial", 10, "bold")).pack(pady=15)
        
        # FIXED: Changed tk.Separator to ttk.Separator
        ttk.Separator(f, orient='horizontal').pack(fill='x', pady=10)
        
        tk.Label(f, text="TANK SETTINGS", font=("Arial", 10, "bold")).pack(pady=5)
        tk.Label(f, text="Volume (Gal):").pack()
        self.vol_ent = tk.Entry(f); self.vol_ent.insert(0, str(self.settings["volume"])); self.vol_ent.pack()
        tk.Button(f, text="UPDATE VOLUME", command=self.save_settings, bg="#27ae60", fg="white").pack(pady=5)

    def save_maint(self):
        d = datetime.now().strftime("%Y-%m-%d %H:%M")
        logged = False
        data = {"Alk": self.m_alk.get(), "Cal": self.m_cal.get(), "Mag": self.m_mag.get(), "pH": self.live_ph.get()}
        
        for name, val in data.items():
            if val:
                self.save_to_csv(d, "Test", name, val)
                logged = True
        
        if logged:
            messagebox.showinfo("Success", "Parameters logged.")
            for ent in [self.m_alk, self.m_cal, self.m_mag]: ent.delete(0, tk.END)

    def save_settings(self):
        try:
            self.settings["volume"] = float(self.vol_ent.get())
            self.settings["last_ph"] = float(self.live_ph.get())
            with open(SETTINGS_FILE, "w") as f: json.dump(self.settings, f)
            messagebox.showinfo("Success", "Settings updated.")
        except: messagebox.showerror("Error", "Invalid volume.")

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.b_menu.config(values=list(self.ranges[p]["brands"].keys())); self.b_menu.current(0)
        t = self.ranges[p]["target"]
        self.targ_ent.delete(0, tk.END); self.targ_ent.insert(0, str(t))

    def perform_calc(self):
        try:
            p, vol = self.p_var.get(), float(self.settings["volume"])
            curr, targ = float(self.curr_ent.get()), float(self.targ_ent.get())
            strength = self.ranges[p]["brands"][self.b_var.get()]
            
            # Auto-detect PPM for Alkalinity
            is_ppm = False
            if p == "Alkalinity" and curr > 20:
                strength *= 17.86
                is_ppm = True
            
            diff = targ - curr
            if diff <= 0: self.res_lbl.config(text="Status: Optimal.", fg="green"); return
            
            total_ml = (diff * vol) / strength
            limit = self.safety_limits[p]
            if is_ppm: limit *= 17.86
            
            days = max(1, int(diff / limit) + (1 if diff % limit > 0 else 0))
            
            ph_val = float(self.live_ph.get())
            if ph_val >= 8.45: days = max(days, 6)
            
            msg = f"TOTAL DOSE: {total_ml:.1f} mL\nDaily: {total_ml/days:.1f} mL over {days} days"
            if ph_val >= 8.45: msg += f"\n\n⚠️ HIGH pH DETECTED: {ph_val}\nSlowing dose to protect system."
            
            self.res_lbl.config(text=msg, fg="#c0392b" if ph_val >= 8.45 or days > 1 else "#2980b9")
        except: messagebox.showerror("Error", "Invalid numeric values.")

    def save_to_csv(self, date, type, param, val):
        with open(LOG_FILE, "a", newline='') as f:
            csv.writer(f).writerow([date, type, param, val])
        self.refresh_logs()

    def build_log_tab(self):
        f = ttk.Frame(self.log_tab, padding="20"); f.pack(fill="both", expand=True)
        self.txt = tk.Text(f, height=20, state="disabled", font=("Consolas", 10))
        self.txt.pack(fill="both", expand=True)
        tk.Button(f, text="REFRESH HISTORY", command=self.refresh_logs).pack(pady=5)
        self.refresh_logs()

    def refresh_logs(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                content = f.read()
                self.txt.config(state="normal"); self.txt.delete("1.0", tk.END)
                self.txt.insert(tk.END, content); self.txt.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
