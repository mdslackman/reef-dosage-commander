import tkinter as tk
from tkinter import ttk, messagebox
import csv, os, sys
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.14.4")
        self.root.geometry("1000x900")
        
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
        self.ranges = {
            "Alkalinity": {"units": ["dKH", "ppm"], "target": 8.5, "low": 7.0, "high": 11.0, "brands": ["ESV B-Ionic Alk (Part 1)", "Fritz RPM Liquid Alk"]},
            "Calcium": {"units": ["ppm"], "target": 420, "low": 380, "high": 480, "brands": ["ESV B-Ionic Cal (Part 2)", "Fritz RPM Liquid Cal"]},
            "Magnesium": {"units": ["ppm"], "target": 1350, "low": 1250, "high": 1450, "brands": ["Fritz RPM Liquid Mag"]}
        }

        # Vars
        self.vol_var = tk.StringVar(); self.p_var = tk.StringVar(value="Alkalinity")
        self.u_var = tk.StringVar(); self.b_var = tk.StringVar()
        self.curr_val_var = tk.StringVar(); self.targ_val_var = tk.StringVar()
        self.custom_strength = tk.StringVar(); self.ph_var = tk.StringVar()
        
        self.curr_val_var.trace_add("write", self.handle_unit_auto_switch)
        self.u_var.trace_add("write", self.sync_target_unit)
        
        self.notebook = ttk.Notebook(root)
        self.tabs = {name: ttk.Frame(self.notebook) for name in ["Dosage", "Maintenance", "Trends", "History"]}
        for name, frame in self.tabs.items(): self.notebook.add(frame, text=f" {name} ")
        self.notebook.pack(expand=True, fill="both")
        
        self.build_dosage(); self.build_maint(); self.build_trends(); self.build_history()
        self.update_param_selection()

    def init_csv(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="") as f:
                csv.writer(f).writerow(["Timestamp", "Parameter", "Value"])

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
        
        l_style = ("Arial", 12, "bold")
        
        def add_field(text, var, combo=False, vals=None, color=None):
            row = ttk.Frame(f); row.pack(fill="x", pady=6)
            tk.Label(row, text=text, font=l_style, width=22, anchor="w").pack(side="left")
            if combo:
                cb = ttk.Combobox(row, textvariable=var, values=vals, state="readonly", font=("Arial", 12))
                cb.pack(side="right", expand=True, fill="x"); return cb
            else:
                e = tk.Entry(row, textvariable=var, font=("Arial", 12))
                if color: e.config(bg=color)
                e.pack(side="right", expand=True, fill="x")

        add_field("Tank Volume (Gal):", self.vol_var, color="#ffffcc")
        self.p_menu = add_field("Category:", self.p_var, True, list(self.ranges.keys()))
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)
        self.u_menu = add_field("Unit:", self.u_var, True)
        self.b_menu = add_field("Product Choice:", self.b_var, True)
        add_field("Current Reading:", self.curr_val_var)
        add_field("Target Goal:", self.targ_val_var)
        add_field("pH Level (Optional):", self.ph_var)
        add_field("Custom Strength (OPTIONAL):", self.custom_strength, color="#e8f4f8")

        tk.Button(f, text="CALCULATE SAFE DOSE", command=self.perform_calc, bg="#2c3e50", fg="white", font=("Arial", 13, "bold"), height=2).pack(fill="x", pady=20)
        self.res_lbl = tk.Label(f, text="---", font=("Arial", 15, "bold"), fg="#2980b9", justify="center")
        self.res_lbl.pack(pady=10)

    def perform_calc(self):
        try:
            p, vol, unit = self.p_var.get(), float(self.vol_var.get()), self.u_var.get()
            curr, targ = float(self.curr_val_var.get()), float(self.targ_val_var.get())
            
            std_curr = curr / 17.86 if (p == "Alkalinity" and unit == "ppm") else curr
            std_targ = targ / 17.86 if (p == "Alkalinity" and unit == "ppm") else targ
            
            strength = float(self.custom_strength.get()) if self.custom_strength.get() else self.brand_data.get(self.b_var.get(), 1.0)
            
            diff = std_targ - std_curr
            if diff <= 0:
                self.res_lbl.config(text="LEVELS OPTIMAL - NO DOSE NEEDED", fg="green")
            else:
                total_ml = (diff * vol) / strength
                # SAFETY SPREAD: Max 1.4 dKH (25 ppm) increase per day
                max_daily_rise = 1.4
                days_needed = max(1, round(diff / max_daily_rise, 1))
                
                output = f"TOTAL DOSE: {total_ml:.1f} mL\n"
                if days_needed > 1:
                    output += f"⚠️ SAFETY SPREAD: Dose {total_ml/days_needed:.1f} mL/day for {days_needed} days"
                else:
                    output += "Dose can be administered in a single day."
                self.res_lbl.config(text=output, fg="#c0392b")
        except: self.res_lbl.config(text="INPUT ERROR: Verify Volume and Readings", fg="red")

    def build_maint(self):
        f = ttk.Frame(self.tabs["Maintenance"], padding="40"); f.pack(fill="both")
        self.m_entries = {}
        for p in ["Alkalinity", "Calcium", "Magnesium"]:
            row = ttk.Frame(f); row.pack(fill="x", pady=10)
            tk.Label(row, text=f"{p}:", font=("Arial", 13), width=15).pack(side="left")
            e = tk.Entry(row, font=("Arial", 13)); e.pack(side="right", expand=True, fill="x"); self.m_entries[p] = e
        tk.Button(f, text="SAVE TEST RESULTS", command=self.save_data, bg="#27ae60", fg="white", font=("Arial", 13, "bold")).pack(fill="x", pady=30)

    def save_data(self):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            with open(self.log_file, "a", newline="") as f:
                writer = csv.writer(f)
                for p, ent in self.m_entries.items():
                    if ent.get(): writer.writerow([ts, p, ent.get()])
            messagebox.showinfo("Success", "Data Saved."); self.refresh_hist()
        except: messagebox.showerror("Error", "File Access Error")

    def build_trends(self):
        f = self.tabs["Trends"]
        ctrls = ttk.Frame(f); ctrls.pack(fill="x", pady=10)
        tk.Button(ctrls, text="REFRESH GRAPH", command=self.update_graph, font=("Arial", 10, "bold")).pack(side="left", padx=20)
        
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=f)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_graph(self):
        if not os.path.exists(self.log_file): return
        p = self.p_var.get()
        vals = []
        with open(self.log_file, "r") as f:
            reader = csv.reader(f); next(reader)
            for row in reader:
                if row[1] == p: vals.append(float(row[2]))
        
        self.ax.clear()
        if vals:
            self.ax.plot(vals, marker='o', color='#2980b9', linewidth=2, label=f"Your {p}")
            # Target & Limits logic
            target = self.ranges[p]["target"]
            # Convert target to ppm for graph if unit is ppm
            if p == "Alkalinity" and self.u_var.get() == "ppm": target *= 17.86
            
            self.ax.axhline(y=target, color='green', linestyle='--', alpha=0.5, label="Target")
            self.ax.fill_between(range(len(vals)), self.ranges[p]["low"], self.ranges[p]["high"], color='green', alpha=0.1)
            self.ax.set_title(f"{p} Trend Analysis")
            self.ax.legend()
        self.canvas.draw()

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu['values'] = self.ranges[p]["units"]; self.u_menu.current(0)
        self.b_menu['values'] = self.ranges[p]["brands"]; self.b_menu.current(0)
        self.sync_target_unit()

    def build_history(self):
        f = self.tabs["History"]
        self.hist_txt = tk.Text(f, font=("Courier New", 12), bg="#f4f4f4"); self.hist_txt.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Button(f, text="RELOAD LOG FILE", command=self.refresh_hist).pack(pady=10)

    def refresh_hist(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                self.hist_txt.delete("1.0", tk.END); self.hist_txt.insert(tk.END, f.read())

    def hard_exit(self):
        self.root.destroy(); os._exit(0)

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
