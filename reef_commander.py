import tkinter as tk
from tkinter import ttk, messagebox
import csv, os, sys
from datetime import datetime

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.13.7")
        
        # --- UI LOCKDOWN ---
        # Fixed window size to prevent scaling issues
        self.root.geometry("900x800")
        self.root.resizable(False, False) 
        
        # Master Kill Switch
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.log_file = "reef_logs.csv"
        self.init_csv()

        # Concentrations (1mL in 1 Gal)
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

        self.vol_var = tk.StringVar()
        self.p_var = tk.StringVar(value="Alkalinity")
        self.u_var = tk.StringVar()
        self.b_var = tk.StringVar()
        
        # Main Layout
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

    def build_dosage(self):
        f = ttk.Frame(self.tabs["Dosage"], padding="40")
        f.pack(fill="both", expand=True)
        
        # Volume
        tk.Label(f, text="Tank Volume (Gal):", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w")
        tk.Entry(f, textvariable=self.vol_var, width=20, bg="#ffffcc", font=("Arial", 11)).grid(row=0, column=1, sticky="w", pady=10)

        # Dropdowns
        tk.Label(f, text="Parameter:").grid(row=1, column=0, sticky="w")
        self.p_menu = ttk.Combobox(f, textvariable=self.p_var, state="readonly", font=("Arial", 11))
        self.p_menu.grid(row=1, column=1, sticky="ew", pady=5)
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)

        tk.Label(f, text="Unit:").grid(row=2, column=0, sticky="w")
        self.u_menu = ttk.Combobox(f, textvariable=self.u_var, state="readonly", font=("Arial", 11))
        self.u_menu.grid(row=2, column=1, sticky="ew", pady=5)

        tk.Label(f, text="Product:").grid(row=3, column=0, sticky="w")
        self.b_menu = ttk.Combobox(f, textvariable=self.b_var, state="readonly", font=("Arial", 11))
        self.b_menu.grid(row=3, column=1, sticky="ew", pady=5)

        # Inputs
        tk.Label(f, text="Current Reading:").grid(row=4, column=0, sticky="w")
        self.curr_ent = tk.Entry(f, font=("Arial", 11))
        self.curr_ent.grid(row=4, column=1, sticky="ew", pady=5)
        # BIND: Check for unit correction while typing
        self.curr_ent.bind("<KeyRelease>", self.check_unit_sync)

        tk.Label(f, text="Target Goal:").grid(row=5, column=0, sticky="w")
        self.targ_ent = tk.Entry(f, font=("Arial", 11))
        self.targ_ent.grid(row=5, column=1, sticky="ew", pady=5)

        tk.Button(f, text="CALCULATE DOSAGE", command=self.perform_calc, bg="#2c3e50", fg="white", height=2, font=("Arial", 10, "bold")).grid(row=6, columnspan=2, pady=25, sticky="ew")
        
        self.res_lbl = tk.Label(f, text="Enter values to calculate.", font=("Arial", 13, "bold"), fg="#2980b9", wraplength=600)
        self.res_lbl.grid(row=7, columnspan=2, pady=20)

    def check_unit_sync(self, event=None):
        """Auto-switches dKH to ppm if user types a large number."""
        try:
            val = float(self.curr_ent.get())
            if self.p_var.get() == "Alkalinity" and self.u_var.get() == "dKH" and val > 25:
                self.u_menu.set("ppm")
                self.res_lbl.config(text=f"Switched to ppm (Value {val} is high for dKH)", fg="orange")
        except ValueError:
            pass

    def perform_calc(self):
        try:
            p, vol, unit = self.p_var.get(), float(self.vol_var.get()), self.u_var.get()
            curr, targ = float(self.curr_ent.get()), float(self.targ_ent.get())

            # Math conversion
            std_curr = curr / 17.86 if (p == "Alkalinity" and unit == "ppm") else curr
            std_targ = targ / 17.86 if (p == "Alkalinity" and unit == "ppm") else targ

            strength = self.brand_data.get(self.b_var.get(), 1.0)
            total_ml = ((std_targ - std_curr) * vol) / strength
            
            if total_ml <= 0:
                self.res_lbl.config(text="Status: Optimal (No dose needed)", fg="green")
            else:
                self.res_lbl.config(text=f"REQUIRED DOSE: {total_ml:.1f} mL", fg="#c0392b")
        except Exception:
            self.res_lbl.config(text="Input Error: Check volume and numbers.", fg="red")

    def build_maint(self):
        f = ttk.Frame(self.tabs["Maintenance"], padding="30"); f.pack(fill="both")
        self.m_entries = {}
        for i, p in enumerate(["Alkalinity", "Calcium", "Magnesium"]):
            tk.Label(f, text=f"{p}:", font=("Arial", 10)).grid(row=i, column=0, pady=10, sticky="w")
            e = tk.Entry(f, font=("Arial", 10)); e.grid(row=i, column=1, padx=20); self.m_entries[p] = e
        tk.Button(f, text="LOG TEST RESULTS", command=self.save_data, bg="#27ae60", fg="white", width=25).grid(row=4, columnspan=2, pady=30)

    def save_data(self):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            with open(self.log_file, "a", newline="") as f:
                writer = csv.writer(f)
                for p, ent in self.m_entries.items():
                    if ent.get(): writer.writerow([ts, p, ent.get()])
            messagebox.showinfo("Success", "Data logged to CSV.")
            self.refresh_hist()
        except Exception:
            messagebox.showerror("Error", "Check if CSV is open in another program.")

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu['values'] = self.ranges[p]["units"]; self.u_menu.current(0)
        self.b_menu['values'] = self.ranges[p]["brands"]; self.b_menu.current(0)
        self.targ_ent.delete(0, tk.END); self.targ_ent.insert(0, str(self.ranges[p]["target"]))

    def build_history(self):
        f = self.tabs["History"]
        self.hist_txt = tk.Text(f, font=("Courier New", 10), bg="#f4f4f4"); self.hist_txt.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Button(f, text="REFRESH LOG", command=self.refresh_hist).pack(pady=5)

    def refresh_hist(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                self.hist_txt.delete("1.0", tk.END); self.hist_txt.insert(tk.END, f.read())

    def build_mix(self):
        f = self.tabs["Mix Guide"]
        guide = "DIY BULK SOLUTIONS (1 GALLON RO/DI)\n" + ("-"*40) + \
                "\n\nAlk: 2 Cups Soda Ash (raises pH)\nCal: 2.5 Cups Calcium Chloride\nMag: 5 Cups Magnesium Chloride"
        tk.Label(f, text=guide, font=("Courier New", 12, "bold"), justify="left", padx=30, pady=50).pack()

    def on_closing(self):
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
