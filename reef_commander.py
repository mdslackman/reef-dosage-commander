import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv, os, sys
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.14.8")
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
        self.ranges = {
            "Alkalinity": {"target": 8.5, "low": 7.0, "high": 11.0, "units": ["dKH", "ppm"]},
            "Calcium": {"target": 420, "low": 380, "high": 480, "units": ["ppm"]},
            "Magnesium": {"target": 1350, "low": 1250, "high": 1450, "units": ["ppm"]}
        }

        # --- VARIABLES ---
        self.vol_var = tk.StringVar(); self.p_var = tk.StringVar(value="Alkalinity")
        self.u_var = tk.StringVar(); self.b_var = tk.StringVar()
        self.curr_val_var = tk.StringVar(); self.targ_val_var = tk.StringVar()
        self.custom_str = tk.StringVar(); self.ph_var = tk.StringVar()
        self.m_u_var = tk.StringVar(value="dKH"); self.graph_p = tk.StringVar(value="Alkalinity")
        
        # --- TRACES ---
        self.curr_val_var.trace_add("write", self.handle_unit_auto_switch)
        self.u_var.trace_add("write", self.sync_target_unit)
        self.custom_str.trace_add("write", self.toggle_product_source)
        self.graph_p.trace_add("write", lambda *args: self.update_graph())
        
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
        
        # Volume & Core Logic
        r_vol = ttk.Frame(f); r_vol.pack(fill="x", pady=5)
        tk.Label(r_vol, text="Tank Volume (Gal):", font=("Arial", 11, "bold"), width=25, anchor="w").pack(side="left")
        tk.Entry(r_vol, textvariable=self.vol_var, font=("Arial", 11)).pack(side="right", expand=True, fill="x")

        r_cat = ttk.Frame(f); r_cat.pack(fill="x", pady=5)
        tk.Label(r_cat, text="Category:", font=("Arial", 11, "bold"), width=25, anchor="w").pack(side="left")
        self.p_menu = ttk.Combobox(r_cat, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly", font=("Arial", 11))
        self.p_menu.pack(side="right", expand=True, fill="x")
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)

        r_unit = ttk.Frame(f); r_unit.pack(fill="x", pady=5)
        tk.Label(r_unit, text="Unit:", font=("Arial", 11, "bold"), width=25, anchor="w").pack(side="left")
        self.u_menu = ttk.Combobox(r_unit, textvariable=self.u_var, state="readonly", font=("Arial", 11))
        self.u_menu.pack(side="right", expand=True, fill="x")

        # PRODUCT BOX
        chem_frame = ttk.LabelFrame(f, text=" Dosing Product Source ", padding=15)
        chem_frame.pack(fill="x", pady=15)
        
        r_b = ttk.Frame(chem_frame); r_b.pack(fill="x", pady=5)
        tk.Label(r_b, text="Select Product:", font=("Arial", 10)).pack(side="left")
        self.b_menu = ttk.Combobox(r_b, textvariable=self.b_var, state="readonly")
        self.b_menu.pack(side="right", expand=True, fill="x")
        
        tk.Label(chem_frame, text="-- OR --", font=("Arial", 8, "italic")).pack()
        
        r_c = ttk.Frame(chem_frame); r_c.pack(fill="x", pady=5)
        tk.Label(r_c, text="(Optional) Chem Strength:", font=("Arial", 10)).pack(side="left")
        tk.Entry(r_c, textvariable=self.custom_str).pack(side="right", expand=True, fill="x")

        # Measurements
        for label, var in [("Current Reading:", self.curr_val_var), ("Target Goal:", self.targ_val_var), ("pH (Safety Check):", self.ph_var)]:
            row = ttk.Frame(f); row.pack(fill="x", pady=5)
            tk.Label(row, text=label, font=("Arial", 11, "bold"), width=25, anchor="w").pack(side="left")
            tk.Entry(row, textvariable=var, font=("Arial", 11)).pack(side="right", expand=True, fill="x")

        tk.Button(f, text="CALCULATE STABILITY DOSE", command=self.perform_calc, bg="#1a252f", fg="white", font=("Arial", 12, "bold"), height=2).pack(fill="x", pady=20)
        self.res_lbl = tk.Label(f, text="---", font=("Arial", 14, "bold"), fg="#2980b9")
        self.res_lbl.pack(pady=10)

    def perform_calc(self):
        try:
            p, vol, unit = self.p_var.get(), float(self.vol_var.get()), self.u_var.get()
            curr, targ = float(self.curr_val_var.get()), float(self.targ_val_var.get())
            std_curr = curr / 17.86 if (p == "Alkalinity" and unit == "ppm") else curr
            std_targ = targ / 17.86 if (p == "Alkalinity" and unit == "ppm") else targ
            strength = float(self.custom_str.get()) if self.custom_str.get() else self.brand_data.get(self.b_var.get(), 1.0)
            total_ml = ((std_targ - std_curr) * vol) / strength
            
            if total_ml <= 0:
                self.res_lbl.config(text="LEVELS OPTIMAL", fg="green")
            else:
                days = 7 if (total_ml > 95 or abs(std_targ - std_curr) > 1.0) else 1
                self.res_lbl.config(text=f"TOTAL: {total_ml:.1f} mL\n✅ DOSE: {total_ml/days:.1f} mL/day for {days} days", fg="#c0392b")
        except: self.res_lbl.config(text="ERROR: Check Tank Volume and Inputs", fg="red")

    def build_maint(self):
        f = ttk.Frame(self.tabs["Maintenance"], padding="40"); f.pack(fill="both")
        self.m_entries = {}
        for p in ["Alkalinity", "Calcium", "Magnesium"]:
            row = ttk.Frame(f); row.pack(fill="x", pady=10)
            tk.Label(row, text=f"{p}:", font=("Arial", 12, "bold"), width=15, anchor="w").pack(side="left")
            e = tk.Entry(row, font=("Arial", 12)); e.pack(side="left", expand=True, fill="x")
            if p == "Alkalinity":
                ttk.Combobox(row, textvariable=self.m_u_var, values=["dKH", "ppm"], state="readonly", width=6).pack(side="left", padx=10)
            else:
                tk.Label(row, text="ppm", font=("Arial", 10, "italic"), width=8).pack(side="left", padx=10)
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
            messagebox.showinfo("Success", "Log Entry Saved."); self.refresh_hist()
        except: messagebox.showerror("Error", "Check file permissions.")

    def build_trends(self):
        f = self.tabs["Trends"]
        ctrls = ttk.Frame(f, padding=10); ctrls.pack(fill="x")
        tk.Label(ctrls, text="Filter Parameter:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        # Wider OptionMenu to prevent clipping the checkmark/text
        om = ttk.OptionMenu(ctrls, self.graph_p, "Alkalinity", "Alkalinity", "Calcium", "Magnesium")
        om.config(width=15); om.pack(side="left", padx=10)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=f)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_graph(self):
        if not os.path.exists(self.log_file): return
        p, dates, vals = self.graph_p.get(), [], []
        with open(self.log_file, "r") as f:
            reader = list(csv.reader(f))[1:]
            for row in reader:
                if row[1] == p:
                    v = float(row[2])
                    if p == "Alkalinity" and row[3] == "ppm": v /= 17.86
                    dates.append(row[0].split(" ")[0]); vals.append(v)
        self.ax.clear()
        if vals:
            self.ax.plot(dates, vals, marker='o', color='#2980b9', linewidth=2)
            t, l, h = self.ranges[p]["target"], self.ranges[p]["low"], self.ranges[p]["high"]
            self.ax.axhline(t, color='green', linestyle='--', label="Target")
            self.ax.axhspan(l, h, color='green', alpha=0.15)
            self.ax.set_title(f"Stability Trends: {p}"); self.ax.set_ylabel('Reading'); plt.setp(self.ax.get_xticklabels(), rotation=30)
        self.canvas.draw()

    def build_history(self):
        f = self.tabs["History"]
        columns = ("Timestamp", "Parameter", "Value", "Unit")
        self.tree = ttk.Treeview(f, columns=columns, show="headings")
        for col in columns: self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        btn_f = ttk.Frame(f)
        btn_f.pack(fill="x", pady=10, padx=20)
        tk.Button(btn_f, text="Delete Entry", command=self.delete_entry, bg="#e74c3c", fg="white", width=15).pack(side="left", padx=5)
        tk.Button(btn_f, text="Export CSV", command=self.export_data, bg="#3498db", fg="white", width=15).pack(side="left", padx=5)
        tk.Button(btn_f, text="Clear All", command=self.clear_all, bg="#c0392b", fg="white", width=15).pack(side="right", padx=5)
        self.refresh_hist()

    def export_data(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            import shutil
            shutil.copy2(self.log_file, path)
            messagebox.showinfo("Exported", f"Data saved to {path}")

    def refresh_hist(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                reader = list(csv.reader(f))[1:]
                for row in reader: self.tree.insert("", "end", values=row)

    def delete_entry(self):
        selected = self.tree.selection()
        if not selected: return
        item_vals = [str(x) for x in self.tree.item(selected[0])['values']]
        data = []
        with open(self.log_file, "r") as f:
            reader = list(csv.reader(f))
            header = reader[0]
            for row in reader[1:]:
                if row != item_vals: data.append(row)
        with open(self.log_file, "w", newline="") as f:
            writer = csv.writer(f); writer.writerow(header); writer.writerows(data)
        self.refresh_hist(); self.update_graph()

    def clear_all(self):
        if messagebox.askyesno("Confirm", "Wipe all records?"):
            with open(self.log_file, "w", newline="") as f:
                csv.writer(f).writerow(["Timestamp", "Parameter", "Value", "Unit"])
            self.refresh_hist(); self.update_graph()

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu['values'] = self.ranges[p]["units"]; self.u_menu.current(0)
        self.b_menu['values'] = [k for k in self.brand_data.keys() if p[:3] in k] if p != "Magnesium" else ["Fritz RPM Liquid Mag"]
        self.b_menu.current(0); self.sync_target_unit()

    def hard_exit(self):
        self.root.destroy(); os._exit(0)

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
