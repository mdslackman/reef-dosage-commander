import tkinter as tk
from tkinter import ttk, messagebox
import csv, os, sys
from datetime import datetime

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.13.9")
        
        # --- UI LOCKDOWN ---
        self.root.geometry("900x800")
        self.root.resizable(False, False) 
        
        # Hard Kill Process on Exit
        self.root.protocol("WM_DELETE_WINDOW", self.hard_exit)
        
        self.log_file = "reef_logs.csv"
        self.init_csv()

        # Data & Constants
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

        # Variables with Traces for Auto-Switching
        self.vol_var = tk.StringVar()
        self.p_var = tk.StringVar(value="Alkalinity")
        self.u_var = tk.StringVar()
        self.b_var = tk.StringVar()
        self.curr_val_var = tk.StringVar()
        
        # TRACE: Watch the current reading for high values
        self.curr_val_var.trace_add("write", self.handle_unit_auto_switch)
        
        # UI Layout
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
        """Auto-flips from dKH to ppm if value > 25."""
        try:
            val = float(self.curr_val_var.get())
            if self.p_var.get() == "Alkalinity" and self.u_var.get() == "dKH" and val > 25:
                self.u_var.set("ppm")
        except ValueError:
            pass

    def build_dosage(self):
        # Using a main frame that fills the tab space
        f = ttk.Frame(self.tabs["Dosage"], padding="50")
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1) # Allow column 1 to expand

        # Styling for larger text
        lbl_font = ("Arial", 14, "bold")
        ent_font = ("Arial", 14)

        tk.Label(f, text="Tank Volume (Gal):", font=lbl_font).grid(row=0, column=0, sticky="w", pady=15)
        tk.Entry(f, textvariable=self.vol_var, font=ent_font, bg="#ffffcc").grid(row=0, column=1, sticky="ew")

        tk.Label(f, text="Parameter:", font=lbl_font).grid(row=1, column=0, sticky="w", pady=15)
        self.p_menu = ttk.Combobox(f, textvariable=self.p_var, state="readonly", font=ent_font)
        self.p_menu.grid(row=1, column=1, sticky="ew")
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)

        tk.Label(f, text="Unit:", font=lbl_font).grid(row=2, column=0, sticky="w", pady=15)
        self.u_menu = ttk.Combobox(f, textvariable=self.u_var, state="readonly", font=ent_font)
        self.u_menu.grid(row=2, column=1, sticky="ew")

        tk.Label(f, text="Current Reading:", font=lbl_font).grid(row=3, column=0, sticky="w", pady=15)
        tk.Entry(f, textvariable=self.curr_val_var, font=ent_font).grid(row=3, column=1, sticky="ew")

        tk.Label(f, text="Target Goal:", font=lbl_font).grid(row=4, column=0, sticky="w", pady=15)
        self.targ_ent = tk.Entry(f, font=ent_font)
        self.targ_ent.grid(row=4, column=1, sticky="ew")

        tk.Button(f, text="CALCULATE DOSAGE", command=self.perform_calc, bg="#2c3e50", fg="white", font=("Arial", 14, "bold"), height=2).grid(row=5, columnspan=2, pady=30, sticky="ew")
        
        self.res_lbl = tk.Label(f, text="Ready", font=("Arial", 16, "bold"), fg="#2980b9", wraplength=700)
        self.res_lbl.grid(row=6, columnspan=2, pady=20)

    def perform_calc(self):
        try:
            p, vol, unit = self.p_var.get(), float(self.vol_var.get()), self.u_var.get()
            curr, targ = float(self.curr_val_var.get()), float(self.targ_ent.get())

            std_curr = curr / 17.86 if (p == "Alkalinity" and unit == "ppm") else curr
            std_targ = targ / 17.86 if (p == "Alkalinity" and unit == "ppm") else targ

            strength = self.brand_data.get(self.b_var.get(), 1.0)
            total_ml = ((std_targ - std_curr) * vol) / strength
            
            if total_ml <= 0:
                self.res_lbl.config(text="STATUS: OPTIMAL", fg="green")
            else:
                self.res_lbl.config(text=f"DOSE: {total_ml:.1f} mL Total", fg="#c0392b")
        except:
            self.res_lbl.config(text="ERROR: Check Inputs", fg="red")

    def build_maint(self):
        f = ttk.Frame(self.tabs["Maintenance"], padding="50"); f.pack(fill="both")
        self.m_entries = {}
        for i, p in enumerate(["Alkalinity", "Calcium", "Magnesium"]):
            tk.Label(f, text=f"{p}:", font=("Arial", 12)).grid(row=i, column=0, pady=15, sticky="w")
            e = tk.Entry(f, font=("Arial", 12)); e.grid(row=i, column=1, padx=20, sticky="ew"); self.m_entries[p] = e
        tk.Button(f, text="LOG DATA", command=self.save_data, bg="#27ae60", fg="white", font=("Arial", 12, "bold")).grid(row=4, columnspan=2, pady=30, sticky="ew")

    def save_data(self):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            with open(self.log_file, "a", newline="") as f:
                writer = csv.writer(f)
                for p, ent in self.m_entries.items():
                    if ent.get(): writer.writerow([ts, p, ent.get()])
            messagebox.showinfo("Success", "Logs updated.")
            self.refresh_hist()
        except:
            messagebox.showerror("Error", "File error.")

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu['values'] = self.ranges[p]["units"]; self.u_menu.current(0)
        self.targ_ent.delete(0, tk.END); self.targ_ent.insert(0, str(self.ranges[p]["target"]))

    def build_history(self):
        f = self.tabs["History"]
        self.hist_txt = tk.Text(f, font=("Courier New", 12), bg="#f8f9fa"); self.hist_txt.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Button(f, text="REFRESH", command=self.refresh_hist).pack(pady=10)

    def build_mix(self):
        f = self.tabs["Mix Guide"]
        guide = "BULK RECIPES (1 GAL)\n" + ("="*20) + "\nAlk: 2 Cups Soda Ash\nCal: 2.5 Cups Calcium Chloride\nMag: 5 Cups Magnesium Chloride"
        tk.Label(f, text=guide, font=("Courier New", 16, "bold"), justify="left", padx=50, pady=100).pack()

    def refresh_hist(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                self.hist_txt.delete("1.0", tk.END); self.hist_txt.insert(tk.END, f.read())

    def hard_exit(self):
        self.root.destroy()
        os._exit(0) # Forced OS-level termination

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
