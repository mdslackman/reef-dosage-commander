import tkinter as tk
from tkinter import ttk, messagebox
import csv, json, os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.13.1")
        self.root.geometry("1200x1000")
        
        # Financial Data & Pricing
        self.prices = {
            "Fritz RPM Liquid Alkalinity": 23.99,
            "ESV B-Ionic Alk (Part 1)": 24.92,
            "Fritz RPM Liquid Calcium": 23.99,
            "Fritz RPM Liquid Magnesium": 38.49
        }
        
        # FIX: Explicitly convert dict_keys to a list for indexing/slicing
        price_keys = list(self.prices.keys())
        
        self.zones = {
            "Alkalinity": [5, 7, 8, 9, 11, 14],      
            "Calcium": [300, 380, 400, 450, 500, 600],
            "Magnesium": [1100, 1250, 1300, 1400, 1500, 1700],
            "pH": [7.5, 7.8, 8.1, 8.4, 8.5, 9.0]
        }
        
        self.targets = {"Alk": 8.5, "Cal": 420, "Mag": 1350, "pH": 8.2}
        self.safety_limits = {"Alkalinity": 1.4, "Calcium": 20.0, "Magnesium": 100.0}
        
        self.ranges = {
            "Alkalinity": {"units": ["dKH", "ppm"], "target": 8.5, "brands": price_keys[:2]},
            "Calcium": {"units": ["ppm"], "target": 420, "brands": [price_keys[2]]},
            "Magnesium": {"units": ["ppm"], "target": 1350, "brands": [price_keys[3]]}
        }

        self.live_ph = tk.StringVar(value="")
        self.vol_var = tk.StringVar(value="") 
        
        # High Visibility Styling
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Arial', 11))
        self.style.configure('TButton', font=('Arial', 11, 'bold'))

        self.notebook = ttk.Notebook(root)
        self.calc_tab = ttk.Frame(self.notebook)
        self.maint_tab = ttk.Frame(self.notebook)
        self.trend_tab = ttk.Frame(self.notebook)
        self.mix_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.calc_tab, text=" Dosage & Consumption ")
        self.notebook.add(self.maint_tab, text=" Maintenance ")
        self.notebook.add(self.trend_tab, text=" Analytics ")
        self.notebook.add(self.mix_tab, text=" Bulk Mixing Guide ")
        self.notebook.add(self.log_tab, text=" History ")
        self.notebook.pack(expand=1, fill="both")
        
        self.build_calc_tab()
        self.build_maint_tab()
        self.build_trend_dashboard()
        self.build_mixing_guide()
        self.build_log_tab()
        self.update_param_selection()

    def build_calc_tab(self):
        f = ttk.Frame(self.calc_tab, padding="40"); f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)

        top = tk.LabelFrame(f, text=" System Configuration ", padx=15, pady=15)
        top.grid(row=0, columnspan=3, sticky="ew", pady=(0, 20))
        tk.Label(top, text="Volume (Gal):", font=("Arial", 11, "bold")).grid(row=0, column=0)
        tk.Entry(top, textvariable=self.vol_var, width=12, bg="#ffffcc", font=("Arial", 12)).grid(row=0, column=1, padx=10)
        
        self.p_var = tk.StringVar(value="Alkalinity"); self.u_var = tk.StringVar(); self.b_var = tk.StringVar()

        labels = ["Parameter:", "Unit:", "Current Reading:", "Target Goal:", "Product:", "Manual Conc. Override:"]
        for i, text in enumerate(labels):
            tk.Label(f, text=text).grid(row=i+2, column=0, sticky="w", pady=8)

        self.p_menu = ttk.Combobox(f, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly", font=("Arial", 11))
        self.p_menu.grid(row=2, column=1, sticky="ew"); self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)

        self.u_menu = ttk.Combobox(f, textvariable=self.u_var, state="readonly", font=("Arial", 11))
        self.u_menu.grid(row=3, column=1, sticky="ew")

        self.curr_ent = tk.Entry(f, font=("Arial", 11)); self.curr_ent.grid(row=4, column=1, sticky="ew")
        self.targ_ent = tk.Entry(f, font=("Arial", 11)); self.targ_ent.grid(row=5, column=1, sticky="ew")

        self.b_menu = ttk.Combobox(f, textvariable=self.b_var, state="readonly", font=("Arial", 11))
        self.b_menu.grid(row=6, column=1, sticky="ew")

        self.custom_strength = tk.Entry(f, font=("Arial", 11)); self.custom_strength.grid(row=7, column=1, sticky="ew")

        btn_frame = ttk.Frame(f)
        btn_frame.grid(row=8, columnspan=3, pady=30, sticky="ew")
        btn_frame.columnconfigure(0, weight=1); btn_frame.columnconfigure(1, weight=1)

        tk.Button(btn_frame, text="CORRECTION DOSE", command=self.perform_calc, bg="#2980b9", fg="white", height=2).grid(row=0, column=0, padx=5, sticky="ew")
        tk.Button(btn_frame, text="CONSUMPTION RATE", command=self.calc_consumption, bg="#d35400", fg="white", height=2).grid(row=0, column=1, padx=5, sticky="ew")
        
        self.res_lbl = tk.Label(f, text="Awaiting input...", font=("Arial", 12, "bold"), wraplength=800, pady=20)
        self.res_lbl.grid(row=9, columnspan=3)

    def build_mixing_guide(self):
        f = ttk.Frame(self.mix_tab, padding="40"); f.pack(fill="both", expand=True)
        tk.Label(f, text="BULK MIXING RECIPES (1 GALLON)", font=("Arial", 14, "bold")).pack(pady=10)
        
        guide = (
            "Standard DIY Strength to match ESV/Fritz Liquids:\n\n"
            "• ALKALINITY: Mix 2 cups (400g) Soda Ash into 1 Gal RO/DI.\n"
            "• CALCIUM: Mix 2.5 cups (500g) Calcium Chloride into 1 Gal RO/DI.\n"
            "• MAGNESIUM: Mix 5 cups (1000g) Mag Chloride/Sulfate into 1 Gal RO/DI.\n\n"
            "Note: Use a scale for best accuracy. Dissolve fully before use."
        )
        tk.Label(f, text=guide, font=("Courier New", 12), justify="left", relief="ridge", padx=20, pady=20, bg="#fdfdfd").pack(fill="x")

    def calc_consumption(self):
        if not os.path.exists("aquarium_data.csv") or not self.vol_var.get():
            messagebox.showwarning("Incomplete", "Please set Volume and ensure history has 2+ logs.")
            return
        p_code = self.p_var.get()[:3]
        logs = []
        with open("aquarium_data.csv", "r") as f:
            for row in csv.reader(f):
                if row[2] == p_code: logs.append((datetime.strptime(row[0], "%Y-%m-%d %H:%M"), float(row[3])))
        
        if len(logs) < 2:
            self.res_lbl.config(text="⚠️ ERROR: NEED MORE DATA POINTS", fg="red")
            return

        last, prev = logs[-1], logs[-2]
        days = (last[0] - prev[0]).total_seconds() / 86400 
        drop = prev[1] - last[1] 

        if drop <= 0:
            self.res_lbl.config(text=f"STABLE: No drop detected over {days:.1f} days.", fg="blue")
            return

        daily_drop = drop / days
        strength = float(self.custom_strength.get()) if self.custom_strength.get() else 0.6
        daily_ml = (daily_drop * float(self.vol_var.get())) / strength
        
        self.res_lbl.config(text=f"CONSUMPTION: {daily_drop:.2f} {self.u_var.get()}/day\nSUGGESTED DOSE: {daily_ml:.1f} mL / day", fg="#d35400")

    def perform_calc(self):
        try:
            p, vol = self.p_var.get(), float(self.vol_var.get())
            curr, targ = float(self.curr_ent.get()), float(self.targ_ent.get())
            self.targets[p[:3]] = targ 
            
            strength = float(self.custom_strength.get()) if self.custom_strength.get() else 0.6
            diff = targ - curr
            if diff <= 0: self.res_lbl.config(text="OPTIMAL: No correction needed.", fg="green"); return
            
            total_ml = (diff * vol) / strength
            limit = self.safety_limits[p]
            days = max(1, int(diff / limit) + (1 if diff % limit > 0 else 0))
            self.res_lbl.config(text=f"TOTAL DOSE: {total_ml:.1f} mL\nDAILY: {total_ml/days:.1f} mL for {days} days.", fg="#2980b9")
        except: self.res_lbl.config(text="ERROR: Check your Volume or Current/Target numbers.", fg="red")

    def build_trend_dashboard(self):
        self.trend_notebook = ttk.Notebook(self.trend_tab)
        self.t_alk = ttk.Frame(self.trend_notebook); self.t_cal = ttk.Frame(self.trend_notebook)
        self.t_mag = ttk.Frame(self.trend_notebook); self.t_ph = ttk.Frame(self.trend_notebook)
        self.trend_notebook.add(self.t_alk, text=" Alkalinity "); self.trend_notebook.add(self.t_cal, text=" Calcium ")
        self.trend_notebook.add(self.t_mag, text=" Magnesium "); self.trend_notebook.add(self.t_ph, text=" pH ")
        self.trend_notebook.pack(expand=1, fill="both")
        tk.Button(self.trend_tab, text="RELOAD ANALYTICS", command=self.update_all_graphs, bg="#27ae60", fg="white").pack(pady=5)
        self.graph_canvases = {}
        for name, frame in [("Alk", self.t_alk), ("Cal", self.t_cal), ("Mag", self.t_mag), ("pH", self.t_ph)]:
            fig, ax = plt.subplots(figsize=(8, 5)); canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack(fill="both", expand=True); self.graph_canvases[name] = (fig, ax, canvas)

    def update_all_graphs(self):
        if not os.path.exists("aquarium_data.csv"): return
        data = {"Alk": ([], []), "Cal": ([], []), "Mag": ([], []), "pH": ([], [])}
        with open("aquarium_data.csv", "r") as f:
            for row in csv.reader(f):
                if row[2] in data:
                    data[row[2]][0].append(row[0].split(" ")[0]); data[row[2]][1].append(float(row[3]))
        for p_key, (fig, ax, canvas) in self.graph_canvases.items():
            ax.clear(); x, y = data[p_key]
            if not x: continue
            z = self.zones[{"Alk":"Alkalinity", "Cal":"Calcium", "Mag":"Magnesium", "pH":"pH"}[p_key]]
            ax.axhspan(z[0], z[1], color='red', alpha=0.1); ax.axhspan(z[1], z[2], color='yellow', alpha=0.1)  
            ax.axhspan(z[2], z[3], color='green', alpha=0.15); ax.axhspan(z[3], z[4], color='yellow', alpha=0.1)  
            ax.axhline(y=self.targets[p_key], color='blue', linestyle='--', label="Goal")
            ax.plot(x[-15:], y[-15:], marker='o', linestyle='-', linewidth=2, color='#2c3e50', label="Actual")
            ax.legend(); fig.autofmt_xdate(); canvas.draw()

    def build_maint_tab(self):
        f = ttk.Frame(self.maint_tab, padding="30"); f.pack(fill="both")
        grid = ttk.Frame(f); grid.pack(pady=10)
        self.m_entries = {}
        for i, p in enumerate(["Alkalinity", "Calcium", "Magnesium"]):
            tk.Label(grid, text=f"{p}:").grid(row=i, column=0); e = tk.Entry(grid, font=("Arial", 11)); e.grid(row=i, column=1, pady=5); self.m_entries[p] = e
        tk.Label(grid, text="pH (Opt):").grid(row=3, column=0); tk.Entry(grid, textvariable=self.live_ph, font=("Arial", 11)).grid(row=3, column=1)
        tk.Button(f, text="LOG TEST RESULTS", command=self.save_maint, bg="#8e44ad", fg="white", width=25).pack(pady=15)

    def save_maint(self):
        d = datetime.now().strftime("%Y-%m-%d %H:%M")
        for p, ent in self.m_entries.items():
            if ent.get(): self.save_to_csv(d, "Test", p[:3], ent.get())
        if self.live_ph.get(): self.save_to_csv(d, "Test", "pH", self.live_ph.get())
        [e.delete(0, tk.END) for e in self.m_entries.values()]; self.update_all_graphs()

    def save_to_csv(self, d, t, p, v):
        with open("aquarium_data.csv", "a", newline='') as f: csv.writer(f).writerow([d, t, p, v])

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu.config(values=self.ranges[p]["units"]); self.u_menu.current(0)
        self.b_menu.config(values=self.ranges[p]["brands"]); self.b_menu.current(0)
        self.targ_ent.delete(0, tk.END); self.targ_ent.insert(0, str(self.ranges[p]["target"]))

    def build_log_tab(self):
        f = ttk.Frame(self.log_tab, padding="20"); f.pack(fill="both", expand=True)
        self.txt = tk.Text(f, height=20, state="disabled", font=("Courier", 10))
        self.txt.pack(fill="both", expand=True)
        tk.Button(f, text="REFRESH HISTORY", command=self.refresh_logs).pack(pady=5)

    def refresh_logs(self):
        if os.path.exists("aquarium_data.csv"):
            with open("aquarium_data.csv", "r") as f:
                self.txt.config(state="normal"); self.txt.delete("1.0", tk.END); self.txt.insert(tk.END, f.read()); self.txt.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
