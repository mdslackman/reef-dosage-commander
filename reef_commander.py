import tkinter as tk
from tkinter import ttk, messagebox
import csv, os, sys
from datetime import datetime

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.14.1")
        
        # UI LOCKDOWN
        self.root.geometry("900x850")
        self.root.resizable(False, False) 
        self.root.protocol("WM_DELETE_WINDOW", self.hard_exit)
        
        self.log_file = "reef_logs.csv"
        self.init_csv()

        # Product Data
        self.brand_data = {
            "ESV B-Ionic Alk (Part 1)": 1.4,
            "Fritz RPM Liquid Alk": 1.4,
            "ESV B-Ionic Cal (Part 2)": 20.0,
            "Fritz RPM Liquid Cal": 20.0,
            "Fritz RPM Liquid Mag": 100.0
        }
        
        self.ranges = {
            "Alkalinity": {"units": ["dKH", "ppm"], "target": 8.5, "brands": ["ESV B-Ionic Alk (Part 1)", "Fritz RPM Liquid Alk"]},
            "Calcium": {"units": ["ppm"], "target": 420, "brands": ["ESV B-Ionic Cal (Part 2)", "Fritz RPM Liquid Cal"]},
            "Magnesium": {"units": ["ppm"], "target": 1350, "brands": ["Fritz RPM Liquid Mag"]}
        }

        # Variables
        self.vol_var = tk.StringVar()
        self.p_var = tk.StringVar(value="Alkalinity")
        self.u_var = tk.StringVar()
        self.b_var = tk.StringVar()
        self.curr_val_var = tk.StringVar()
        self.targ_val_var = tk.StringVar()
        self.custom_strength = tk.StringVar()
        
        # Traces for Auto-Switching
        self.curr_val_var.trace_add("write", self.handle_unit_auto_switch)
        self.u_var.trace_add("write", self.sync_target_unit)
        
        # UI Structure
        self.notebook = ttk.Notebook(root)
        self.tabs = {name: ttk.Frame(self.notebook) for name in ["Dosage", "Maintenance", "History", "Mix Guide"]}
        for name, frame in self.tabs.items(): 
            self.notebook.add(frame, text=f" {name} ")
        self.notebook.pack(expand=True, fill="both")
        
        self.build_dosage()
        self.build_maint()
        self.build_history()
        self.build_mix()
        self.update_param_selection()

    def init_csv(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="") as f:
                csv.writer(f).writerow(["Timestamp", "Parameter", "Value"])

    def handle_unit_auto_switch(self, *args):
        try:
            val = float(self.curr_val_var.get())
            # If user types > 25, they clearly mean PPM
            if self.p_var.get() == "Alkalinity" and self.u_var.get() == "dKH" and val > 25:
                self.u_var.set("ppm")
        except: pass

    def sync_target_unit(self, *args):
        p = self.p_var.get()
        u = self.u_var.get()
        base_target = self.ranges[p]["target"]
        if p == "Alkalinity" and u == "ppm":
            self.targ_val_var.set(str(round(base_target * 17.86)))
        else:
            self.targ_val_var.set(str(base_target))

    def build_dosage(self):
        f = ttk.Frame(self.tabs["Dosage"], padding="30")
        f.pack(fill="both", expand=True)
        
        # Grid Configuration for full-width fields
        f.columnconfigure(1, weight=1)
        l_font, e_font = ("Arial", 14, "bold"), ("Arial", 14)

        # 1. Volume
        tk.Label(f, text="Tank Volume (Gal):", font=l_font).grid(row=0, column=0, sticky="w", pady=10)
        tk.Entry(f, textvariable=self.vol_var, font=e_font, bg="#ffffcc").grid(row=0, column=1, sticky="ew")

        # 2. Category Dropdown
        tk.Label(f, text="Category:", font=l_font).grid(row=1, column=0, sticky="w", pady=10)
        self.p_menu = ttk.Combobox(f, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly", font=e_font)
        self.p_menu.grid(row=1, column=1, sticky="ew")
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)

        # 3. Unit Dropdown
        tk.Label(f, text="Unit:", font=l_font).grid(row=2, column=0, sticky="w", pady=10)
        self.u_menu = ttk.Combobox(f, textvariable=self.u_var, state="readonly", font=e_font)
        self.u_menu.grid(row=2, column=1, sticky="ew")

        # 4. Product Dropdown
        tk.Label(f, text="Product:", font=l_font).grid(row=3, column=0, sticky="w", pady=10)
        self.b_menu = ttk.Combobox(f, textvariable=self.b_var, state="readonly", font=e_font)
        self.b_menu.grid(row=3, column=1, sticky="ew")

        # 5. Current Reading
        tk.Label(f, text="Current Reading:", font=l_font).grid(row=4, column=0, sticky="w", pady=10)
        tk.Entry(f, textvariable=self.curr_val_var, font=e_font).grid(row=4, column=1, sticky="ew")

        # 6. Target Goal
        tk.Label(f, text="Target Goal:", font=l_font).grid(row=5, column=0, sticky="w", pady=10)
        tk.Entry(f, textvariable=self.targ_val_var, font=e_font).grid(row=5, column=1, sticky="ew")

        # 7. Custom Strength
        tk.Label(f, text="Custom Strength (Opt):", font=("Arial", 10)).grid(row=6, column=0, sticky="w", pady=5)
        tk.Entry(f, textvariable=self.custom_strength, font=("Arial", 10)).grid(row=6, column=1, sticky="w")

        # 8. Calculate Button
        tk.Button(f, text="CALCULATE DOSAGE", command=self.perform_calc, bg="#2c3e50", fg="white", font=("Arial", 14, "bold"), height=2).grid(row=7, columnspan=2, pady=25, sticky="ew")
        
        # 9. Results Area
        self.res_lbl = tk.Label(f, text="---", font=("Arial", 18, "bold"), fg="#2980b9", wraplength=700)
        self.res_lbl.grid(row=8, columnspan=2, pady=10)

    def perform_calc(self):
        try:
            p = self.p_var.get()
            vol = float(self.vol_var.get())
            unit = self.u_var.get()
            curr = float(self.curr_val_var.get())
            targ = float(self.targ_val_var.get())
            
            # Standardization math
            std_curr = curr / 17.86 if (p == "Alkalinity" and unit == "ppm") else curr
            std_targ = targ / 17.86 if (p == "Alkalinity" and unit == "ppm") else targ

            # Strength logic
            if self.custom_strength.get():
                strength = float(self.custom_strength.get())
            else:
                strength = self.brand_data.get(self.b_var.get(), 1.0)

            diff = std_targ - std_curr
            if diff <= 0:
                self.res_lbl.config(text="STATUS: OPTIMAL", fg="green")
            else:
                total_ml = (diff * vol) / strength
                self.res_lbl.config(text=f"DOSE: {total_ml:.1f} mL Total", fg="#c0392b")
        except Exception as e:
            self.res_lbl.config(text=f"ERROR: Check Numbers", fg="red")

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu['values'] = self.ranges[p]["units"]
        self.u_menu.current(0)
        self.b_menu['values'] = self.ranges[p]["brands"]
        self.b_menu.current(0)
        self.sync_target_unit()

    def build_maint(self):
        f = ttk.Frame(self.tabs["Maintenance"], padding="50"); f.pack(fill="both")
        self.m_entries = {}
        for i, p in enumerate(["Alkalinity", "Calcium", "Magnesium"]):
            tk.Label(f, text=f"{p}:", font=("Arial", 14)).grid(row=i, column=0, pady=15, sticky="w")
            e = tk.Entry(f, font=("Arial", 14)); e.grid(row=i, column=1, padx=20, sticky="ew")
            self.m_entries[p] = e
        tk.Button(f, text="LOG DATA", command=self.save_data, bg="#27ae60", fg="white", font=("Arial", 14, "bold")).grid(row=4, columnspan=2, pady=40, sticky="ew")

    def save_data(self):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            with open(self.log_file, "a", newline="") as f:
                writer = csv.writer(f)
                for p, ent in self.m_entries.items():
                    if ent.get(): writer.writerow([ts, p, ent.get()])
            messagebox.showinfo("Success", "Data Saved.")
            self.refresh_hist()
        except: messagebox.showerror("Error", "Save Failed.")

    def build_history(self):
        f = self.tabs["History"]
        self.hist_txt = tk.Text(f, font=("Courier New", 12)); self.hist_txt.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Button(f, text="REFRESH", command=self.refresh_hist).pack(pady=10)

    def refresh_hist(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                self.hist_txt.delete("1.0", tk.END); self.hist_txt.insert(tk.END, f.read())

    def build_mix(self):
        f = self.tabs["Mix Guide"]
        tk.Label(f, text="MIXING RECIPES (1 GAL)\nAlk: 2 Cups Soda Ash\nCal: 2.5 Cups Calcium Chloride", font=("Arial", 16, "bold")).pack(pady=100)

    def hard_exit(self):
        self.root.destroy()
        os._exit(0)

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
