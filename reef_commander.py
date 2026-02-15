import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv, os, sys
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.15.7")
        self.root.geometry("1150x980")
        self.root.protocol("WM_DELETE_WINDOW", self.hard_exit)
        
        self.log_file = "reef_logs.csv"
        self.config_file = "app_config.txt"
        self.init_csv()

        self.brand_data = {
            "ESV B-Ionic Alk (Part 1)": 1.4, "Fritz RPM Liquid Alk": 1.4,
            "ESV B-Ionic Cal (Part 2)": 20.0, "Fritz RPM Liquid Cal": 20.0,
            "Fritz RPM Liquid Mag": 100.0, "DIY Vinegar (5%)": 0.5,
            "Generic Carbon (NoPox)": 3.0
        }
        
        self.ranges = {
            "Alkalinity": {"target": 8.5, "low": 7.8, "high": 9.2, "crit_low": 7.0, "crit_high": 11.5, "units": ["dKH", "ppm"]},
            "Calcium": {"target": 420, "low": 400, "high": 440, "crit_low": 350, "crit_high": 500, "units": ["ppm"]},
            "Magnesium": {"target": 1350, "low": 1300, "high": 1400, "crit_low": 1200, "crit_high": 1550, "units": ["ppm"]},
            "Nitrate": {"target": 5.0, "low": 2.0, "high": 15.0, "crit_low": 0.0, "crit_high": 50.0, "units": ["ppm"]},
            "Phosphate": {"target": 0.03, "low": 0.01, "high": 0.08, "crit_low": 0.0, "crit_high": 0.25, "units": ["ppm"]},
            "Salinity": {"target": 1.025, "low": 1.024, "high": 1.026, "crit_low": 1.020, "crit_high": 1.030, "units": ["SG"]},
            "Temperature": {"target": 78.0, "low": 77.0, "high": 79.5, "crit_low": 72.0, "crit_high": 85.0, "units": ["°F"]}
        }

        # --- VARIABLES ---
        self.vol_var = tk.StringVar(value=self.load_config())
        self.p_var = tk.StringVar(value="Alkalinity")
        self.u_var = tk.StringVar(); self.b_var = tk.StringVar()
        self.curr_val_var = tk.StringVar(); self.targ_val_var = tk.StringVar()
        self.custom_str = tk.StringVar(); self.ph_fuge_var = tk.StringVar()
        self.m_u_var = tk.StringVar(value="dKH")
        self.m_alk_entry_var = tk.StringVar()
        self.harvest_var = tk.BooleanVar(value=False)

        # --- TRACES ---
        self.curr_val_var.trace_add("write", self.handle_unit_auto_switch)
        self.m_alk_entry_var.trace_add("write", self.handle_maint_auto_switch)
        self.u_var.trace_add("write", self.sync_target_unit)
        self.custom_str.trace_add("write", self.toggle_product_source)
        self.vol_var.trace_add("write", lambda *args: self.save_config())

        self.notebook = ttk.Notebook(root)
        self.tabs = {name: ttk.Frame(self.notebook) for name in ["Action Plan", "Maintenance", "Trends", "History"]}
        for name, frame in self.tabs.items(): self.notebook.add(frame, text=f" {name} ")
        self.notebook.pack(expand=True, fill="both")
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        
        self.build_dosage(); self.build_maint(); self.build_trends(); self.build_history()
        self.update_param_selection()

    def init_csv(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="") as f:
                csv.writer(f).writerow(["Timestamp", "Parameter", "Value", "Unit"])

    def load_config(self):
        return open(self.config_file, "r").read().strip() if os.path.exists(self.config_file) else ""

    def save_config(self):
        with open(self.config_file, "w") as f: f.write(self.vol_var.get())

    def on_tab_change(self, event):
        tab_name = self.notebook.tab(self.notebook.select(), "text").strip()
        if tab_name == "Trends": self.refresh_all_graphs()
        if tab_name == "History": self.refresh_hist()

    def handle_unit_auto_switch(self, *args):
        try:
            if self.p_var.get() == "Alkalinity" and float(self.curr_val_var.get()) > 25:
                self.u_var.set("ppm")
        except: pass

    def handle_maint_auto_switch(self, *args):
        try:
            if float(self.m_alk_entry_var.get()) > 25: self.m_u_var.set("ppm")
        except: pass

    def sync_target_unit(self, *args):
        p, u = self.p_var.get(), self.u_var.get()
        if p in self.ranges:
            base = self.ranges[p]["target"]
            self.targ_val_var.set(str(round(base * 17.86)) if p == "Alkalinity" and u == "ppm" else str(base))

    def build_dosage(self):
        f = ttk.Frame(self.tabs["Action Plan"], padding="20")
        f.pack(fill="both", expand=True)
        
        def row_add(text, var, combo=False, vals=None):
            row = ttk.Frame(f); row.pack(fill="x", pady=4)
            tk.Label(row, text=text, font=("Arial", 10, "bold"), width=30, anchor="w").pack(side="left")
            if combo:
                cb = ttk.Combobox(row, textvariable=var, values=vals, state="readonly")
                cb.pack(side="right", expand=True, fill="x"); return cb
            else:
                tk.Entry(row, textvariable=var).pack(side="right", expand=True, fill="x")

        row_add("Tank Volume (Gallons):", self.vol_var)
        self.p_menu = row_add("Correction Category:", self.p_var, True, ["Alkalinity", "Calcium", "Magnesium", "Nitrate", "Salinity"])
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)
        self.u_menu = row_add("Measurement Unit:", self.u_var, True)

        chem_frame = ttk.LabelFrame(f, text=" Correction Settings ", padding=15)
        chem_frame.pack(fill="x", pady=10)
        
        row_b = ttk.Frame(chem_frame); row_b.pack(fill="x", pady=2)
        tk.Label(row_b, text="Brand Product:").pack(side="left")
        self.b_menu = ttk.Combobox(row_b, textvariable=self.b_var, state="readonly")
        self.b_menu.pack(side="right", expand=True, fill="x")
        tk.Label(chem_frame, text="-- OR --", font=("Arial", 8, "italic")).pack()
        row_c = ttk.Frame(chem_frame); row_c.pack(fill="x", pady=2)
        tk.Label(row_c, text="(Optional) Custom Strength:").pack(side="left")
        tk.Entry(row_c, textvariable=self.custom_str).pack(side="right", expand=True, fill="x")
        
        row_add("Current Tank Reading:", self.curr_val_var)
        row_add("Target Goal:", self.targ_val_var)
        
        row_ph = ttk.Frame(f); row_ph.pack(fill="x", pady=4)
        self.ph_label = tk.Label(row_ph, text="pH (Safety Check):", font=("Arial", 10, "bold"), width=30, anchor="w")
        self.ph_label.pack(side="left")
        tk.Entry(row_ph, textvariable=self.ph_fuge_var).pack(side="right", expand=True, fill="x")

        tk.Button(f, text="CALCULATE ACTION PLAN", command=self.perform_calc, bg="#1a252f", fg="white", font=("Arial", 11, "bold"), height=2).pack(fill="x", pady=15)
        
        # STATUS LABELS (No Popups)
        self.res_lbl = tk.Label(f, text="---", font=("Arial", 12, "bold"), fg="#2980b9", justify="center", wraplength=600)
        self.res_lbl.pack(pady=5)
        self.status_log_lbl = tk.Label(f, text="", font=("Arial", 9, "italic"), fg="#27ae60")
        self.status_log_lbl.pack()

    def perform_calc(self):
        try:
            p, vol = self.p_var.get(), float(self.vol_var.get())
            curr, targ = float(self.curr_val_var.get()), float(self.targ_val_var.get())
            strength = float(self.custom_str.get()) if self.custom_str.get() else self.brand_data.get(self.b_var.get(), 1.0)
            
            std_curr = curr / (17.86 if (p == "Alkalinity" and self.u_var.get() == "ppm") else 1)
            std_targ = targ / (17.86 if (p == "Alkalinity" and self.u_var.get() == "ppm") else 1)
            total_ml = ((std_targ - std_curr) * vol) / strength
            
            if p == "Salinity":
                res_txt = f"Replace {(vol * (curr-targ))/targ:.2f}gal with RODI." if curr > targ else f"Add {((targ-curr)*vol*130):.0f}g salt."
                self.res_lbl.config(text=res_txt, fg="#e67e22")
            elif total_ml <= 0:
                self.res_lbl.config(text="LEVELS OPTIMAL", fg="green")
            else:
                days = 7 if (total_ml > 95 or abs(std_targ - std_curr) > 1.0) else 1
                forecast = (datetime.now() + timedelta(days=days)).strftime("%b %d")
                self.res_lbl.config(text=f"DOSE: {total_ml/days:.1f} mL/day | TARGET: {forecast}", fg="#c0392b")
                
                # SILENT AUTO-LOG (LOCKED)
                self.silent_log(f"Dose {p}", f"{total_ml/days:.1f}", "mL/day")
                self.status_log_lbl.config(text=f"✅ DOSE CALCULATION LOGGED AND LOCKED TO HISTORY")

        except: self.res_lbl.config(text="ERROR: Check Inputs", fg="red")

    def silent_log(self, param, val, unit):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(self.log_file, "a", newline="") as f:
            csv.writer(f).writerow([ts, param, val, unit])

    def build_maint(self):
        f = ttk.Frame(self.tabs["Maintenance"], padding="20"); f.pack(fill="both")
        self.m_entries = {}
        for g_name, params in [("Core Elements", ["Alkalinity", "Calcium", "Magnesium"]), ("Nutrients", ["Nitrate", "Phosphate"]), ("Environment", ["Salinity", "Temperature"])]:
            lf = ttk.LabelFrame(f, text=f" {g_name} ", padding=10); lf.pack(fill="x", pady=4)
            for p in params:
                row = ttk.Frame(lf); row.pack(fill="x", pady=2)
                tk.Label(row, text=p, font=("Arial", 9, "bold"), width=15, anchor="w").pack(side="left")
                e = tk.Entry(row, textvariable=(self.m_alk_entry_var if p == "Alkalinity" else None))
                e.pack(side="left", expand=True, fill="x")
                u_val = self.m_u_var if p == "Alkalinity" else tk.StringVar(value=self.ranges[p]["units"][0])
                if p == "Alkalinity":
                    ttk.Combobox(row, textvariable=u_val, values=["dKH", "ppm"], state="readonly", width=6).pack(side="left", padx=5)
                else:
                    tk.Label(row, text=u_val.get(), width=6, font=("Arial", 8, "italic")).pack(side="left", padx=5)
                self.m_entries[p] = (e, u_val)
        
        tk.Checkbutton(f, text="Harvested Macroalgae", variable=self.harvest_var).pack(pady=5)
        tk.Button(f, text="LOG TEST RESULTS (SILENT)", command=self.save_maint_silent, bg="#27ae60", fg="white", font=("Arial", 11, "bold")).pack(fill="x", pady=10)
        self.maint_status = tk.Label(f, text="", font=("Arial", 9, "italic"), fg="#27ae60")
        self.maint_status.pack()

    def save_maint_silent(self):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        logged_any = False
        with open(self.log_file, "a", newline="") as f:
            w = csv.writer(f)
            for p, (ent, u) in self.m_entries.items():
                if ent.get(): 
                    w.writerow([ts, p, ent.get(), u.get()])
                    logged_any = True
            if self.harvest_var.get(): w.writerow([ts, "Harvest", "1", "Event"])
        if logged_any: self.maint_status.config(text="✅ TEST DATA LOGGED SILENTLY")

    def build_trends(self):
        self.canvas_base = tk.Canvas(self.tabs["Trends"])
        scroll = ttk.Scrollbar(self.tabs["Trends"], orient="vertical", command=self.canvas_base.yview)
        self.scroll_frame = ttk.Frame(self.canvas_base)
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas_base.configure(scrollregion=self.canvas_base.bbox("all")))
        self.canvas_base.create_window((0,0), window=self.scroll_frame, anchor="nw")
        self.canvas_base.configure(yscrollcommand=scroll.set)
        self.canvas_base.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.figs_data = []
        for p in self.ranges.keys():
            fig, ax = plt.subplots(figsize=(9, 2.5))
            c = FigureCanvasTkAgg(fig, master=self.scroll_frame)
            c.get_tk_widget().pack(fill="x", padx=10, pady=5)
            self.figs_data.append({"fig": fig, "ax": ax, "p": p, "canvas": c})

    def refresh_all_graphs(self):
        if not os.path.exists(self.log_file): return
        with open(self.log_file, "r") as f:
            all_r = list(csv.reader(f))[1:]
            harvests = [r[0].split(" ")[0] for r in all_r if r[1] == "Harvest"]
        for item in self.figs_data:
            p, ax, c = item["p"], item["ax"], item["canvas"]
            dates, vals = [], []
            for r in all_r:
                if r[1] == p:
                    dates.append(r[0].split(" ")[0])
                    vals.append(float(r[2]) / (17.86 if p == "Alkalinity" and r[3] == "ppm" else 1))
            ax.clear()
            if vals:
                ax.plot(dates, vals, marker='o', color='black', linewidth=1.5, zorder=10)
                rng = self.ranges[p]
                ax.axhspan(rng["low"], rng["high"], color='#2ecc71', alpha=0.4, zorder=1) # Green
                ax.axhspan(rng["crit_low"], rng["low"], color='#f1c40f', alpha=0.25, zorder=1) # Yellow
                ax.axhspan(rng["high"], rng["crit_high"], color='#f1c40f', alpha=0.25, zorder=1)
                ax.axhspan(ax.get_ylim()[0], rng["crit_low"], color='#e74c3c', alpha=0.2, zorder=0) # Red
                ax.axhspan(rng["crit_high"], ax.get_ylim()[1], color='#e74c3c', alpha=0.2, zorder=0)
                ax.axhline(rng["target"], color='darkgreen', linestyle='--', alpha=0.7)
                for h in harvests: ax.axvline(h, color='orange', alpha=0.4, linestyle=':')
                ax.set_title(f"{p} Stability Chart", fontsize=10, fontweight='bold')
            c.draw()

    def build_history(self):
        f = self.tabs["History"]
        self.tree = ttk.Treeview(f, columns=("TS", "P", "V", "U"), show="headings")
        for c in ["TS", "P", "V", "U"]: self.tree.heading(c, text=c)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        btn_f = ttk.Frame(f); btn_f.pack(fill="x", pady=5, padx=20)
        tk.Button(btn_f, text="Delete Entry", command=self.delete_entry, bg="#e74c3c", fg="white").pack(side="left")
        tk.Button(btn_f, text="Export CSV", command=self.export_data, bg="#3498db", fg="white").pack(side="left", padx=10)
        self.refresh_hist()

    def refresh_hist(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                for r in list(csv.reader(f))[1:]: self.tree.insert("", "end", values=r)

    def delete_entry(self):
        sel = self.tree.selection()
        if sel:
            v = [str(x) for x in self.tree.item(sel[0])['values']]
            with open(self.log_file, "r") as f:
                r = list(csv.reader(f))
                header, data = r[0], [row for row in r[1:] if row != v]
            with open(self.log_file, "w", newline="") as f:
                writer = csv.writer(f); writer.writerow(header); writer.writerows(data)
            self.refresh_hist()

    def export_data(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if path: import shutil; shutil.copy2(self.log_file, path)

    def toggle_product_source(self, *args):
        self.b_menu.configure(state="disabled" if self.custom_str.get().strip() else "readonly")

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu['values'] = self.ranges[p]["units"]; self.u_menu.current(0)
        self.b_menu['values'] = [k for k in self.brand_data.keys() if p[:3] in k or (p == "Nitrate" and "Carbon" in k)]
        if self.b_menu['values']: self.b_menu.current(0)
        self.ph_label.config(text="Refugium Light Hrs:" if p == "Nitrate" else "pH (Safety Check):")
        self.sync_target_unit()

    def hard_exit(self):
        self.save_config(); self.root.destroy(); os._exit(0)

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
