import tkinter as tk
from tkinter import ttk, messagebox
import csv, os, sys
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.20.2 - Target Goal Edition")
        self.root.geometry("1450x950")
        self.root.protocol("WM_DELETE_WINDOW", self.hard_exit)
        
        self.log_file = "reef_logs.csv"
        self.config_file = "app_config.txt"
        self.unit_file = "unit_config.txt"
        self.init_csv()

        # Database
        self.brand_data = {
            "Alkalinity": {"Fritz RPM Liquid": 1.4, "ESV B-Ionic Part 1": 1.4, "Custom": 1.0},
            "Calcium": {"ESV B-Ionic Part 2": 20.0, "Fritz RPM Liquid": 20.0, "Custom": 1.0},
            "Magnesium": {"Fritz RPM Liquid": 100.0, "Custom": 1.0},
            "Nitrate": {"Generic Carbon (NoPox)": 3.0, "DIY Vinegar (5%)": 0.5, "Custom": 1.0},
            "Phosphate": {"Custom": 1.0}
        }

        self.test_instructions = {
            "Salifert": {
                "Alkalinity": [("4ml water", 0), ("2 drops KH-Ind", 0), ("Titrate until Pink", 0)],
                "Calcium": [("2ml water", 0), ("1 scoop Ca-1", 0), ("8 drops Ca-2", 10), ("Titrate Ca-3", 0)],
                "Magnesium": [("2ml water", 0), ("5 drops Mg-1", 0), ("1 scoop Mg-2", 0), ("Titrate Mg-3", 0)]
            },
            "Hanna": {
                "Alkalinity": [("10ml water (C1)", 0), ("Add 1ml Reagent", 0), ("Press Button", 0)],
                "Phosphate": [("10ml water (C1)", 0), ("Add packet/Shake 2m", 120), ("Hold for 3m Timer", 180)],
                "Nitrate": [("10ml water (C1)", 0), ("Add packet/Shake 2m", 120), ("Wait for 7m Timer", 420)]
            }
        }

        self.ranges = {
            "Alkalinity": {"target": 8.5, "low": 7.5, "high": 9.5, "danger_low": 6.5, "danger_high": 11.0, "max_daily": 1.4, "unit": "dKH", "ppm_target": 152},
            "Calcium": {"target": 420, "low": 380, "high": 460, "danger_low": 350, "danger_high": 500, "max_daily": 25.0, "unit": "ppm"},
            "Magnesium": {"target": 1350, "low": 1250, "high": 1450, "danger_low": 1100, "danger_high": 1600, "max_daily": 100.0, "unit": "ppm"},
            "Nitrate": {"target": 5.0, "low": 1.0, "high": 20.0, "danger_low": 0.0, "danger_high": 50.0, "max_daily": 5.0, "unit": "ppm"},
            "Phosphate": {"target": 0.03, "low": 0.01, "high": 0.1, "danger_low": 0.0, "danger_high": 0.5, "max_daily": 0.02, "unit": "ppm"}
        }

        # Vars
        self.vol_var = tk.StringVar(value=self.load_config(self.config_file, "220"))
        self.unit_mode = tk.StringVar(value=self.load_config(self.unit_file, "Gallons"))
        self.alk_u_var = tk.StringVar(value="ppm")
        self.p_var = tk.StringVar(value="Alkalinity")
        self.b_var = tk.StringVar(); self.custom_strength = tk.StringVar(value="1.4")
        self.curr_val_var = tk.StringVar(); self.targ_val_var = tk.StringVar(value="152")
        self.ph_var = tk.StringVar(); self.readout_var = tk.StringVar()
        self.t_brand_var = tk.StringVar(); self.t_param_var = tk.StringVar()
        self.m_vars = {p: tk.StringVar() for p in self.ranges.keys()}

        self.notebook = ttk.Notebook(root)
        self.tabs = {name: ttk.Frame(self.notebook) for name in ["Action Plan", "Maintenance", "Trends", "Testing & History"]}
        for name, frame in self.tabs.items(): self.notebook.add(frame, text=f" {name} ")
        self.notebook.pack(expand=True, fill="both")
        
        self.build_dosage(); self.build_maint(); self.build_history(); self.build_trends()
        self.update_product_list()
        
        # Observers
        self.curr_val_var.trace_add("write", lambda *a: self.smart_detect(self.curr_val_var))
        self.p_var.trace_add("write", self.update_product_list)
        self.t_param_var.trace_add("write", self.update_kits)
        self.t_brand_var.trace_add("write", self.update_steps)
        self.b_var.trace_add("write", self.toggle_custom_ui)

    def load_config(self, path, default):
        if not os.path.exists(path): return default
        with open(path, "r") as f: return f.read().strip()

    def build_dosage(self):
        f = ttk.Frame(self.tabs["Action Plan"], padding=20); f.pack(fill="both")
        r0 = ttk.LabelFrame(f, text=" 1. System Volume ", padding=10); r0.pack(fill="x", pady=5)
        tk.Entry(r0, textvariable=self.vol_var, width=10).pack(side="left", padx=5)
        ttk.Radiobutton(r0, text="Liters", variable=self.unit_mode, value="Liters").pack(side="left", padx=5)
        ttk.Radiobutton(r0, text="Gallons", variable=self.unit_mode, value="Gallons").pack(side="left", padx=5)

        r1 = ttk.LabelFrame(f, text=" 2. Parameter & Product ", padding=10); r1.pack(fill="x", pady=5)
        ttk.Combobox(r1, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly").pack(side="left", padx=5)
        ttk.Radiobutton(r1, text="dKH", variable=self.alk_u_var, value="dKH", command=self.sync_target).pack(side="left")
        ttk.Radiobutton(r1, text="PPM", variable=self.alk_u_var, value="ppm", command=self.sync_target).pack(side="left")
        
        tk.Label(r1, text="Product:").pack(side="left", padx=(10,0))
        self.b_cb = ttk.Combobox(r1, textvariable=self.b_var, state="readonly"); self.b_cb.pack(side="left", padx=5)
        self.custom_pane = ttk.Frame(r1)
        tk.Label(self.custom_pane, text="Strength (dKH/100L):").pack(side="left")
        tk.Entry(self.custom_pane, textvariable=self.custom_strength, width=8).pack(side="left")

        r3 = ttk.LabelFrame(f, text=" 3. Measurements ", padding=10); r3.pack(fill="x", pady=10)
        tk.Label(r3, text="Current:").pack(side="left"); tk.Entry(r3, textvariable=self.curr_val_var, width=10).pack(side="left", padx=5)
        tk.Label(r3, text="Target:").pack(side="left"); tk.Entry(r3, textvariable=self.targ_val_var, width=10).pack(side="left", padx=5)
        tk.Label(r3, text="pH (Opt):").pack(side="left", padx=10); tk.Entry(r3, textvariable=self.ph_var, width=8).pack(side="left")
        
        tk.Button(f, text="CALCULATE ACTION PLAN", command=self.calc_dose, bg="#2c3e50", fg="white", font=('Arial', 10, 'bold')).pack(fill="x", pady=10)
        self.res_lbl = tk.Label(f, text="---", font=("Arial", 12, "bold"), fg="#2980b9", justify="left"); self.res_lbl.pack()

    def sync_target(self):
        if self.p_var.get() == "Alkalinity":
            self.targ_val_var.set("152" if self.alk_u_var.get() == "ppm" else "8.5")

    def calc_dose(self):
        try:
            liters = float(self.vol_var.get()) * (3.78541 if self.unit_mode.get() == "Gallons" else 1.0)
            curr = float(self.curr_val_var.get()); targ = float(self.targ_val_var.get())
            param = self.p_var.get()
            
            gap = (targ - curr) / 17.86 if (param == "Alkalinity" and self.alk_u_var.get() == "ppm") else (targ - curr)
            strength = float(self.custom_strength.get()) if self.b_var.get() == "Custom" else self.brand_data[param][self.b_var.get()]
            
            total_ml = (gap * liters) / strength
            max_d = self.ranges[param]["max_daily"]
            days = max(1, abs(gap) / max_d)
            if self.ph_var.get() and float(self.ph_var.get()) > 8.35 and param == "Alkalinity": days *= 1.5
            
            days = int(days) + (1 if days % 1 > 0 else 0)
            daily_ml = total_ml / days
            
            self.res_lbl.config(text=f"Total: {total_ml:.1f} mL\nPlan: {daily_ml:.1f} mL/day for {days} days.", fg="#27ae60")
        except: self.res_lbl.config(text="Input Error", fg="red")

    def build_maint(self):
        f = ttk.Frame(self.tabs["Maintenance"], padding=20); f.pack(fill="both")
        for p in self.ranges.keys():
            r = ttk.Frame(f); r.pack(fill="x", pady=5)
            tk.Label(r, text=p, width=15, anchor="w").pack(side="left")
            tk.Entry(r, textvariable=self.m_vars[p]).pack(side="left", fill="x", expand=True)
            if p == "Alkalinity":
                ttk.Radiobutton(r, text="ppm", variable=self.alk_u_var, value="ppm").pack(side="left", padx=2)
                ttk.Radiobutton(r, text="dKH", variable=self.alk_u_var, value="dKH").pack(side="left", padx=2)
        tk.Button(f, text="LOG ALL", command=self.save_maint, bg="green", fg="white").pack(fill="x", pady=20)

    def build_trends(self):
        f = self.tabs["Trends"]; self.t_canv = ttk.Frame(f); self.t_canv.pack(fill="both", expand=True)
        tk.Button(f, text="REFRESH GRAPHS", command=self.refresh_graphs).pack(); self.refresh_graphs()

    def refresh_graphs(self):
        for w in self.t_canv.winfo_children(): w.destroy()
        try:
            df = pd.read_csv(self.log_file); df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            fig, axes = plt.subplots(len(self.ranges), 1, figsize=(8, 14), constrained_layout=True)
            for i, (p, r) in enumerate(self.ranges.items()):
                subset = df[df['Parameter'] == p].sort_values('Timestamp')
                ax = axes[i]
                
                # Determine Unit for labeling and scaling
                current_unit = r['unit']
                target_val = r['target']
                if p == "Alkalinity" and not subset.empty:
                    if subset.iloc[-1]['Value'] > 25:
                        current_unit = "ppm"
                        target_val = r['ppm_target']
                    else:
                        current_unit = "dKH"
                        target_val = r['target']
                
                if not subset.empty: ax.plot(subset['Timestamp'], subset['Value'], marker='o', color='black', label='Reading')
                
                # Safety zones scaling
                low, high = (r['low'] * 17.86, r['high'] * 17.86) if current_unit == "ppm" and p == "Alkalinity" else (r['low'], r['high'])
                
                ax.axhspan(low, high, color='green', alpha=0.15, label='Optimal Range')
                # NEW: TARGET GOAL LINE
                ax.axhline(target_val, color='blue', linestyle='--', alpha=0.8, label=f'Goal ({target_val})')
                
                ax.set_ylabel(current_unit, fontweight='bold')
                ax.set_title(f"{p} ({current_unit})")
                ax.legend(loc='upper right', fontsize='x-small')
                
            FigureCanvasTkAgg(fig, master=self.t_canv).get_tk_widget().pack(fill="both", expand=True)
        except: pass

    def build_history(self):
        f = self.tabs["Testing & History"]
        left = ttk.Frame(f, width=450, padding=10); left.pack(side="left", fill="y")
        ttk.Combobox(left, textvariable=self.t_param_var, values=list(self.ranges.keys()), state="readonly").pack(fill="x", pady=5)
        self.kit_cb = ttk.Combobox(left, textvariable=self.t_brand_var, state="readonly"); self.kit_cb.pack(fill="x", pady=5)
        self.step_f = ttk.LabelFrame(left, text=" Workflow ", padding=10); self.step_f.pack(fill="both", expand=True, pady=10)
        res_f = ttk.Frame(left); res_f.pack(fill="x")
        tk.Entry(res_f, textvariable=self.readout_var).pack(side="left", fill="x", expand=True)
        tk.Button(res_f, text="LOG", command=self.save_hist, bg="green", fg="white").pack(side="right")
        right = ttk.Frame(f, padding=10); right.pack(side="right", fill="both", expand=True)
        self.tree = ttk.Treeview(right, columns=("T", "P", "V"), show="headings")
        for c, h in [("T", "Time"), ("P", "Param"), ("V", "Value")]: self.tree.heading(c, text=h)
        self.tree.pack(fill="both", expand=True); self.tree.bind("<Button-3>", self.show_context_menu); self.refresh_history_table()

    def update_steps(self, *a):
        for w in self.step_f.winfo_children(): w.destroy()
        brand, p = self.t_brand_var.get(), self.t_param_var.get()
        if brand in self.test_instructions and p in self.test_instructions[brand]:
            for txt, sec in self.test_instructions[brand][p]:
                r = ttk.Frame(self.step_f); r.pack(fill="x", pady=2)
                tk.Checkbutton(r, text=txt).pack(side="left")
                if sec > 0:
                    btn = tk.Button(r, text=f"Start {sec}s", command=lambda rb=r, s=sec: self.run_timer(rb, s))
                    btn.pack(side="right")

    def run_timer(self, parent, seconds):
        btn = parent.winfo_children()[-1]
        if seconds > 0:
            btn.config(text=f"{seconds}s", state="disabled", bg="#f1c40f")
            self.root.after(1000, lambda: self.run_timer(parent, seconds-1))
        else: btn.config(text="DONE", state="normal", bg="#2ecc71", fg="white")

    def update_product_list(self, *a):
        brands = list(self.brand_data.get(self.p_var.get(), {}).keys())
        self.b_cb['values'] = brands
        if brands: self.b_cb.current(0)
        self.toggle_custom_ui()

    def toggle_custom_ui(self, *args):
        if self.b_var.get() == "Custom": self.custom_pane.pack(side="left", padx=10)
        else: self.custom_pane.pack_forget()

    def update_kits(self, *a):
        kits = [k for k in self.test_instructions if self.t_param_var.get() in self.test_instructions[k]]
        self.kit_cb['values'] = kits; self.kit_cb.current(0) if kits else self.kit_cb.set("")

    def smart_detect(self, var):
        try:
            v = float(var.get())
            if v > 20 and self.alk_u_var.get() == "dKH": self.alk_u_var.set("ppm")
            elif 0 < v < 15 and self.alk_u_var.get() == "ppm": self.alk_u_var.set("dKH")
        except: pass

    def save_hist(self):
        if self.readout_var.get():
            with open(self.log_file, "a", newline="") as f:
                csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), self.t_param_var.get(), self.readout_var.get(), ""])
            self.refresh_all()

    def save_maint(self):
        with open(self.log_file, "a", newline="") as f:
            w = csv.writer(f); ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            for p, v in self.m_vars.items():
                if v.get(): w.writerow([ts, p, v.get(), ""])
        self.refresh_all(); messagebox.showinfo("Logged", "Maintenance data saved.")

    def show_context_menu(self, e):
        row = self.tree.identify_row(e.y)
        if row:
            self.tree.selection_set(row)
            m = tk.Menu(self.root, tearoff=0); m.add_command(label="Delete", command=self.delete_entry); m.post(e.x_root, e.y_root)

    def delete_entry(self):
        sel = self.tree.item(self.tree.selection())['values']
        df = pd.read_csv(self.log_file)
        df = df[~((df['Timestamp'] == str(sel[0])) & (df['Parameter'] == str(sel[1])))]
        df.to_csv(self.log_file, index=False); self.refresh_all()

    def refresh_history_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if os.path.exists(self.log_file):
            df = pd.read_csv(self.log_file)
            for _, r in df.tail(15).iterrows(): self.tree.insert("", 0, values=(r['Timestamp'], r['Parameter'], r['Value']))

    def init_csv(self):
        if not os.path.exists(self.log_file): pd.DataFrame(columns=["Timestamp", "Parameter", "Value", "Unit"]).to_csv(self.log_file, index=False)
    def refresh_all(self): self.refresh_history_table(); self.refresh_graphs()
    def hard_exit(self):
        with open(self.config_file, "w") as f: f.write(self.vol_var.get())
        with open(self.unit_file, "w") as f: f.write(self.unit_mode.get())
        self.root.destroy(); os._exit(0)

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
