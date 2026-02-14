import tkinter as tk
from tkinter import ttk
import csv, json, os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

# --- FILE PATHS ---
LOG_FILE = "aquarium_data.csv"
SETTINGS_FILE = "settings.json"

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.12.2")
        
        # QUALITY OF LIFE: Lock window size to prevent layout distortion
        self.root.geometry("900x950")
        self.root.resizable(False, False) 
        
        self.safety_limits = {"Alkalinity": 1.4, "Calcium": 20.0, "Magnesium": 100.0}
        self.load_settings()
        
        self.ranges = {
            "Alkalinity": {"units": ["dKH", "ppm"], "target": 8.5, "brands": {"Fritz RPM Liquid Alkalinity": 0.6, "ESV B-Ionic Alk (Part 1)": 1.9}},
            "Calcium": {"units": ["ppm"], "target": 420, "brands": {"Fritz RPM Liquid Calcium": 15.0}},
            "Magnesium": {"units": ["ppm"], "target": 1350, "brands": {"Fritz RPM Liquid Magnesium": 18.0}}
        }

        self.live_ph = tk.StringVar(value=str(self.settings.get("last_ph", 8.2)))
        self.vol_var = tk.StringVar(value="") 
        
        self.notebook = ttk.Notebook(root)
        self.calc_tab = ttk.Frame(self.notebook)
        self.maint_tab = ttk.Frame(self.notebook)
        self.graph_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.calc_tab, text=" Dosage ")
        self.notebook.add(self.maint_tab, text=" Maintenance ")
        self.notebook.add(self.graph_tab, text=" Trends ")
        self.notebook.add(self.log_tab, text=" History ")
        self.notebook.pack(expand=1, fill="both")
        
        self.build_calc_tab()
        self.build_maint_tab()
        self.build_graph_tab()
        self.build_log_tab()
        self.update_param_selection()

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, "r") as f: self.settings = json.load(f)
        except: self.settings = {"last_ph": 8.2}

    def build_calc_tab(self):
        f = ttk.Frame(self.calc_tab, padding="20"); f.pack(fill="both", expand=True)
        
        top = tk.LabelFrame(f, text=" System Status ", padx=10, pady=10)
        top.grid(row=0, columnspan=3, sticky="ew", pady=(0, 20))
        tk.Label(top, text="Volume (Gal):").grid(row=0, column=0)
        tk.Entry(top, textvariable=self.vol_var, width=8, bg="#ffffcc").grid(row=0, column=1, padx=5)
        tk.Label(top, text="System pH:").grid(row=0, column=2, padx=10)
        tk.Label(top, textvariable=self.live_ph, font=("Arial", 14, "bold"), fg="blue").grid(row=0, column=3)

        self.p_var = tk.StringVar(value="Alkalinity"); self.u_var = tk.StringVar(); self.b_var = tk.StringVar()

        tk.Label(f, text="Parameter:").grid(row=2, column=0, sticky="w")
        self.p_menu = ttk.Combobox(f, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly")
        self.p_menu.grid(row=2, column=1, pady=5, sticky="ew")
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)

        tk.Label(f, text="Unit:").grid(row=3, column=0, sticky="w")
        self.u_menu = ttk.Combobox(f, textvariable=self.u_var, state="readonly")
        self.u_menu.grid(row=3, column=1, pady=5, sticky="ew")

        tk.Label(f, text="Current Reading:").grid(row=4, column=0, sticky="w")
        self.curr_ent = tk.Entry(f); self.curr_ent.grid(row=4, column=1, pady=5, sticky="ew")
        self.curr_ent.bind("<KeyRelease>", self.auto_detect_ppm)

        tk.Label(f, text="Target (Overrideable):").grid(row=5, column=0, sticky="w")
        self.targ_ent = tk.Entry(f); self.targ_ent.grid(row=5, column=1, pady=5, sticky="ew")

        tk.Label(f, text="Dose-Time pH:").grid(row=6, column=0, sticky="w")
        self.ph_calc_ent = tk.Entry(f, textvariable=self.live_ph); self.ph_calc_ent.grid(row=6, column=1, pady=5, sticky="ew")

        tk.Label(f, text="Product:").grid(row=7, column=0, sticky="w")
        self.b_menu = ttk.Combobox(f, textvariable=self.b_var, state="readonly"); self.b_menu.grid(row=7, column=1, pady=5, sticky="ew")

        tk.Button(f, text="CALCULATE", command=self.perform_calc, bg="#2980b9", fg="white", font=("Arial", 10, "bold")).grid(row=8, columnspan=3, pady=20, sticky="ew")
        self.res_lbl = tk.Label(f, text="", font=("Consolas", 11, "bold"), wraplength=450); self.res_lbl.grid(row=9, columnspan=3)

    def auto_detect_ppm(self, event=None):
        if self.p_var.get() == "Alkalinity":
            val = self.curr_ent.get()
            try:
                if float(val) > 25:
                    if self.u_var.get() != "ppm":
                        self.u_var.set("ppm")
                        self.targ_ent.delete(0, tk.END)
                        self.targ_ent.insert(0, "151.8")
            except ValueError: pass

    def build_maint_tab(self):
        f = ttk.Frame(self.maint_tab, padding="20"); f.pack(fill="both")
        tk.Label(f, text="TEST LOG", font=("Arial", 12, "bold")).pack()
        grid = ttk.Frame(f); grid.pack(pady=10)
        self.m_entries = {}
        for i, p in enumerate(["Alkalinity", "Calcium", "Magnesium"]):
            tk.Label(grid, text=f"{p}:").grid(row=i, column=0)
            e = tk.Entry(grid); e.grid(row=i, column=1, pady=2); self.m_entries[p] = e
        tk.Label(grid, text="pH:").grid(row=3, column=0)
        tk.Entry(grid, textvariable=self.live_ph).grid(row=3, column=1)
        self.m_status = tk.Label(f, text="", fg="green")
        self.m_status.pack()
        tk.Button(f, text="SAVE LOG", command=self.save_maint, bg="#8e44ad", fg="white").pack(pady=10)

    def perform_calc(self):
        if not self.vol_var.get():
            self.res_lbl.config(text="ERROR: VOLUME REQUIRED", fg="red"); return
        try:
            p, u, vol = self.p_var.get(), self.u_var.get(), float(self.vol_var.get())
            curr, targ = float(self.curr_ent.get()), float(self.targ_ent.get())
            strength = self.ranges[p]["brands"][self.b_var.get()]
            if p == "Alkalinity" and u == "ppm": strength *= 17.86
            diff = targ - curr
            if diff <= 0: self.res_lbl.config(text="Status: Optimal", fg="green"); return
            total_ml = (diff * vol) / strength
            limit = self.safety_limits[p]
            if p == "Alkalinity" and u == "ppm": limit *= 17.86
            days = max(1, int(diff / limit) + (1 if diff % limit > 0 else 0))
            if float(self.live_ph.get()) >= 8.45: days = max(days, 6)
            self.res_lbl.config(text=f"TOTAL: {total_ml:.1f}mL\nDAILY: {total_ml/days:.1f}mL over {days} days", fg="black")
        except: self.res_lbl.config(text="ERROR: CHECK NUMBERS", fg="red")

    def build_graph_tab(self):
        # UI for Graphing
        self.fig, self.ax1 = plt.subplots(figsize=(6, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_tab)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        tk.Button(self.graph_tab, text="REFRESH TRENDS", command=self.update_graph).pack(pady=10)

    def update_graph(self):
        if not os.path.exists(LOG_FILE): return
        self.ax1.clear()
        dates, alks, phs = [], [], []
        with open(LOG_FILE, "r") as f:
            for row in csv.reader(f):
                if row[2] == "Alk":
                    dates.append(row[0].split(" ")[0])
                    alks.append(float(row[3]))
                if row[2] == "pH":
                    phs.append(float(row[3]))
        
        # Plot Alk on left axis
        lns1 = self.ax1.plot(dates[-10:], alks[-10:], marker='o', color='teal', label="Alkalinity")
        self.ax1.set_ylabel("Alkalinity (dKH/ppm)", color='teal')
        
        # Plot pH on right axis
        self.ax2 = self.ax1.twinx()
        self.ax2.clear()
        lns2 = self.ax2.plot(dates[-10:], phs[-10:], marker='s', color='red', label="pH")
        self.ax2.set_ylabel("pH", color='red')
        
        self.ax1.set_title("Alkalinity vs pH Trend (Last 10 Logs)")
        self.fig.autofmt_xdate()
        self.canvas.draw()

    def save_maint(self):
        d = datetime.now().strftime("%Y-%m-%d %H:%M")
        logged = False
        for p, ent in self.m_entries.items():
            if ent.get():
                self.save_to_csv(d, "Test", p[:3], ent.get()); logged = True
        if self.live_ph.get(): self.save_to_csv(d, "Test", "pH", self.live_ph.get()); logged = True
        if logged:
            self.m_status.config(text=f"Logged at {d}"); [e.delete(0, tk.END) for e in self.m_entries.values()]
            self.refresh_logs(); self.update_graph()

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu.config(values=self.ranges[p]["units"]); self.u_menu.current(0)
        self.b_menu.config(values=list(self.ranges[p]["brands"].keys())); self.b_menu.current(0)
        self.targ_ent.delete(0, tk.END); self.targ_ent.insert(0, str(self.ranges[p]["target"]))

    def save_to_csv(self, date, type, param, val):
        with open(LOG_FILE, "a", newline='') as f: csv.writer(f).writerow([date, type, param, val])

    def build_log_tab(self):
        f = ttk.Frame(self.log_tab, padding="20"); f.pack(fill="both", expand=True)
        self.txt = tk.Text(f, height=20, state="disabled", font=("Consolas", 10)); self.txt.pack(fill="both", expand=True)
        self.refresh_logs()

    def refresh_logs(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                content = f.read(); self.txt.config(state="normal")
                self.txt.delete("1.0", tk.END); self.txt.insert(tk.END, content); self.txt.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
