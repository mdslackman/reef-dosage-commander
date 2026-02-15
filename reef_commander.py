import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv, os, sys
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.15.3")
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
            "Alkalinity": {"target": 8.5, "low": 7.0, "high": 11.0, "units": ["dKH", "ppm"]},
            "Calcium": {"target": 420, "low": 380, "high": 480, "units": ["ppm"]},
            "Magnesium": {"target": 1350, "low": 1250, "high": 1450, "units": ["ppm"]},
            "Nitrate": {"target": 5.0, "low": 1.0, "high": 20.0, "units": ["ppm"]},
            "Phosphate": {"target": 0.03, "low": 0.01, "high": 0.1, "units": ["ppm"]},
            "Salinity": {"target": 1.025, "low": 1.023, "high": 1.027, "units": ["SG"]},
            "Temperature": {"target": 78.0, "low": 75.0, "high": 82.0, "units": ["°F"]}
        }

        # --- VARIABLES ---
        self.vol_var = tk.StringVar(value=self.load_config())
        self.p_var = tk.StringVar(value="Alkalinity")
        self.u_var = tk.StringVar(); self.b_var = tk.StringVar()
        self.curr_val_var = tk.StringVar(); self.targ_val_var = tk.StringVar()
        self.custom_str = tk.StringVar(); self.ph_var = tk.StringVar()
        self.m_u_var = tk.StringVar(value="dKH")
        self.m_alk_entry_var = tk.StringVar()
        self.fuge_light_hrs = tk.StringVar(value="12")
        self.harvest_var = tk.BooleanVar(value=False)

        # --- TRACES ---
        self.curr_val_var.trace_add("write", self.handle_unit_auto_switch)
        self.m_alk_entry_var.trace_add("write", self.handle_maint_auto_switch)
        self.u_var.trace_add("write", self.sync_target_unit)
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
        if self.notebook.tab(self.notebook.select(), "text").strip() == "Trends":
            self.refresh_all_graphs()

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
            row = ttk.Frame(f); row.pack(fill="x", pady=2)
            tk.Label(row, text=text, font=("Arial", 10, "bold"), width=28, anchor="w").pack(side="left")
            if combo:
                cb = ttk.Combobox(row, textvariable=var, values=vals, state="readonly")
                cb.pack(side="right", expand=True, fill="x"); return cb
            else:
                tk.Entry(row, textvariable=var).pack(side="right", expand=True, fill="x")

        row_add("Tank Volume (Gal):", self.vol_var)
        self.p_menu = row_add("Correction Type:", self.p_var, True, ["Alkalinity", "Calcium", "Magnesium", "Nitrate", "Salinity"])
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)
        self.u_menu = row_add("Unit:", self.u_var, True)

        chem_frame = ttk.LabelFrame(f, text=" Correction Settings ", padding=10)
        chem_frame.pack(fill="x", pady=10)
        
        self.b_menu = ttk.Combobox(chem_frame, textvariable=self.b_var, state="readonly")
        self.b_menu.pack(fill="x", pady=2)
        
        row_add("Current Reading:", self.curr_val_var)
        row_add("Target Goal:", self.targ_val_var)
        row_add("pH / Fuge Light Hours:", self.ph_var)

        tk.Button(f, text="CALCULATE ACTION PLAN", command=self.perform_calc, bg="#1a252f", fg="white", font=("Arial", 11, "bold"), height=2).pack(fill="x", pady=15)
        self.res_lbl = tk.Label(f, text="---", font=("Arial", 12, "bold"), fg="#2980b9", justify="center", wraplength=550)
        self.res_lbl.pack(pady=5)

    def perform_calc(self):
        try:
            p, vol = self.p_var.get(), float(self.vol_var.get())
            curr, targ = float(self.curr_val_var.get()), float(self.targ_val_var.get())
            strength = self.brand_data.get(self.b_var.get(), 1.0)
            
            if p == "Salinity":
                if curr > targ:
                    rodi = (vol * (curr - targ)) / targ
                    self.res_lbl.config(text=f"HYPOSALINITY ALERT:\nRemove {rodi:.2f}g saltwater. Replace with RODI.", fg="#e67e22")
                else:
                    salt = (targ - curr) * vol * 130
                    self.res_lbl.config(text=f"RAISE SALINITY:\nAdd {salt:.0f}g salt. Max increase 0.001 SG per 24hrs.", fg="#2980b9")
                return

            if p == "Nitrate":
                dose = (0.1 if curr > 10 else 0.05) * vol
                self.res_lbl.config(text=f"NUTRIENT EXPORT:\nCarbon Dose: {dose:.1f} mL daily.\nCheck Refugium lighting if Nitrate stays > 15ppm.", fg="#8e44ad")
                return

            std_curr = curr / 17.86 if (p == "Alkalinity" and self.u_var.get() == "ppm") else curr
            std_targ = targ / 17.86 if (p == "Alkalinity" and self.u_var.get() == "ppm") else targ
            total_ml = ((std_targ - std_curr) * vol) / strength
            
            if total_ml <= 0: self.res_lbl.config(text="LEVELS OPTIMAL", fg="green")
            else:
                days = 7 if (total_ml > 95 or abs(std_targ - std_curr) > 1.0) else 1
                self.res_lbl.config(text=f"TOTAL: {total_ml:.1f} mL\n✅ DOSE: {total_ml/days:.1f} mL/day for {days} days", fg="#c0392b")
        except: self.res_lbl.config(text="ERROR: Check Inputs", fg="red")

    def build_maint(self):
        f = ttk.Frame(self.tabs["Maintenance"], padding="20"); f.pack(fill="both")
        self.m_entries = {}
        
        for g_name, params in [("Core", ["Alkalinity", "Calcium", "Magnesium"]), ("Nutrients", ["Nitrate", "Phosphate"]), ("Env", ["Salinity", "Temperature"])]:
            lf = ttk.LabelFrame(f, text=f" {g_name} ", padding=10); lf.pack(fill="x", pady=2)
            for p in params:
                row = ttk.Frame(lf); row.pack(fill="x", pady=1)
                tk.Label(row, text=p, font=("Arial", 9, "bold"), width=12).pack(side="left")
                e = tk.Entry(row, textvariable=(self.m_alk_entry_var if p == "Alkalinity" else None))
                e.pack(side="left", expand=True, fill="x")
                self.m_entries[p] = (e, tk.StringVar(value=self.ranges[p]["units"][0]))

        fuge_f = ttk.LabelFrame(f, text=" Biological Export ", padding=10)
        fuge_f.pack(fill="x", pady=5)
        tk.Checkbutton(fuge_f, text="Harvested Algae Today?", variable=self.harvest_var).pack(side="left")
        
        tk.Button(f, text="LOG DATA", command=self.save_data, bg="#27ae60", fg="white", font=("Arial", 11, "bold")).pack(fill="x", pady=15)

    def save_data(self):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            with open(self.log_file, "a", newline="") as f:
                w = csv.writer(f)
                for p, (ent, u) in self.m_entries.items():
                    if ent.get(): w.writerow([ts, p, ent.get(), u.get()])
                if self.harvest_var.get(): w.writerow([ts, "Harvest", "1", "Event"])
            messagebox.showinfo("Success", "Logged."); self.refresh_hist()
        except: messagebox.showerror("Error", "Save Failed.")

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
        for p in list(self.ranges.keys()):
            fig, ax = plt.subplots(figsize=(9, 2.2))
            c = FigureCanvasTkAgg(fig, master=self.scroll_frame)
            c.get_tk_widget().pack(fill="x", padx=10, pady=2)
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
                    dates.append(r[0].split(" ")[0]); vals.append(float(r[2]) / (17.86 if p == "Alkalinity" and r[3] == "ppm" else 1))
            ax.clear()
            if vals:
                ax.plot(dates, vals, marker='o', color='#2980b9', linewidth=1.5)
                ax.axhline(self.ranges[p]["target"], color='green', linestyle='--', alpha=0.3)
                for h in harvests: ax.axvline(h, color='orange', alpha=0.3, label="Harvest")
                ax.set_title(f"{p}", fontsize=9, loc='left')
            c.draw()

    def build_history(self):
        f = self.tabs["History"]
        self.tree = ttk.Treeview(f, columns=("TS", "P", "V", "U"), show="headings")
        for c in ["TS", "P", "V", "U"]: self.tree.heading(c, text=c)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        btn_f = ttk.Frame(f); btn_f.pack(fill="x", pady=10, padx=20)
        tk.Button(btn_f, text="Delete Selected", command=self.delete_entry, bg="#e74c3c", fg="white").pack(side="left")
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

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu['values'] = self.ranges[p]["units"]; self.u_menu.current(0)
        self.b_menu['values'] = [k for k in self.brand_data.keys() if p[:3] in k or (p == "Nitrate" and "Carbon" in k)]
        if self.b_menu['values']: self.b_menu.current(0)
        self.sync_target_unit()

    def hard_exit(self):
        self.save_config(); self.root.destroy(); os._exit(0)

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
