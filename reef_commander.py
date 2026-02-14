import tkinter as tk
from tkinter import ttk, messagebox
import csv, os, sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.13.6")
        self.root.geometry("1100x950")
        
        # --- CRITICAL: ZOMBIE PROCESS KILLER ---
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # --- DATA INITIALIZATION ---
        self.log_file = "reef_logs.csv"
        self.init_csv()

        # --- PRODUCT & UNIT DATA ---
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
        
        # --- UI ARCHITECTURE ---
        self.notebook = ttk.Notebook(root)
        self.tabs = {name: ttk.Frame(self.notebook) for name in ["Dosage", "Maintenance", "Trends", "Mix Guide", "History"]}
        for name, frame in self.tabs.items(): 
            self.notebook.add(frame, text=f" {name} ")
        self.notebook.pack(expand=1, fill="both")
        
        self.build_dosage()
        self.build_maint()
        self.build_trends()
        self.build_mix()
        self.build_history()
        self.update_param_selection()

    def init_csv(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="") as f:
                csv.writer(f).writerow(["Timestamp", "Parameter", "Value"])

    def build_dosage(self):
        f = ttk.Frame(self.tabs["Dosage"], padding="30"); f.pack(fill="both", expand=True)
        
        tk.Label(f, text="Tank Volume (Gal):", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        tk.Entry(f, textvariable=self.vol_var, width=15, bg="#ffffcc").grid(row=0, column=1, sticky="w", pady=5)

        for i, (txt, var) in enumerate([("Parameter:", self.p_var), ("Unit:", self.u_var), ("Product:", self.b_var)]):
            tk.Label(f, text=txt).grid(row=i+1, column=0, sticky="w")
            cb = ttk.Combobox(f, textvariable=var, state="readonly")
            cb.grid(row=i+1, column=1, sticky="ew", pady=5)
            if txt == "Parameter:": 
                cb['values'] = list(self.ranges.keys())
                cb.bind("<<ComboboxSelected>>", self.update_param_selection)
            if txt == "Unit:": self.u_menu = cb
            if txt == "Product:": self.b_menu = cb

        tk.Label(f, text="Current Reading:").grid(row=4, column=0, sticky="w")
        self.curr_ent = tk.Entry(f); self.curr_ent.grid(row=4, column=1, sticky="ew", pady=5)

        tk.Label(f, text="Target Goal:").grid(row=5, column=0, sticky="w")
        self.targ_ent = tk.Entry(f); self.targ_ent.grid(row=5, column=1, sticky="ew", pady=5)

        tk.Label(f, text="Strength Override (Opt):").grid(row=6, column=0, sticky="w")
        self.strength_ent = tk.Entry(f); self.strength_ent.grid(row=6, column=1, sticky="ew", pady=5)

        tk.Button(f, text="CALCULATE DOSE", command=self.perform_calc, bg="#2980b9", fg="white", height=2).grid(row=7, columnspan=2, pady=20, sticky="ew")
        self.res_lbl = tk.Label(f, text="Awaiting Input...", font=("Arial", 12, "bold"), wraplength=500); self.res_lbl.grid(row=8, columnspan=2)

    def perform_calc(self):
        try:
            p, vol, unit = self.p_var.get(), float(self.vol_var.get()), self.u_var.get()
            curr, targ = float(self.curr_ent.get()), float(self.targ_ent.get())

            # PPM to dKH Live Update Fix
            if p == "Alkalinity" and unit == "dKH" and curr > 25:
                curr = curr / 17.86
                self.curr_ent.delete(0, tk.END); self.curr_ent.insert(0, f"{curr:.2f}")
                messagebox.showinfo("Unit Corrected", f"Converted {curr*17.86:.0f}ppm to {curr:.2f} dKH")

            std_curr = curr / 17.86 if (p == "Alkalinity" and unit == "ppm") else curr
            std_targ = targ / 17.86 if (p == "Alkalinity" and unit == "ppm") else targ

            strength = float(self.strength_ent.get()) if self.strength_ent.get() else self.brand_data.get(self.b_var.get(), 1.0)
            total_ml = ((std_targ - std_curr) * vol) / strength
            
            if total_ml <= 0:
                self.res_lbl.config(text="Reading is at or above target.", fg="green")
            else:
                self.res_lbl.config(text=f"Total Dose Required: {total_ml:.1f} mL\n({self.b_var.get()})", fg="blue")
        except:
            self.res_lbl.config(text="Error: Verify all numbers and Volume.", fg="red")

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
            messagebox.showinfo("Success", "Logs updated successfully.")
            self.refresh_hist()
        except:
            messagebox.showerror("Error", "Could not write to log file.")

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu['values'] = self.ranges[p]["units"]; self.u_menu.current(0)
        self.b_menu['values'] = self.ranges[p]["brands"]; self.b_menu.current(0)
        self.targ_ent.delete(0, tk.END); self.targ_ent.insert(0, str(self.ranges[p]["target"]))

    def build_trends(self):
        f = self.tabs["Trends"]
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=f)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        tk.Button(f, text="Generate/Refresh Graph", command=self.update_graph).pack(pady=10)

    def update_graph(self):
        if not os.path.exists(self.log_file): return
        data = []
        with open(self.log_file, "r") as f:
            reader = csv.reader(f); next(reader)
            for row in reader:
                if row[1] == self.p_var.get(): data.append(float(row[2]))
        
        self.ax.clear()
        if data:
            self.ax.plot(data, marker='o', linestyle='-', color='#2980b9')
            self.ax.set_title(f"{self.p_var.get()} History")
        else:
            self.ax.text(0.5, 0.5, 'No data for this parameter yet', ha='center')
        self.canvas.draw()

    def build_mix(self):
        txt = "BULK MIXING RECIPES (1 GALLON RO/DI)\n\n" \
              "ALKALINITY: Mix 2 cups (400g) Soda Ash\n" \
              "CALCIUM: Mix 2.5 cups (500g) Calcium Chloride\n" \
              "MAGNESIUM: Mix 5 cups (1000g) Magnesium Chloride"
        tk.Label(self.tabs["Mix Guide"], text=txt, font=("Courier", 12), justify="left", relief="ridge", padx=20, pady=20).pack(pady=40)

    def build_history(self):
        f = self.tabs["History"]
        self.hist_txt = tk.Text(f, height=25, font=("Courier", 10)); self.hist_txt.pack(fill="both", expand=True)
        tk.Button(f, text="Manually Refresh Log", command=self.refresh_hist).pack(pady=5)

    def refresh_hist(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                self.hist_txt.delete("1.0", tk.END); self.hist_txt.insert(tk.END, f.read())

    def on_closing(self):
        """Standard exit and hard process termination."""
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
