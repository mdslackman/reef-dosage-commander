import tkinter as tk
from tkinter import ttk, messagebox
import sys, os

class AquariumCommanderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Aquarium Commander Pro v0.13.3")
        self.root.geometry("1000x900")
        
        # --- CRITICAL FIX: CLEAN EXIT ---
        # This ensures the app kills itself fully when the window is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.prices = {
            "Fritz RPM Liquid Alkalinity": 23.99,
            "ESV B-Ionic Alk (Part 1)": 24.92,
            "Fritz RPM Liquid Calcium": 23.99,
            "Fritz RPM Liquid Magnesium": 38.49
        }
        price_keys = list(self.prices.keys())
        
        self.safety_ranges = {
            "Alkalinity": {"min": 5.0, "max": 13.0}, # dKH
            "Calcium": {"min": 350.0, "max": 550.0},
            "Magnesium": {"min": 1100.0, "max": 1600.0}
        }
        
        self.ranges = {
            "Alkalinity": {"units": ["dKH", "ppm"], "target": 8.5, "brands": price_keys[:2]},
            "Calcium": {"units": ["ppm"], "target": 420, "brands": [price_keys[2]]},
            "Magnesium": {"units": ["ppm"], "target": 1350, "brands": [price_keys[3]]}
        }

        self.vol_var = tk.StringVar()
        self.p_var = tk.StringVar(value="Alkalinity")
        self.u_var = tk.StringVar()
        
        self.build_ui()
        self.update_param_selection()

    def build_ui(self):
        f = ttk.Frame(self.root, padding="40"); f.pack(fill="both", expand=True)
        
        tk.Label(f, text="Volume (Gal):").grid(row=0, column=0, sticky="w")
        tk.Entry(f, textvariable=self.vol_var, width=15, bg="#ffffcc").grid(row=0, column=1, sticky="w", pady=5)

        tk.Label(f, text="Parameter:").grid(row=1, column=0, sticky="w")
        self.p_menu = ttk.Combobox(f, textvariable=self.p_var, values=list(self.ranges.keys()), state="readonly")
        self.p_menu.grid(row=1, column=1, sticky="ew", pady=5)
        self.p_menu.bind("<<ComboboxSelected>>", self.update_param_selection)

        tk.Label(f, text="Unit:").grid(row=2, column=0, sticky="w")
        self.u_menu = ttk.Combobox(f, textvariable=self.u_var, state="readonly")
        self.u_menu.grid(row=2, column=1, sticky="ew", pady=5)

        tk.Label(f, text="Current Reading:").grid(row=3, column=0, sticky="w")
        self.curr_ent = tk.Entry(f); self.curr_ent.grid(row=3, column=1, sticky="ew", pady=5)

        tk.Label(f, text="Target Goal:").grid(row=4, column=0, sticky="w")
        self.targ_ent = tk.Entry(f); self.targ_ent.grid(row=4, column=1, sticky="ew", pady=5)

        tk.Button(f, text="RUN SAFETY & DOSAGE CALC", command=self.perform_calc, bg="#2980b9", fg="white", height=2).grid(row=5, columnspan=2, pady=20, sticky="ew")
        
        self.res_lbl = tk.Label(f, text="Ready.", font=("Arial", 12, "bold"), wraplength=500)
        self.res_lbl.grid(row=6, columnspan=2)

    def perform_calc(self):
        try:
            p, vol, unit = self.p_var.get(), float(self.vol_var.get()), self.u_var.get()
            curr, targ = float(self.curr_ent.get()), float(self.targ_ent.get())

            # --- FIX: REAL-TIME PPM TO DKH UPDATE ---
            if p == "Alkalinity" and unit == "ppm":
                converted_curr = curr / 17.86
                converted_targ = targ / 17.86
                # Force the UI to show the dKH equivalent so the user sees the safety check
                self.res_lbl.config(text=f"Note: {curr}ppm is approx {converted_curr:.2f} dKH", fg="black")
                std_curr, std_targ = converted_curr, converted_targ
            else:
                std_curr, std_targ = curr, targ

            # Safety Logic
            safe = self.safety_ranges[p]
            if std_curr < safe['min']:
                self.res_lbl.config(text=f"⚠️ CRITICAL LOW: {curr} {unit} is dangerous!", fg="red")
                return
            elif std_curr > safe['max']:
                self.res_lbl.config(text=f"⚠️ CRITICAL HIGH: {curr} {unit} is over limit!", fg="red")
                return

            diff = std_targ - std_curr
            if diff <= 0:
                self.res_lbl.config(text="STATUS: OPTIMAL", fg="green")
                return

            # Basic dosage logic (0.6 strength for Alk)
            total_ml = (diff * vol) / (0.6 if p == "Alkalinity" else 1.0)
            self.res_lbl.config(text=f"DOSE: {total_ml:.1f} mL Total", fg="blue")

        except ValueError:
            self.res_lbl.config(text="ERROR: Enter valid numbers", fg="red")

    def on_closing(self):
        """Forces the entire process to terminate."""
        self.root.destroy()
        sys.exit(0)

    def update_param_selection(self, e=None):
        p = self.p_var.get()
        self.u_menu.config(values=self.ranges[p]["units"]); self.u_menu.current(0)
        self.targ_ent.delete(0, tk.END); self.targ_ent.insert(0, str(self.ranges[p]["target"]))

if __name__ == "__main__":
    root = tk.Tk(); app = AquariumCommanderPro(root); root.mainloop()
