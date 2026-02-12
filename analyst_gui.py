"""
PC Analyst Pro - Advanced System Diagnostic & Maintenance Suite
================================================================
Required external libraries (install via pip):
    pip install psutil pywin32 speedtest-cli

Optional:
    pip install pynvml   (for NVIDIA GPU monitoring)

Run as Administrator for full functionality (crash dump access, cleanup, etc.)
"""

# ─── Standard Library ───────────────────────────────────────────────────────
import os
import sys
import glob
import struct
import shutil
import threading
import subprocess
import time
import webbrowser
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext
import tkinter as tk
from tkinter import ttk

# ─── Third-Party: psutil (required) ─────────────────────────────────────────
try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False

# ─── Third-Party: pywin32 (optional, Windows only) ──────────────────────────
WIN32_OK = False
try:
    import win32evtlog
    import win32con
    import win32evtlogutil
    WIN32_OK = True
except ImportError:
    pass

# ─── Third-Party: pynvml (optional, NVIDIA GPUs) ────────────────────────────
GPU_SUPPORT = False
try:
    import pynvml
    pynvml.nvmlInit()
    GPU_SUPPORT = True
except Exception:
    pass

# ─── Third-Party: speedtest-cli (optional) ──────────────────────────────────
SPEEDTEST_OK = False
try:
    import speedtest as speedtest_lib
    SPEEDTEST_OK = True
except ImportError:
    pass


# ════════════════════════════════════════════════════════════════════════════
# BSOD / ERROR CODE KNOWLEDGE BASE
# ════════════════════════════════════════════════════════════════════════════

BSOD_DB = {
    "0x0000000A": {
        "name": "IRQL_NOT_LESS_OR_EQUAL",
        "category": "Memory / Driver",
        "plain": "A driver tried to access memory it shouldn't. Usually caused by a faulty or outdated driver.",
        "fix": "Update all drivers — especially chipset, network, and display drivers. Run Windows Memory Diagnostic."
    },
    "0x0000001E": {
        "name": "KMODE_EXCEPTION_NOT_HANDLED",
        "category": "Driver / Software",
        "plain": "A kernel-mode program generated an error the OS couldn't handle.",
        "fix": "Check recently installed software or drivers. Boot into Safe Mode and uninstall suspect apps."
    },
    "0x00000024": {
        "name": "NTFS_FILE_SYSTEM",
        "category": "Disk I/O Error",
        "plain": "The NTFS file system driver encountered a disk error — likely a failing hard drive.",
        "fix": "Run CHKDSK immediately. Back up your data. Consider replacing the hard drive."
    },
    "0x00000050": {
        "name": "PAGE_FAULT_IN_NONPAGED_AREA",
        "category": "Memory Corruption",
        "plain": "The system tried to read a memory page that didn't exist — often bad RAM or a corrupt driver.",
        "fix": "Run Windows Memory Diagnostic. Update or roll back recently changed drivers."
    },
    "0x00000074": {
        "name": "BAD_SYSTEM_CONFIG_INFO",
        "category": "Registry / Boot",
        "plain": "The system registry is damaged or misconfigured. Can occur after a failed update.",
        "fix": "Boot from Windows installation media and use Startup Repair. Restore a registry backup."
    },
    "0x0000007E": {
        "name": "SYSTEM_THREAD_EXCEPTION_NOT_HANDLED",
        "category": "Driver Failure",
        "plain": "A system thread threw an exception that wasn't caught — almost always a driver bug.",
        "fix": "Boot into Safe Mode. Update or uninstall the most recently installed/updated driver."
    },
    "0x0000007F": {
        "name": "UNEXPECTED_KERNEL_MODE_TRAP",
        "category": "Hardware / Overheating",
        "plain": "The CPU hit a fatal condition — can be caused by overheating, bad RAM, or overclocking.",
        "fix": "Check CPU temperatures. Remove overclocking. Test RAM with MemTest86."
    },
    "0x0000009F": {
        "name": "DRIVER_POWER_STATE_FAILURE",
        "category": "Power / Driver",
        "plain": "A driver failed to respond during a power transition (sleep/wake/shutdown).",
        "fix": "Update drivers — especially USB, network, and display. Disable fast startup in Power Settings."
    },
    "0x000000EF": {
        "name": "CRITICAL_PROCESS_DIED",
        "category": "Critical System Process",
        "plain": "A core Windows process (like lsass.exe or winlogon.exe) crashed and took the OS with it.",
        "fix": "Run SFC /scannow in Command Prompt as Administrator. May require Windows repair install."
    },
    "0x0000003B": {
        "name": "SYSTEM_SERVICE_EXCEPTION",
        "category": "Driver / Software",
        "plain": "An exception occurred while executing a routine transition from user to kernel mode.",
        "fix": "Update Windows and all drivers. Check for corrupt system files with SFC /scannow."
    },
    "0x00000116": {
        "name": "VIDEO_TDR_FAILURE",
        "category": "GPU Driver Failure",
        "plain": "Your graphics card's driver stopped responding and couldn't recover. Common with GPU overloads.",
        "fix": "Update or clean-install your GPU drivers. Check GPU temperatures. Reduce GPU overclock if any."
    },
    "0x000000D1": {
        "name": "DRIVER_IRQL_NOT_LESS_OR_EQUAL",
        "category": "Driver / Memory",
        "plain": "A network or hardware driver tried to access paged memory at too high an interrupt level.",
        "fix": "Update network adapter and chipset drivers. Disable recently added hardware temporarily."
    },
    "UNKNOWN": {
        "name": "Unknown Error Code",
        "category": "Unclassified",
        "plain": "This error code is not in the local database. The system experienced an unexpected failure.",
        "fix": "Search the error code on Microsoft's online BSOD documentation for specific guidance."
    }
}

