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
        self.root.title("Aquarium Commander Pro v0.12.3")
        self.root.geometry("950x980")
        
        # Allow resizing again, but we use grid weights below to scale content
        self.root.resizable(True, True) 
        
        self.safety_limits = {"Alkalinity": 1.4, "Calcium": 20.0, "Magnesium": 100.0}
        self.load_settings()
        
        self.ranges = {
            "Alkalinity": {"units": ["dKH", "ppm"], "target": 8.5, "brands": ["Fritz RPM Liquid Alkalinity", "ESV B-Ionic Alk (Part 1)"]},
            "Calcium": {"units": ["ppm"], "target": 420, "brands": ["Fritz RPM Liquid Calcium"]},
            "Magnesium": {"units": ["ppm"], "target": 1350, "brands": ["Fritz RPM Liquid Magnesium"]}
        }

        # pH starts empty for user input
        self.live_ph = tk.StringVar(value="")
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
        except: self.settings = {}

    def build_calc_tab(self):
        f = ttk.Frame(self.calc_tab, padding="30")
        f.pack(fill="both", expand=True)
        # Configure grid to scale with window
        f.columnconfigure(1, weight=1)

        # --- TOP SECTION ---
        top = tk.LabelFrame(f, text=" Required Configuration ", padx=15, pady=15)
        top.grid(row=0, columnspan=3, sticky="ew", pady=(0, 20))
        top.columnconfigure(1, weight=1)

        tk.Label(top, text="Tank Volume (Gal):", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w")
        self.vol_ent = tk.Entry(top, textvariable=self.vol_var, width=10, bg="#ffffcc", font=("Arial", 11))
        self.vol_ent.grid(row=0, column=1, sticky="w", padx=10)
        
        tk.Label(top, text="Dose-Time pH (Optional):", font=("Arial", 11)).grid(row=0, column=2, padx=10)
        self.ph_calc_ent = tk.Entry(top, textvariable=self.live_ph, width=8, font=("Arial", 11))
        self.ph_calc_ent.grid(row=0, column=3, sticky="w")

        # --- INPUTS ---
        labels = ["Parameter:", "Unit Type:", "Current Reading:", "Target (Overrideable):", "Product/Concentration:"]
        self.p_var = tk.StringVar(value="Alkalinity"); self.u_var = tk.StringVar(); self.b_var = tk.StringVar()

        for i, text in enumerate(labels):
            tk.Label(f, text=text, font=("Arial", 11)).grid(row=i+2, column=0, sticky="w", pady=10)

        self.p_menu = ttk.Combobox(f, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly", font=("Arial", 11))
        self.p_menu.grid(row=2, column=1, sticky="ew"); self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)

        self.u_menu = ttk.Combobox(f, textvariable=self.u_var, state="readonly", font=("Arial", 11))
        self.u_menu.grid(row=3, column=1, sticky="ew")

        self.curr_ent = tk.Entry(f, font=("Arial", 11))
        self.curr_ent.grid(row=4, column=1, sticky="ew"); self.curr_ent.bind("<KeyRelease>", self.auto_detect_ppm)

        self.targ_ent = tk.Entry(f, font=("Arial", 11))
        self.targ_ent.grid(row=5, column=1, sticky="ew")

        # CHANGED: Product dropdown now allows typing (state="normal")
        self.b_menu = ttk.Combobox(f, textvariable=self.b_var, state="normal", font=("Arial", 11))
        self.b_menu.grid(row=6, column=1, sticky="ew")

        tk.Button(f, text="GENERATE DOSAGE PLAN", command=self.perform_calc, bg="#2980b9", fg="white", font=("Arial", 12, "bold"), height=2).grid(row=8, columnspan=3, pady=30, sticky="ew")
        
        self.res_lbl = tk.Label(f, text="", font=("Segoe UI", 13, "bold"), wraplength=600, justify="center")
        self.res_lbl.grid(row=9, columnspan=3, pady=10)

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

    def perform_calc(self):
        if not self.vol_var.get():
            self.res_lbl.config(text="⚠️ PLEASE ENTER TANK VOLUME", fg="red"); return
        try:
            p, u, vol = self.p_var.get(), self.u_var.get(), float(self.vol_var.get())
            curr, targ = float(self.curr_ent.get()), float(self.targ_ent.get())
            
            # Map products to concentration (default to 0.6 if custom text entered)
            product_map = {"Fritz RPM Liquid Alkalinity": 0.6, "ESV B-Ionic Alk (Part 1)": 1.9, "Fritz RPM Liquid Calcium": 15.0, "Fritz RPM Liquid Magnesium": 18.0}
            strength = product_map.get(self.b_var.get(), 0.6)
            
            if p == "Alkalinity" and u == "ppm": strength *= 17.86
            diff = targ - curr
            if diff <= 0: self.res_lbl.config(text="STATUS: OPTIMAL", fg="#27ae60"); return
            
            total_ml = (diff * vol) / strength
            limit = self.safety_limits[p]
            if p == "Alkalinity" and u == "ppm": limit *= 17.86
            
            days = max(1, int(diff / limit) + (1 if diff % limit > 0 else 0))
            
            # Check pH if provided
            ph_input = self.live_ph.get()
            if ph_input:
                if float(ph_input) >= 8.45: days = max(days, 6)
            
            msg = f"PLAN: {total_ml:.1f}mL Total Fluid\nDose {total_ml/days:.1f}mL per day for {days} days."
            self.res_lbl.config(text=msg, fg="#2c3e50")
        except: self.res_lbl.config(text="⚠️ INPUT ERROR: CHECK NUMBERS", fg="red")

    def build_maint_tab(self):
        f = ttk.Frame(self.maint_tab, padding="30"); f.pack(fill="both", expand=True)
        tk.Label(f, text="MAINTENANCE LOG", font=("Arial", 14, "bold")).pack(pady=10)
        grid = ttk.Frame(f); grid.pack(pady=20)
        self.m_entries = {}
        params = ["Alkalinity", "Calcium", "Magnesium"]
        for i, p in enumerate(params):
            tk.Label(grid, text=f"{p}:", font=("Arial", 11)).grid(row=i, column=0, padx=10, pady=5)
            e = tk.Entry(grid, font=("Arial", 11)); e.grid(row=i, column=1, pady=5); self.m_entries[p] = e
        
        tk.Label(grid, text="pH (Optional):", font=("Arial", 11)).grid(row=3, column=0, padx=10)
        tk.Entry(grid, textvariable=self.live_ph, font=("Arial", 11)).grid(row=3, column=1, pady=5)
        
        self.m_status = tk.Label(f, text="", fg="#27ae60", font=("Arial", 10, "italic"))
        self.m_status.pack(pady=10)
        tk.Button(f, text="SAVE DATA", command=self.save_maint, bg="#8e44ad", fg="white", font=("bold"), width=20).pack()

    def save_maint(self):
        d = datetime.now().strftime("%Y-%m-%d %H:%M")
        logged = False
        for p, ent in self.m_entries.items():
            if ent.get():
                self.save_to_csv(d, "Test", p[:3], ent.get()); logged = True
        if self.live_ph.get(): 
            self.save_to_csv(d, "Test", "pH", self.live_ph.get()); logged = True
        if logged:
            self.m_status.config(text=f"Success! Data saved at {d}")
            [e.delete(0, tk.END) for e in self.m_entries.values()]
            self.refresh_logs(); self.update_graph()

    def build_graph_tab(self):
        # Allow the graph to expand with the window
        self.fig, self.ax1 = plt.subplots(figsize=(7, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_tab)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        tk.Button(self.graph_tab, text="RELOAD GRAPH", command=self.update_graph, font=("Arial", 10)).pack(pady=10)

    def update_graph(self):
        if not os.path.exists(LOG_FILE): return
        self.ax1.clear()
        dates, alks, phs = [], [], []
        try:
            with open(LOG_FILE, "r") as f:
                for row in csv.reader(f):
                    if row[2] == "Alk":
                        dates.append(row[0].split(" ")[0])
                        alks.append(float(row[3]))
                    if row[2] == "pH":
                        phs.append(float(row[3]))
            
            if alks:
                self.ax1.plot(dates[-10:], alks[-10:], marker='o', color='teal', label="Alk")
                self.ax1.set_ylabel("Alk", color='teal')
                if phs:
                    ax2 = self.ax1.twinx()
                    ax2.clear()
                    ax2.plot(dates[-10:], phs[-10:], marker='s', color='red', label="pH")
                    ax2.set_ylabel("pH", color='red')
            self.ax1.set_title("Water Chemistry Trends")
            self.fig.autofmt_xdate()
            self.canvas.draw()
        except: pass

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu.config(values=self.ranges[p]["units"]); self.u_menu.current(0)
        self.b_menu.config(values=self.ranges[p]["brands"]); self.b_menu.current(0)
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
