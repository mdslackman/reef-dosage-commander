import tkinter as tk
from tkinter import messagebox, ttk
import csv
import os
import math
from datetime import datetime

# --- CONFIGURATION ---
LOG_FILE = "aquarium_data.csv"
GALLONS = 220  # You can change this to an input field later if you have multiple tanks

class AquariumCommander:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Dosage Commander v8.0")
        self.root.geometry("500x650")
        
        # Style
        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))

        # --- TABS ---
        self.notebook = ttk.Notebook(root)
        self.calc_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.calc_tab, text="  Dosage Calculator  ")
        self.notebook.add(self.log_tab, text="  Test History  ")
        self.notebook.pack(expand=1, fill="both")

        self.build_calc_tab()
        self.build_log_tab()

    def build_calc_tab(self):
        # Title
        tk.Label(self.calc_tab, text="Chemical Adjuster", font=("Segoe UI", 14, "bold")).pack(pady=10)

        # Parameter Selection
        tk.Label(self.calc_tab, text="Select Parameter:").pack()
        self.param_var = tk.StringVar(value="Alkalinity")
        params = ["Alkalinity", "Calcium", "Magnesium"]
        self.param_menu = ttk.Combobox(self.calc_tab, textvariable=self.param_var, values=params, state="readonly")
        self.param_menu.pack(pady=5)

        # Inputs
        tk.Label(self.calc_tab, text="Current Level:").pack()
        self.curr_ent = tk.Entry(self.calc_tab, justify='center')
        self.curr_ent.pack(pady=5)

        tk.Label(self.calc_tab, text="Target Level:").pack()
        self.targ_ent = tk.Entry(self.calc_tab, justify='center')
        self.targ_ent.pack(pady=5)

        tk.Label(self.calc_tab, text="Product Strength (1mL adds X to 1 Gal):").pack()
        self.strength_ent = tk.Entry(self.calc_tab, justify='center')
        self.strength_ent.pack(pady=5)

        tk.Label(self.calc_tab, text="Current pH (Optional):").pack()
        self.ph_ent = tk.Entry(self.calc_tab, justify='center')
        self.ph_ent.pack(pady=5)

        # Action Button
        calc_btn = tk.Button(self.calc_tab, text="RUN SAFETY CHECK & CALCULATE", command=self.run_calc, 
                             bg="#008080", fg="white", font=("Segoe UI", 10, "bold"), padx=10, pady=5)
        calc_btn.pack(pady=20)

        # Output Display
        self.result_box = tk.Text(self.calc_tab, height=10, width=55, font=("Consolas", 9), state="disabled", bg="#f0f0f0")
        self.result_box.pack(pady=10, padx=10)

    def log_message(self, message):
        self.result_box.config(state="normal")
        self.result_box.delete('1.0', tk.END)
        self.result_box.insert(tk.END, message)
        self.result_box.config(state="disabled")

    def get_last_test(self, param):
        if not os.path.exists(LOG_FILE): return None
        try:
            with open(LOG_FILE, "r") as f:
                reader = list(csv.reader(f))
                for row in reversed(reader):
                    if row[2] == "Test" and row[3] == param: return float(row[4])
        except: return None
        return None

    def run_calc(self):
        try:
            name = self.param_var.get()
            curr = float(self.curr_ent.get())
            targ = float(self.targ_ent.get())
            strength = float(self.strength_ent.get())
            ph_str = self.ph_ent.get()
            ph = float(ph_str) if ph_str else None

            # 1. Convert Alk if needed
            if name == "Alkalinity" and curr > 20:
                curr *= 0.056
                self.log_message(f"Note: Converted ppm to {curr:.2f} dKH\n")

            # 2. Safety Logic
            warnings = []
            if name == "Alkalinity" and ph and ph >= 8.5:
                messagebox.showerror("CRITICAL", "pH is too high (8.5+)! Dosing aborted.")
                return
            
            if name == "Alkalinity" and ph and ph >= 8.35:
                warnings.append("!! High pH: Split dose into 3 parts.")
            
            last_mag = self.get_last_test("Magnesium")
            if name in ["Alkalinity", "Calcium"] and (last_mag is None or last_mag < 1300):
                warnings.append(f"!! Low/Unknown Mag ({last_mag}): Stability at risk.")

            # 3. Dosage Math
            diff = targ - curr
            if diff <= 0:
                self.log_message("Target reached. No dose needed.")
                return

            total_ml = (diff * GALLONS) / strength
            
            # 4. Final Report
            output = f"--- DOSAGE REPORT ---\n"
            output += f"Total to Add: {total_ml:.1f} mL\n"
            output += f"Status: {name} increase of {diff:.2f}\n"
            if warnings:
                output += "\nSAFETY WARNINGS:\n" + "\n".join(warnings)
            
            self.log_message(output)
            
            # Ask to log
            if messagebox.askyesno("Save Dose", f"Did you dose {total_ml:.1f}mL now?"):
                self.save_to_csv("Dose", name, total_ml, ph)
                self.build_log_tab() # Refresh history

        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers in the fields.")

    def save_to_csv(self, type, param, val, ph):
        file_exists = os.path.isfile(LOG_FILE)
        with open(LOG_FILE, "a", newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "Tank", "Type", "Parameter", "Value", "pH"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), "Generic", type, param, f"{val:.2f}", ph])

    def build_log_tab(self):
        # Simple scrollable list of recent events
        for widget in self.log_tab.winfo_children(): widget.destroy()
        
        tk.Label(self.log_tab, text="Recent Activity (Last 15)", font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()[-15:]
                for line in reversed(lines):
                    tk.Label(self.log_tab, text=line.strip(), font=("Consolas", 8)).pack(anchor="w", padx=10)
        else:
            tk.Label(self.log_tab, text="No logs found yet.").pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = AquariumCommander(root)
    root.mainloop()
