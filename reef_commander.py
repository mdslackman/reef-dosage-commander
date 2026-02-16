import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv, os, sys, time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.16.1")
        self.root.geometry("1200x980")
        self.root.protocol("WM_DELETE_WINDOW", self.hard_exit)
        
        self.log_file = "reef_logs.csv"
        self.config_file = "app_config.txt"
        self.init_csv()

        # Database
        self.brand_data = {
            "ESV B-Ionic Alk (Part 1)": 1.4, "Fritz RPM Liquid Alk": 1.4,
            "ESV B-Ionic Cal (Part 2)": 20.0, "Fritz RPM Liquid Cal": 20.0,
            "Fritz RPM Liquid Mag": 100.0, "DIY Vinegar (5%)": 0.5,
            "Generic Carbon (NoPox)": 3.0
        }

        self.test_instructions = {
            "Salifert": {
                "Alkalinity": {"steps": ["4ml tank water", "2 drops KH-Ind", "Draw 1ml Reagent", "Add dropwise until Pink"], "time": 0},
                "Calcium": {"steps": ["2ml tank water", "1 scoop Ca-1 powder", "Draw 1ml Ca-2", "Add 0.6ml then dropwise"], "time": 0},
                "Magnesium": {"steps": ["2ml tank water", "6 drops Mg-1", "1 scoop Mg-2", "Add Mg-3 dropwise"], "time": 0},
                "Nitrate": {"steps": ["1ml tank water", "4ml NO3-1", "1 scoop NO3-2", "Swirl 30s", "Wait 3 mins"], "time": 180},
                "Phosphate": {"steps": ["10ml tank water", "4 drops PO4-1", "1 scoop PO4-2", "Wait 5 mins"], "time": 300}
            },
            "Hanna": {
                "Alkalinity": {"steps": ["10ml water (C1)", "Press button", "Add 1ml Reagent", "Invert 5x", "Press button (C2)"], "time": 0},
                "Phosphate": {"steps": ["10ml water (C1)", "Add reagent packet", "Shake 2 mins", "Hold button for timer"], "time": 180},
                "Nitrate (HR)": {"steps": ["10ml water (C1)", "Add reagent packet", "Shake 2 mins", "Hold button for timer"], "time": 420}
            }
        }

        self.ranges = {
            "Alkalinity": {"target": 8.5, "low": 7.8, "high": 9.2, "crit_low": 7.0, "crit_high": 11.5, "units": ["dKH", "ppm"]},
            "Calcium": {"target": 420, "low": 400, "high": 440, "crit_low": 350, "crit_high": 500, "units": ["ppm"]},
            "Magnesium": {"target": 1350, "low": 1300, "high": 1400, "crit_low": 1200, "crit_high": 1550, "units": ["ppm"]},
            "Nitrate": {"target": 5.0, "low": 2.0, "high": 15.0, "crit_low": 0.0, "crit_high": 50.0, "units": ["ppm"]},
            "Phosphate": {"target": 0.03, "low": 0.01, "high": 0.08, "crit_low": 0.0, "crit_high": 0.25, "units": ["ppm"]},
            "Salinity": {"target": 1.025, "low": 1.024, "high": 1.026, "crit_low": 1.020, "crit_high": 1.030, "units": ["SG"]},
            "Temperature": {"target": 25.5, "low": 25.0, "high": 26.5, "crit_low": 22.0, "crit_high": 29.5, "units": ["°C", "°F"]}
        }

        # Variables
        self.unit_mode = tk.StringVar(value="Liters")
        self.vol_var = tk.StringVar(value=self.load_config())
        self.p_var = tk.StringVar(value="Alkalinity")
        self.u_var = tk.StringVar(); self.b_var = tk.StringVar()
        self.curr_val_var = tk.StringVar(); self.targ_val_var = tk.StringVar()
        self.custom_str = tk.StringVar(); self.ph_fuge_var = tk.StringVar()
        self.m_u_var = tk.StringVar(value="dKH"); self.m_alk_entry_var = tk.StringVar()
        self.harvest_var = tk.BooleanVar(value=False)
        self.t_brand_var = tk.StringVar(value="Salifert"); self.t_param_var = tk.StringVar(value="Alkalinity")
        self.ppb_input = tk.StringVar(); self.ppm_output = tk.StringVar(value="--- ppm")
        self.timer_running = False; self.remaining_time = 0

        # UI
        self.notebook = ttk.Notebook(root)
        self.tabs = {name: ttk.Frame(self.notebook) for name in ["Action Plan", "Maintenance", "Trends", "Testing & History"]}
        for name, frame in self.tabs.items(): self.notebook.add(frame, text=f" {name} ")
        self.notebook.pack(expand=True, fill="both")
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        
        self.build_dosage(); self.build_maint(); self.build_trends(); self.build_history()
        self.update_param_selection()

    # --- MATH ENGINE (METRIC BASE) ---
    def get_liters(self):
        try:
            val = float(self.vol_var.get() or 0)
            return val if self.unit_mode.get() == "Liters" else val * 3.78541
        except: return 0

    def init_csv(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="") as f:
                csv.writer(f).writerow(["Timestamp", "Parameter", "Value", "Unit"])

    def load_config(self):
        return open(self.config_file, "r").read().strip() if os.path.exists(self.config_file) else "100"

    def save_config(self):
        with open(self.config_file, "w") as f: f.write(self.vol_var.get())

    def on_tab_change(self, event):
        name = self.notebook.tab(self.notebook.select(), "text").strip()
        if name == "Trends": self.refresh_all_graphs()
        if name == "Testing & History": self.refresh_hist()

    # --- TAB 1: ACTION PLAN ---
    def build_dosage(self):
        f = ttk.Frame(self.tabs["Action Plan"], padding=20); f.pack(fill="both")
        
        # Unit Config Header
        cfg = ttk.LabelFrame(f, text=" System Configuration ", padding=10); cfg.pack(fill="x", pady=5)
        ttk.Label(cfg, text="Volume:").pack(side="left")
        ttk.Entry(cfg, textvariable=self.vol_var, width=10).pack(side="left", padx=5)
        ttk.Radiobutton(cfg, text="Liters", variable=self.unit_mode, value="Liters").pack(side="left")
        ttk.Radiobutton(cfg, text="Gallons", variable=self.unit_mode, value="Gallons").pack(side="left")

        # Inputs
        tk.Label(f, text="Parameter:").pack(anchor="w")
        self.p_menu = ttk.Combobox(f, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly")
        self.p_menu.pack(fill="x", pady=2); self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)
        
        tk.Label(f, text="Product:").pack(anchor="w")
        self.b_menu = ttk.Combobox(f, textvariable=self.b_var, state="readonly")
        self.b_menu.pack(fill="x", pady=2)
        
        tk.Label(f, text="Current Reading:").pack(anchor="w")
        tk.Entry(f, textvariable=self.curr_val_var).pack(fill="x", pady=2)
        
        tk.Label(f, text="Target Goal:").pack(anchor="w")
        tk.Entry(f, textvariable=self.targ_val_var).pack(fill="x", pady=2)

        tk.Button(f, text="CALCULATE ACTION PLAN", command=self.perform_calc, bg="#1a252f", fg="white", height=2).pack(fill="x", pady=10)
        self.res_lbl = tk.Label(f, text="---", font=("Arial", 11, "bold"), fg="#2980b9")
        self.res_lbl.pack()
        self.status_log_lbl = tk.Label(f, text="", font=("Arial", 8, "italic"), fg="#27ae60"); self.status_log_lbl.pack()

    def perform_calc(self):
        try:
            p, vol_l = self.p_var.get(), self.get_liters()
            curr, targ = float(self.curr_val_var.get()), float(self.targ_val_var.get())
            strength = self.brand_data.get(self.b_var.get(), 1.0)
            
            # Internal math is per Liter
            total_ml = ((targ - curr) * vol_l) / strength
            
            if total_ml <= 0:
                self.res_lbl.config(text="LEVELS OPTIMAL", fg="green")
            else:
                days = 7 if total_ml > 100 else 1
                self.res_lbl.config(text=f"TOTAL: {total_ml:.1f}mL | DOSE: {total_ml/days:.1f}mL/day", fg="#c0392b")
                self.status_log_lbl.config(text="✅ CALCULATION LOCKED TO HISTORY")
                self.silent_log(f"Dose {p}", f"{total_ml/days:.1f}", "mL/day")
        except: self.res_lbl.config(text="ERROR: Check Inputs", fg="red")

    # --- TAB 2: MAINTENANCE ---
    def build_maint(self):
        f = ttk.Frame(self.tabs["Maintenance"], padding=20); f.pack(fill="both")
        self.m_entries = {}
        for p in self.ranges.keys():
            row = ttk.Frame(f); row.pack(fill="x", pady=2)
            tk.Label(row, text=p, width=15, anchor="w").pack(side="left")
            e = tk.Entry(row); e.pack(side="left", expand=True, fill="x")
            u = tk.Label(row, text=self.ranges[p]["units"][0], width=8); u.pack(side="left")
            self.m_entries[p] = (e, u)
        
        tk.Button(f, text="LOG TEST RESULTS (SILENT)", command=self.save_maint, bg="#27ae60", fg="white").pack(fill="x", pady=10)

    def save_maint(self):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(self.log_file, "a", newline="") as f:
            w = csv.writer(f)
            for p, (ent, u) in self.m_entries.items():
                if ent.get(): w.writerow([ts, p, ent.get(), u.cget("text")])
        messagebox.showinfo("Logged", "Data saved silently.")

    # --- TAB 3: TRENDS ---
    def build_trends(self):
        self.canvas_base = tk.Canvas(self.tabs["Trends"])
        scroll = ttk.Scrollbar(self.tabs["Trends"], orient="vertical", command=self.canvas_base.yview)
        self.scroll_frame = ttk.Frame(self.canvas_base)
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas_base.configure(scrollregion=self.canvas_base.bbox("all")))
        self.canvas_base.create_window((0,0), window=self.scroll_frame, anchor="nw")
        self.canvas_base.configure(yscrollcommand=scroll.set)
        self.canvas_base.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")
        self.figs = []
        for p in self.ranges.keys():
            fig, ax = plt.subplots(figsize=(8, 2.2))
            c = FigureCanvasTkAgg(fig, master=self.scroll_frame)
            c.get_tk_widget().pack(fill="x", pady=5)
            self.figs.append((p, ax, c))

    def refresh_all_graphs(self):
        if not os.path.exists(self.log_file): return
        with open(self.log_file, "r") as f:
            data = list(csv.reader(f))[1:]
        for p, ax, c in self.figs:
            ax.clear()
            dates = [r[0].split(" ")[0] for r in data if r[1] == p]
            vals = [float(r[2]) for r in data if r[1] == p]
            if vals:
                ax.plot(dates, vals, marker='o', color='black')
                rng = self.ranges[p]
                ax.axhspan(rng["low"], rng["high"], color='green', alpha=0.2)
                ax.axhspan(rng["crit_low"], rng["low"], color='yellow', alpha=0.1)
                ax.axhspan(rng["high"], rng["crit_high"], color='yellow', alpha=0.1)
                ax.set_title(p)
            c.draw()

    # --- TAB 4: TESTING & HISTORY ---
    def build_history(self):
        f = self.tabs["Testing & History"]
        walk_f = ttk.LabelFrame(f, text=" Guided Test Assistant ", padding=10)
        walk_f.pack(side="left", fill="both", padx=10, pady=10, width=400)
        
        # PPB Converter
        conv = ttk.LabelFrame(walk_f, text=" Hanna PPB -> PPM ", padding=5); conv.pack(fill="x", pady=5)
        ttk.Entry(conv, textvariable=self.ppb_input, width=10).pack(side="left")
        self.ppb_input.trace_add("write", self.convert_ppb)
        ttk.Label(conv, text=" ppb = ").pack(side="left")
        ttk.Label(conv, textvariable=self.ppm_output, font=("Arial", 10, "bold")).pack(side="left")

        # Timer
        self.timer_lbl = tk.Label(walk_f, text="00:00", font=("Consolas", 20)); self.timer_lbl.pack()
        self.timer_btn = tk.Button(walk_f, text="START TIMER", command=self.start_timer, state="disabled"); self.timer_btn.pack(fill="x")

        ttk.Combobox(walk_f, textvariable=self.t_brand_var, values=["Salifert", "Hanna"]).pack(fill="x", pady=2)
        ttk.Combobox(walk_f, textvariable=self.t_param_var, values=list(self.test_instructions["Salifert"].keys())).pack(fill="x", pady=2)
        tk.Button(walk_f, text="LOAD STEPS", command=self.update_walkthrough).pack(fill="x", pady=5)
        self.check_frame = ttk.Frame(walk_f); self.check_frame.pack()

        # History Tree
        self.tree = ttk.Treeview(f, columns=("TS", "P", "V", "U"), show="headings")
        for c in ["TS", "P", "V", "U"]: self.tree.heading(c, text=c)
        self.tree.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    # --- HELPERS ---
    def convert_ppb(self, *args):
        try: self.ppm_output.set(f"{(float(self.ppb_input.get()) * 3.066 / 1000):.3f} ppm")
        except: self.ppm_output.set("--- ppm")

    def update_walkthrough(self):
        for w in self.check_frame.winfo_children(): w.destroy()
        d = self.test_instructions.get(self.t_brand_var.get(), {}).get(self.t_param_var.get())
        if d:
            for s in d["steps"]: tk.Checkbutton(self.check_frame, text=s, wraplength=350).pack(anchor="w")
            self.remaining_time = d["time"]
            self.timer_btn.config(state="normal" if d["time"] > 0 else "disabled")
            self.timer_lbl.config(text=f"{d['time']//60:02d}:{d['time']%60:02d}")

    def start_timer(self):
        self.timer_running = True; self.run_timer()

    def run_timer(self):
        if self.timer_running and self.remaining_time > 0:
            self.remaining_time -= 1
            self.timer_lbl.config(text=f"{self.remaining_time//60:02d}:{self.remaining_time%60:02d}")
            self.root.after(1000, self.run_timer)
        elif self.remaining_time <= 0: self.timer_lbl.config(text="DONE!", fg="red")

    def silent_log(self, p, v, u):
        with open(self.log_file, "a", newline="") as f:
            csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), p, v, u])

    def refresh_hist(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                for r in list(csv.reader(f))[1:]: self.tree.insert("", "end", values=r)

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.b_menu['values'] = [k for k in self.brand_data.keys() if p[:3] in k or (p == "Nitrate" and "Carbon" in k)]
        if self.b_menu['values']: self.b_menu.current(0)
        self.targ_val_var.set(str(self.ranges[p]["target"]))

    def hard_exit(self): self.save_config(); self.root.destroy(); os._exit(0)

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
