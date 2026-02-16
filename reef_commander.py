import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv, os, sys, time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.16.6")
        self.root.geometry("1200x950")
        self.root.protocol("WM_DELETE_WINDOW", self.hard_exit)
        
        self.log_file = "reef_logs.csv"
        self.config_file = "app_config.txt"
        self.init_csv()

        # --- DATABASE ---
        self.brand_data = {
            "Alkalinity": {"ESV B-Ionic Part 1": 1.4, "Fritz RPM Liquid": 1.4, "Custom": 1.0},
            "Calcium": {"ESV B-Ionic Part 2": 20.0, "Fritz RPM Liquid": 20.0, "Custom": 1.0},
            "Magnesium": {"Fritz RPM Liquid": 100.0, "Custom": 1.0},
            "Nitrate": {"Generic Carbon (NoPox)": 3.0, "DIY Vinegar (5%)": 0.5, "Custom": 1.0},
            "Phosphate": {"Custom": 1.0}
        }

        self.test_instructions = {
            "Salifert": {
                "Alkalinity": {"steps": ["4ml water", "2 drops KH-Ind (swirl)", "Add reagent until Pink"], "time": 0},
                "Calcium": {"steps": ["2ml water", "1 scoop Ca-1 powder", "Add 0.6ml Ca-2 then dropwise"], "time": 0},
                "Magnesium": {"steps": ["2ml water", "6 drops Mg-1", "1 scoop Mg-2", "Dropwise Mg-3 until Blue"], "time": 0},
                "Nitrate": {"steps": ["1ml water", "4ml NO3-1", "1 scoop NO3-2", "Swirl 30s", "Wait 3 mins"], "time": 180},
                "Phosphate": {"steps": ["10ml water", "4 drops PO4-1", "1 scoop PO4-2", "Wait 5 mins"], "time": 300}
            },
            "Hanna": {
                "Alkalinity": {"steps": ["10ml water (C1)", "Press button", "Add 1ml Reagent", "Invert 5x", "Press (C2)"], "time": 0},
                "Phosphate": {"steps": ["10ml water (C1)", "Add reagent packet", "Shake 2 mins", "Long press for timer"], "time": 180},
                "Nitrate": {"steps": ["10ml water (C1)", "Add reagent packet", "Shake 2 mins", "Hold for timer"], "time": 420}
            }
        }

        self.ranges = {
            "Alkalinity": {"target": 8.5, "low": 7.8, "high": 9.2, "units": "dKH"},
            "Calcium": {"target": 420, "low": 400, "high": 440, "units": "ppm"},
            "Magnesium": {"target": 1350, "low": 1300, "high": 1400, "units": "ppm"},
            "Nitrate": {"target": 5.0, "low": 2.0, "high": 15.0, "units": "ppm"},
            "Phosphate": {"target": 0.03, "low": 0.01, "high": 0.08, "units": "ppm"},
            "Salinity": {"target": 1.025, "low": 1.024, "high": 1.026, "units": "SG"}
        }

        # --- VARIABLES ---
        self.unit_mode = tk.StringVar(value="Liters")
        self.vol_var = tk.StringVar(value=self.load_config())
        self.p_var = tk.StringVar(value="Alkalinity")
        self.alk_u_var = tk.StringVar(value="dKH")
        self.b_var = tk.StringVar()
        self.custom_strength = tk.StringVar(value="1.0")
        self.curr_val_var = tk.StringVar(); self.targ_val_var = tk.StringVar()
        self.ph_var = tk.StringVar()
        self.t_brand_var = tk.StringVar(); self.t_param_var = tk.StringVar()
        self.ppb_input = tk.StringVar(); self.ppm_output = tk.StringVar(value="--- ppm")
        self.timer_running = False; self.remaining_time = 0

        # UI Tabs
        self.notebook = ttk.Notebook(root)
        self.tabs = {name: ttk.Frame(self.notebook) for name in ["Action Plan", "Maintenance", "Trends", "Testing & History"]}
        for name, frame in self.tabs.items(): self.notebook.add(frame, text=f" {name} ")
        self.notebook.pack(expand=True, fill="both")
        
        self.build_dosage(); self.build_maint(); self.build_trends(); self.build_history()
        self.update_brands()

    # --- ACTION PLAN (Tab 1) ---
    def build_dosage(self):
        f = ttk.Frame(self.tabs["Action Plan"], padding=20); f.pack(fill="both")
        cfg = ttk.LabelFrame(f, text=" System Configuration ", padding=10); cfg.pack(fill="x", pady=5)
        ttk.Label(cfg, text="Volume:").pack(side="left")
        ttk.Entry(cfg, textvariable=self.vol_var, width=8).pack(side="left", padx=5)
        ttk.Radiobutton(cfg, text="Liters", variable=self.unit_mode, value="Liters").pack(side="left")
        ttk.Radiobutton(cfg, text="Gallons", variable=self.unit_mode, value="Gallons").pack(side="left")

        row1 = ttk.Frame(f); row1.pack(fill="x", pady=5)
        ttk.Label(row1, text="Parameter:").pack(side="left")
        p_cb = ttk.Combobox(row1, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly")
        p_cb.pack(side="left", padx=5); p_cb.bind("<<ComboboxSelected>>", self.update_brands)
        self.alk_unit_frame = ttk.Frame(row1)
        ttk.Radiobutton(self.alk_unit_frame, text="dKH", variable=self.alk_u_var, value="dKH").pack(side="left")
        ttk.Radiobutton(self.alk_unit_frame, text="PPM", variable=self.alk_u_var, value="ppm").pack(side="left")

        row2 = ttk.Frame(f); row2.pack(fill="x", pady=5)
        ttk.Label(row2, text="Product:").pack(side="left")
        self.b_cb = ttk.Combobox(row2, textvariable=self.b_var, state="readonly")
        self.b_cb.pack(side="left", padx=5); self.b_cb.bind("<<ComboboxSelected>>", self.toggle_custom)
        self.custom_f = ttk.Frame(row2)
        ttk.Label(self.custom_f, text="Strength:").pack(side="left")
        ttk.Entry(self.custom_f, textvariable=self.custom_strength, width=8).pack(side="left")

        row3 = ttk.Frame(f); row3.pack(fill="x", pady=5)
        ttk.Label(row3, text="Current:").pack(side="left")
        ttk.Entry(row3, textvariable=self.curr_val_var, width=10).pack(side="left", padx=5)
        ttk.Label(row3, text="Target:").pack(side="left")
        ttk.Entry(row3, textvariable=self.targ_val_var, width=10).pack(side="left", padx=5)
        ttk.Label(row3, text="pH (Log):").pack(side="left")
        ttk.Entry(row3, textvariable=self.ph_var, width=8).pack(side="left", padx=5)

        tk.Button(f, text="CALCULATE", command=self.perform_calc, bg="#2c3e50", fg="white", height=2).pack(fill="x", pady=15)
        self.res_lbl = tk.Label(f, text="---", font=("Arial", 12, "bold"), fg="#2980b9"); self.res_lbl.pack()

    # --- TESTING & HISTORY (Tab 4) ---
    def build_history(self):
        f = self.tabs["Testing & History"]
        walk_f = ttk.LabelFrame(f, text=" Guided Assistant ", padding=10)
        walk_f.pack(side="left", fill="both", padx=10, pady=10); walk_f.pack_propagate(False); walk_f.configure(width=420)
        
        # Safe Range Reference (New)
        self.range_info = tk.Label(walk_f, text="Select a test to see safe ranges", font=("Arial", 9, "italic"), fg="#7f8c8d")
        self.range_info.pack(pady=(0, 10))

        ttk.Label(walk_f, text="1. Select Test Type:").pack(anchor="w")
        t_cb = ttk.Combobox(walk_f, textvariable=self.t_param_var, values=list(self.ranges.keys()), state="readonly")
        t_cb.pack(fill="x", pady=2); t_cb.bind("<<ComboboxSelected>>", self.filter_test_brands)
        
        ttk.Label(walk_f, text="2. Select Kit Brand:").pack(anchor="w")
        self.tb_cb = ttk.Combobox(walk_f, textvariable=self.t_brand_var, state="readonly")
        self.tb_cb.pack(fill="x", pady=2); self.tb_cb.bind("<<ComboboxSelected>>", self.auto_load_steps)

        self.conv_f = ttk.LabelFrame(walk_f, text=" Hanna PPB -> PPM ", padding=5)
        ttk.Entry(self.conv_f, textvariable=self.ppb_input, width=10).pack(side="left")
        self.ppb_input.trace_add("write", self.convert_ppb)
        ttk.Label(self.conv_f, text=" ppb = ").pack(side="left")
        ttk.Label(self.conv_f, textvariable=self.ppm_output, font=("Arial", 10, "bold"), fg="#2980b9").pack(side="left")

        self.timer_lbl = tk.Label(walk_f, text="00:00", font=("Consolas", 28, "bold"))
        self.timer_lbl.pack(pady=10)
        self.t_btn = tk.Button(walk_f, text="START TIMER", command=self.toggle_timer_btn, bg="#27ae60", fg="white", font=("Arial", 10, "bold"))
        self.t_btn.pack(fill="x", pady=5)
        
        self.check_frame = ttk.Frame(walk_f); self.check_frame.pack(fill="both", expand=True, pady=10)

    # --- CORE METHODS ---
    def auto_load_steps(self, e=None):
        self.reset_timer()
        brand, param = self.t_brand_var.get(), self.t_param_var.get()
        
        # Converter visibility
        if brand == "Hanna" and param == "Phosphate": self.conv_f.pack(fill="x", pady=5)
        else: self.conv_f.pack_forget()

        # Update Reference Chart
        r = self.ranges.get(param)
        if r: self.range_info.config(text=f"SAFE RANGE: {r['low']} - {r['high']} {r['units']} (Target: {r['target']})", fg="#27ae60", font=("Arial", 9, "bold"))

        for w in self.check_frame.winfo_children(): w.destroy()
        d = self.test_instructions.get(brand, {}).get(param)
        if d:
            for s in d["steps"]: tk.Checkbutton(self.check_frame, text=s, wraplength=380, justify="left").pack(anchor="w", pady=2)
            self.remaining_time = d["time"]
            self.timer_lbl.config(text=f"{self.remaining_time//60:02d}:{self.remaining_time%60:02d}", fg="black")
            self.t_btn.config(state="normal" if d["time"] > 0 else "disabled")

    def toggle_timer_btn(self):
        if self.timer_running:
            self.timer_running = False
            self.t_btn.config(text="START TIMER", bg="#27ae60")
        else:
            self.timer_running = True
            self.t_btn.config(text="STOP TIMER", bg="#c0392b")
            self.run_timer()

    def reset_timer(self):
        self.timer_running = False
        self.t_btn.config(text="START TIMER", bg="#27ae60")

    def run_timer(self):
        if self.timer_running and self.remaining_time > 0:
            self.remaining_time -= 1
            self.timer_lbl.config(text=f"{self.remaining_time//60:02d}:{self.remaining_time%60:02d}")
            self.root.after(1000, self.run_timer)
        elif self.remaining_time <= 0 and self.timer_running:
            self.timer_running = False
            self.timer_lbl.config(text="TIME UP!", fg="red")
            self.t_btn.config(text="START TIMER", bg="#27ae60")

    def filter_test_brands(self, e=None):
        p = self.t_param_var.get()
        valid = [b for b in ["Salifert", "Hanna"] if p in self.test_instructions[b]]
        self.tb_cb['values'] = valid
        if valid: self.tb_cb.current(0); self.auto_load_steps()
        else: self.tb_cb.set(""); self.auto_load_steps()

    def update_brands(self, e=None):
        p = self.p_var.get()
        self.b_cb['values'] = list(self.brand_data.get(p, {}).keys())
        self.b_cb.current(0); self.toggle_custom()
        self.targ_val_var.set(str(self.ranges[p]["target"]))
        if p == "Alkalinity": self.alk_unit_frame.pack(side="left", padx=10)
        else: self.alk_unit_frame.pack_forget()

    def toggle_custom(self, e=None):
        if self.b_var.get() == "Custom": self.custom_f.pack(side="left", padx=5)
        else: self.custom_f.pack_forget()

    def perform_calc(self):
        try:
            v_val = float(self.vol_var.get() or 0)
            vol = v_val if self.unit_mode.get() == "Liters" else v_val * 3.785
            curr, targ = float(self.curr_val_var.get()), float(self.targ_val_var.get())
            str_val = float(self.custom_strength.get()) if self.b_var.get() == "Custom" else self.brand_data[self.p_var.get()][self.b_var.get()]
            res = ((targ - curr) * vol) / str_val
            self.res_lbl.config(text=f"Recommended Dose: {res:.2f} mL", fg="#c0392b" if res > 0 else "#27ae60")
        except: self.res_lbl.config(text="Error: Check Inputs", fg="red")

    def build_maint(self):
        f = ttk.Frame(self.tabs["Maintenance"], padding=20); f.pack(fill="both")
        self.m_entries = {}
        for p in ["Alkalinity", "Calcium", "Magnesium", "Nitrate", "Phosphate", "Salinity"]:
            row = ttk.Frame(f); row.pack(fill="x", pady=5)
            tk.Label(row, text=p, width=15, font=("Arial", 10, "bold")).pack(side="left")
            e = tk.Entry(row); e.pack(side="left", fill="x", expand=True)
            self.m_entries[p] = e
        tk.Button(f, text="SAVE TEST RESULTS", command=self.save_maint, bg="#27ae60", fg="white", height=2).pack(fill="x", pady=20)

    def save_maint(self):
        with open(self.log_file, "a", newline="") as f:
            w = csv.writer(f); ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            for p, e in self.m_entries.items():
                if e.get(): w.writerow([ts, p, e.get(), self.ranges[p]['units']])
        messagebox.showinfo("Saved", "Data logged successfully.")

    def build_trends(self):
        self.canvas_base = tk.Canvas(self.tabs["Trends"])
        scroll = ttk.Scrollbar(self.tabs["Trends"], orient="vertical", command=self.canvas_base.yview)
        self.scroll_frame = ttk.Frame(self.canvas_base)
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas_base.configure(scrollregion=self.canvas_base.bbox("all")))
        self.canvas_base.create_window((0,0), window=self.scroll_frame, anchor="nw")
        self.canvas_base.configure(yscrollcommand=scroll.set)
        self.canvas_base.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")
        self.figs = []
        for p in ["Alkalinity", "Calcium", "Magnesium", "Nitrate", "Phosphate", "Salinity"]:
            fig, ax = plt.subplots(figsize=(8, 2))
            c = FigureCanvasTkAgg(fig, master=self.scroll_frame)
            c.get_tk_widget().pack(fill="x", pady=5)
            self.figs.append((p, ax, c))

    def convert_ppb(self, *args):
        try: self.ppm_output.set(f"{(float(self.ppb_input.get()) * 3.066 / 1000):.3f} ppm")
        except: self.ppm_output.set("--- ppm")

    def init_csv(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="") as f:
                csv.writer(f).writerow(["Timestamp", "Parameter", "Value", "Unit"])

    def load_config(self):
        return open(self.config_file, "r").read().strip() if os.path.exists(self.config_file) else "0"

    def hard_exit(self):
        with open(self.config_file, "w") as f: f.write(self.vol_var.get())
        self.root.destroy(); os._exit(0)

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