# ════════════════════════════════════════════════════════════════════════════
# COLOUR & STYLE CONSTANTS
# ════════════════════════════════════════════════════════════════════════════

C = {
    "bg":        "#0d1117",
    "surface":   "#161b22",
    "border":    "#30363d",
    "blue":      "#58a6ff",
    "green":     "#3fb950",
    "red":       "#f85149",
    "yellow":    "#e3b341",
    "purple":    "#bc8cff",
    "muted":     "#8b949e",
    "text":      "#e6edf3",
    "white":     "#ffffff",
}


# ════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION CLASS
# ════════════════════════════════════════════════════════════════════════════

class PCAnalystPro:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PC Analyst Pro  ·  System Engineering Suite")
        self.root.geometry("1100x820")
        self.root.minsize(900, 700)
        self.root.configure(bg=C["bg"])

        # Report save directory
        self.report_dir = os.path.join(
            os.path.expanduser("~"), "Documents", "PC Analyst Reports"
        )
        os.makedirs(self.report_dir, exist_ok=True)

        # Shared state
        self.scan_results: list[dict] = []   # [{code, path, time, detail}]
        self.running = True

        self._build_ui()
        self._start_monitor_thread()

    # ─────────────────────────────────────────────────────────────────────
    # UI CONSTRUCTION
    # ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_notebook()
        self._build_console()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C["surface"], height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(
            hdr,
            text="⚙  PC ANALYST PRO",
            font=("Segoe UI", 18, "bold"),
            bg=C["surface"], fg=C["blue"]
        ).pack(side="left", padx=24, pady=16)

        self.clock_lbl = tk.Label(
            hdr, text="", font=("Consolas", 10),
            bg=C["surface"], fg=C["muted"]
        )
        self.clock_lbl.pack(side="right", padx=24)
        self._tick_clock()

    def _tick_clock(self):
        self.clock_lbl.config(text=datetime.now().strftime("%d %b %Y  %H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    def _build_notebook(self):
        style = ttk.Style()
        style.theme_use("default")

        style.configure("Dark.TNotebook",
                        background=C["bg"], borderwidth=0)
        style.configure("Dark.TNotebook.Tab",
                        background=C["surface"], foreground=C["muted"],
                        font=("Segoe UI", 10, "bold"),
                        padding=[16, 8], borderwidth=0)
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", C["blue"])],
                  foreground=[("selected", C["white"])])

        nb = ttk.Notebook(self.root, style="Dark.TNotebook")
        nb.pack(fill="x", padx=16, pady=(12, 0))

        # ── Tab 1: Dashboard ──────────────────────────────────────────────
        dash = tk.Frame(nb, bg=C["bg"])
        nb.add(dash, text="  📊  Dashboard  ")
        self._build_dashboard(dash)

        # ── Tab 2: Analysis ───────────────────────────────────────────────
        analysis = tk.Frame(nb, bg=C["bg"])
        nb.add(analysis, text="  🔍  Analysis  ")
        self._build_analysis_tab(analysis)

        # ── Tab 3: Cleanup ────────────────────────────────────────────────
        cleanup = tk.Frame(nb, bg=C["bg"])
        nb.add(cleanup, text="  🧹  Cleanup  ")
        self._build_cleanup_tab(cleanup)

        # ── Tab 4: Network ────────────────────────────────────────────────
        net = tk.Frame(nb, bg=C["bg"])
        nb.add(net, text="  🌐  Network  ")
        self._build_network_tab(net)

    # ── Dashboard Tab ──────────────────────────────────────────────────────

    def _build_dashboard(self, parent):
        outer = tk.Frame(parent, bg=C["bg"])
        outer.pack(fill="x", padx=24, pady=16)

        self.cpu_bar  = self._metric_row(outer, "CPU",  C["blue"])
        self.ram_bar  = self._metric_row(outer, "RAM",  C["green"])
        self.gpu_bar  = self._metric_row(outer, "GPU",  C["purple"])
        self.disk_bar = self._metric_row(outer, "DISK", C["yellow"])

    def _metric_row(self, parent, label: str, color: str):
        row = tk.Frame(parent, bg=C["bg"])
        row.pack(fill="x", pady=5)

        lbl = tk.Label(
            row, text=f"{label}:  0%",
            font=("Segoe UI", 10, "bold"), width=14, anchor="w",
            bg=C["bg"], fg=C["text"]
        )
        lbl.pack(side="left")

        # Style name must be in the form  "<Name>.Horizontal.TProgressbar"
        # so ttk can resolve the layout automatically.  We sanitise the
        # label to strip any characters that confuse Tcl's layout lookup.
        safe   = label.replace(" ", "").replace("(", "").replace(")", "")
        style_name = f"{safe}.Horizontal.TProgressbar"

        s = ttk.Style()
        # Ensure the layout exists by copying from the base style first,
        # then override colours.  This avoids the "Layout not found" error
        # on Python 3.12+ / Tk 8.6.13+.
        try:
            base_layout = s.layout("Horizontal.TProgressbar")
            s.layout(style_name, base_layout)
        except Exception:
            pass  # layout already exists or base unavailable — proceed anyway

        s.configure(style_name,
                    background=color,
                    troughcolor=C["surface"],
                    thickness=18)

        bar = ttk.Progressbar(row, length=700, mode="determinate",
                              style=style_name)
        bar.pack(side="left", fill="x", expand=True, padx=10)

        val_lbl = tk.Label(row, text="", width=6,
                           font=("Consolas", 9), anchor="e",
                           bg=C["bg"], fg=color)
        val_lbl.pack(side="left")

        return (bar, lbl, val_lbl)

    # ── Analysis Tab ───────────────────────────────────────────────────────

    def _build_analysis_tab(self, parent):
        btn_frame = tk.Frame(parent, bg=C["bg"])
        btn_frame.pack(pady=16, padx=24, anchor="w")

        self._styled_btn(btn_frame, "⚡  Quick Scan",
                         self._run_quick_scan, C["green"]).pack(side="left", padx=6)
        self._styled_btn(btn_frame, "🔬  Deep Scan",
                         self._run_deep_scan, C["blue"]).pack(side="left", padx=6)

        # Crash report list
        list_frame = tk.Frame(parent, bg=C["surface"],
                              highlightbackground=C["border"], highlightthickness=1)
        list_frame.pack(fill="x", padx=24, pady=(0, 8))

        tk.Label(list_frame, text="Crash Report History",
                 font=("Segoe UI", 11, "bold"),
                 bg=C["surface"], fg=C["text"]).pack(anchor="w", padx=12, pady=(10, 4))

        cols = ("time", "code", "category", "file")
        self.crash_tree = ttk.Treeview(list_frame, columns=cols,
                                       show="headings", height=6)

        tree_style = ttk.Style()
        tree_style.configure("Treeview",
                             background=C["bg"],
                             fieldbackground=C["bg"],
                             foreground=C["text"],
                             rowheight=24,
                             font=("Consolas", 9))
        tree_style.configure("Treeview.Heading",
                             background=C["surface"],
                             foreground=C["muted"],
                             font=("Segoe UI", 9, "bold"))
        tree_style.map("Treeview", background=[("selected", C["blue"])])

        for col, heading, width in [
            ("time",     "Timestamp",    160),
            ("code",     "Error Code",   130),
            ("category", "Category",     180),
            ("file",     "Source File",  300),
        ]:
            self.crash_tree.heading(col, text=heading)
            self.crash_tree.column(col, width=width, anchor="w")

        self.crash_tree.pack(fill="x", padx=12, pady=(0, 4))
        self.crash_tree.bind("<Double-1>", self._on_crash_detail)

        tk.Label(list_frame,
                 text="Double-click a row to view plain-English diagnosis",
                 font=("Segoe UI", 8, "italic"),
                 bg=C["surface"], fg=C["muted"]).pack(anchor="w", padx=12, pady=(0, 8))

    # ── Cleanup Tab ────────────────────────────────────────────────────────

    def _build_cleanup_tab(self, parent):
        opt_frame = tk.Frame(parent, bg=C["bg"])
        opt_frame.pack(fill="x", padx=24, pady=16)

        tk.Label(opt_frame, text="Select areas to clean:",
                 font=("Segoe UI", 11, "bold"),
                 bg=C["bg"], fg=C["text"]).grid(row=0, column=0,
                                                columnspan=2, sticky="w", pady=(0, 8))

        self.clean_opts = {}
        options = [
            ("temp",    "System Temp Folders   (%TEMP%, C:\\Windows\\Temp)"),
            ("prefetch","Windows Prefetch       (C:\\Windows\\Prefetch)"),
            ("updates", "Old Windows Update Cache"),
            ("browser", "Browser Caches        (Chrome, Edge, Firefox)"),
        ]
        for i, (key, label) in enumerate(options):
            var = tk.BooleanVar(value=True)
            self.clean_opts[key] = var
            cb = tk.Checkbutton(
                opt_frame, text=label, variable=var,
                font=("Segoe UI", 10),
                bg=C["bg"], fg=C["text"],
                selectcolor=C["surface"],
                activebackground=C["bg"],
                activeforeground=C["text"]
            )
            cb.grid(row=i + 1, column=0, sticky="w", padx=8, pady=3)

        self._styled_btn(
            opt_frame, "🧹  Start Cleanup", self._run_cleanup, C["yellow"]
        ).grid(row=len(options) + 1, column=0, sticky="w", padx=8, pady=12)

        self.clean_progress = ttk.Progressbar(
            opt_frame, mode="indeterminate", length=400
        )
        self.clean_progress.grid(row=len(options) + 2, column=0,
                                 sticky="w", padx=8)

    # ── Network Tab ────────────────────────────────────────────────────────

    def _build_network_tab(self, parent):
        btn_row = tk.Frame(parent, bg=C["bg"])
        btn_row.pack(pady=16, padx=24, anchor="w")

        self._styled_btn(btn_row, "🌐  Run Diagnostics",
                         self._run_network_diag, C["blue"]).pack(side="left", padx=6)
        self._styled_btn(btn_row, "⚡  Speed Test",
                         self._run_speed_test, C["green"]).pack(side="left", padx=6)

        metrics_frame = tk.Frame(parent, bg=C["surface"],
                                 highlightbackground=C["border"], highlightthickness=1)
        metrics_frame.pack(fill="x", padx=24, pady=(0, 12))

        tk.Label(metrics_frame, text="Network Health",
                 font=("Segoe UI", 11, "bold"),
                 bg=C["surface"], fg=C["text"]).pack(anchor="w", padx=12, pady=(10, 6))

        inner = tk.Frame(metrics_frame, bg=C["surface"])
        inner.pack(fill="x", padx=12, pady=(0, 12))

        self.net_labels = {}
        metrics = [
            ("status",   "Connection Status"),
            ("ping",     "Ping Latency"),
            ("download", "Download Speed"),
            ("upload",   "Upload Speed"),
            ("dns",      "DNS Status"),
        ]
        for i, (key, label) in enumerate(metrics):
            tk.Label(inner, text=f"{label}:", width=22, anchor="w",
                     font=("Segoe UI", 10, "bold"),
                     bg=C["surface"], fg=C["muted"]).grid(
                row=i, column=0, sticky="w", pady=3)

            val = tk.Label(inner, text="—",
                           font=("Consolas", 10),
                           bg=C["surface"], fg=C["text"])
            val.grid(row=i, column=1, sticky="w", padx=12, pady=3)
            self.net_labels[key] = val

    # ── Console (shared across tabs) ───────────────────────────────────────

    def _build_console(self):
        console_hdr = tk.Frame(self.root, bg=C["bg"])
        console_hdr.pack(fill="x", padx=20, pady=(8, 0))

        tk.Label(console_hdr, text="Operation Log",
                 font=("Segoe UI", 9, "bold"),
                 bg=C["bg"], fg=C["muted"]).pack(side="left")

        self._styled_btn(
            console_hdr, "📄  Export Report",
            self._export_report, C["muted"], small=True
        ).pack(side="right", padx=4)

        self.console = tk.Text(
            self.root,
            bg=C["surface"], fg=C["text"],
            font=("Consolas", 9),
            padx=12, pady=10,
            borderwidth=1, relief="flat",
            state="disabled",
            height=10
        )
        self.console.pack(fill="both", expand=True, padx=20, pady=(4, 16))
        self.console.tag_configure("blue",   foreground=C["blue"])
        self.console.tag_configure("green",  foreground=C["green"])
        self.console.tag_configure("red",    foreground=C["red"])
        self.console.tag_configure("yellow", foreground=C["yellow"])
        self.console.tag_configure("purple", foreground=C["purple"])
        self.console.tag_configure("muted",  foreground=C["muted"])

    # ─────────────────────────────────────────────────────────────────────
    # HELPER: styled button
    # ─────────────────────────────────────────────────────────────────────

    def _styled_btn(self, parent, text, cmd, color, small=False):
        font = ("Segoe UI", 9, "bold") if small else ("Segoe UI", 10, "bold")
        pad = (8, 4) if small else (14, 8)
        btn = tk.Button(
            parent, text=text, command=cmd,
            font=font, padx=pad[0], pady=pad[1],
            bg=color, fg=C["bg"],
            activebackground=C["text"], activeforeground=C["bg"],
            relief="flat", cursor="hand2", bd=0
        )
        return btn

    # ─────────────────────────────────────────────────────────────────────
    # LOGGING
    # ─────────────────────────────────────────────────────────────────────

    def log(self, text: str, color: str = ""):
        def _do():
            self.console.config(state="normal")
            ts = datetime.now().strftime("[%H:%M:%S]")
            line = f"{ts}  {text}\n"
            self.console.insert("end", line, color or "")
            self.console.see("end")
            self.console.config(state="disabled")
        self.root.after(0, _do)

    # ─────────────────────────────────────────────────────────────────────
    # LIVE MONITOR THREAD
    # ─────────────────────────────────────────────────────────────────────

    def _start_monitor_thread(self):
        t = threading.Thread(target=self._monitor_loop, daemon=True)
        t.start()

    def _monitor_loop(self):
        while self.running:
            try:
                cpu  = psutil.cpu_percent(interval=1) if PSUTIL_OK else 0
                ram  = psutil.virtual_memory().percent if PSUTIL_OK else 0
                disk = psutil.disk_usage("/").percent if PSUTIL_OK else 0

                gpu = 0
                if GPU_SUPPORT:
                    try:
                        h = pynvml.nvmlDeviceGetHandleByIndex(0)
                        gpu = pynvml.nvmlDeviceGetUtilizationRates(h).gpu
                    except Exception:
                        pass

                self.root.after(0, lambda c=cpu:  self._set_bar(self.cpu_bar,  c))
                self.root.after(0, lambda r=ram:  self._set_bar(self.ram_bar,  r))
                self.root.after(0, lambda g=gpu:  self._set_bar(self.gpu_bar,  g))
                self.root.after(0, lambda d=disk: self._set_bar(self.disk_bar, d))
            except Exception as e:
                print(f"Monitor error: {e}")
            time.sleep(2)

    def _set_bar(self, bar_tuple, value: float):
        bar, lbl, val_lbl = bar_tuple
        bar["value"] = value
        name = lbl.cget("text").split(":")[0]
        lbl.config(text=f"{name}:  {value:.0f}%")
        val_lbl.config(text=f"{value:.0f}%")

    # ─────────────────────────────────────────────────────────────────────
    # ANALYSIS — QUICK SCAN
    # ─────────────────────────────────────────────────────────────────────

    def _run_quick_scan(self):
        threading.Thread(target=self._quick_scan, daemon=True).start()

    def _quick_scan(self):
        self.log("━━━  QUICK SCAN STARTED  ━━━", "blue")

        # 1. CPU temperature (psutil supports sensors on Linux; Windows needs wmi)
        self.log("Checking core services …", "muted")
        critical = ["lsass.exe", "csrss.exe", "winlogon.exe", "svchost.exe"]
        found = {p.info["name"].lower()
                 for p in psutil.process_iter(["name"])
                 if PSUTIL_OK}
        for svc in critical:
            if svc in found:
                self.log(f"  ✓  {svc} — running", "green")
            else:
                self.log(f"  ✗  {svc} — NOT FOUND (may need admin rights)", "red")

        # 2. Disk usage
        if PSUTIL_OK:
            usage = psutil.disk_usage("/")
            pct = usage.percent
            color = "red" if pct > 90 else ("yellow" if pct > 75 else "green")
            self.log(
                f"Disk usage: {pct:.1f}%  "
                f"({usage.used // (1024**3)} GB used / {usage.total // (1024**3)} GB total)",
                color
            )

        # 3. RAM pressure
        if PSUTIL_OK:
            ram = psutil.virtual_memory()
            self.log(
                f"RAM: {ram.percent:.1f}% used  "
                f"({ram.available // (1024**2)} MB free)",
                "green" if ram.percent < 80 else "red"
            )

        self.log("━━━  QUICK SCAN COMPLETE  ━━━", "blue")

    # ─────────────────────────────────────────────────────────────────────
    # ANALYSIS — DEEP SCAN
    # ─────────────────────────────────────────────────────────────────────

    def _run_deep_scan(self):
        threading.Thread(target=self._deep_scan, daemon=True).start()

    def _deep_scan(self):
        self.log("━━━  DEEP SCAN STARTED  ━━━", "blue")
        self.scan_results.clear()
        self.root.after(0, lambda: self.crash_tree.delete(*self.crash_tree.get_children()))

        # ── A. Windows Event Log crash analysis ──────────────────────────
        self.log("Scanning Windows Event Logs for BSODs …", "muted")
        if WIN32_OK:
            self._parse_event_logs()
        else:
            self.log(
                "  ⚠  pywin32 not installed — falling back to Minidump scan",
                "yellow"
            )
            self._parse_minidumps()

        # ── B. Disk S.M.A.R.T. (via wmic) ────────────────────────────────
        self.log("\nQuerying S.M.A.R.T. disk health …", "muted")
        self._smart_check()

        # ── C. Background process anomalies ───────────────────────────────
        self.log("\nScanning background processes …", "muted")
        self._process_audit()

        # ── D. High-CPU processes ─────────────────────────────────────────
        self.log("\nTop CPU-consuming processes:", "muted")
        if PSUTIL_OK:
            procs = sorted(
                psutil.process_iter(["name", "cpu_percent"]),
                key=lambda p: p.info.get("cpu_percent") or 0,
                reverse=True
            )[:5]
            for p in procs:
                cpu = p.info.get("cpu_percent") or 0
                col = "red" if cpu > 30 else ("yellow" if cpu > 10 else "green")
                self.log(f"  {p.info['name']:<30} {cpu:>6.1f}% CPU", col)

        self.log("\n━━━  DEEP SCAN COMPLETE  ━━━", "blue")
        if not self.scan_results:
            self.log("No crash events found — system appears stable.", "green")

    def _parse_event_logs(self):
        """Read System event log for BugCheck (BSOD) events (Event ID 1001)."""
        try:
            h = win32evtlog.OpenEventLog(None, "System")
            flags = (win32evtlog.EVENTLOG_BACKWARDS_READ |
                     win32evtlog.EVENTLOG_SEQUENTIAL_READ)
            limit = 500
            count = 0

            while count < limit:
                records = win32evtlog.ReadEventLog(h, flags, 0)
                if not records:
                    break
                for rec in records:
                    count += 1
                    if rec.EventID & 0xFFFF == 1001:
                        # BugCheck event — extract stop code from message
                        msg = win32evtlogutil.SafeFormatMessage(rec, "System")
                        code = self._extract_stop_code(msg)
                        ts   = rec.TimeGenerated.Format()
                        self._add_crash_record(ts, code, "Event Log")
                    if count >= limit:
                        break

            win32evtlog.CloseEventLog(h)
        except Exception as ex:
            self.log(f"  Event log access error: {ex}", "yellow")

    def _parse_minidumps(self):
        """Fallback: parse Minidump file headers for BugCheck codes."""
        mini_dir = r"C:\Windows\Minidump"
        if not os.path.isdir(mini_dir):
            self.log("  No Minidump directory found.", "muted")
            return

        try:
            dmp_files = sorted(
                glob.glob(os.path.join(mini_dir, "*.dmp")),
                key=os.path.getmtime,
                reverse=True
            )[:10]

            if not dmp_files:
                self.log("  No .dmp files in Minidump folder.", "muted")
                return

            for path in dmp_files:
                code = self._read_minidump_code(path)
                mtime = datetime.fromtimestamp(
                    os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
                self._add_crash_record(mtime, code, os.path.basename(path))

        except PermissionError:
            self.log(
                "  PermissionError: Run as Administrator to read Minidumps.",
                "yellow"
            )

    def _read_minidump_code(self, path: str) -> str:
        """
        Read BugCheck stop code from a Minidump file.
        MINIDUMP_HEADER is at offset 0; BugCheck stream contains the stop code.
        We do a best-effort parse of the fixed-size header.
        """
        try:
            with open(path, "rb") as f:
                data = f.read(0x1000)   # read first 4 KB

            # Minidump signature: "MDMP"
            if data[:4] != b"MDMP":
                return "UNKNOWN"

            # Number of streams at offset 0x10, stream directory at 0x1C
            num_streams  = struct.unpack_from("<I", data, 0x10)[0]
            rva_dir      = struct.unpack_from("<I", data, 0x1C)[0]

            STREAM_TYPE_EXCEPTION = 6  # ExceptionStream contains stop code

            for i in range(min(num_streams, 32)):
                entry_off = rva_dir + i * 12
                if entry_off + 12 > len(data):
                    break
                stype  = struct.unpack_from("<I", data, entry_off)[0]
                # ssize  = struct.unpack_from("<I", data, entry_off + 4)[0]
                s_rva  = struct.unpack_from("<I", data, entry_off + 8)[0]

                if stype == STREAM_TYPE_EXCEPTION:
                    # ExceptionRecord.ExceptionCode at stream_rva + 0 (first DWORD)
                    if s_rva + 4 <= len(data):
                        code_val = struct.unpack_from("<I", data, s_rva)[0]
                        return f"0x{code_val:08X}"
            return "UNKNOWN"
        except Exception:
            return "UNKNOWN"

    @staticmethod
    def _extract_stop_code(message: str) -> str:
        """Extract hex stop code like 0x0000009F from event log message."""
        import re
        m = re.search(r"0x[0-9A-Fa-f]{8}", message)
        return m.group(0).upper() if m else "UNKNOWN"

    def _add_crash_record(self, timestamp: str, code: str, source: str):
        entry = BSOD_DB.get(code.upper(), BSOD_DB["UNKNOWN"])
        category = entry["category"]
        self.scan_results.append({
            "time":     timestamp,
            "code":     code,
            "category": category,
            "file":     source,
        })
        self.log(
            f"  🔴  {timestamp}  |  {code}  |  {category}",
            "red"
        )

        def _insert():
            self.crash_tree.insert(
                "", "end",
                values=(timestamp, code, category, source)
            )
        self.root.after(0, _insert)

    def _smart_check(self):
        """Check disk health via wmic."""
        try:
            result = subprocess.run(
                ["wmic", "diskdrive", "get",
                 "Status,Model,Size", "/format:csv"],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            lines = [l.strip() for l in result.stdout.splitlines()
                     if l.strip() and l.strip() != "Node,Model,Size,Status"]
            for line in lines:
                parts = line.split(",")
                if len(parts) >= 4:
                    status = parts[-1].strip()
                    model  = parts[1].strip() if len(parts) > 2 else "Unknown"
                    size_b = int(parts[2].strip()) if parts[2].strip().isdigit() else 0
                    size_gb = size_b // (1024 ** 3)
                    col = "green" if status.lower() == "ok" else "red"
                    self.log(
                        f"  Disk: {model}  —  {size_gb} GB  —  Status: {status}",
                        col
                    )
        except Exception as e:
            self.log(f"  S.M.A.R.T. query failed: {e}", "yellow")

    def _process_audit(self):
        if not PSUTIL_OK:
            return
        suspicious_names = {
            "cryptominer", "xmrig", "minerd",
            "nssm", "mimikatz", "rat.exe"
        }
        found_suspicious = False
        for proc in psutil.process_iter(["name", "pid"]):
            if proc.info["name"].lower() in suspicious_names:
                self.log(
                    f"  ⚠  Suspicious process: {proc.info['name']} (PID {proc.info['pid']})",
                    "red"
                )
                found_suspicious = True
        if not found_suspicious:
            self.log("  No suspicious processes detected.", "green")

    # ─────────────────────────────────────────────────────────────────────
    # CRASH DETAIL MODAL
    # ─────────────────────────────────────────────────────────────────────

    def _on_crash_detail(self, event):
        sel = self.crash_tree.selection()
        if not sel:
            return
        row = self.crash_tree.item(sel[0], "values")
        timestamp, code, category, source = row
        entry = BSOD_DB.get(code.upper(), BSOD_DB["UNKNOWN"])
        self._show_detail_modal(timestamp, code, entry)

    def _show_detail_modal(self, ts: str, code: str, entry: dict):
        modal = tk.Toplevel(self.root)
        modal.title(f"Crash Analysis — {code}")
        modal.configure(bg=C["bg"])
        modal.resizable(False, False)
        modal.grab_set()

        def _row(parent, label, value, val_color=C["text"]):
            f = tk.Frame(parent, bg=C["bg"])
            f.pack(fill="x", padx=20, pady=4)
            tk.Label(f, text=label, width=18, anchor="w",
                     font=("Segoe UI", 10, "bold"),
                     bg=C["bg"], fg=C["muted"]).pack(side="left")
            tk.Label(f, text=value,
                     font=("Segoe UI", 10),
                     bg=C["bg"], fg=val_color,
                     wraplength=400, justify="left").pack(side="left", fill="x", expand=True)

        # Header
        tk.Label(modal,
                 text=f"🔴  {entry['name']}",
                 font=("Segoe UI", 14, "bold"),
                 bg=C["bg"], fg=C["red"]).pack(pady=(20, 4))

        sep = tk.Frame(modal, bg=C["border"], height=1)
        sep.pack(fill="x", padx=20, pady=8)

        _row(modal, "Stop Code:",   code,              C["yellow"])
        _row(modal, "Category:",    entry["category"], C["blue"])
        _row(modal, "Occurred:",    ts)

        sep2 = tk.Frame(modal, bg=C["border"], height=1)
        sep2.pack(fill="x", padx=20, pady=8)

        tk.Label(modal, text="What happened:",
                 font=("Segoe UI", 10, "bold"),
                 bg=C["bg"], fg=C["muted"]).pack(anchor="w", padx=20)

        tk.Label(modal, text=entry["plain"],
                 font=("Segoe UI", 10),
                 bg=C["bg"], fg=C["text"],
                 wraplength=440, justify="left").pack(anchor="w", padx=20, pady=(4, 12))

        tk.Label(modal, text="Recommended fix:",
                 font=("Segoe UI", 10, "bold"),
                 bg=C["bg"], fg=C["muted"]).pack(anchor="w", padx=20)

        tk.Label(modal, text=entry["fix"],
                 font=("Segoe UI", 10),
                 bg=C["bg"], fg=C["green"],
                 wraplength=440, justify="left").pack(anchor="w", padx=20, pady=(4, 20))

        self._styled_btn(modal, "  Close  ", modal.destroy, C["blue"]).pack(pady=(0, 16))

    # ─────────────────────────────────────────────────────────────────────
    # CLEANUP
    # ─────────────────────────────────────────────────────────────────────

    def _run_cleanup(self):
        threading.Thread(target=self._cleanup, daemon=True).start()

    def _cleanup(self):
        self.root.after(0, self.clean_progress.start)
        self.log("━━━  SYSTEM CLEANUP STARTED  ━━━", "yellow")
        total_freed = 0

        # ── Temp folders ──────────────────────────────────────────────────
        if self.clean_opts["temp"].get():
            targets = [
                os.environ.get("TEMP", ""),
                os.environ.get("TMP", ""),
                r"C:\Windows\Temp",
            ]
            for folder in targets:
                if folder and os.path.isdir(folder):
                    freed = self._clean_folder(folder)
                    total_freed += freed
                    self.log(
                        f"  Temp [{folder}]: {freed / 1024**2:.2f} MB freed",
                        "green"
                    )

        # ── Prefetch ──────────────────────────────────────────────────────
        if self.clean_opts["prefetch"].get():
            prefetch = r"C:\Windows\Prefetch"
            if os.path.isdir(prefetch):
                freed = self._clean_folder(prefetch, ext_filter=".pf")
                total_freed += freed
                self.log(f"  Prefetch: {freed / 1024**2:.2f} MB freed", "green")
            else:
                self.log("  Prefetch folder not found or no access.", "muted")

        # ── Windows Update cache ───────────────────────────────────────────
        if self.clean_opts["updates"].get():
            wu_cache = r"C:\Windows\SoftwareDistribution\Download"
            if os.path.isdir(wu_cache):
                freed = self._clean_folder(wu_cache)
                total_freed += freed
                self.log(
                    f"  WU Cache: {freed / 1024**2:.2f} MB freed", "green"
                )
            else:
                self.log("  Windows Update cache: folder not accessible.", "muted")

        # ── Browser caches ────────────────────────────────────────────────
        if self.clean_opts["browser"].get():
            local = os.path.join(os.environ.get("LOCALAPPDATA", ""), )
            browser_paths = {
                "Chrome": os.path.join(
                    os.environ.get("LOCALAPPDATA", ""),
                    "Google", "Chrome", "User Data", "Default", "Cache"
                ),
                "Edge": os.path.join(
                    os.environ.get("LOCALAPPDATA", ""),
                    "Microsoft", "Edge", "User Data", "Default", "Cache"
                ),
                "Firefox": self._find_firefox_cache(),
            }
            for browser, path in browser_paths.items():
                if path and os.path.isdir(path):
                    freed = self._clean_folder(path)
                    total_freed += freed
                    self.log(
                        f"  {browser} Cache: {freed / 1024**2:.2f} MB freed",
                        "green"
                    )

        self.log(
            f"\n  TOTAL FREED: {total_freed / 1024**2:.2f} MB",
            "yellow"
        )
        self.log("━━━  CLEANUP COMPLETE  ━━━", "yellow")
        self.root.after(0, self.clean_progress.stop)

    @staticmethod
    def _clean_folder(path: str, ext_filter: str = "") -> int:
        freed = 0
        for root_dir, _, files in os.walk(path):
            for fname in files:
                if ext_filter and not fname.endswith(ext_filter):
                    continue
                fpath = os.path.join(root_dir, fname)
                try:
                    freed += os.path.getsize(fpath)
                    os.remove(fpath)
                except (PermissionError, FileNotFoundError, OSError):
                    pass
        return freed

    @staticmethod
    def _find_firefox_cache() -> str:
        base = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Mozilla", "Firefox", "Profiles"
        )
        if not os.path.isdir(base):
            return ""
        for profile in os.listdir(base):
            candidate = os.path.join(base, profile, "cache2")
            if os.path.isdir(candidate):
                return candidate
        return ""

    # ─────────────────────────────────────────────────────────────────────
    # NETWORK DIAGNOSTICS
    # ─────────────────────────────────────────────────────────────────────

    def _run_network_diag(self):
        threading.Thread(target=self._network_diag, daemon=True).start()

    def _network_diag(self):
        self.log("━━━  NETWORK DIAGNOSTICS  ━━━", "blue")

        # DNS flush
        try:
            subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.log("  DNS cache flushed.", "green")
            self._set_net_label("dns", "Flushed ✓", C["green"])
        except Exception as e:
            self.log(f"  DNS flush failed: {e}", "yellow")
            self._set_net_label("dns", f"Error: {e}", C["yellow"])

        # Ping
        targets = [("8.8.8.8", "Google DNS"), ("1.1.1.1", "Cloudflare DNS")]
        connected = False
        for ip, name in targets:
            try:
                r = subprocess.run(
                    ["ping", "-n", "4", ip],
                    capture_output=True, text=True, timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if "TTL=" in r.stdout:
                    # Extract average ping
                    import re
                    m = re.search(r"Average = (\d+)ms", r.stdout)
                    avg = m.group(1) + " ms" if m else "OK"
                    self.log(f"  {name} ({ip}): reachable — avg {avg}", "green")
                    self._set_net_label("ping",   avg, C["green"])
                    self._set_net_label("status", "Connected ✓", C["green"])
                    connected = True
                    break
                else:
                    self.log(f"  {name} ({ip}): unreachable", "red")
            except Exception as ex:
                self.log(f"  Ping error: {ex}", "red")

        if not connected:
            self._set_net_label("status", "No internet", C["red"])
            self._set_net_label("ping",   "—",           C["muted"])

        self.log("━━━  DIAGNOSTICS COMPLETE  ━━━", "blue")

    def _run_speed_test(self):
        if not SPEEDTEST_OK:
            messagebox.showwarning(
                "Missing Library",
                "speedtest-cli is not installed.\n\n"
                "Install it with:\n  pip install speedtest-cli"
            )
            return
        threading.Thread(target=self._speed_test, daemon=True).start()

    def _speed_test(self):
        self.log("━━━  SPEED TEST IN PROGRESS (may take 30s)  ━━━", "blue")
        self._set_net_label("download", "Testing …", C["yellow"])
        self._set_net_label("upload",   "Testing …", C["yellow"])
        self._set_net_label("ping",     "Testing …", C["yellow"])
        try:
            st = speedtest_lib.Speedtest(secure=True)
            st.get_best_server()

            dl = st.download() / 1_000_000
            ul = st.upload()   / 1_000_000
            ping_ms = st.results.ping

            self._set_net_label("download", f"{dl:.2f}  Mbps", C["green"])
            self._set_net_label("upload",   f"{ul:.2f}  Mbps", C["green"])
            self._set_net_label("ping",     f"{ping_ms:.0f} ms",
                                C["green"] if ping_ms < 80 else C["yellow"])

            self.log(f"  ↓ Download : {dl:.2f} Mbps", "green")
            self.log(f"  ↑ Upload   : {ul:.2f} Mbps", "green")
            self.log(f"  ◌ Ping     : {ping_ms:.0f} ms",
                     "green" if ping_ms < 80 else "yellow")
        except Exception as e:
            self.log(f"  Speed test error: {e}", "red")
            self._set_net_label("download", "Error", C["red"])
            self._set_net_label("upload",   "Error", C["red"])

        self.log("━━━  SPEED TEST COMPLETE  ━━━", "blue")

    def _set_net_label(self, key: str, text: str, color: str):
        def _do():
            if key in self.net_labels:
                self.net_labels[key].config(text=text, fg=color)
        self.root.after(0, _do)

    # ─────────────────────────────────────────────────────────────────────
    # REPORT EXPORT
    # ─────────────────────────────────────────────────────────────────────

    def _export_report(self):
        default_name = f"System_Report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        path = filedialog.asksaveasfilename(
            initialdir=self.report_dir,
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save System Report"
        )
        if not path:
            return

        try:
            console_text = self.console.get("1.0", "end")

            with open(path, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write("  PC ANALYST PRO  —  SYSTEM REPORT\n")
                f.write(f"  Generated: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")

                # System summary
                if PSUTIL_OK:
                    cpu  = psutil.cpu_count()
                    ram  = psutil.virtual_memory().total // (1024**3)
                    disk = psutil.disk_usage("/")
                    f.write("SYSTEM SUMMARY\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"CPU Cores  : {cpu}\n")
                    f.write(f"Total RAM  : {ram} GB\n")
                    f.write(f"Disk Total : {disk.total // (1024**3)} GB\n")
                    f.write(f"Disk Free  : {disk.free  // (1024**3)} GB\n\n")

                # Crash records
                if self.scan_results:
                    f.write("CRASH REPORT HISTORY\n")
                    f.write("-" * 40 + "\n")
                    for r in self.scan_results:
                        f.write(
                            f"  [{r['time']}]  {r['code']}  |  "
                            f"{r['category']}  |  {r['file']}\n"
                        )
                    f.write("\n")

                # Operation log
                f.write("OPERATION LOG\n")
                f.write("-" * 40 + "\n")
                f.write(console_text)

            messagebox.showinfo(
                "Report Saved",
                f"Report successfully saved to:\n\n{path}"
            )
            self.log(f"Report exported → {os.path.basename(path)}", "green")

        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    # ─────────────────────────────────────────────────────────────────────
    # SHUTDOWN
    # ─────────────────────────────────────────────────────────────────────

    def on_close(self):
        self.running = False
        self.root.destroy()


# ════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app  = PCAnalystPro(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()