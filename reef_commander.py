import tkfrom tkinter import ttk, messagebox
import csv, os, sys
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ReeferMadness:
    def __init__(self, root):
        self.root = root
        self.root.title("Reefer Madness v0.21.3 - UI RECOVERY")
        self.root.geometry("1450x950")
        
        # 1. PRE-LOAD SETTINGS
        base_dir = os.path.expanduser("~/Documents/ReeferMadness")
        if not os.path.exists(base_dir): os.makedirs(base_dir)
        self.log_file = os.path.join(base_dir, "reef_logs.csv")
        self.config_file = os.path.join(base_dir, "app_config.txt")
        self.init_csv()

        # 2. GLOBAL VARIABLES
        self.vol_var = tk.StringVar(value="220")
        self.unit_mode = tk.StringVar(value="Gallons")
        self.alk_u_var = tk.StringVar(value="ppm")
        self.p_var = tk.StringVar(value="Alkalinity")
        self.b_var = tk.StringVar()
        self.custom_strength = tk.StringVar(value="1.0")
        self.curr_val_var = tk.StringVar()
        self.targ_val_var = tk.StringVar(value="152")
        self.ph_var = tk.StringVar()
        self.status_dose_var = tk.StringVar(value="System Ready")
        self.m_vars = {p: tk.StringVar() for p in ["Alkalinity", "Calcium", "Magnesium", "Nitrate", "Phosphate"]}

        # 3. BUILD THE NOTEBOOK FIRST (ENSURES TABS APPEAR)
        self.nb = ttk.Notebook(root)
        self.tabs = {n: ttk.Frame(self.nb) for n in ["Action Plan", "Maintenance", "Trends", "History"]}
        for n, f in self.tabs.items(): self.nb.add(f, text=f" {n} ")
        self.nb.pack(expand=True, fill="both")

        # 4. DATA CONSTANTS
        self.brand_data = {
            "Alkalinity": {"Fritz RPM Liquid": 1.4, "ESV B-Ionic Part 1": 1.4, "Custom": 1.0},
            "Calcium": {"ESV B-Ionic Part 2": 20.0, "Fritz RPM Liquid": 20.0, "Custom": 1.0},
            "Magnesium": {"Fritz RPM Liquid": 100.0, "Custom": 1.0},
            "Nitrate": {"Generic Carbon (NoPox)": 3.0, "DIY Vinegar (5%)": 0.5, "Custom": 1.0},
            "Phosphate": {"Custom": 1.0}
        }

        # 5. EXECUTE BUILDERS
        try:
            self.build_dosage()
            self.build_maint()
            self.build_history()
            self.build_trends()
            self.update_product_list()
        except Exception as e:
            print(f"UI Build Error: {e}")

    def build_dosage(self):
        f = self.tabs["Action Plan"]
        # System Volume
        v_f = ttk.LabelFrame(f, text=" 1. System Volume "); v_f.pack(fill="x", padx=10, pady=5)
        tk.Entry(v_f, textvariable=self.vol_var, width=10).pack(side="left", padx=5)
        ttk.Radiobutton(v_f, text="Gallons", variable=self.unit_mode, value="Gallons").pack(side="left")
        ttk.Radiobutton(v_f, text="Liters", variable=self.unit_mode, value="Liters").pack(side="left")

        # Product
        p_f = ttk.LabelFrame(f, text=" 2. Product "); p_f.pack(fill="x", padx=10, pady=5)
        ttk.Combobox(p_f, textvariable=self.p_var, values=list(self.brand_data.keys())).pack(side="left", padx=5)
        ttk.Radiobutton(p_f, text="dKH", variable=self.alk_u_var, value="dKH").pack(side="left")
        ttk.Radiobutton(p_f, text="PPM", variable=self.alk_u_var, value="ppm").pack(side="left")
        self.b_cb = ttk.Combobox(p_f, textvariable=self.b_var)
        self.b_cb.pack(side="left", padx=5)

        # Plan
        c_f = ttk.LabelFrame(f, text=" 3. Correction "); c_f.pack(fill="x", padx=10, pady=5)
        tk.Label(c_f, text="Current:").pack(side="left"); tk.Entry(c_f, textvariable=self.curr_val_var, width=8).pack(side="left")
        tk.Label(c_f, text="Target:").pack(side="left"); tk.Entry(c_f, textvariable=self.targ_val_var, width=8).pack(side="left")
        
        tk.Button(f, text="CALCULATE PLAN", command=self.calc_dose, bg="#2c3e50", fg="white").pack(fill="x", padx=10, pady=10)
        self.res_lbl = tk.Label(f, text="---", font=("Arial", 12, "bold")); self.res_lbl.pack()

    def build_maint(self):
        f = self.tabs["Maintenance"]
        log_f = ttk.LabelFrame(f, text=" Log Daily Readings "); log_f.pack(fill="x", padx=10, pady=10)
        
        # Unit context for logging
        u_row = ttk.Frame(log_f); u_row.pack(fill="x")
        tk.Label(u_row, text="Unit:").pack(side="left")
        ttk.Radiobutton(u_row, text="dKH", variable=self.alk_u_var, value="dKH").pack(side="left")
        ttk.Radiobutton(u_row, text="PPM", variable=self.alk_u_var, value="ppm").pack(side="left")

        for p in self.m_vars:
            r = ttk.Frame(log_f); r.pack(fill="x", pady=2)
            tk.Label(r, text=p, width=15).pack(side="left")
            tk.Entry(r, textvariable=self.m_vars[p]).pack(side="left")
            
        tk.Button(log_f, text="SAVE ALL DATA", command=self.save_maint, bg="#27ae60", fg="white").pack(fill="x", pady=10)

    def build_history(self):
        f = self.tabs["History"]
        btn_f = ttk.Frame(f); btn_f.pack(fill="x")
        tk.Button(btn_f, text="DELETE SELECTED", command=self.delete_entry, bg="#c0392b", fg="white").pack(side="right", padx=10)
        
        self.tree = ttk.Treeview(f, columns=("ID", "T", "P", "V"), show="headings")
        for c, h in [("ID", "Idx"), ("T", "Time"), ("P", "Param"), ("V", "Value")]: self.tree.heading(c, text=h)
        self.tree.pack(fill="both", expand=True)
        self.refresh_history_table()

    def build_trends(self):
        f = self.tabs["Trends"]
        self.t_canv = ttk.Frame(f); self.t_canv.pack(fill="both", expand=True)
        tk.Button(f, text="REFRESH GRAPHS", command=self.refresh_graphs).pack()

    def update_product_list(self, *a):
        p = self.p_var.get()
        brands = list(self.brand_data.get(p, {}).keys())
        self.b_cb['values'] = brands
        self.b_var.set(brands[0])

    def save_maint(self):
        with open(self.log_file, "a", newline="") as f:
            w = csv.writer(f); ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            for p, v in self.m_vars.items():
                if v.get(): w.writerow([ts, p, v.get()])
        messagebox.showinfo("Success", "Logs Saved"); self.refresh_history_table()

    def refresh_history_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if os.path.exists(self.log_file):
            df = pd.read_csv(self.log_file, names=["T", "P", "V"])
            for i, r in df.iterrows(): self.tree.insert("", "end", values=(i, r['T'], r['P'], r['V']))

    def refresh_graphs(self):
        # Placeholder to ensure no crashes during recovery
        for w in self.t_canv.winfo_children(): w.destroy()
        tk.Label(self.t_canv, text="Graphing Engine Ready").pack()

    def calc_dose(self):
        # Basic logic for verification
        self.res_lbl.config(text="Calculation Logic Active")

    def init_csv(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f: pass

    def delete_entry(self):
        messagebox.showinfo("History", "Delete logic standby")

if __name__ == "__main__":
    root = tk.Tk()
    app = ReeferMadness(root)
    root.mainloop()
