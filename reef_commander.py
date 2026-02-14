import tkinter as tk
from tkinter import ttk, messagebox
import csv, os, sys
from datetime import datetime

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.14.2")
        
        # --- UI LOCKDOWN ---
        self.root.geometry("900x850")
        self.root.resizable(False, False) 
        self.root.protocol("WM_DELETE_WINDOW", self.hard_exit)
        
        self.log_file = "reef_logs.csv"
        self.init_csv()

        # Data
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

        # Vars
        self.vol_var = tk.StringVar()
        self.p_var = tk.StringVar(value="Alkalinity")
        self.u_var = tk.StringVar()
        self.b_var = tk.StringVar()
        self.curr_val_var = tk.StringVar()
        self.targ_val_var = tk.StringVar()
        self.custom_strength = tk.StringVar()
        
        # Traces
        self.curr_val_var.trace_add("write", self.handle_unit_auto_switch)
        self.u_var.trace_add("write", self.sync_target_unit)
        
        self.notebook = ttk.Notebook(root)
        self.tabs = {name: ttk.Frame(self.notebook) for name in ["Dosage", "Maintenance", "History", "Mix Guide"]}
        for name, frame in self.tabs.items(): self.notebook.add(frame, text=f" {name} ")
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
            if self.p_var.get() == "Alkalinity" and self.u_var.get() == "dKH" and val > 25:
                self.u_var.set("ppm")
        except: pass

    def sync_target_unit(self, *args):
        p, u = self.p_var.get(), self.u_var.get()
        base = self.ranges[p]["target"]
        if p == "Alkalinity" and u == "ppm":
            self.targ_val_var.set(str(round(base * 17.86)))
        else:
            self.targ_val_var.set(str(base))

    def build_dosage(self):
        # Using pack() with padding to force visibility of every row
        container = ttk.Frame(self.tabs["Dosage"], padding="30")
        container.pack(fill="both", expand=True)

        font_l = ("Arial", 13, "bold")
        font_e = ("Arial", 13)

        # Helper to create rows quickly and ensure they are packed
        def make_row(label_text, variable, is_combo=False, combo_vals=None):
            row = ttk.Frame(container)
            row.pack(fill="x", pady=8)
            tk.Label(row, text=label_text, font=font_l, width=20, anchor="w").pack(side="left")
            if is_combo:
                cb = ttk.Combobox(row, textvariable=variable, values=combo_vals, state="readonly", font=font_e)
                cb.pack(side="right", expand=True, fill="x")
                return cb
            else:
                tk.Entry(row, textvariable=variable, font=font_e).pack(side="right", expand=True, fill="x")
                return None

        make_row("Tank Volume (Gal):", self.vol_var)
        self.p_menu = make_row("Category:", self.p_var, True, list(self.ranges.keys()))
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)
        
        self.u_menu = make_row("Unit:", self.u_var, True)
        self.b_menu = make_row("Product:", self.b_var, True)
        
        make_row("Current Reading:", self.curr_val_var)
        make_row("Target Goal:", self.targ_val_var)
        make_row("Custom Strength (Opt):", self.custom_strength)

        btn = tk.Button(container, text="CALCULATE DOSAGE", command=self.perform_calc, bg="#2c3e50", fg="white", font=("Arial", 14, "bold"), pady=10)
        btn.pack(fill="x", pady=20)
        
        self.res_lbl = tk.Label(container, text="---", font=("Arial", 16, "bold"), fg="#2980b9", wraplength=700)
        self.res_lbl.pack(pady=10)

    def perform_calc(self):
        try:
            p, vol, unit = self.p_var.get(), float(self.vol_var.get()), self.u_var.get()
            curr, targ = float(self.curr_val_var.get()), float(self.targ_val_var.get())
            
            # Standardization
            std_curr = curr / 17.86 if (p == "Alkalinity" and unit == "ppm") else curr
            std_targ = targ / 17.86 if (p == "Alkalinity" and unit == "ppm") else targ

            strength = float(self.custom_strength.get()) if self.custom_strength.get() else self.brand_data.get(self.b_var.get(), 1.0)

            diff = std_targ - std_curr
            if diff <= 0.001: # Use small float instead of 0 to avoid precision errors
                self.res_lbl.config(text="STATUS: OPTIMAL", fg="green")
            else:
                total_ml = (diff * vol) / strength
                self.res_lbl.config(text=f"DOSE: {total_ml:.1f} mL Total", fg="#c0392b")
        except:
            self.res_lbl.config(text="ERROR: Check Numbers", fg="red")

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
        for p in ["Alkalinity", "Calcium", "Magnesium"]:
            row = ttk.Frame(f); row.pack(fill="x", pady=10)
            tk.Label(row, text=f"{p}:", font=("Arial", 14), width=15, anchor="w").pack(side="left")
            e = tk.Entry(row, font=("Arial", 14)); e.pack(side="right", expand=True, fill="x")
            self.m_entries[p] = e
        tk.Button(f, text="LOG DATA", command=self.save_data, bg="#27ae60", fg="white", font=("Arial", 14, "bold"), pady=10).pack(fill="x", pady=20)

    def save_data(self):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            with open(self.log_file, "a", newline="") as f:
                writer = csv.writer(f)
                for p, ent in self.m_entries.items():
                    if ent.get(): writer.writerow([ts, p, ent.get()])
            messagebox.showinfo("Success", "Logs updated.")
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
        tk.Label(f, text="BULK MIXING (1 GAL)\nAlk: 2 Cups Soda Ash\nCal: 2.5 Cups Calcium Chloride", font=("Arial", 16, "bold"), pady=100).pack()

    def hard_exit(self):
        self.root.destroy()
        os._exit(0)

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
