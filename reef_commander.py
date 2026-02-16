import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import csv, os, sys
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.18.7")
        self.root.geometry("1450x950")
        self.root.protocol("WM_DELETE_WINDOW", self.hard_exit)
        
        self.log_file = "reef_logs.csv"
        self.config_file = "app_config.txt"
        self.init_csv()

        # Database
        self.brand_data = {
            "Alkalinity": {"ESV B-Ionic Part 1": 1.4, "Fritz RPM Liquid": 1.4, "Custom": 1.0},
            "Calcium": {"ESV B-Ionic Part 2": 20.0, "Fritz RPM Liquid": 20.0, "Custom": 1.0},
            "Magnesium": {"Fritz RPM Liquid": 100.0, "Custom": 1.0},
            "Nitrate": {"Generic Carbon (NoPox)": 3.0, "DIY Vinegar (5%)": 0.5, "Custom": 1.0},
            "Phosphate": {"Custom": 1.0}
        }

        self.test_instructions = {
            "Salifert": {
                "Alkalinity": [("4ml water", 0), ("2 drops KH-Ind", 0), ("Titrate until Pink", 0)],
                "Calcium": [("2ml water", 0), ("1 scoop Ca-1", 0), ("8 drops Ca-2", 10), ("Titrate Ca-3", 0)],
                "Magnesium": [("2ml water", 0), ("5 drops Mg-1", 0), ("1 scoop Mg-2", 0), ("Titrate Mg-3", 0)],
                "Nitrate": [("1ml water + 4ml NO3-1", 0), ("1 scoop NO3-2", 30), ("Wait 3 mins", 180)],
                "Phosphate": [("10ml water + 4 drops PO4-1", 0), ("1 scoop PO4-2", 10), ("Wait 5 mins", 300)]
            },
            "Hanna": {
                "Alkalinity": [("10ml water (C1)", 0), ("Add 1ml Reagent", 0), ("Press Button", 0)],
                "Phosphate": [("10ml water (C1)", 0), ("Add packet/Shake 2m", 120), ("Long Press", 180)],
                "Nitrate": [("10ml water (C1)", 0), ("Add packet/Shake 2m", 120), ("Wait 7 mins", 420)]
            }
        }

        self.ranges = {
            "Alkalinity": {"target": 8.5, "low": 7.5, "high": 9.5, "ppm_target": 152, "ppm_low": 134, "ppm_high": 170},
            "Calcium": {"target": 420, "low": 380, "high": 460},
            "Magnesium": {"target": 1350, "low": 1250, "high": 1450},
            "Nitrate": {"target": 5.0, "low": 1.0, "high": 20.0},
            "Phosphate": {"target": 0.03, "low": 0.01, "high": 0.1}
        }

        # Global Variables
        self.vol_var = tk.StringVar(value=self.load_config())
        self.unit_mode = tk.StringVar(value="Liters")
        self.p_var = tk.StringVar(value="Alkalinity")
        self.alk_u_var = tk.StringVar(value="dKH")
        self.b_var = tk.StringVar()
        self.custom_strength = tk.StringVar(value="1.0")
        self.curr_val_var = tk.StringVar()
        self.targ_val_var = tk.StringVar(value="8.5")
        self.ph_var = tk.StringVar()
        self.readout_var = tk.StringVar()
        self.t_brand_var = tk.StringVar(); self.t_param_var = tk.StringVar()
        self.m_vars = {p: tk.StringVar() for p in self.ranges.keys()}

        self.notebook = ttk.Notebook(root)
        self.tabs = {name: ttk.Frame(self.notebook) for name in ["Action Plan", "Maintenance", "Trends", "Testing & History"]}
        for name, frame in self.tabs.items(): self.notebook.add(frame, text=f" {name} ")
        self.notebook.pack(expand=True, fill="both")
        
        self.build_dosage(); self.build_maint(); self.build_history(); self.build_trends()
        
        # Traces
        self.curr_val_var.trace_add("write", lambda *a: self.smart_detect(self.curr_val_var))
        self.m_vars["Alkalinity"].trace_add("write", lambda *a: self.smart_detect(self.m_vars["Alkalinity"]))
        self.alk_u_var.trace_add("write", self.sync_targets)
        self.p_var.trace_add("write", self.update_product_list)

    def build_dosage(self):
        f = ttk.Frame(self.tabs["Action Plan"], padding=20); f.pack(fill="both")
        
        # Volume/Units
        row0 = ttk.Frame(f); row0.pack(fill="x", pady=5)
        tk.Label(row0, text="System Volume:").pack(side="left")
        tk.Entry(row0, textvariable=self.vol_var, width=10).pack(side="left", padx=5)
        ttk.Radiobutton(row0, text="Liters", variable=self.unit_mode, value="Liters").pack(side="left")
        ttk.Radiobutton(row0, text="Gallons", variable=self.unit_mode, value="Gallons").pack(side="left")

        # Param/Alk Units
        row1 = ttk.Frame(f); row1.pack(fill="x", pady=5)
        tk.Label(row1, text="Parameter:").pack(side="left")
        ttk.Combobox(row1, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly").pack(side="left", padx=5)
        self.alk_u_pane = ttk.Frame(row1)
        ttk.Radiobutton(self.alk_u_pane, text="dKH", variable=self.alk_u_var, value="dKH").pack(side="left")
        ttk.Radiobutton(self.alk_u_pane, text="PPM", variable=self.alk_u_var, value="ppm").pack(side="left")
        self.alk_u_pane.pack(side="left", padx=10)

        # RESTORED: Product & Concentration
        row2 = ttk.Frame(f); row2.pack(fill="x", pady=5)
        tk.Label(row2, text="Product:").pack(side="left")
        self.b_cb = ttk.Combobox(row2, textvariable=self.b_var, state="readonly")
        self.b_cb.pack(side="left", padx=5)
        self.b_cb.bind("<<ComboboxSelected>>", self.toggle_custom_ui)
        
        self.custom_pane = ttk.Frame(row2)
        tk.Label(self.custom_pane, text="Strength:").pack(side="left")
        tk.Entry(self.custom_pane, textvariable=self.custom_strength, width=8).pack(side="left", padx=5)
        self.update_product_list()

        # Values & pH
        row3 = ttk.Frame(f); row3.pack(fill="x", pady=10)
        tk.Label(row3, text="Current:").pack(side="left")
        tk.Entry(row3, textvariable=self.curr_val_var, width=10).pack(side="left", padx=5)
        tk.Label(row3, text="Target:").pack(side="left")
        tk.Entry(row3, textvariable=self.targ_val_var, width=10).pack(side="left", padx=5)
        tk.Label(row3, text="pH (Optional):").pack(side="left", padx=(15, 0))
        tk.Entry(row3, textvariable=self.ph_var, width=8).pack(side="left", padx=5)

        tk.Button(f, text="CALCULATE DOSAGE", command=self.calc_dose, bg="#2c3e50", fg="white", height=2).pack(fill="x", pady=10)
        self.res_lbl = tk.Label(f, text="---", font=("Arial", 14, "bold")); self.res_lbl.pack()

    def update_product_list(self, *args):
        p = self.p_var.get()
        # Show/Hide Alk units UI
        if p == "Alkalinity": self.alk_u_pane.pack(side="left", padx=10)
        else: self.alk_u_pane.pack_forget()
        
        brands = list(self.brand_data.get(p, {}).keys())
        self.b_cb['values'] = brands
        if brands: self.b_cb.current(0)
        self.toggle_custom_ui()

    def toggle_custom_ui(self, *args):
        if self.b_var.get() == "Custom": self.custom_pane.pack(side="left")
        else: self.custom_pane.pack_forget()

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Delete Entry", command=self.delete_entry)
            menu.add_command(label="Edit Value", command=self.edit_entry)
            menu.post(event.x_root, event.y_root)

    def delete_entry(self):
        sel = self.tree.item(self.tree.selection())['values']
        df = pd.read_csv(self.log_file)
        # Filter by timestamp and parameter
        df = df[~((df['Timestamp'] == sel[0]) & (df['Parameter'] == sel[1]))]
        df.to_csv(self.log_file, index=False)
        self.refresh_all()

    def edit_entry(self):
        new_val = simpledialog.askfloat("Edit", "Enter new measurement value:")
        if new_val is not None:
            sel = self.tree.item(self.tree.selection())['values']
            df = pd.read_csv(self.log_file)
            df.loc[(df['Timestamp'] == sel[0]) & (df['Parameter'] == sel[1]), 'Value'] = new_val
            df.to_csv(self.log_file, index=False)
            self.refresh_all()

    def build_maint(self):
        f = ttk.Frame(self.tabs["Maintenance"], padding=20); f.pack(fill="both")
        for p in self.ranges.keys():
            r = ttk.Frame(f); r.pack(fill="x", pady=4)
            tk.Label(r, text=p, width=15, anchor="w").pack(side="left")
            tk.Entry(r, textvariable=self.m_vars[p]).pack(side="left", expand=True, fill="x")
            if p == "Alkalinity":
                ttk.Radiobutton(r, text="dKH", variable=self.alk_u_var, value="dKH").pack(side="left")
                ttk.Radiobutton(r, text="PPM", variable=self.alk_u_var, value="ppm").pack(side="left")
        tk.Button(f, text="SAVE MEASUREMENTS", command=self.save_maint, bg="#27ae60", fg="white", height=2).pack(fill="x", pady=20)

    def build_history(self):
        f = self.tabs["Testing & History"]
        left = ttk.Frame(f, width=400, padding=10); left.pack(side="left", fill="y")
        ttk.Combobox(left, textvariable=self.t_param_var, values=list(self.ranges.keys())).pack(fill="x")
        self.kit_cb = ttk.Combobox(left, textvariable=self.t_brand_var); self.kit_cb.pack(fill="x", pady=5)
        self.t_param_var.trace_add("write", self.update_kits)
        self.t_brand_var.trace_add("write", self.update_steps)
        self.step_f = ttk.Frame(left); self.step_f.pack(fill="both", expand=True)
        res_f = ttk.Frame(left); res_f.pack(fill="x")
        tk.Entry(res_f, textvariable=self.readout_var).pack(side="left", expand=True, fill="x")
        tk.Button(res_f, text="LOG", command=self.save_hist, bg="#27ae60", fg="white").pack(side="right")
        
        right = ttk.Frame(f, padding=10); right.pack(side="right", fill="both", expand=True)
        self.tree = ttk.Treeview(right, columns=("T", "P", "V"), show="headings")
        for c, h in [("T", "Timestamp"), ("P", "Param"), ("V", "Value")]: self.tree.heading(c, text=h)
        self.tree.pack(fill="both", expand=True)
        # RE-BOUND: Context Menu
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.refresh_history_table()

    def run_timer(self, btn, seconds):
        if seconds > 0:
            btn.config(text=f"{seconds}s", bg="#f1c40f")
            self.root.after(1000, lambda: self.run_timer(btn, seconds-1))
        else:
            btn.config(text="DONE!", bg="#2ecc71")
            messagebox.showinfo("Timer", "Step Complete!")

    def smart_detect(self, var):
        try:
            val_str = var.get()
            if not val_str: return
            val = float(val_str)
            if val > 30 and self.alk_u_var.get() == "dKH": self.alk_u_var.set("ppm")
            elif 0 < val < 20 and self.alk_u_var.get() == "ppm": self.alk_u_var.set("dKH")
        except: pass

    def sync_targets(self, *args):
        if self.p_var.get() == "Alkalinity":
            self.targ_val_var.set("152" if self.alk_u_var.get() == "ppm" else "8.5")

    def save_maint(self):
        with open(self.log_file, "a", newline="") as f:
            w = csv.writer(f); ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            for p, var in self.m_vars.items():
                if var.get(): w.writerow([ts, p, var.get(), ""])
        self.refresh_all(); messagebox.showinfo("Saved", "Log updated.")

    def build_trends(self):
        f = self.tabs["Trends"]
        btn_f = ttk.Frame(f); btn_f.pack(fill="x", pady=5)
        tk.Button(btn_f, text="REFRESH GRAPHS", command=self.refresh_graphs).pack(side="left", padx=10)
        self.t_canv = ttk.Frame(f); self.t_canv.pack(fill="both", expand=True)
        self.refresh_graphs()

    def refresh_graphs(self):
        for w in self.t_canv.winfo_children(): w.destroy()
        df = pd.read_csv(self.log_file)
        if df.empty: return
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        fig, axes = plt.subplots(len(self.ranges), 1, figsize=(8, 12), constrained_layout=True)
        for i, (p, r) in enumerate(self.ranges.items()):
            subset = df[df['Parameter'] == p]
            if subset.empty: continue
            is_ppm = subset['Value'].max() > 30 if p == "Alkalinity" else False
            target = r['ppm_target'] if is_ppm else r['target']
            low, high = (r['ppm_low'], r['ppm_high']) if is_ppm else (r['low'], r['high'])
            axes[i].plot(subset['Timestamp'], subset['Value'], marker='o', color='black')
            axes[i].axhspan(low, high, color='green', alpha=0.2)
            axes[i].axhline(target, color='red', linestyle='--', alpha=0.5)
            axes[i].set_title(f"{p} ({'PPM' if is_ppm else 'dKH'})")
            axes[i].grid(True, alpha=0.3)
        FigureCanvasTkAgg(fig, master=self.t_canv).get_tk_widget().pack(fill="both", expand=True)

    def update_kits(self, *a):
        p = self.t_param_var.get()
        self.kit_cb['values'] = [b for b in self.test_instructions if p in self.test_instructions[b]]

    def update_steps(self, *a):
        for w in self.step_f.winfo_children(): w.destroy()
        brand, p = self.t_brand_var.get(), self.t_param_var.get()
        if brand in self.test_instructions and p in self.test_instructions[brand]:
            for txt, sec in self.test_instructions[brand][p]:
                r = ttk.Frame(self.step_f); r.pack(fill="x", pady=2)
                tk.Checkbutton(r, text=txt).pack(side="left")
                if sec > 0:
                    btn = tk.Button(r, text=f"⏲ {sec}s")
                    btn.config(command=lambda b=btn, s=sec: self.run_timer(b, s))
                    btn.pack(side="right")

    def save_hist(self):
        if self.readout_var.get():
            with open(self.log_file, "a", newline="") as f:
                csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), self.t_param_var.get(), self.readout_var.get(), ""])
            self.refresh_all()

    def refresh_history_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if os.path.exists(self.log_file):
            df = pd.read_csv(self.log_file)
            for _, r in df.tail(20).iterrows(): self.tree.insert("", 0, values=(r['Timestamp'], r['Parameter'], r['Value']))

    def refresh_all(self): self.refresh_history_table(); self.refresh_graphs()

    def init_csv(self):
        if not os.path.exists(self.log_file):
            pd.DataFrame(columns=["Timestamp", "Parameter", "Value", "Unit"]).to_csv(self.log_file, index=False)

    def calc_dose(self):
        try:
            v = float(self.vol_var.get()) * (1 if self.unit_mode.get() == "Liters" else 3.785)
            diff = float(self.targ_val_var.get()) - float(self.curr_val_var.get())
            if diff <= 0: self.res_lbl.config(text="Levels Optimal", fg="green"); return
            
            p = self.p_var.get()
            prod = self.b_var.get()
            strength = float(self.custom_strength.get()) if prod == "Custom" else self.brand_data[p][prod]
            
            dose = (diff * v) / strength
            self.res_lbl.config(text=f"Dose: {dose:.2f} mL", fg="red")
        except: self.res_lbl.config(text="Check Inputs", fg="red")

    def load_config(self):
        return open(self.config_file, "r").read().strip() if os.path.exists(self.config_file) else "100"

    def hard_exit(self):
        with open(self.config_file, "w") as f: f.write(self.vol_var.get())
        self.root.destroy(); os._exit(0)

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
