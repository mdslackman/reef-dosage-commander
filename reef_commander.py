import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv, os, sys
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.17.5")
        self.root.geometry("1400x950")
        self.root.protocol("WM_DELETE_WINDOW", self.hard_exit)
        
        self.log_file = "reef_logs.csv"
        self.config_file = "app_config.txt"
        self.init_csv()

        # --- FULL DATABASE RESTORED ---
        self.brand_data = {
            "Alkalinity": {"ESV B-Ionic Part 1": 1.4, "Fritz RPM Liquid": 1.4, "Custom": 1.0},
            "Calcium": {"ESV B-Ionic Part 2": 20.0, "Fritz RPM Liquid": 20.0, "Custom": 1.0},
            "Magnesium": {"Fritz RPM Liquid": 100.0, "Custom": 1.0},
            "Nitrate": {"Generic Carbon (NoPox)": 3.0, "DIY Vinegar (5%)": 0.5, "Custom": 1.0},
            "Phosphate": {"Custom": 1.0}
        }

        self.test_instructions = {
            "Salifert": {
                "Alkalinity": {"steps": [("4ml water", 0), ("2 drops KH-Ind", 0), ("Titrate until Pink", 0)]},
                "Calcium": {"steps": [("2ml water", 0), ("1 scoop Ca-1", 0), ("8 drops Ca-2 / Swirl 10s", 10), ("Titrate Ca-3", 0)]},
                "Magnesium": {"steps": [("2ml water", 0), ("5 drops Mg-1", 0), ("1 scoop Mg-2", 0), ("Titrate Mg-3", 0)]},
                "Nitrate": {"steps": [("1ml water + 4ml NO3-1", 0), ("1 scoop NO3-2 / Swirl 30s", 30), ("Wait 3 mins", 180)]},
                "Phosphate": {"steps": [("10ml water + 4 drops PO4-1", 0), ("1 scoop PO4-2 / Shake 10s", 10), ("Wait 5 mins", 300)]}
            },
            "Hanna": {
                "Alkalinity": {"steps": [("10ml water (C1) / Press button", 0), ("Add 1ml Reagent / Invert 5x", 0), ("Press button", 0)]},
                "Phosphate": {"steps": [("10ml water (C1) / Press button", 0), ("Add packet / Shake 2 mins", 120), ("Insert / Long press", 180)]},
                "Nitrate": {"steps": [("10ml water (C1) / Press button", 0), ("Add packet / Shake 2 mins", 120), ("Hold for 7m timer", 420)]}
            }
        }

        self.ranges = {
            "Alkalinity": {"target": 8.5, "units": "dKH"},
            "Calcium": {"target": 420, "units": "ppm"},
            "Magnesium": {"target": 1350, "units": "ppm"},
            "Nitrate": {"target": 5.0, "units": "ppm"},
            "Phosphate": {"target": 0.03, "units": "ppm"}
        }

        # --- VARIABLES ---
        self.vol_var = tk.StringVar(value=self.load_config())
        self.unit_mode = tk.StringVar(value="Liters")
        self.p_var = tk.StringVar(value="Alkalinity")
        self.alk_u_var = tk.StringVar(value="dKH")
        self.b_var = tk.StringVar()
        self.curr_val_var = tk.StringVar()
        self.targ_val_var = tk.StringVar(value="8.5")
        self.ph_var = tk.StringVar()
        self.readout_var = tk.StringVar()
        self.t_brand_var = tk.StringVar(); self.t_param_var = tk.StringVar()

        # UI Layout
        self.notebook = ttk.Notebook(root)
        self.tabs = {name: ttk.Frame(self.notebook) for name in ["Action Plan", "Maintenance", "Trends", "Testing & History"]}
        for name, frame in self.tabs.items(): self.notebook.add(frame, text=f" {name} ")
        self.notebook.pack(expand=True, fill="both")
        
        self.build_dosage(); self.build_maint(); self.build_history(); self.build_trends()
        self.p_var.trace_add("write", self.update_dosage_targets)

    # --- TAB 1: ACTION PLAN (RESTORED) ---
    def build_dosage(self):
        f = ttk.Frame(self.tabs["Action Plan"], padding=20); f.pack(fill="both")
        cfg = ttk.LabelFrame(f, text=" System Configuration ", padding=10); cfg.pack(fill="x")
        tk.Label(cfg, text="Volume:").pack(side="left")
        tk.Entry(cfg, textvariable=self.vol_var, width=8).pack(side="left", padx=5)
        ttk.Radiobutton(cfg, text="Liters", variable=self.unit_mode, value="Liters").pack(side="left")
        ttk.Radiobutton(cfg, text="Gallons", variable=self.unit_mode, value="Gallons").pack(side="left")

        inp = ttk.Frame(f, padding=10); inp.pack(fill="x")
        tk.Label(inp, text="Parameter:").grid(row=0, column=0, sticky="w")
        self.p_cb = ttk.Combobox(inp, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly")
        self.p_cb.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(inp, text="Current Value:").grid(row=1, column=0, sticky="w")
        tk.Entry(inp, textvariable=self.curr_val_var).grid(row=1, column=1, pady=5)
        
        tk.Label(inp, text="Target Value:").grid(row=2, column=0, sticky="w")
        tk.Entry(inp, textvariable=self.targ_val_var).grid(row=2, column=1, pady=5)

        tk.Label(inp, text="pH (Optional):").grid(row=3, column=0, sticky="w")
        tk.Entry(inp, textvariable=self.ph_var).grid(row=3, column=1, pady=5)

        tk.Button(f, text="CALCULATE DOSAGE", command=self.calc_dose, bg="#2c3e50", fg="white", height=2).pack(fill="x", pady=10)
        self.res_lbl = tk.Label(f, text="---", font=("Arial", 14, "bold"))
        self.res_lbl.pack()

    def update_dosage_targets(self, *args):
        p = self.p_var.get()
        if p in self.ranges: self.targ_val_var.set(str(self.ranges[p]["target"]))

    def calc_dose(self):
        try:
            curr, targ = float(self.curr_val_var.get()), float(self.targ_val_var.get())
            if curr >= targ:
                self.res_lbl.config(text="Safe level. No dose needed.", fg="green")
                return
            vol = float(self.vol_var.get()) * (1 if self.unit_mode.get()=="Liters" else 3.785)
            # Basic dose logic: (Difference * Vol) / Constant (Simplified for demo)
            dose = (targ - curr) * vol * 0.1 
            self.res_lbl.config(text=f"Recommended Dose: {dose:.2f} mL", fg="#c0392b")
        except: self.res_lbl.config(text="Error: Check Inputs", fg="red")

    # --- TAB 2: MAINTENANCE (RESTORED) ---
    def build_maint(self):
        f = ttk.Frame(self.tabs["Maintenance"], padding=20); f.pack(fill="both")
        self.m_entries = {}
        for p in self.ranges.keys():
            row = ttk.Frame(f); row.pack(fill="x", pady=5)
            tk.Label(row, text=p, width=15).pack(side="left")
            e = tk.Entry(row); e.pack(side="left", fill="x", expand=True)
            self.m_entries[p] = e
        tk.Button(f, text="SAVE MAINTENANCE LOG", command=self.save_maint, bg="#27ae60", fg="white").pack(fill="x", pady=20)

    def save_maint(self):
        with open(self.log_file, "a", newline="") as f:
            w = csv.writer(f); ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            for p, e in self.m_entries.items():
                if e.get(): w.writerow([ts, p, e.get(), ""])
        self.refresh_all()
        messagebox.showinfo("Saved", "Logs updated successfully.")

    # --- TAB 3: TRENDS & EXPORT (RESTORED) ---
    def build_trends(self):
        f = self.tabs["Trends"]
        btn_f = ttk.Frame(f); btn_f.pack(fill="x", padx=10, pady=5)
        tk.Button(btn_f, text="Export Excel/CSV", command=self.export_excel).pack(side="left", padx=5)
        tk.Button(btn_f, text="Export PDF Report", command=self.export_pdf).pack(side="left", padx=5)
        
        self.trend_container = ttk.Frame(f)
        self.trend_container.pack(fill="both", expand=True)
        self.refresh_graphs()

    def refresh_graphs(self):
        for w in self.trend_container.winfo_children(): w.destroy()
        data = self.get_log_data()
        if not data: return
        
        fig, axes = plt.subplots(len(self.ranges), 1, figsize=(8, 10), constrained_layout=True)
        for i, (param, info) in enumerate(self.ranges.items()):
            p_data = [d for d in data if d['param'] == param]
            if not p_data: continue
            dates = [datetime.strptime(d['ts'], "%Y-%m-%d %H:%M") for d in p_data]
            values = [float(d['val']) for d in p_data]
            axes[i].plot(dates, values, marker='o', label="Readout")
            axes[i].axhline(y=info['target'], color='r', linestyle='--')
            axes[i].set_title(param); axes[i].grid(True, alpha=0.3)

        canvas = FigureCanvasTkAgg(fig, master=self.trend_container)
        canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True)

    # --- EXPORT METHODS ---
    def export_excel(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if path:
            df = pd.read_csv(self.log_file)
            df.to_excel(path, index=False)
            messagebox.showinfo("Exported", f"Data saved to {path}")

    def export_pdf(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf")
        if path:
            c = canvas.Canvas(path, pagesize=letter)
            c.drawString(100, 750, f"Reef Commander Pro Report - {datetime.now().strftime('%Y-%m-%d')}")
            y = 700
            with open(self.log_file, 'r') as f:
                reader = csv.reader(f)
                for row in list(reader)[-20:]:
                    c.drawString(100, y, f"{row[0]} | {row[1]}: {row[2]}")
                    y -= 20
            c.save()
            messagebox.showinfo("Exported", "PDF Report Generated.")

    # --- TAB 4: HISTORY & GUIDED (RESTORED) ---
    def build_history(self):
        f = self.tabs["Testing & History"]
        left = ttk.Frame(f, padding=10); left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="Select Test Type:").pack(anchor="w")
        p_cb = ttk.Combobox(left, textvariable=self.t_param_var, values=list(self.ranges.keys()), state="readonly")
        p_cb.pack(fill="x", pady=5); p_cb.bind("<<ComboboxSelected>>", self.filter_test_brands)
        
        tk.Label(left, text="Select Brand:").pack(anchor="w")
        self.tb_cb = ttk.Combobox(left, textvariable=self.t_brand_var, state="readonly")
        self.tb_cb.pack(fill="x", pady=5); self.tb_cb.bind("<<ComboboxSelected>>", self.load_instructions)

        self.instr_box = ttk.Frame(left); self.instr_box.pack(fill="both", expand=True)
        
        res_f = ttk.LabelFrame(left, text=" Log Result ", padding=10)
        res_f.pack(fill="x", side="bottom")
        tk.Entry(res_f, textvariable=self.readout_var, width=10).pack(side="left", padx=5)
        tk.Button(res_f, text="SAVE ALL", command=self.comprehensive_save, bg="#27ae60", fg="white").pack(side="left")

        right = ttk.LabelFrame(f, text=" Log History ", padding=10)
        right.pack(side="right", fill="both", padx=10, pady=10)
        self.tree = ttk.Treeview(right, columns=("TS", "P", "V"), show="headings")
        self.tree.heading("TS", text="Date"); self.tree.heading("P", text="Param"); self.tree.heading("V", text="Val")
        self.tree.pack(fill="both", expand=True)
        self.refresh_history_table()

    def filter_test_brands(self, e):
        p = self.t_param_var.get()
        brands = [b for b in self.test_instructions if p in self.test_instructions[b]]
        self.tb_cb['values'] = brands
        self.tb_cb.set("")

    def load_instructions(self, e):
        for w in self.instr_box.winfo_children(): w.destroy()
        brand, p = self.t_brand_var.get(), self.t_param_var.get()
        if brand in self.test_instructions and p in self.test_instructions[brand]:
            for txt, sec in self.test_instructions[brand][p]["steps"]:
                row = ttk.Frame(self.instr_box); row.pack(fill="x", pady=2)
                tk.Checkbutton(row, text=txt).pack(side="left")
                if sec > 0: tk.Button(row, text=f"⏲ {sec}s").pack(side="right")

    def comprehensive_save(self):
        val, param = self.readout_var.get(), self.t_param_var.get()
        if val and param:
            with open(self.log_file, "a", newline="") as f:
                csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), param, val, ""])
            self.refresh_all()

    def refresh_all(self):
        self.refresh_history_table()
        self.refresh_graphs()

    def refresh_history_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        data = self.get_log_data()
        for d in reversed(data[-20:]): self.tree.insert("", "end", values=(d['ts'], d['param'], d['val']))

    def get_log_data(self):
        data = []
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader: data.append({'ts': row['Timestamp'], 'param': row['Parameter'], 'val': row['Value']})
        return data

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
