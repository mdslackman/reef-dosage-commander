import tkinter as tk
from tkinter import ttk, messagebox
import csv, os, sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.13.5")
        self.root.geometry("1100x950")
        
        # 1. Kill process on exit (Zombie Fix)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 2. Data Persistence Check
        self.log_file = "reef_logs.csv"
        self.init_csv()

        # 3. Product & Brand Concentrations
        self.brand_data = {
            "ESV B-Ionic Alk (Part 1)": 1.4,
            "Fritz RPM Liquid Alk": 1.4,
            "ESV B-Ionic Cal (Part 2)": 20.0,
            "Fritz RPM Liquid Cal": 20.0,
            "Fritz RPM Liquid Mag": 100.0
        }
        
        self.ranges = {
            "Alkalinity": {"units": ["dKH", "ppm"], "target": 8.5, "brands": ["ESV B-Ionic Alk (Part 1)", "Fritz RPM Liquid Alk"]},
            "Calcium": {"units": ["ppm"], "target": 420, "brands": ["ESV B-Ionic Cal (Part 2)", "Fritz RPM Liquid Cal"]},
            "Magnesium": {"units": ["ppm"], "target": 1350, "brands": ["Fritz RPM Liquid Mag"]}
        }

        self.vol_var = tk.StringVar(); self.live_ph = tk.StringVar()
        self.p_var = tk.StringVar(value="Alkalinity"); self.u_var = tk.StringVar(); self.b_var = tk.StringVar()
        
        # UI Setup
        self.notebook = ttk.Notebook(root)
        self.tabs = {name: ttk.Frame(self.notebook) for name in ["Dosage", "Maintenance", "Trends", "Mix Guide", "History"]}
        for name, frame in self.tabs.items(): self.notebook.add(frame, text=f" {name} ")
        self.notebook.pack(expand=1, fill="both")
        
        self.build_dosage(); self.build_maint(); self.build_trends(); self.build_mix(); self.build_history()
        self.update_param_selection()

    def init_csv(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="") as f:
                csv.writer(f).writerow(["Timestamp", "Parameter", "Value"])

    def build_dosage(self):
        f = ttk.Frame(self.tabs["Dosage"], padding="30"); f.pack(fill="both", expand=True)
        tk.Label(f, text="Tank Volume (Gal):", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        tk.Entry(f, textvariable=self.vol_var, width=15, bg="#ffffcc").grid(row=0, column=1, sticky="w", pady=5)

        # Standard Menus
        for i, (txt, var) in enumerate([("Parameter:", self.p_var), ("Unit:", self.u_var), ("Product:", self.b_var)]):
            tk.Label(f, text=txt).grid(row=i+1, column=0, sticky="w")
            cb = ttk.Combobox(f, textvariable=var, state="readonly")
            cb.grid(row=i+1, column=1, sticky="ew", pady=5)
            if txt == "Parameter:": 
                cb['values'] = list(self.ranges.keys())
                cb.bind("<<ComboboxSelected>>", self.update_param_selection)
            if txt == "Unit:": self.u_menu = cb
            if txt == "Product:": self.b_menu = cb

        self.curr_ent = tk.Entry(f); self.curr_ent.grid(row=4, column=1, sticky="ew", pady=5)
        tk.Label(f, text="Current Reading:").grid(row=4, column=0, sticky="w")
        
        self.targ_ent = tk.Entry(f); self.targ_ent.grid(row=5, column=1, sticky="ew", pady=5)
        tk.Label(f, text="Target Goal:").grid(row=5, column=0, sticky="w")

        tk.Button(f, text="CALCULATE DOSE", command=self.perform_calc, bg="#2980b9", fg="white", height=2).grid(row=7, columnspan=2, pady=20, sticky="ew")
        self.res_lbl = tk.Label(f, text="Ready", font=("Arial", 12, "bold"), wraplength=500); self.res_lbl.grid(row=8, columnspan=2)

    def perform_calc(self):
        try:
            p, vol, unit = self.p_var.get(), float(self.vol_var.get()), self.u_var.get()
            curr, targ = float(self.curr_ent.get()), float(self.targ_ent.get())

            # PPM to dKH logic
            if p == "Alkalinity" and unit == "dKH" and curr > 25:
                curr = curr / 17.86
                self.curr_ent.delete(0, tk.END); self.curr_ent.insert(0, f"{curr:.2f}")

            std_curr = curr / 17.86 if (p == "Alkalinity" and unit == "ppm") else curr
            std_targ = targ / 17.86 if (p == "Alkalinity" and unit == "ppm") else targ

            strength = self.brand_data.get(self.b_var.get(), 1.0)
            total_ml = ((std_targ - std_curr) * vol) / strength
            
            if total_ml <= 0:
                self.res_lbl.config(text="Reading is at or above target.", fg="green")
            else:
                self.res_lbl.config(text=f"Total Dose: {total_ml:.1f} mL", fg="blue")
        except:
            self.res_lbl.config(text="Error: Check Inputs", fg="red")

    def build_maint(self):
        f = ttk.Frame(self.tabs["Maintenance"], padding="30"); f.pack()
        self.m_entries = {}
        for i, p in enumerate(["Alkalinity", "Calcium", "Magnesium"]):
            tk.Label(f, text=f"{p}:").grid(row=i, column=0, pady=5)
            e = tk.Entry(f); e.grid(row=i, column=1, padx=10); self.m_entries[p] = e
        tk.Label(f, text="pH (Optional):").grid(row=3, column=0)
        tk.Entry(f, textvariable=self.live_ph).grid(row=3, column=1, pady=5)
        tk.Button(f, text="LOG DATA", command=self.save_data, bg="#27ae60", fg="white", width=20).grid(row=4, columnspan=2, pady=20)

    def save_data(self):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            with open(self.log_file, "a", newline="") as f:
                writer = csv.writer(f)
                for p, ent in self.m_entries.items():
                    if ent.get(): writer.writerow([ts, p, ent.get()])
                if self.live_ph.get(): writer.writerow([ts, "pH", self.live_ph.get()])
            messagebox.showinfo("Success", "Logs saved.")
            self.refresh_hist()
        except:
            messagebox.showerror("Error", "Could not save log file.")

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu['values'] = self.ranges[p]["units"]; self.u_menu.current(0)
        self.b_menu['values'] = self.ranges[p]["brands"]; self.b_menu.current(0)
        self.targ_ent.delete(0, tk.END); self.targ_ent.insert(0, str(self.ranges[p]["target"]))

    def build_trends(self):
        # Trends logic for actual graphing
        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tabs["Trends"])
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        tk.Button(self.tabs["Trends"], text="Update Graph", command=self.update_graph).pack()

    def update_graph(self):
        if not os.path.exists(self.log_file): return
        data = []
        with open(self.log_file, "r") as f:
            reader = csv.reader(f); next(reader)
            for row in reader:
                if row[1] == self.p_var.get(): data.append(float(row[2]))
        self.ax.clear(); self.ax.plot(data, marker='o'); self.canvas.draw()

    def build_mix(self):
        txt = "MIXING GUIDE (1 GALLON RO/DI)\n\nAlk: 2 Cups Soda Ash\nCal: 2.5 Cups Calcium Chloride\nMag: 5 Cups Magnesium Chloride"
        tk.Label(self.tabs["Mix Guide"], text=txt, font=("Courier", 12), justify="left", relief="sunken", padx=20, pady=20).pack(pady=40)

    def build_history(self):
        self.hist_txt = tk.Text(self.tabs["History"], height=20); self.hist_txt.pack(fill="both", expand=True)
        tk.Button(self.tabs["History"], text="Refresh", command=self.refresh_hist).pack()

    def refresh_hist(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                self.hist_txt.delete("1.0", tk.END); self.hist_txt.insert(tk.END, f.read())

    def on_closing(self):
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
