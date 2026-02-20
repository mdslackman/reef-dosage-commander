import tkinter as tk
from tkinter import ttk, messagebox
import csv, os
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ReeferMadness:
    def __init__(self, root):
        self.root = root
        self.root.title("Reefer Madness v0.24.0 - Interactive Pro")
        self.root.geometry("1500x950")
        
        self.db = {
            "Alkalinity": {
                "target": 8.5, "low": 7.5, "high": 9.5, "max_daily": 1.4, "unit": "dKH", "custom_unit": "dKH per mL",
                "dosing": {"Fritz RPM Liquid": 1.4, "ESV B-Ionic Pt 1": 1.4, "Custom": 1.0},
                "kits": {
                    "Hanna Checker": ["1. Fill cuvette 10ml", "2. Zero the meter", "3. Add reagent & shake 2 mins", "4. Insert & Read"],
                    "Salifert Kit": ["1. 4ml Tank Water", "2. Add 2 drops KH-Ind", "3. Titrate until Pink/Red"]
                }
            },
            "Calcium": {
                "target": 420, "low": 400, "high": 440, "max_daily": 25.0, "unit": "ppm", "custom_unit": "PPM per mL",
                "dosing": {"ESV B-Ionic Pt 2": 20.0, "Fritz RPM": 20.0, "Custom": 1.0},
                "kits": {"Red Sea Pro": ["1. 5ml Water", "2. 5 drops Ca-A", "3. 1 scoop Ca-B", "4. Titrate"]}
            },
            "Magnesium": {
                "target": 1350, "low": 1280, "high": 1420, "max_daily": 100.0, "unit": "ppm", "custom_unit": "PPM per mL",
                "dosing": {"Fritz Magnesium": 100.0, "Custom": 1.0},
                "kits": {"Salifert": ["1. 2ml Water", "2. 6 drops Mg-1", "3. Titrate"]}
            },
            "Nitrate": { "target": 5.0, "low": 2.0, "high": 10.0, "max_daily": 5.0, "unit": "ppm", "custom_unit": "PPM per mL", "dosing": {"Custom": 1.0}, "kits": {"Salifert": ["1. 1ml Water", "2. NO3-1 & NO3-2", "3. Wait 3 mins"]} },
            "Phosphate": { "target": 0.03, "low": 0.01, "high": 0.08, "max_daily": 0.02, "unit": "ppm", "custom_unit": "PPM per mL", "dosing": {"Custom": 1.0}, "kits": {"Hanna ULR": ["1. 10ml Water", "2. Add Reagent", "3. Wait 3 mins"]} }
        }

        self.log_file = os.path.join(os.path.expanduser("~/Documents/ReeferMadness"), "reef_pro_v24.csv")
        if not os.path.exists(os.path.dirname(self.log_file)): os.makedirs(os.path.dirname(self.log_file))

        # Variables
        self.vol_v = tk.StringVar(value="220"); self.u_mode = tk.StringVar(value="Gallons")
        self.p_var = tk.StringVar(value="Alkalinity"); self.b_var = tk.StringVar()
        self.curr_v = tk.StringVar(); self.targ_v = tk.StringVar(value="152"); self.ph_v = tk.StringVar()
        self.alk_mode = tk.StringVar(value="ppm"); self.c_strength = tk.StringVar(value="1.4")
        
        # Consumption Tracker Variables
        self.cp_var = tk.StringVar(value="Alkalinity"); self.cb_var = tk.StringVar()
        self.c_s = tk.StringVar(); self.c_e = tk.StringVar(); self.c_d = tk.StringVar(value="3")
        self.cons_alk_mode = tk.StringVar(value="dKH")
        self.maint_c_strength = tk.StringVar(value="1.0")

        self.nb = ttk.Notebook(self.root)
        self.tabs = {n: ttk.Frame(self.nb) for n in ["Action Plan", "Maintenance", "Trends", "History"]}
        for n, f in self.tabs.items(): self.nb.add(f, text=f" {n} ")
        self.nb.pack(expand=True, fill="both")

        self.build_action_plan(); self.build_maint(); self.build_trends(); self.build_history()
        
        # Action Plan Traces
        self.p_var.trace_add("write", self.sync_ui)
        self.b_var.trace_add("write", self.toggle_custom_visibility)
        self.curr_v.trace_add("write", self.auto_unit_sense)
        self.alk_mode.trace_add("write", self.update_target_by_unit)
        self.timer_running = False
        self.timer_after_id = None
        
        self.sync_ui()

    def auto_unit_sense(self, *a):
        if self.p_var.get() == "Alkalinity":
            try:
                val = float(self.curr_v.get())
                if val > 30 and self.alk_mode.get() == "dKH": self.alk_mode.set("ppm")
                elif 0 < val <= 30 and self.alk_mode.get() == "ppm": self.alk_mode.set("dKH")
            except: pass

    def update_target_by_unit(self, *a):
        if self.p_var.get() == "Alkalinity":
            self.targ_v.set("152" if self.alk_mode.get() == "ppm" else "8.5")

    def toggle_custom_visibility(self, *a):
        if self.b_var.get() == "Custom": self.c_frame.pack(side="left", padx=10)
        else: self.c_frame.pack_forget()

    def toggle_maint_custom_visibility(self, *a):
        if self.cb_var.get() == "Custom": self.maint_c_frame.pack(side="left", padx=10)
        else: self.maint_c_frame.pack_forget()

    def sync_ui(self, *a):
        p = self.p_var.get()
        brands = list(self.db[p]["dosing"].keys())
        self.b_cb['values'] = brands
        self.b_var.set(brands[0])
        self.c_lbl.config(text=self.db[p]["custom_unit"])
        if p == "Alkalinity": self.alk_box.pack(side="left")
        else: self.alk_box.pack_forget(); self.targ_v.set(str(self.db[p]["target"]))

    def build_action_plan(self):
        f = self.tabs["Action Plan"]
        cfg = ttk.LabelFrame(f, text=" 1. System Config ", padding=10); cfg.pack(fill="x", padx=20, pady=5)
        tk.Entry(cfg, textvariable=self.vol_v, width=8).pack(side="left")
        ttk.Radiobutton(cfg, text="Gallons", variable=self.u_mode, value="Gallons").pack(side="left", padx=5)
        ttk.Radiobutton(cfg, text="Liters", variable=self.u_mode, value="Liters").pack(side="left")

        sel = ttk.LabelFrame(f, text=" 2. Product Selection ", padding=10); sel.pack(fill="x", padx=20, pady=5)
        ttk.Combobox(sel, textvariable=self.p_var, values=list(self.db.keys()), state="readonly").pack(side="left")
        self.b_cb = ttk.Combobox(sel, textvariable=self.b_var, state="readonly"); self.b_cb.pack(side="left", padx=10)
        self.c_frame = ttk.Frame(sel); tk.Label(self.c_frame, text="Conc:").pack(side="left")
        tk.Entry(self.c_frame, textvariable=self.c_strength, width=8).pack(side="left"); self.c_lbl = tk.Label(self.c_frame, text="unit"); self.c_lbl.pack(side="left")

        inp = ttk.LabelFrame(f, text=" 3. Safety Calculator ", padding=10); inp.pack(fill="x", padx=20, pady=5)
        tk.Label(inp, text="Current:").pack(side="left"); tk.Entry(inp, textvariable=self.curr_v, width=8).pack(side="left", padx=5)
        tk.Label(inp, text="Target:").pack(side="left"); tk.Entry(inp, textvariable=self.targ_v, width=8).pack(side="left", padx=5)
        tk.Label(inp, text="pH:").pack(side="left", padx=5); tk.Entry(inp, textvariable=self.ph_v, width=5).pack(side="left")
        self.alk_box = ttk.Frame(inp)
        ttk.Radiobutton(self.alk_box, text="dKH", variable=self.alk_mode, value="dKH").pack(side="left")
        ttk.Radiobutton(self.alk_box, text="PPM", variable=self.alk_mode, value="ppm").pack(side="left")

        tk.Button(f, text="GENERATE SAFETY PLAN", command=self.calc_safety, bg="#2c3e50", fg="white", font='bold').pack(pady=10)
        self.res = tk.Label(f, text="Ready", font=("Arial", 11), justify="left"); self.res.pack()

    def build_maint(self):
        f = self.tabs["Maintenance"]
        cf = ttk.LabelFrame(f, text=" Consumption Tracker ", padding=10); cf.pack(fill="x", padx=20, pady=5)
        ttk.Combobox(cf, textvariable=self.cp_var, values=list(self.db.keys()), state="readonly").pack(side="left")
        self.cb_cb_maint = ttk.Combobox(cf, textvariable=self.cb_var, state="readonly"); self.cb_cb_maint.pack(side="left", padx=5)
        
        # Maint Custom Field
        self.maint_c_frame = ttk.Frame(cf); tk.Label(self.maint_c_frame, text="Conc:").pack(side="left")
        tk.Entry(self.maint_c_frame, textvariable=self.maint_c_strength, width=8).pack(side="left")
        self.maint_c_lbl = tk.Label(self.maint_c_frame, text="unit"); self.maint_c_lbl.pack(side="left")

        self.cons_alk_box = ttk.Frame(cf)
        ttk.Radiobutton(self.cons_alk_box, text="dKH", variable=self.cons_alk_mode, value="dKH").pack(side="left")
        ttk.Radiobutton(self.cons_alk_box, text="PPM", variable=self.cons_alk_mode, value="ppm").pack(side="left")
        self.cons_alk_box.pack(side="left", padx=5)

        tk.Label(cf, text="Start:").pack(side="left", padx=2); tk.Entry(cf, textvariable=self.c_s, width=5).pack(side="left")
        tk.Label(cf, text="End:").pack(side="left", padx=2); tk.Entry(cf, textvariable=self.c_e, width=5).pack(side="left")
        tk.Label(cf, text="Days:").pack(side="left", padx=2); tk.Entry(cf, textvariable=self.c_d, width=3).pack(side="left")
        tk.Button(cf, text="CALC mL/DAY", command=self.calc_cons_ml, bg="#16a085", fg="white").pack(side="left", padx=5)
        self.cr_lbl = tk.Label(cf, text="-- mL/Day", font='bold'); self.cr_lbl.pack(side="left")

        self.cp_var.trace_add("write", lambda *a: self.sync_maint_ui())
        self.cb_var.trace_add("write", self.toggle_maint_custom_visibility)
        self.sync_maint_ui()

        lf = ttk.LabelFrame(f, text=" Daily Log ", padding=10); lf.pack(fill="both", expand=True, padx=20)
        self.log_vars = {p: tk.StringVar() for p in self.db.keys()}
        self.log_alk_unit = tk.StringVar(value="ppm")
        for p in self.db.keys():
            r = ttk.Frame(lf); r.pack(fill="x", pady=2)
            tk.Label(r, text=p, width=12).pack(side="left")
            tk.Entry(r, textvariable=self.log_vars[p], width=10).pack(side="left")
            if p == "Alkalinity":
                ttk.Radiobutton(r, text="dKH", variable=self.log_alk_unit, value="dKH").pack(side="left", padx=5)
                ttk.Radiobutton(r, text="PPM", variable=self.log_alk_unit, value="ppm").pack(side="left")
        tk.Button(lf, text="SAVE TO LOG", command=self.save_entry, bg="#27ae60", fg="white").pack(pady=10)

    def sync_maint_ui(self):
        p = self.cp_var.get()
        brands = list(self.db[p]["dosing"].keys())
        self.cb_cb_maint['values'] = brands
        self.cb_var.set(brands[0])
        self.maint_c_lbl.config(text=self.db[p]["custom_unit"])
        if p == "Alkalinity": self.cons_alk_box.pack(side="left")
        else: self.cons_alk_box.pack_forget()

    def build_history(self):
        f = self.tabs["History"]
        ref = ttk.LabelFrame(f, text=" Dynamic Test Kit Checklist & Timer ", padding=15); ref.pack(fill="x", padx=20, pady=5)
        sel_f = ttk.Frame(ref); sel_f.pack(fill="x")
        self.h_p_var = tk.StringVar(value="Alkalinity"); self.h_k_var = tk.StringVar()
        ttk.Combobox(sel_f, textvariable=self.h_p_var, values=list(self.db.keys()), state="readonly").pack(side="left", padx=5)
        self.h_k_cb = ttk.Combobox(sel_f, textvariable=self.h_k_var, state="readonly"); self.h_k_cb.pack(side="left")
        
        # Clickable/Cancellable Timer
        self.timer_lbl = tk.Label(sel_f, text="00:00", font=("Arial", 16, "bold"), fg="#e67e22", cursor="hand2")
        self.timer_lbl.pack(side="right", padx=20)
        self.timer_lbl.bind("<Button-1>", self.cancel_timer)
        tk.Label(sel_f, text="Click timer to cancel", font=("Arial", 7)).pack(side="right")
        
        self.h_p_var.trace_add("write", self.sync_history_kits)
        self.h_k_var.trace_add("write", self.draw_checklist)
        self.check_f = ttk.Frame(ref); self.check_f.pack(fill="x", pady=10)
        
        # History Table with Delete
        self.tree = ttk.Treeview(f, columns=("T", "P", "V"), show="headings")
        for c in ("T", "P", "V"): self.tree.heading(c, text=c)
        self.tree.pack(fill="both", expand=True, padx=20)
        tk.Button(f, text="DELETE SELECTED ROW", command=self.delete_row, bg="#c0392b", fg="white").pack(pady=10)
        self.sync_history_kits()
        self.refresh_history()

    def sync_history_kits(self, *a):
        p = self.h_p_var.get(); kits = list(self.db[p]["kits"].keys())
        self.h_k_cb['values'] = kits; self.h_k_var.set(kits[0])

    def draw_checklist(self, *a):
        for w in self.check_f.winfo_children(): w.destroy()
        p, k = self.h_p_var.get(), self.h_k_var.get()
        for step in self.db[p]["kits"].get(k, []):
            r = ttk.Frame(self.check_f); r.pack(anchor="w", pady=2)
            tk.Checkbutton(r).pack(side="left")
            tk.Label(r, text=step).pack(side="left")
            if "mins" in step:
                try:
                    m = int(step.split("mins")[0].split()[-1])
                    tk.Button(r, text="START TIMER", command=lambda t=m: self.start_timer(t), bg="#e67e22", fg="white", font=("Arial", 8)).pack(side="left", padx=10)
                except: pass

    def start_timer(self, mins):
        if self.timer_running: self.cancel_timer()
        self.timer_running = True
        self.timer_lbl.config(fg="#e67e22")
        end_time = datetime.now() + timedelta(minutes=mins)
        def update():
            if not self.timer_running: return
            rem = end_time - datetime.now()
            if rem.total_seconds() > 0:
                self.timer_lbl.config(text=f"{int(rem.total_seconds()//60):02}:{int(rem.total_seconds()%60):02}")
                self.timer_after_id = self.root.after(1000, update)
            else:
                self.timer_lbl.config(text="DONE!", fg="red")
                self.timer_running = False
                messagebox.showinfo("Timer", "Test period complete!")
        update()

    def cancel_timer(self, event=None):
        self.timer_running = False
        if self.timer_after_id: self.root.after_cancel(self.timer_after_id)
        self.timer_lbl.config(text="00:00", fg="#e67e22")

    def calc_safety(self):
        try:
            p = self.p_var.get(); vol = float(self.vol_v.get()) * (3.785 if self.u_mode.get() == "Gallons" else 1.0)
            cur, tar = float(self.curr_v.get()), float(self.targ_v.get())
            diff = (tar - cur) / 17.86 if (p == "Alkalinity" and self.alk_mode.get() == "ppm") else (tar - cur)
            strn = float(self.c_strength.get()) if self.b_var.get() == "Custom" else self.db[p]["dosing"][self.b_var.get()]
            tot = (diff * vol) / strn
            days = max(1, int(abs(diff) / self.db[p]["max_daily"]) + 1)
            if p == "Alkalinity" and self.ph_v.get() and float(self.ph_v.get()) > 8.3: days = max(days, 3)
            self.res.config(text=f"Total: {tot:.1f} mL | Dose: {tot/days:.1f} mL/day for {days} days")
        except: messagebox.showerror("Error", "Check inputs.")

    def calc_cons_ml(self):
        try:
            p = self.cp_var.get(); vol = float(self.vol_v.get()) * (3.785 if self.u_mode.get() == "Gallons" else 1.0)
            s, e, d = float(self.c_s.get()), float(self.c_e.get()), float(self.c_d.get())
            if d <= 0: raise ValueError
            drop = (s - e) / d
            if p == "Alkalinity" and self.cons_alk_mode.get() == "ppm": drop /= 17.86
            strn = float(self.maint_c_strength.get()) if self.cb_var.get() == "Custom" else self.db[p]["dosing"][self.cb_var.get()]
            res = (drop * vol) / strn
            self.cr_lbl.config(text=f"{abs(res):.1f} mL/Day")
        except: messagebox.showerror("Math Error", "Ensure all fields are filled and days > 0.")

    def save_entry(self):
        try:
            with open(self.log_file, "a", newline="") as f:
                w = csv.writer(f); ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                for p, v in self.log_vars.items():
                    if v.get():
                        val = float(v.get())
                        if p == "Alkalinity" and self.log_alk_unit.get() == "dKH": val *= 17.86
                        w.writerow([ts, p, val]); v.set("")
            self.refresh_history(); messagebox.showinfo("Saved", "Logged.")
        except: pass

    def build_trends(self):
        f = self.tabs["Trends"]
        self.chart_f = ttk.Frame(f); self.chart_f.pack(fill="both", expand=True)
        tk.Button(f, text="REFRESH GRAPHS", command=self.draw_graphs).pack()

    def draw_graphs(self):
        for w in self.chart_f.winfo_children(): w.destroy()
        if not os.path.exists(self.log_file) or os.stat(self.log_file).st_size < 10: return
        df = pd.read_csv(self.log_file, names=["T", "P", "V"]); df['T'] = pd.to_datetime(df['T'])
        fig, axes = plt.subplots(5, 1, figsize=(8, 14), constrained_layout=True)
        for i, p in enumerate(self.db.keys()):
            sub = df[df['P'] == p].sort_values('T')
            f = 17.86 if p == "Alkalinity" else 1.0
            axes[i].set_title(f"{p}")
            axes[i].axhspan(self.db[p]['low']*f, self.db[p]['high']*f, color='green', alpha=0.1)
            if not sub.empty: axes[i].plot(sub['T'], sub['V'], marker='o')
        FigureCanvasTkAgg(fig, master=self.chart_f).get_tk_widget().pack(fill="both", expand=True)

    def refresh_history(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                for r in csv.reader(f): self.tree.insert("", "end", values=r)

    def delete_row(self):
        sel = self.tree.selection()
        if not sel: return
        rows = []
        with open(self.log_file, "r") as f: rows = list(csv.reader(f))
        val = self.tree.item(sel[0])['values']
        rows = [r for r in rows if not (r[0] == str(val[0]) and r[1] == val[1])]
        with open(self.log_file, "w", newline="") as f: csv.writer(f).writerows(rows)
        self.refresh_history()

if __name__ == "__main__":
    root = tk.Tk(); app = ReeferMadness(root); root.mainloop()
