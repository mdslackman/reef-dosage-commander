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
        self.root.title("Aquarium Commander Pro v0.11.5 - pH Guardian")
        self.root.geometry("850x950")
        
        self.safety_limits = {"Alkalinity": 1.4, "Calcium": 20.0, "Magnesium": 100.0}
        self.load_settings()
        
        self.ranges = {
            "Alkalinity": {
                "units": ["dKH", "ppm"], "target": 8.5,
                "brands": {"Fritz RPM Liquid Alkalinity": 0.6, "ESV B-Ionic Alk (Part 1)": 1.9}
            },
            "Calcium": {
                "units": ["ppm"], "target": 420,
                "brands": {"Fritz RPM Liquid Calcium": 15.0, "ESV B-Ionic Cal (Part 2)": 16.0}
            },
            "Magnesium": {
                "units": ["ppm"], "target": 1350,
                "brands": {"Fritz RPM Liquid Magnesium": 18.0}
            }
        }

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
        
        # --- THE PH METER (Top of UI) ---
        self.ph_frame = tk.Frame(f, bg="#2c3e50", pady=5)
        self.ph_frame.grid(row=0, columnspan=3, sticky="ew", pady=(0, 15))
        self.ph_disp = tk.Label(self.ph_frame, text=f"CURRENT pH: {self.settings.get('last_ph', 'N/A')}", 
                                fg="#f1c40f", bg="#2c3e50", font=("Arial", 12, "bold"))
        self.ph_disp.pack()

        tk.Label(f, text=f"Tank: {self.settings['tank_name']} ({self.settings['volume']} Gal)", font=("Arial", 10, "bold")).grid(row=1, columnspan=3, pady=5)
        
        self.p_var = tk.StringVar(value="Alkalinity"); self.u_var = tk.StringVar(value="dKH")
        self.b_var = tk.StringVar(value="Fritz RPM Liquid Alkalinity")
        self.dyn_u = tk.StringVar(value="dKH")

        # Inputs
        tk.Label(f, text="Parameter:").grid(row=2, column=0, sticky="w")
        self.p_menu = ttk.Combobox(f, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly")
        self.p_menu.grid(row=2, column=1, pady=5, sticky="ew")
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)

        tk.Label(f, text="Unit:").grid(row=3, column=0, sticky="w")
        self.u_menu = ttk.Combobox(f, textvariable=self.u_var, state="readonly")
        self.u_menu.grid(row=3, column=1, pady=5, sticky="ew")
        self.u_menu.bind("<<ComboboxSelected>>", self.sync_all)

        tk.Label(f, text="Current Level:").grid(row=4, column=0, sticky="w")
        self.curr_ent = tk.Entry(f); self.curr_ent.grid(row=4, column=1, pady=5, sticky="ew")
        tk.Label(f, textvariable=self.dyn_u).grid(row=4, column=2)

        tk.Label(f, text="Target Level:").grid(row=5, column=0, sticky="w")
        self.targ_ent = tk.Entry(f); self.targ_ent.grid(row=5, column=1, pady=5, sticky="ew")
        tk.Label(f, textvariable=self.dyn_u).grid(row=5, column=2)

        # --- OPTIONAL PH INPUT ---
        tk.Label(f, text="Current pH:").grid(row=6, column=0, sticky="w")
        self.ph_ent = tk.Entry(f); self.ph_ent.grid(row=6, column=1, pady=5, sticky="ew")
        tk.Label(f, text="(Optional)").grid(row=6, column=2)

        tk.Label(f, text="Product:").grid(row=7, column=0, sticky="w")
        self.b_menu = ttk.Combobox(f, textvariable=self.b_var, state="readonly")
        self.b_menu.grid(row=7, column=1, pady=5, sticky="ew")

        self.calc_btn = tk.Button(f, text="CALCULATE", command=self.perform_calc, bg="#2980b9", fg="white", font=("Arial", 10, "bold"))
        self.calc_btn.grid(row=8, column=0, columnspan=3, pady=20, sticky="ew")
        self.res_lbl = tk.Label(f, text="", font=("Consolas", 11, "bold"), wraplength=450); self.res_lbl.grid(row=9, columnspan=3)

    def build_maint_tab(self):
        f = ttk.Frame(self.maint_tab, padding="20"); f.pack(fill="both")
        tk.Label(f, text="Tank Settings & Monitoring", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(f, text="Volume (Gallons):").pack()
        self.vol_ent = tk.Entry(f); self.vol_ent.insert(0, str(self.settings["volume"])); self.vol_ent.pack()
        tk.Label(f, text="Latest pH:").pack()
        self.m_ph = tk.Entry(f); self.m_ph.insert(0, str(self.settings.get("last_ph", 8.2))); self.m_ph.pack()
        tk.Button(f, text="SAVE SETTINGS", command=self.save_settings, bg="#27ae60", fg="white").pack(pady=20)

    def save_settings(self):
        self.settings["volume"] = float(self.vol_ent.get())
        self.settings["last_ph"] = float(self.m_ph.get())
        with open(SETTINGS_FILE, "w") as f: json.dump(self.settings, f)
        self.ph_disp.config(text=f"CURRENT pH: {self.settings['last_ph']}")
        messagebox.showinfo("Success", "Settings Updated.")

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu.config(values=self.ranges[p]["units"]); self.u_menu.set(self.ranges[p]["units"][0])
        self.b_menu.config(values=list(self.ranges[p]["brands"].keys())); self.b_menu.current(0)
        self.sync_all()

    def sync_all(self, e=None):
        p, u = self.p_var.get(), self.u_var.get(); self.dyn_u.set(u)
        t = self.ranges[p]["target"]
        if p == "Alkalinity" and u == "ppm": t = round(t * 17.86, 1)
        self.targ_ent.delete(0, tk.END); self.targ_ent.insert(0, str(t))

    def perform_calc(self):
        try:
            p, u, vol = self.p_var.get(), self.u_var.get(), float(self.settings["volume"])
            curr, targ = float(self.curr_ent.get()), float(self.targ_ent.get())
            strength = self.ranges[p]["brands"][self.b_var.get()]
            
            if p == "Alkalinity" and u == "ppm" and strength < 2.0: strength *= 17.86
            
            total_ml = ((targ - curr) * vol) / strength
            limit = self.safety_limits[p]
            if p == "Alkalinity" and u == "ppm": limit *= 17.86
            
            days = max(1, int((targ-curr) / limit) + (1 if (targ-curr) % limit > 0 else 0))
            
            # --- pH SAFETY FLAG ---
            ph_val = float(self.ph_ent.get()) if self.ph_ent.get() else self.settings.get("last_ph", 8.2)
            ph_warning = ""
            if ph_val >= 8.45:
                days = max(days, 6) # Force at least a 6-day spread if pH is high
                ph_warning = f"\n\n⚠️ HIGH pH DETECTED ({ph_val})\nDose reduced to prevent precipitation."

            msg = f"TOTAL: {total_ml:.1f} mL\nDaily: {total_ml/days:.1f} mL ({days} days){ph_warning}"
            self.res_lbl.config(text=msg, fg="#c0392b" if ph_val >= 8.45 or days > 1 else "#2980b9")
        except: messagebox.showerror("Error", "Check numeric inputs.")

    def build_log_tab(self):
        f = ttk.Frame(self.log_tab, padding="20"); f.pack(fill="both", expand=True)
        self.txt = tk.Text(f, height=20, state="disabled"); self.txt.pack(fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
