import tkinter as tk
from tkinter import ttk, messagebox
import csv, os, sys
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.14.6")
        self.root.geometry("1150x900")
        self.root.protocol("WM_DELETE_WINDOW", self.hard_exit)
        
        self.log_file = "reef_logs.csv"
        self.init_csv()

        self.brand_data = {
            "ESV B-Ionic Alk (Part 1)": 1.4,
            "Fritz RPM Liquid Alk": 1.4,
            "ESV B-Ionic Cal (Part 2)": 20.0,
            "Fritz RPM Liquid Cal": 20.0,
            "Fritz RPM Liquid Mag": 100.0
        }
        # Refined Ranges with Warning Thresholds
        self.ranges = {
            "Alkalinity": {"target": 8.5, "low": 7.0, "high": 11.0, "units": ["dKH", "ppm"]},
            "Calcium": {"target": 420, "low": 380, "high": 480, "units": ["ppm"]},
            "Magnesium": {"target": 1350, "low": 1250, "high": 1450, "units": ["ppm"]}
        }

        # --- VARIABLES ---
        self.vol_var = tk.StringVar()
        self.p_var = tk.StringVar(value="Alkalinity")
        self.u_var = tk.StringVar()
        self.b_var = tk.StringVar()
        self.curr_val_var = tk.StringVar()
        self.targ_val_var = tk.StringVar()
        self.custom_str = tk.StringVar()
        self.ph_var = tk.StringVar()
        
        # Maint Tab Vars
        self.m_u_var = tk.StringVar(value="dKH")
        
        # Traces
        self.curr_val_var.trace_add("write", self.handle_unit_auto_switch)
        self.u_var.trace_add("write", self.sync_target_unit)
        self.custom_str.trace_add("write", self.toggle_product_source)
        
        self.notebook = ttk.Notebook(root)
        self.tabs = {name: ttk.Frame(self.notebook) for name in ["Dosage", "Maintenance", "Trends", "History"]}
        for name, frame in self.tabs.items(): self.notebook.add(frame, text=f" {name} ")
        self.notebook.pack(expand=True, fill="both")
        
        self.build_dosage(); self.build_maint(); self.build_trends(); self.build_history()
        self.update_param_selection()

    def init_csv(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="") as f:
                csv.writer(f).writerow(["Timestamp", "Parameter", "Value", "Unit"])

    def toggle_product_source(self, *args):
        """Disables product dropdown if custom chemical strength is provided."""
        if self.custom_str.get().strip():
            self.b_menu.configure(state="disabled")
        else:
            self.b_menu.configure(state="readonly")

    def handle_unit_auto_switch(self, *args):
        try:
            val = float(self.curr_val_var.get())
            if self.p_var.get() == "Alkalinity" and self.u_var.get() == "dKH" and val > 25:
                self.u_var.set("ppm")
        except: pass

    def sync_target_unit(self, *args):
        p, u = self.p_var.get(), self.u_var.get()
        base = self.ranges[p]["target"]
        if p == "Alkalinity" and u == "ppm":
            self.targ_val_var.set(str(round(base * 17.86)))
        else: self.targ_val_var.set(str(base))

    def build_dosage(self):
        f = ttk.Frame(self.tabs["Dosage"], padding="30")
        f.pack(fill="both", expand=True)
        
        def add_field(text, var, combo=False, vals=None):
            row = ttk.Frame(f); row.pack(fill="x", pady=6)
            tk.Label(row, text=text, font=("Arial", 11, "bold"), width=28, anchor="w").pack(side="left")
            if combo:
                cb = ttk.Combobox(row, textvariable=var, values=vals, state="readonly", font=("Arial", 11))
                cb.pack(side="right", expand=True, fill="x"); return cb
            else:
                tk.Entry(row, textvariable=var, font=("Arial", 11)).pack(side="right", expand=True, fill="x")

        add_field("Tank Volume (Gal):", self.vol_var)
        self.p_menu = add_field("Category:", self.p_var, True, list(self.ranges.keys()))
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)
        self.u_menu = add_field("Unit:", self.u_var, True)
        self.b_menu = add_field("Product Choice:", self.b_var, True)
        add_field("Current Reading:", self.curr_val_var)
        add_field("Target Goal:", self.targ_val_var)
        add_field("pH (Safety Check):", self.ph_var)
        
        tk.Label(f, text="--- OR ---", font=("Arial", 9, "italic")).pack(pady=5)
        add_field("Custom Chemical Strength (Optional):", self.custom_str)

        tk.Button(f, text="CALCULATE STABILITY DOSE", command=self.perform_calc, bg="#1a252f", fg="white", font=("Arial", 12, "bold"), height=2).pack(fill="x", pady=20)
        self.res_lbl = tk.Label(f, text="---", font=("Arial", 14, "bold"), fg="#2980b9", justify="center")
        self.res_lbl.pack(pady=10)

    def perform_calc(self):
        try:
            p, vol, unit = self.p_var.get(), float(self.vol_var.get()), self.u_var.get()
            curr, targ = float(self.curr_val_var.get()), float(self.targ_val_var.get())
            
            # Unit Standarization
            std_curr = curr / 17.86 if (p == "Alkalinity" and unit == "ppm") else curr
            std_targ = targ / 17.86 if (p == "Alkalinity" and unit == "ppm") else targ
            
            strength = float(self.custom_str.get()) if self.custom_str.get() else self.brand_data.get(self.b_var.get(), 1.0)
            
            total_ml = ((std_targ - std_curr) * vol) / strength
            
            if total_ml <= 0:
                self.res_lbl.config(text="LEVELS OPTIMAL - NO DOSE REQUIRED", fg="green")
            else:
                # --- SAFETY LOGIC ---
                # 1. 95ml Daily Cap
                # 2. 7-Day spread for large corrections (> 1.0 dKH)
                days = 1
                if total_ml > 95 or abs(std_targ - std_curr) > 1.0:
                    days = 7
                
                daily_dose = total_ml / days
                msg = f"TOTAL CORRECTION: {total_ml:.1f} mL\n"
                msg += f"✅ SAFETY PROTOCOL: Dose {daily_dose:.1f} mL/day for {days} days"
                self.res_lbl.config(text=msg, fg="#c0392b")
        except: self.res_lbl.config(text="ERROR: Check Tank Volume and Inputs", fg="red")

    def build_maint(self):
        f = ttk.Frame(self.tabs["Maintenance"], padding="40"); f.pack(fill="both")
        self.m_entries = {}
        
        # Maintenance Unit Toggle
        u_row = ttk.Frame(f); u_row.pack(fill="x", pady=10)
        tk.Label(u_row, text="Log Alkalinity as:", font=("Arial", 11, "bold")).pack(side="left")
        ttk.Combobox(u_row, textvariable=self.m_u_var, values=["dKH", "ppm"], state="readonly").pack(side="right")

        for p in ["Alkalinity", "Calcium", "Magnesium"]:
            row = ttk.Frame(f); row.pack(fill="x", pady=10)
            tk.Label(row, text=f"{p}:", font=("Arial", 12), width=15, anchor="w").pack(side="left")
            e = tk.Entry(row, font=("Arial", 12)); e.pack(side="right", expand=True, fill="x")
            self.m_entries[p] = e
            
        tk.Button(f, text="LOG TEST RESULTS", command=self.save_data, bg="#27ae60", fg="white", font=("Arial", 12, "bold"), height=2).pack(fill="x", pady=30)

    def save_data(self):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            with open(self.log_file, "a", newline="") as f:
                writer = csv.writer(f)
                for p, ent in self.m_entries.items():
                    if ent.get():
                        unit = self.m_u_var.get() if p == "Alkalinity" else "ppm"
                        writer.writerow([ts, p, ent.get(), unit])
            messagebox.showinfo("Success", "Maintenance Log Updated."); self.refresh_hist()
        except: messagebox.showerror("Error", "Could not write to reef_logs.csv")

    def build_trends(self):
        f = self.tabs["Trends"]
        ctrls = ttk.Frame(f, padding=10); ctrls.pack(fill="x")
        self.graph_p = tk.StringVar(value="Alkalinity")
        tk.Label(ctrls, text="Parameter View:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        ttk.OptionMenu(ctrls, self.graph_p, "Alkalinity", "Alkalinity", "Calcium", "Magnesium").pack(side="left", padx=10)
        tk.Button(ctrls, text="REFRESH TRENDS", command=self.update_graph, bg="#34495e", fg="white").pack(side="left", padx=10)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=f)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_graph(self):
        if not os.path.exists(self.log_file): return
        p = self.graph_p.get()
        dates, vals = [], []
        
        with open(self.log_file, "r") as f:
            reader = csv.reader(f); next(reader)
            for row in reader:
                if row[1] == p:
                    v = float(row[2])
                    # Logic: If looking at Alk graph, convert ppm entries to dKH for uniform visualization
                    if p == "Alkalinity" and row[3] == "ppm": v = v / 17.86
                    dates.append(row[0].split(" ")[0]); vals.append(v)
        
        self.ax.clear()
        if vals:
            self.ax.plot(dates, vals, marker='o', color='#2980b9', linewidth=2, label=f"Measured {p}")
            t, l, h = self.ranges[p]["target"], self.ranges[p]["low"], self.ranges[p]["high"]
            
            # Draw Zones
            self.ax.axhline(t, color='green', linestyle='--', linewidth=1.5, label="Target Goal")
            self.ax.axhspan(l, h, color='green', alpha=0.15, label="Safe Range")
            self.ax.axhspan(h, h + (h*0.2), color='red', alpha=0.1, label="Danger High")
            self.ax.axhspan(l - (l*0.2), l, color='red', alpha=0.1, label="Danger Low")
            
            self.ax.set_title(f"Reef Stability Trends: {p}", fontsize=14, pad=15)
            self.ax.set_xlabel("Time (Date Logged)", fontsize=10)
            self.ax.set_ylabel(f"Reading ({'dKH' if p=='Alkalinity' else 'ppm'})", fontsize=10)
            self.ax.legend(loc='upper right', frameon=True, fontsize='small')
            plt.setp(self.ax.get_xticklabels(), rotation=35, horizontalalignment='right')
        
        self.fig.tight_layout(); self.canvas.draw()

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu['values'] = self.ranges[p]["units"]; self.u_menu.current(0)
        # Filter brands for Mag
        if p == "Magnesium": self.b_menu['values'] = ["Fritz RPM Liquid Mag"]
        else: self.b_menu['values'] = [k for k in self.brand_data.keys() if p[:3] in k]
        self.b_menu.current(0)
        self.sync_target_unit()

    def build_history(self):
        f = self.tabs["History"]
        self.hist_txt = tk.Text(f, font=("Courier New", 10), bg="#fdfdfd"); self.hist_txt.pack(fill="both", expand=True, padx=15, pady=15)
        tk.Button(f, text="SYNC WITH LOG FILE", command=self.refresh_hist).pack(pady=10)

    def refresh_hist(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                self.hist_txt.delete("1.0", tk.END); self.hist_txt.insert(tk.END, f.read())

    def hard_exit(self):
        self.root.destroy(); os._exit(0)

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
