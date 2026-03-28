import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkhtmlview import HTMLLabel
import requests
import threading
import os
import json
import random
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import deque

CONFIG_FILE = "config.json"

# 🎨 Colors
BG = "#003153"
TAB = "#0b3d5c"
ACTIVE = "#1f5f8b"


class CSVAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDP Client 1.0")
        self.root.geometry("600x800")
        self.root.configure(bg=BG)

        self.stop_flag = False
        self.current_request = None
        self.csv_file = None
        self.config = {}
        self._last_html = ""

        self.project_dir = self.find_project_root()
        self.csv_folder = os.path.join(self.project_dir, "Saved", "Profiling", "CSV")

        self.apply_theme()
        self.load_config()
        self.build_ui()
        self.auto_load_csv()

    # ---------------- PROJECT ROOT ----------------
    def find_project_root(self):
        current = os.path.abspath(os.path.dirname(__file__))
        while True:
            if any(f.endswith(".uproject") for f in os.listdir(current)):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                return os.getcwd()
            current = parent

    # ---------------- THEME ----------------
    def apply_theme(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=BG)
        style.configure("TNotebook.Tab", background=TAB, foreground="white")
        style.map("TNotebook.Tab", background=[("selected", ACTIVE)])

    # ---------------- CONFIG ----------------
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                self.config = json.load(f)

    def save_config(self):
        self.config = {
            "url": self.url_entry.get(),
            "model": self.model_var.get(),
            "mode": self.mode_var.get(),
            "sampling": self.sample_var.get(),
            "detail": self.detail_var.get(),
            "trim": self.trim_var.get()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)
        self.config_path_label.config(
            text=f"Saved: {os.path.abspath(CONFIG_FILE)}"
        )

    # ---------------- UI ----------------
    def build_ui(self):
        # ---------------- Menu Bar ----------------
        menubar = tk.Menu(self.root)
        process_menu = tk.Menu(menubar, tearoff=0)
        process_menu.add_command(label="Go", command=self.start_analysis)
        process_menu.add_command(label="Stop", command=self.stop_analysis)
        menubar.add_cascade(label="Process", menu=process_menu)
        tabs_menu = tk.Menu(menubar, tearoff=0)
        tabs_menu.add_command(label="Connection", command=lambda: self.select_tab(0))
        tabs_menu.add_command(label="Settings", command=lambda: self.select_tab(1))
        tabs_menu.add_command(label="Custom Dataset", command=lambda: self.select_tab(2))
        tabs_menu.add_command(label="Ask", command=lambda: self.select_tab(3))
        tabs_menu.add_command(label="Export", command=lambda: self.select_tab(4))
        tabs_menu.add_separator()
        tabs_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Options", menu=tabs_menu)
        self.root.config(menu=menubar)

        # ---------------- Top Bar ----------------
        top_bar = tk.Frame(self.root, bg=BG)
        top_bar.pack(fill="x", pady=5)

        tk.Label(top_bar, text="PDP Client 1.0",
                 bg=BG, fg="white", font=("Lato", 18, "bold")).pack(side="left", padx=10)

        save_btn_frame = tk.Frame(top_bar, bg=BG)
        save_btn_frame.pack(side="right", padx=10)
        tk.Button(save_btn_frame, text="Save Config",
                  command=self.save_config,
                  bg=ACTIVE, fg="white").pack()
        self.config_path_label = tk.Label(save_btn_frame, text="",
                                          bg=BG, fg="white", font=("Arial", 8))
        self.config_path_label.pack()

        # ---------------- Notebook ----------------
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="x", padx=10, pady=5)

        self.tab_conn = tk.Frame(self.notebook, bg=BG)
        self.tab_perf = tk.Frame(self.notebook, bg=BG)
        self.tab_csv = tk.Frame(self.notebook, bg=BG)
        self.tab_ask = tk.Frame(self.notebook, bg=BG)
        self.tab_export = tk.Frame(self.notebook, bg=BG)

        self.notebook.add(self.tab_conn, text="Connection")
        self.notebook.add(self.tab_perf, text="Settings")
        self.notebook.add(self.tab_csv, text="Custom Dataset")
        self.notebook.add(self.tab_ask, text="Ask")
        self.notebook.add(self.tab_export, text="Export")

        self.build_connection_tab()
        self.build_perf_tab()
        self.build_csv_tab()
        self.build_ask_tab()
        self.build_export_tab()

        # ---------------- CSV Label ----------------
        self.csv_label = tk.Label(self.root, text="Dataset not available",
                                  bg=BG, fg="white")
        self.csv_label.pack(pady=5)

        # ---------------- Progress ----------------
        self.progress = ttk.Progressbar(self.root, length=450)
        self.progress.pack(pady=5)
        self.progress_label = tk.Label(self.root, text="Idle",
                                       bg=BG, fg="white")
        self.progress_label.pack()

        # ---------------- Buttons ----------------
        btn_frame = tk.Frame(self.root, bg=BG)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Go",
                  command=self.start_analysis,
                  bg="#007acc", fg="white").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Stop",
                  command=self.stop_analysis,
                  bg="#cc3300", fg="white").pack(side="left", padx=5)

        # ---------------- HTML Report Viewer (replaces Text widget) ----------------
        html_frame = tk.Frame(self.root, bg=BG)
        html_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.html_label = HTMLLabel(
            html_frame,
            html="<h2 style='color:#aad4f5;' style='text-align: center;'>Press Go to begin</h2>",
            background="#0b1f33"
        )
        self.html_label.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(html_frame, command=self.html_label.yview)
        scrollbar.pack(side="right", fill="y")
        self.html_label.config(yscrollcommand=scrollbar.set)

    # ---------------- TAB SELECT ----------------
    def select_tab(self, index):
        self.notebook.select(index)

    # ---------------- CONNECTION TAB ----------------
    def build_connection_tab(self):
        tk.Label(self.tab_conn, text="Server URL",
                 bg=BG, fg="white").pack(anchor="w", padx=10)
        self.url_entry = tk.Entry(self.tab_conn)
        self.url_entry.insert(0, self.config.get("url", "http://localhost:11434"))
        self.url_entry.pack(fill="x", padx=10)

        self.model_var = tk.StringVar(value=self.config.get("model", "llama3"))
        self.model_dropdown = tk.OptionMenu(self.tab_conn, self.model_var, "")
        self.model_dropdown.pack(anchor="w", padx=10)

        tk.Button(self.tab_conn, text="Fetch Models",
                  command=self.load_models).pack(padx=10, pady=5)
        self.load_models()

    def load_models(self):
        try:
            res = requests.get(f"{self.url_entry.get()}/api/tags", timeout=3)
            models = [m["name"] for m in res.json().get("models", [])]
            menu = self.model_dropdown["menu"]
            menu.delete(0, "end")
            for m in models:
                menu.add_command(label=m, command=lambda v=m: self.model_var.set(v))
            if models:
                self.model_var.set(models[0])
        except:
            pass

    # ---------------- PERFORMANCE TAB ----------------
    def build_perf_tab(self):
        self.mode_var = tk.StringVar(value=self.config.get("mode", "Fast"))
        self.sample_var = tk.StringVar(value=self.config.get("sampling", "Tail"))
        self.detail_var = tk.StringVar(value=self.config.get("detail", "Low"))
        self.trim_var = tk.BooleanVar(value=self.config.get("trim", True))

        tk.Label(self.tab_perf, text="Mode", bg=BG, fg="white").pack(anchor="w", padx=10)
        ttk.Combobox(self.tab_perf, textvariable=self.mode_var,
                     values=["Fast", "Balanced", "Full"]).pack(padx=10, pady=3)
        tk.Label(self.tab_perf, text="Sampling", bg=BG, fg="white").pack(anchor="w", padx=10)
        ttk.Combobox(self.tab_perf, textvariable=self.sample_var,
                     values=["Head", "Tail", "Random"]).pack(padx=10, pady=3)
        tk.Label(self.tab_perf, text="Detail", bg=BG, fg="white").pack(anchor="w", padx=10)
        ttk.Combobox(self.tab_perf, textvariable=self.detail_var,
                     values=["Low", "Medium", "High"]).pack(padx=10, pady=3)
        tk.Checkbutton(
            self.tab_perf,
            text="Trim CSV (faster)",
            variable=self.trim_var,
            bg=BG, fg="white",
            selectcolor=BG,
            activebackground=BG,
            activeforeground="white"
        ).pack(anchor="w", padx=10)

    # ---------------- CSV TAB ----------------
    def build_csv_tab(self):
        tk.Button(self.tab_csv, text="Load CSV",
                  command=self.load_csv).pack(pady=10)

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[(".csv", "*.csv")])
        if path:
            self.csv_file = path
            self.csv_label.config(text=f"Loaded: {os.path.basename(path)}")

    def auto_load_csv(self):
        if not os.path.exists(self.csv_folder):
            self.csv_label.config(text="CSV folder not found")
            return
        files = [os.path.join(self.csv_folder, f)
                 for f in os.listdir(self.csv_folder) if f.endswith(".csv")]
        if not files:
            self.csv_label.config(text="No CSV files found")
            return
        self.csv_file = max(files, key=os.path.getmtime)
        self.csv_label.config(text=f"Latest Dataset: {os.path.basename(self.csv_file)}")

    # ---------------- FAST CSV SAMPLER ----------------
    def process_data(self):
        max_lines = 300 if self.trim_var.get() else 3000
        with open(self.csv_file, "r", encoding="utf-8", errors="ignore") as f:
            if self.sample_var.get() == "Head":
                return "".join([next(f, "") for _ in range(max_lines)])
            elif self.sample_var.get() == "Tail":
                return "".join(deque(f, max_lines))
            else:
                sample = []
                for i, line in enumerate(f):
                    if i < max_lines:
                        sample.append(line)
                    else:
                        j = random.randint(0, i)
                        if j < max_lines:
                            sample[j] = line
                return "".join(sample)

    # ---------------- CHART GENERATION ----------------
    def generate_charts(self):
        """Build bar + line charts from CSV, return (bar_path, line_path, table_html)."""
        try:
            df = pd.read_csv(self.csv_file, engine="python", on_bad_lines="skip")
            df.columns = [c.strip() for c in df.columns]
            numeric_df = df.select_dtypes(include="number")

            avg = numeric_df.mean().sort_values(ascending=False)
            top10 = avg.head(10)

            # Bar chart
            bar_path = os.path.abspath("chart_bar.png")
            plt.figure(figsize=(7, 3.5))
            top10.plot(kind="bar", color="#1f5f8b")
            plt.xticks(rotation=45, ha="right", fontsize=8)
            plt.title("Top Metrics (Average)", fontsize=10)
            plt.tight_layout()
            plt.savefig(bar_path, dpi=90)
            plt.close()

            # Line chart – top 3 columns
            line_path = os.path.abspath("chart_line.png")
            top3_cols = top10.index[:3]
            plt.figure(figsize=(7, 3))
            for col in top3_cols:
                plt.plot(numeric_df[col].values, label=col)
            plt.legend(fontsize=8)
            plt.title("Performance Over Time (Top 3)", fontsize=10)
            plt.tight_layout()
            plt.savefig(line_path, dpi=90)
            plt.close()

            table_html = top10.to_frame(name="Average").to_html(border=1)
            return bar_path, line_path, table_html

        except Exception as e:
            return None, None, f"<p><b>Chart error:</b> {e}</p>"

    # ---------------- ANALYSIS ----------------
    def start_analysis(self):
        if not self.csv_file:
            messagebox.showerror("Error", "No CSV loaded")
            return
        self.stop_flag = False
        threading.Thread(target=self.analyze, daemon=True).start()

    def stop_analysis(self):
        self.stop_flag = True
        if self.current_request:
            try:
                self.current_request.close()
            except:
                pass
        self.set_progress(0, "Stopped server request")

    def set_progress(self, v, t):
        self.progress["value"] = v
        self.progress_label.config(text=t)
        self.root.update_idletasks()

    def analyze(self):
        try:
            # --- Step 1: Charts ---
            self.set_progress(20, "Generating charts...")
            bar_path, line_path, table_html = self.generate_charts()
            if self.stop_flag:
                return

            # --- Step 2: CSV sample for AI ---
            self.set_progress(40, "Processing CSV...")
            data = self.process_data()
            if self.stop_flag:
                return

            # --- Step 3: Ollama request ---
            payload = {
                "model": self.model_var.get(),
                "prompt": f"""Analyze Unreal Engine profiling CSV.

Return structured:
[ISSUE]
Cause:
Fix:

CSV:
{data}
""",
                "stream": False
            }
            self.set_progress(70, "Analyzing your capture data...")
            self.current_request = requests.post(
                f"{self.url_entry.get()}/api/generate",
                json=payload,
                timeout=(3, None)
            )
            try:
                result_json = self.current_request.json()
            except:
                text = self.current_request.text.strip().split("\n")[-1]
                result_json = json.loads(text)

            analysis = result_json.get("response", "")

            # ---- HTML ----
            html = f"""
        <h1>Unreal Profiling Report</h1>

        <h2>Top Metrics</h2>
        <img src="chart_bar.png">

        <h2>Performance Over Time</h2>
        <img src="chart_line.png">

        <h2>Table</h2>
        {table_html}

        <h2>AI Analysis</h2>
        <pre>{analysis}</pre>
        """
            self._last_html = html
            self.root.after(0, lambda: self.html_label.set_html(html))
            self.set_progress(100, "Done")

        except Exception as e:
            if not self.stop_flag:
                err_html = f"<h2 style='color:red;'>Error</h2><pre>{e}</pre>"
                self._last_html = err_html
                self.root.after(0, lambda: self.html_label.set_html(err_html))
        finally:
            self.current_request = None
            self.set_progress(0, "Idle")

    # ---------------- ASK TAB ----------------
    def build_ask_tab(self):
        self.ask_entry = tk.Text(self.tab_ask, height=4)
        self.ask_entry.pack(fill="x", padx=10)
        tk.Button(self.tab_ask, text="Ask agent",
                  command=self.run_query).pack()

    def run_query(self):
        q = self.ask_entry.get("1.0", tk.END).strip()
        threading.Thread(target=self.send_query, args=(q,), daemon=True).start()

    def send_query(self, q):
        try:
            self.set_progress(30, "Processing query...")
            res = requests.post(
                f"{self.url_entry.get()}/api/generate",
                json={
                    "model": self.model_var.get(),
                    "prompt": q,
                    "stream": False
                },
                timeout=(3, None)
            )
            try:
                data = res.json()
            except:
                text = res.text.strip().split("\n")[-1]
                data = json.loads(text)
            self.show_result(data.get("response", ""))
            self.set_progress(100, "Done")
        except Exception as e:
            self.show_result(str(e))
        finally:
            self.set_progress(0, "Idle")

    # ---------------- EXPORT TAB ----------------
    def build_export_tab(self):
        tk.Label(self.tab_export, text="Save Analysis Reports", bg=BG, fg="white").pack(pady=5)
        tk.Button(self.tab_export, text="Save as HTML",
                  command=lambda: self.save_result("html")).pack(pady=5)
        tk.Button(self.tab_export, text="Save as CSV",
                  command=lambda: self.save_result("csv")).pack(pady=5)

    def save_result(self, ext):
        if not self._last_html:
            messagebox.showwarning("Warning", "Nothing to save. Run an analysis first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            filetypes=[(f"{ext.upper()} file", f"*.{ext}")]
        )
        if path:
            if ext == "html":
                content = self._last_html
            elif ext == "csv":
                plain = self._strip_html(self._last_html)
                import re
                lines = [l.strip() for l in plain.splitlines() if l.strip()]
                rows = [["Line", "Content"]] + [[str(i + 1), l] for i, l in enumerate(lines)]
                import csv as csv_mod
                import io
                buf = io.StringIO()
                writer = csv_mod.writer(buf)
                writer.writerows(rows)
                content = buf.getvalue()
            else:
                content = self._strip_html(self._last_html)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Saved", f"Saved to {path}")

    # ---------------- ABOUT ----------------
    def show_about(self):
        win = tk.Toplevel(self.root)
        win.title("About")
        win.geometry("300x120")
        win.resizable(False, False)
        win.configure(bg=BG)
        tk.Label(win, text="PDP Client 1.0", bg=BG, fg="white",
                 font=("Lato", 13, "bold")).pack(pady=(18, 4))
        tk.Label(win, text="Made by 9sAE7\nLicensed under GPL 3.0", bg=BG, fg="white",
                 font=("Arial", 10)).pack()
        link = tk.Label(win, text="https://github.com/sayoojjs",
                        bg=BG, fg="#4da6ff", font=("Arial", 9, "underline"),
                        cursor="hand2")
        link.pack(pady=(2, 10))
        link.bind("<Button-1>", lambda e: __import__("webbrowser").open("https://github.com/sayoojjs"))

    @staticmethod
    def _strip_html(html):
        import re
        return re.sub(r"<[^>]+>", "", html)

    # ---------------- POPUP RESULT (Ask tab) ----------------
    def show_result(self, t):
        win = tk.Toplevel(self.root)
        win.title("Agent Response")
        win.geometry("500x400")
        txt = tk.Text(win, bg="#0b1f33", fg="white", wrap="word")
        txt.pack(fill="both", expand=True)
        txt.insert(tk.END, t)


if __name__ == "__main__":
    root = tk.Tk()
    app = CSVAnalyzerApp(root)
    root.mainloop()
