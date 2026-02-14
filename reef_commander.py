import tkinter as tk
from tkinter import messagebox, ttk
import csv
import os
import math
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURATION ---
LOG_FILE = "aquarium_data.csv"
MAINT_FILE = "maintenance_log.csv"
GALLONS = 220 # Default tank volume

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.09 (Pre-Alpha)")
        self.root.geometry("650x800")

        # --- DATA ARCHITECTURE ---
        self.param_data = {
            "Alkalinity": {"units": ["dKH", "ppm", "meq/L"], "target": 8.5},
            "Calcium": {"units": ["ppm", "mg/L"], "target": 420},
            "Magnesium": {"units": ["ppm", "mg/L"], "target": 1350}
        }

        # --- UI TABS ---
        self.notebook = ttk.Notebook(root)
        self.calc_tab = ttk.Frame(self.notebook)
        self.maint_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.calc_tab, text=" Dosage & Safety ")
        self.notebook.add(self.maint_tab, text=" Maintenance ")
        self.notebook.add(self.log_tab, text=" History & Trends ")
        self.notebook.pack(expand=1, fill="both")

        self.build_calc_tab()
        self.build_maint_tab()
        self.build_log_tab()

    # --- TAB 1: CALCULATION & SAFETY ---
    def build_calc_tab(self):
        frame = ttk.Frame(self.calc_tab, padding="20")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Chemical Adjuster", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        # Parameter Select
        tk.Label(frame, text="Parameter:").grid(row=1, column=0, sticky="w")
        self.param_var = tk.StringVar(value="Alkalinity")
        self.param_menu = ttk.Combobox(frame, textvariable=self.param_var, values=list(self.param_data.keys()), state="readonly")
        self.param_menu.grid(row=1, column=1, pady=5, sticky="ew")
        self.param_menu.bind("<<ComboboxSelected>>", self.update_presets)

        # Unit Select
        tk.Label(frame, text="Measurement Unit:").grid(row=2, column=0, sticky="w")
        self.unit_var = tk.StringVar()
        self.unit_menu = ttk.Combobox(frame, textvariable=self.unit_var, state="readonly")
        self.unit_menu.grid(row=2, column=1, pady=5, sticky="ew")

        # Current Level
        tk.Label(frame, text="Current Level:").grid(row=3, column=0, sticky="w")
        self.curr_ent = tk.Entry(frame)
        self.curr_ent.grid(row=3, column=1, pady=5, sticky="ew")
        self.curr_ent.bind("<FocusOut>", self.check_smart_units)

        # Target Level
        tk.Label(frame, text="Target Level:").grid(row=4, column=0, sticky="w")
        self.targ_ent = tk.Entry(frame)
        self.targ_ent.grid(row=4, column=1, pady=5, sticky="ew")

        # pH
        tk.Label(frame, text="Current pH (Optional):").grid(row=5, column=0, sticky="w")
        self.ph_ent = tk.Entry(frame)
        self.ph_ent.grid(row=5, column=1, pady=5, sticky="ew")

        # Strength
        tk.Label(frame, text="Product Strength (1mL adds X to 1 Gal):").grid(row=6, column=0, sticky="w")
        self.strength_ent = tk.Entry(frame)
        self.strength_ent.grid(row=6, column=1, pady=5, sticky="ew")

        # Action Button
        self.calc_btn = tk.Button(frame, text="CALCULATE & RUN SAFETY CHECK", command=self.perform_calculation, 
                                 bg="#2c3e50", fg="white", font=("Arial", 10, "bold"))
        self.calc_btn.grid(row=7, column=0, columnspan=2, pady=20, sticky="ew")

        self.result_label = tk.Label(frame, text="Ready for input...", font=("Consolas", 10), justify="left", wraplength=400, fg="#2980b9")
        self.result_label.grid(row=8, column=0, columnspan=2, pady=10)

        self.update_presets()

    def update_presets(self, event=None):
        param = self.param_var.get()
        data = self.param_data[param]
        self.unit_menu.config(values=data["units"])
        self.unit_menu.set(data["units"][0])
        self.targ_ent.delete(0, tk.END)
        self.targ_ent.insert(0, str(data["target"]))

    def check_smart_units(self, event=None):
        try:
            val = float(self.curr_ent.get())
            if self.param_var.get() == "Alkalinity" and self.unit_var.get() == "dKH" and val > 20:
                if messagebox.askyesno("Unit Suggestion", f"{val} is very high for dKH. Switch to ppm?"):
                    self.unit_menu.set("ppm")
        except: pass

    def perform_calculation(self):
        try:
            name = self.param_var.get()
            curr = float(self.curr_ent.get())
            targ = float(self.targ_ent.get())
            unit = self.unit_var.get()
            strength = float(self.strength_ent.get())
            ph_val = self.ph_ent.get()
            ph = float(ph_val) if ph_val else None

            # Convert to standard units for math
            calc_curr = curr * 0.056 if unit == "ppm" and name == "Alkalinity" else curr
            calc_targ = targ * 0.056 if unit == "ppm" and name == "Alkalinity" else targ

            # Safety Guards
            if name == "Alkalinity" and ph and ph >= 8.5:
                messagebox.showerror("CRITICAL", "pH is too high (8.5+). Dosing aborted to prevent crash.")
                return

            diff = calc_targ - calc_curr
            if diff <= 0:
                self.result_label.config(text="Target already met.", fg="green")
                return

            total_ml = (diff * GALLONS) / strength
            
            output = f"--- DOSAGE PLAN ---\nTotal Dose: {total_ml:.1f} mL\n"
            if name == "Alkalinity" and ph and ph >= 8.35:
                output += "\n[!] WARNING: High pH. Split dose into 4+ parts."

            self.result_label.config(text=output, fg="black")
            
            if messagebox.askyesno("Log Entry", f"Log {total_ml:.1f}mL dose of {name}?"):
                self.save_to_csv("Dose", name, total_ml, ph)
                self.refresh_logs()

        except ValueError:
            messagebox.showerror("Error", "Check numeric inputs.")

    # --- TAB 2: MAINTENANCE ---
    def build_maint_tab(self):
        frame = ttk.Frame(self.maint_tab, padding="20")
        frame.pack(fill="both")
        tk.Label(frame, text="Maintenance Tracker", font=("Arial", 14, "bold")).pack(pady=10)
        
        tasks = ["RO/DI Filter Change", "Carbon/GFO Swap", "Pump Cleaning", "Skimmer Cleaning"]
        for task in tasks:
            f = ttk.Frame(frame)
            f.pack(fill="x", pady=5)
            tk.Label(f, text=task, width=25, anchor="w").pack(side="left")
            tk.Button(f, text="Mark Done", command=lambda t=task: self.log_maint(t)).pack(side="right")

    def log_maint(self, task):
        with open(MAINT_FILE, "a", newline='') as f:
            csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d"), task])
        messagebox.showinfo("Success", f"Logged: {task}")

    # --- TAB 3: HISTORY, GRAPHS & PDF ---
    def build_log_tab(self):
        for widget in self.log_tab.winfo_children(): widget.destroy()
        frame = ttk.Frame(self.log_tab, padding="20")
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="History & Reporting", font=("Arial", 14, "bold")).pack(pady=10)

        # Controls
        ctrl = ttk.Frame(frame)
        ctrl.pack(fill="x", pady=5)
        self.graph_param = tk.StringVar(value="Alkalinity")
        ttk.Combobox(ctrl, textvariable=self.graph_param, values=list(self.param_data.keys()), state="readonly").pack(side="left", padx=5)
        
        tk.Button(ctrl, text="Show Graph", command=self.show_graph, bg="#3498db", fg="white").pack(side="left", padx=5)
        tk.Button(ctrl, text="Export PDF", command=self.export_pdf_report, bg="#27ae60", fg="white").pack(side="left", padx=5)

        self.log_display = tk.Text(frame, height=15, width=70, font=("Consolas", 8), state="disabled")
        self.log_display.pack(pady=10, fill="both", expand=True)
        self.refresh_logs()

    def refresh_logs(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
                self.log_display.config(state="normal")
                self.log_display.delete('1.0', tk.END)
                for line in reversed(lines[-20:]): self.log_display.insert(tk.END, line)
                self.log_display.config(state="disabled")

    def show_graph(self):
        target = self.graph_param.get()
        dates, vals = [], []
        if not os.path.exists(LOG_FILE): return
        
        with open(LOG_FILE, "r") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if row[2] == "Dose" and row[3] == target: # Graphing doses as example
                    dates.append(datetime.strptime(row[0], "%Y-%m-%d %H:%M"))
                    vals.append(float(row[4]))
        
        if not dates: 
            messagebox.showinfo("No Data", "No logged doses for this parameter yet.")
            return

        plt.figure(figsize=(7,4))
        plt.plot(dates, vals, marker='o', color='orange')
        plt.title(f"{target} Dosing History")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def export_pdf_report(self):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, txt="AQUARIUM PERFORMANCE REPORT", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(190, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
        
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, txt="Recent Log Entries:", ln=True)
        pdf.set_font("Arial", size=9)
        
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                for row in list(csv.reader(f))[-10:]:
                    pdf.cell(190, 7, txt=f"{' | '.join(row)}", ln=True)

        report_fn = f"Aquarium_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        pdf.output(report_fn)
        messagebox.showinfo("Exported", f"Saved as {report_fn}")

    def save_to_csv(self, type, param, val, ph):
        exists = os.path.isfile(LOG_FILE)
        with open(LOG_FILE, "a", newline='') as f:
            writer = csv.writer(f)
            if not exists: writer.writerow(["Timestamp", "Tank", "Type", "Parameter", "Value", "pH"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), "Tank1", type, param, f"{val:.2f}", ph])

if __name__ == "__main__":
    root = tk.Tk()
    app = AquariumCommanderPro(root)
    root.mainloop()
