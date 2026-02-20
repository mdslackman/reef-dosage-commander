import tkinter as tk
from tkinter import ttk, messagebox
import csv, os, sys
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ReeferMadness:
    def __init__(self, root):
        self.root = root
        self.root.title("Reefer Madness v0.21.0 - Audited Final")
        self.root.geometry("1450x950")
        self.root.protocol("WM_DELETE_WINDOW", self.hard_exit)
        
        base_dir = os.path.expanduser("~/Documents/ReeferMadness")
        if not os.path.exists(base_dir): os.makedirs(base_dir)
        self.log_file = os.path.join(base_dir, "reef_logs.csv")
        self.config_file = os.path.join(base_dir, "app_config.txt")
        self.unit_file = os.path.join(base_dir, "unit_config.txt")
        self.init_csv()

        self.brand_data = {
            "Alkalinity": {"Fritz RPM Liquid": 1.4, "ESV B-Ionic Part 1": 1.4, "Custom": 1.0},
            "Calcium": {"ESV B-Ionic Part 2": 20.0, "Fritz RPM Liquid": 20.0, "Custom": 1.0},
            "Magnesium": {"Fritz RPM Liquid": 100.0, "Custom": 1.0},
            "Nitrate": {"Generic Carbon (NoPox)": 3.0, "DIY Vinegar (5%)": 0.5, "Custom": 1.0},
            "Phosphate": {"Custom": 1.0}
        }

        self.ranges = {
            "Alkalinity": {"target": 8.5, "low": 7.5, "high": 9.5, "max_daily": 1.4, "unit": "dKH", "ppm_target": 152},
            "Calcium": {"target": 420, "low": 400, "high": 440, "max_daily": 25.0, "unit": "ppm"},
            "Magnesium": {"target": 1350, "low": 1280, "high": 1420, "max_daily": 100.0, "unit": "ppm"},
            "Nitrate": {"target": 5.0, "low": 2.0, "high": 10.0, "max_daily": 5.0, "unit": "ppm"},
            "Phosphate": {"target": 0.03, "low": 0.01, "high": 0.08, "max_daily": 0.02, "unit": "ppm"}
        }

        # VARIABLES
        self.vol_var = tk.StringVar(value=self.load_config(self.config_file, "220"))
        self.unit_mode = tk.StringVar(value=self.load_config(self.unit_file, "Gallons"))
        self.alk_u_var = tk.StringVar(value="ppm")
        self.p_var = tk.StringVar(value="Alkalinity")
        self.b_var = tk.StringVar()
        self.custom_strength = tk.StringVar(value="1.0")
        self.curr_val_var = tk.StringVar(); self.targ_val_var = tk.StringVar(value="152")
        self.ph_var = tk.StringVar(); self.status_dose_var = tk.StringVar(value="Daily Dose: Not Set")
        self.m_vars = {p: tk.StringVar() for p in self.ranges.keys()}

        # UI
        header = tk.Frame(root, bg="#2c3e50", height=40); header.pack(fill="x")
        tk.Label(header, text="REEFER MADNESS v0.21.0", bg="#2c3e50", fg="#3498db", font=("Arial", 10, "bold")).pack(side="left", padx=20)
        tk.Label(header, textvariable=self.status_dose_var, bg="#2c3e50", fg="#2ecc71", font=("Arial", 10, "bold")).pack(side="right", padx=20)

        self.nb = ttk.Notebook(root)
        self.tabs = {n: ttk.Frame(self.nb) for n in ["Action Plan", "Maintenance", "Trends", "History"]}
        for n, f in self.tabs.items(): self.nb.add(f, text=f" {n} ")
        self.nb.pack(expand=True, fill="both")
        
        self.build_dosage(); self.build_maint(); self.build_trends(); self.build_history()
        
        # TRACES
        self.p_var.trace_add("write", self.update_product_list)
        self.alk_u_var.trace_add("write", self.sync_target)
        self.b_var.trace_add("write", self.toggle_custom_visibility)
        self.update_product_list()

    def load_config(self, p, d):
        if not os.path.exists(p): return d
        with open(p, "r") as f: return f.read().strip()

    def sync_target(self, *a):
        p = self.p_var.get()
        if p == "Alkalinity": self.targ_val_var.set("152" if self.alk_u_var.get() == "ppm" else "8.5")
        elif p in self.ranges: self.targ_val_var.set(str(self.ranges[p]["target"]))

    def update_product_list(self, *a):
        p = self.p_var.get()
        brands = list(self.brand_data.get(p, {}).keys())
        self.b_cb['values'] = brands
        if brands: 
            # Logic Audit Fix: Don't overwrite b_var if it's already "Custom"
            if self.b_var.get() not in brands: self.b_var.set(brands[0])
        self.toggle_custom_visibility()

    def toggle_custom_visibility(self, *a):
        if self.b_var.get() == "Custom": self.cpane.pack(side="left", padx=10)
        else: self.cpane.pack_forget()

    def build_dosage(self):
        f = ttk.Frame(self.tabs["Action Plan"], padding=20); f.pack(fill="both")
        r0 = ttk.LabelFrame(f, text=" 1. System Volume ", padding=10); r0.pack(fill="x", pady=5)
        tk.Entry(r0, textvariable=self.vol_var, width=10).pack(side="left")
        ttk.Radiobutton(r0, text="Gallons", variable=self.unit_mode, value="Gallons").pack(side="left", padx=5)
        ttk.Radiobutton(r0, text="Liters", variable=self.unit_mode, value="Liters").pack(side="left", padx=5)

        r1 = ttk.LabelFrame(f, text=" 2. Product Selection ", padding=10); r1.pack(fill="x", pady=5)
        ttk.Combobox(r1, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly").pack(side="left")
        ttk.Radiobutton(r1, text="dKH", variable=self.alk_u_var, value="dKH").pack(side="left", padx=5)
        ttk.Radiobutton(r1, text="PPM", variable=self.alk_u_var, value="ppm").pack(side="left")
        self.b_cb = ttk.Combobox(r1, textvariable=self.b_var, state="readonly"); self.b_cb.pack(side="left", padx=10)
        self.cpane = ttk.Frame(r1); tk.Label(self.cpane, text="Custom Strength:").pack(side="left")
        tk.Entry(self.cpane, textvariable=self.custom_strength, width=8).pack(side="left", padx=5)

        r2 = ttk.LabelFrame(f, text=" 3. Correction Plan ", padding=10); r2.pack(fill="x", pady=5)
        tk.Label(r2, text="Current:").pack(side="left"); tk.Entry(r2, textvariable=self.curr_val_var, width=8).pack(side="left", padx=5)
        tk.Label(r2, text="Target:").pack(side="left"); tk.Entry(r2, textvariable=self.targ_val_var, width=8).pack(side="left", padx=5)
        tk.Label(r2, text="pH (Opt):").pack(side="left", padx=10); tk.Entry(r2, textvariable=self.ph_var, width=6).pack(side="left")
        
        tk.Button(f, text="CALCULATE PLAN", command=self.calc_dose, bg="#2c3e50", fg="white", font=('Arial', 10, 'bold')).pack(fill="x", pady=10)
        self.res_lbl = tk.Label(f, text="---", font=("Arial", 12, "bold"), fg="#2980b9"); self.res_lbl.pack()

    def build_maint(self):
        f = ttk.Frame(self.tabs["Maintenance"], padding=20); f.pack(fill="both")
        cons_f = ttk.LabelFrame(f, text=" 1. Consumption Tracker ", padding=10); cons_f.pack(fill="x", pady=5)
        self.c_s, self.c_e, self.c_d = tk.StringVar(), tk.StringVar(), tk.StringVar(value="3")
        tk.Label(cons_f, text="Start Value:").pack(side="left"); tk.Entry(cons_f, textvariable=self.c_s, width=7).pack(side="left")
        tk.Label(cons_f, text="End Value:").pack(side="left", padx=5); tk.Entry(cons_f, textvariable=self.c_e, width=7).pack(side="left")
        tk.Label(cons_f, text="Days:").pack(side="left", padx=5); tk.Entry(cons_f, textvariable=self.c_d, width=5).pack(side="left")
        tk.Button(cons_f, text="CALC UPTAKE", command=self.calc_consumption, bg="#34495e", fg="white").pack(side="left", padx=10)
        self.c_res = tk.Label(cons_f, text="Daily Drop: 0.00", font=("Arial", 10, "bold"), fg="#8e44ad"); self.c_res.pack(side="left")

        log_f = ttk.LabelFrame(f, text=" 2. Log Readings ", padding=10); log_f.pack(fill="x", pady=15)
        u_row = ttk.Frame(log_f); u_row.pack(fill="x", pady=5)
        tk.Label(u_row, text="Unit Context:").pack(side="left")
        ttk.Radiobutton(u_row, text="dKH", variable=self.alk_u_var, value="dKH").pack(side="left", padx=5)
        ttk.Radiobutton(u_row, text="PPM", variable=self.alk_u_var, value="ppm").pack(side="left")

        for p in self.ranges.keys():
            r = ttk.Frame(log_f); r.pack(fill="x", pady=2)
            tk.Label(r, text=p, width=15, anchor="w").pack(side="left")
            tk.Entry(r, textvariable=self.m_vars[p], width=12).pack(side="left")
        tk.Button(log_f, text="SAVE LOGS", command=self.save_maint, bg="#27ae60", fg="white").pack(fill="x", pady=10)

    def build_history(self):
        f = self.tabs["History"]; f.pack(fill="both")
        test_f = ttk.LabelFrame(f, text=" Manual Entry Controls ", padding=10); test_f.pack(fill="x", padx=10, pady=5)
        self.h_p_var = tk.StringVar(value="Alkalinity"); self.h_v_var = tk.StringVar()
        ttk.Combobox(test_f, textvariable=self.h_p_var, values=list(self.ranges.keys()), state="readonly").pack(side="left", padx=5)
        tk.Entry(test_f, textvariable=self.h_v_var, width=10).pack(side="left", padx=5)
        tk.Button(test_f, text="LOG DATA", command=self.save_manual_history, bg="#2980b9", fg="white").pack(side="left", padx=10)
        tk.Button(test_f, text="DELETE SELECTED ROW", command=self.delete_entry, bg="#c0392b", fg="white").pack(side="right", padx=10)

        self.tree = ttk.Treeview(f, columns=("ID", "T", "P", "V"), show="headings")
        for c, h in [("ID", "Index"), ("T", "Timestamp"), ("P", "Parameter"), ("V", "Value")]: self.tree.heading(c, text=h)
        self.tree.column("ID", width=50); self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.refresh_history_table()

    def build_trends(self):
        f = self.tabs["Trends"]; self.t_canv = ttk.Frame(f); self.t_canv.pack(fill="both", expand=True)
        tk.Button(f, text="REFRESH ALL GRAPHS", command=self.refresh_graphs, bg="#2c3e50", fg="white").pack(pady=5); self.refresh_graphs()

    def refresh_graphs(self):
        for w in self.t_canv.winfo_children(): w.destroy()
        try:
            if not os.path.exists(self.log_file) or os.stat(self.log_file).st_size == 0: return
            df = pd.read_csv(self.log_file); df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            fig, axes = plt.subplots(len(self.ranges), 1, figsize=(8, 14), constrained_layout=True)
            for i, (p, r) in enumerate(self.ranges.items()):
                subset = df[df['Parameter'] == p].sort_values('Timestamp')
                ax = axes[i]; unit, targ = r['unit'], r['target']; low, high = r['low'], r['high']
                if p == "Alkalinity" and not subset.empty and subset.iloc[-1]['Value'] > 25: 
                    unit, targ, low, high = "ppm", r['ppm_target'], r['low']*17.86, r['high']*17.86
                # Safe Zone Restoration
                ax.fill_between(subset['Timestamp'] if not subset.empty else [datetime.now()], low, high, color='#2ecc71', alpha=0.15)
                if not subset.empty: ax.plot(subset['Timestamp'], subset['Value'], marker='o', color='black', linewidth=1.5)
                ax.axhline(targ, color='#3498db', ls='--', alpha=0.8); ax.set_title(f"{p} ({unit})")
            FigureCanvasTkAgg(fig, master=self.t_canv).get_tk_widget().pack(fill="both", expand=True)
        except: pass

    def calc_dose(self):
        try:
            liters = float(self.vol_var.get()) * (3.78541 if self.unit_mode.get() == "Gallons" else 1.0)
            cur, tar, p = float(self.curr_val_var.get()), float(self.targ_val_var.get()), self.p_var.get()
            gap = (tar - cur) / 17.86 if (p == "Alkalinity" and self.alk_u_var.get() == "ppm") else (tar - cur)
            strn = float(self.custom_strength.get()) if self.b_var.get() == "Custom" else self.brand_data[p][self.b_var.get()]
            tot = (gap * liters) / strn
            days = max(1, abs(gap) / self.ranges[p]["max_daily"])
            if self.ph_var.get() and float(self.ph_var.get()) > 8.35 and p == "Alkalinity": days *= 1.5
            days = int(days) + (1 if days % 1 > 0 else 0)
            self.res_lbl.config(text=f"Total: {tot:.1f} mL\nPlan: {tot/days:.1f} mL/day for {days} days", fg="#27ae60")
        except: self.res_lbl.config(text="INPUT ERROR", fg="red")

    def calc_consumption(self):
        try:
            s, e, d = float(self.c_s.get()), float(self.c_e.get()), float(self.c_d.get())
            liters = float(self.vol_var.get()) * (3.78541 if self.unit_mode.get() == "Gallons" else 1.0)
            p, drop = self.p_var.get(), (s - e) / d
            if p == "Alkalinity" and self.alk_u_var.get() == "ppm": drop /= 17.86
            strn = float(self.custom_strength.get()) if self.b_var.get() == "Custom" else self.brand_data[p][self.b_var.get()]
            daily_ml = (drop * liters) / strn
            self.c_res.config(text=f"Drop: {drop:.3f} | Dose: {daily_ml:.2f} mL/day")
            self.status_dose_var.set(f"Daily {p}: {daily_ml:.1f} mL")
        except: messagebox.showerror("Error", "Check Numeric Inputs.")

    def save_manual_history(self):
        if not self.h_v_var.get(): return
        self.write_to_csv(self.h_p_var.get(), self.h_v_var.get())
        self.h_v_var.set(""); self.refresh_all()

    def save_maint(self):
        for p, v in self.m_vars.items():
            if v.get(): self.write_to_csv(p, v.get())
            v.set("")
        self.refresh_all(); messagebox.showinfo("Success", "Daily Logs Saved.")

    def write_to_csv(self, p, v):
        with open(self.log_file, "a", newline="") as f:
            w = csv.writer(f); ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            w.writerow([ts, p, v, ""])

    def delete_entry(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Delete", "Delete row permanently?"):
            row_idx = int(self.tree.item(sel[0])['values'][0])
            df = pd.read_csv(self.log_file)
            df = df.drop(df.index[row_idx]).reset_index(drop=True)
            df.to_csv(self.log_file, index=False)
            self.refresh_all()

    def refresh_history_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if os.path.exists(self.log_file) and os.stat(self.log_file).st_size > 0:
            df = pd.read_csv(self.log_file)
            # Logic Audit: Displaying in descending order so newest is on top
            for i, r in df.iterrows(): self.tree.insert("", 0, values=(i, r['Timestamp'], r['Parameter'], r['Value']))

    def init_csv(self):
        if not os.path.exists(self.log_file): pd.DataFrame(columns=["Timestamp", "Parameter", "Value", "Unit"]).to_csv(self.log_file, index=False)
    def hard_exit(self):
        with open(self.config_file, "w") as f: f.write(self.vol_var.get())
        with open(self.unit_file, "w") as f: f.write(self.unit_mode.get())
        self.root.destroy(); os._exit(0)
    def refresh_all(self): self.refresh_history_table(); self.refresh_graphs()

if __name__ == "__main__":
    root = tk.Tk(); app = ReeferMadness(root); root.mainloop()
