import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkhtmlview import HTMLLabel
import requests
import threading
import os
import json
import random
import base64
import io
import re
import csv as csv_mod
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

# Columns that are frame counters / indices — excluded from charts and tables
_FRAME_COLS = {"frame", "frameindex", "framecounter", "framenum", "framenumber"}


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
        self._bar_b64 = None
        self._line_b64 = None

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

        # ---------------- HTML Report Viewer ----------------
        html_frame = tk.Frame(self.root, bg=BG)
        html_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.html_label = HTMLLabel(
            html_frame,
            html="<h2 style='color:#aad4f5;' style='text-align: center;'>Press Go to begin</h2>",
            background="#4b4e51"
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

    # ---------------- UE VALUE FORMATTER ----------------
    @staticmethod
    def _format_ue_value(col_name, value):
        """
        Format a numeric average the way Unreal Engine stat displays show it.
        Timing values → ms, draw calls → integer, primitive counts → K/M,
        memory → MB/GB, FPS → FPS.  Everything else falls back to ms.
        """
        c = col_name.lower()

        # Large geometry / object counts
        count_kw = ("primitives", "triangles", "polys", "polygon",
                    "vertices", "instances", "batches", "objects", "meshes")
        if any(k in c for k in count_kw):
            if value >= 1_000_000:
                return f"{value / 1_000_000:.2f} M"
            if value >= 1_000:
                return f"{value / 1_000:.1f} K"
            return f"{int(round(value)):,}"

        # Draw calls
        if "drawcall" in c or c == "drawcalls":
            return f"{int(round(value)):,}"

        # Memory
        if "memory" in c or c.startswith("mem"):
            if value >= 1024:
                return f"{value / 1024:.2f} GB"
            return f"{value:.1f} MB"

        # FPS / frame rate
        if "fps" in c or "framerate" in c or "frame_rate" in c:
            return f"{value:.1f} FPS"

        # Percentage stats
        if "percent" in c or c.endswith("%") or "utilization" in c:
            return f"{value:.1f}%"

        # Default: timing in ms (covers GameThread, RenderThread, GPU, RHIThread,
        # Slate/*, Task/*, etc.)
        return f"{value:.2f} ms"

    # ---------------- CSV LOADING / NUMERIC EXTRACTION ----------------
    def _load_numeric_df(self):
        """
        Load self.csv_file fresh, coerce mixed-type columns (e.g. '12.3ms')
        to float, drop frame-index columns, drop all-NaN and constant columns.
        Returns a clean numeric DataFrame where every column has real variance.
        Raises ValueError with a human-readable message if no usable data found.
        """
        df = pd.read_csv(self.csv_file, engine="python", on_bad_lines="skip")
        df.columns = [c.strip() for c in df.columns]

        # Strip whitespace from string cells
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

        # Coerce every column: handles pure numbers and values like '12.3ms', '8%'
        for col in df.columns:
            if col.lower() in _FRAME_COLS:
                continue  # skip frame index columns entirely
            converted = pd.to_numeric(df[col], errors="coerce")
            # Only replace if at least 50% of rows parsed as a number
            if converted.notna().sum() >= max(1, len(df) * 0.5):
                df[col] = converted

        numeric_df = df.select_dtypes(include="number")

        # Remove frame index columns that slipped through
        numeric_df = numeric_df[[
            c for c in numeric_df.columns if c.lower() not in _FRAME_COLS
        ]]

        # Drop fully-NaN columns
        numeric_df = numeric_df.dropna(axis=1, how="all")

        # Drop constant columns (nothing to chart)
        numeric_df = numeric_df.loc[:, numeric_df.nunique() > 1]

        if numeric_df.empty:
            raise ValueError("No numeric columns with variance found in this CSV.")

        avgs = numeric_df.mean(skipna=True).dropna()
        if avgs.empty:
            raise ValueError("Could not compute averages — all columns are NaN.")

        return numeric_df, avgs

    # ---------------- CHART GENERATION ----------------
    def _clear_chart_state(self):
        """Destroy all previous chart data and every open matplotlib figure."""
        self._bar_b64 = None
        self._line_b64 = None
        plt.close("all")

    def _encode_fig(self, fig):
        """Save a figure to an in-memory PNG, base64-encode it, close it, return data URI."""
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=90)
        plt.close(fig)
        buf.seek(0)
        return "data:image/png;base64," + base64.b64encode(buf.read()).decode("utf-8")

    def generate_charts(self):
        """
        Generate bar chart, line chart, and stats table entirely from the
        currently loaded CSV.  Every call reads the file fresh — no state
        is reused from a previous run.

        Returns (bar_b64, line_b64, table_html).
        On error returns (None, None, error_html_string).
        """
        try:
            numeric_df, avgs = self._load_numeric_df()
        except ValueError as e:
            return None, None, f"<p><b>Chart error:</b> {e}</p>"
        except Exception as e:
            return None, None, f"<p><b>Chart error (load):</b> {e}</p>"

        try:
            fname = os.path.basename(self.csv_file)

            # ---- Split metrics into timing-scale and count-scale ----
            # UE timing stats (ms) live roughly in 0–5000.
            # Count stats (draw calls, primitives) live above that.
            timing_avgs = avgs[(avgs >= 0) & (avgs < 5000)].sort_values(ascending=False)
            count_avgs  = avgs[avgs >= 5000].sort_values(ascending=False)

            # Bar chart: prefer timing metrics because they're the primary perf signal.
            # Fall back to all metrics if no timing cols exist.
            bar_source = timing_avgs if not timing_avgs.empty else avgs
            n_bar = min(10, len(bar_source))
            bar_metrics = bar_source.head(n_bar)

            # ---- Bar chart ----
            fig_bar, ax_bar = plt.subplots(figsize=(7, 3.5))
            x = range(len(bar_metrics))
            bars = ax_bar.bar(x, bar_metrics.values, color=ACTIVE)
            ax_bar.set_xticks(list(x))
            ax_bar.set_xticklabels(bar_metrics.index, rotation=45, ha="right", fontsize=8)
            # Y-axis: label in ms if all bar_source values < 5000, otherwise raw
            if bar_source is timing_avgs:
                ax_bar.set_ylabel("ms", fontsize=8)
                ax_bar.yaxis.set_major_formatter(
                    plt.FuncFormatter(lambda v, _: f"{v:.1f}")
                )
            ax_bar.set_title(f"Timing Metrics — Avg per Frame  [{fname}]", fontsize=9)
            # Value labels on top of each bar
            for rect, val in zip(bars, bar_metrics.values):
                ax_bar.text(
                    rect.get_x() + rect.get_width() / 2,
                    rect.get_height() * 1.01,
                    self._format_ue_value(bar_metrics.index[list(bar_metrics.values).index(val)], val),
                    ha="center", va="bottom", fontsize=7, clip_on=True
                )
            fig_bar.tight_layout()
            bar_b64 = self._encode_fig(fig_bar)

            # ---- Line chart: top 3 timing metrics over all frames ----
            line_source = timing_avgs if not timing_avgs.empty else avgs
            n_line = min(3, len(line_source))
            line_cols = line_source.index[:n_line]

            fig_line, ax_line = plt.subplots(figsize=(7, 3))
            for col in line_cols:
                series = numeric_df[col].dropna().reset_index(drop=True)
                if not series.empty:
                    ax_line.plot(series.values, label=f"{col}")
            ax_line.set_xlabel("Frame", fontsize=8)
            ax_line.set_ylabel("ms", fontsize=8)
            ax_line.legend(fontsize=8)
            ax_line.set_title(
                f"Performance Over Time — Top {n_line} Timing Metrics  [{fname}]", fontsize=9
            )
            fig_line.tight_layout()
            line_b64 = self._encode_fig(fig_line)

            # ---- Stats table (UE-style formatted values) ----
            # Show timing metrics first, then count metrics — mirrors UE stat display order
            table_rows = []
            for col, val in timing_avgs.items():
                table_rows.append({"Stat": col,
                                   "Avg": self._format_ue_value(col, val),
                                   "Min": self._format_ue_value(col, numeric_df[col].min()),
                                   "Max": self._format_ue_value(col, numeric_df[col].max())})
            for col, val in count_avgs.items():
                table_rows.append({"Stat": col,
                                   "Avg": self._format_ue_value(col, val),
                                   "Min": self._format_ue_value(col, numeric_df[col].min()),
                                   "Max": self._format_ue_value(col, numeric_df[col].max())})

            if table_rows:
                tdf = pd.DataFrame(table_rows).set_index("Stat")
                table_html = tdf.to_html(border=1)
            else:
                table_html = "<p>No stats available.</p>"

            return bar_b64, line_b64, table_html

        except Exception as e:
            return None, None, f"<p><b>Chart error (render):</b> {e}</p>"

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
            # Step 0 — destroy every trace of the previous run before touching anything
            self._clear_chart_state()
            self._last_html = ""

            # Step 1 — generate charts fresh from the currently loaded CSV
            self.set_progress(20, "Generating charts...")
            bar_b64, line_b64, table_html = self.generate_charts()
            if self.stop_flag:
                return

            self._bar_b64 = bar_b64
            self._line_b64 = line_b64

            # Step 2 — sample CSV text for AI
            self.set_progress(40, "Processing CSV...")
            data = self.process_data()
            if self.stop_flag:
                return

            # Step 3 — Ollama request
            payload = {
                "model": self.model_var.get(),
                "prompt": (
                    "Analyze Unreal Engine profiling CSV.\n\n"
                    "Return structured:\n[ISSUE]\nCause:\nFix:\n\n"
                    f"CSV:\n{data}\n"
                ),
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
            except Exception:
                text = self.current_request.text.strip().split("\n")[-1]
                result_json = json.loads(text)

            analysis = result_json.get("response", "")

            # Step 4 — build self-contained HTML (images are embedded as data URIs)
            bar_tag  = (f'<img src="{self._bar_b64}">'
                        if self._bar_b64 else "<p><i>Bar chart unavailable</i></p>")
            line_tag = (f'<img src="{self._line_b64}">'
                        if self._line_b64 else "<p><i>Line chart unavailable</i></p>")

            html = (
                "<h1>Unreal Profiling Report</h1>"
                f"<p><b>Dataset:</b> {os.path.basename(self.csv_file)}</p>"
                "<h2>Timing Metrics (Average per Frame)</h2>"
                f"{bar_tag}"
                "<h2>Performance Over Time</h2>"
                f"{line_tag}"
                "<h2>Stats Table</h2>"
                f"{table_html}"
                "<h2>Analysis Report</h2>"
                f"<pre>{analysis}</pre>"
            )

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
                json={"model": self.model_var.get(), "prompt": q, "stream": False},
                timeout=(3, None)
            )
            try:
                data = res.json()
            except Exception:
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
                lines = [l.strip() for l in plain.splitlines() if l.strip()]
                rows = [["Line", "Content"]] + [[str(i + 1), l] for i, l in enumerate(lines)]
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
        link = tk.Label(win, text="https://github.com/sayoojjs/Profile_Data_Processor",
                        bg=BG, fg="#4da6ff", font=("Arial", 9, "underline"),
                        cursor="hand2")
        link.pack(pady=(2, 10))
        link.bind("<Button-1>", lambda e: __import__("webbrowser").open(
            "https://github.com/sayoojjs/Profile_Data_Processor"))

    @staticmethod
    def _strip_html(html):
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
