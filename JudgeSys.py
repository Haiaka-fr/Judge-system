import subprocess
import re
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import sys
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil

COLORS = {
    "bg": "#F5F7F8",
    "card": "#FFFFFF",
    "primary": "#4A90E2",
    "accent": "#50C878",
    "text": "#333333",
    "border": "#DCDCDC"
}

class GraderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Code Grading System")
        self.root.geometry("900x980")
        self.root.configure(bg=COLORS["bg"])
        self.grading = False
        
        self.default_font = ("Segoe UI", 12)
        self.title_font = ("Segoe UI", 14, "bold")
        
        self._setup_styles()
        self._setup_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=self.default_font)
        style.configure("Card.TFrame", background=COLORS["card"], relief="flat")

    def _setup_ui(self):
        header = tk.Frame(self.root, bg=COLORS["primary"], height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="Code Grading System", bg=COLORS["primary"], 
                 fg="white", font=("Segoe UI", 16, "bold"), pady=15).pack()

        container = tk.Frame(self.root, bg=COLORS["bg"], padx=30, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        # Resource Path Settings
        self._create_section(container, "Resource Path Settings", [
            ("Test Data (.md):", "test_path", "Browse", lambda: self.browse_file(self.test_path, [("Markdown files", "*.md")])),
            ("Target Script (.py):", "script_path", "Browse", lambda: self.browse_file(self.script_path, [("Python files", "*.py")]))
        ])

        # Contest Parameters
        settings_frame = tk.LabelFrame(container, text="Contest Parameters", bg=COLORS["bg"], 
                                      font=self.title_font, padx=15, pady=15, fg=COLORS["primary"])
        settings_frame.pack(fill=tk.X, pady=10)

        # Time Limit
        tk.Label(settings_frame, text="Time Limit (sec):").grid(row=0, column=0, sticky="w", pady=5)
        self.time_limit_entry = tk.Entry(settings_frame, width=10, font=self.default_font)
        self.time_limit_entry.insert(0, "10.0")
        self.time_limit_entry.grid(row=0, column=1, padx=10, sticky="w")

        # Memory Limit
        tk.Label(settings_frame, text="Memory Limit (MB):").grid(row=0, column=2, sticky="w", pady=5, padx=(20, 0))
        self.memory_limit_entry = tk.Entry(settings_frame, width=10, font=self.default_font)
        self.memory_limit_entry.insert(0, "128")
        self.memory_limit_entry.grid(row=0, column=3, padx=10, sticky="w")

        # Control Buttons
        btn_frame = tk.Frame(container, bg=COLORS["bg"])
        btn_frame.pack(fill=tk.X, pady=15)

        self.run_btn = tk.Button(btn_frame, text="Start Grading", bg=COLORS["primary"], fg="white",
                                 font=self.title_font, relief="flat", padx=30, pady=10, 
                                 cursor="hand2", command=self.start_grading_thread)
        self.run_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = tk.Button(btn_frame, text="Clear Logs", bg="#95a5a6", fg="white",
                                   font=self.title_font, relief="flat", padx=20, pady=10, 
                                   cursor="hand2", command=self.clear_log_area)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # Output Log Area
        report_frame = tk.LabelFrame(container, text="Grading Output & Diagnostics", bg=COLORS["bg"], 
                                    font=self.title_font, padx=10, pady=10, fg=COLORS["primary"])
        report_frame.pack(fill=tk.BOTH, expand=True)

        self.log_area = tk.Text(report_frame, font=("Consolas", 12), bg="#2C3E50", fg="#ECF0F1", 
                               padx=15, pady=15, relief="flat", insertbackground="white")
        self.log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=self.log_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_area.config(yscrollcommand=scrollbar.set)

    def _create_section(self, parent, title, rows):
        frame = tk.LabelFrame(parent, text=title, bg=COLORS["bg"], font=self.title_font, 
                              padx=15, pady=15, fg=COLORS["primary"])
        frame.pack(fill=tk.X, pady=10)
        
        for i, (label_text, attr_name, btn_text, cmd) in enumerate(rows):
            tk.Label(frame, text=label_text).grid(row=i, column=0, sticky="w", pady=5)
            entry = tk.Entry(frame, width=50, font=self.default_font, relief="solid", borderwidth=1)
            entry.grid(row=i, column=1, padx=10, pady=5)
            setattr(self, attr_name, entry)
            tk.Button(frame, text=btn_text, command=cmd, bg="#EEE", relief="groove").grid(row=i, column=2, padx=5)

    def browse_file(self, entry_widget, types):
        filename = filedialog.askopenfilename(filetypes=types)
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def start_grading_thread(self):
        script = self.script_path.get()
        test_file = self.test_path.get()
        
        try:
            time_limit = float(self.time_limit_entry.get())
            if time_limit <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Invalid time limit! Please enter a positive number.")
            return

        try:
            memory_limit = float(self.memory_limit_entry.get())
            if memory_limit <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Invalid memory limit! Please enter a positive number.")
            return

        if not os.path.exists(script) or not os.path.exists(test_file):
            messagebox.showerror("Error", "Invalid file paths!")
            return
        
        self.run_btn.config(state=tk.DISABLED, text="Grading...")
        self.clear_btn.config(state=tk.DISABLED)
        self.log_area.delete(1.0, tk.END)
        self.grading = True
        threading.Thread(target=self.run_grader, args=(script, test_file, time_limit, memory_limit), daemon=True).start()
    
    def clear_log_area(self):
        if not self.grading:
            self.log_area.delete(1.0, tk.END)

    def _eval_single_testcase(self, case_id, inp, exp, python_exe, runner_code, script_name, timeout_limit, memory_limit_mb, env):
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW

        status = ""
        actual = ""
        duration = 0.0
        peak_memory_mb = 0.0
        mle_flag = [False]

        try:
            process = subprocess.Popen(
                [python_exe, "-c", runner_code, script_name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                creationflags=creationflags
            )

            # 背景線程：即時監控進程記憶體使用量
            def monitor_memory():
                nonlocal peak_memory_mb
                try:
                    ps_proc = psutil.Process(process.pid)
                    while process.poll() is None:
                        # 包含衍生子進程的記憶體總和
                        mem_info = ps_proc.memory_info().rss
                        for child in ps_proc.children(recursive=True):
                            mem_info += child.memory_info().rss
                        
                        current_mb = mem_info / (1024 * 1024)
                        if current_mb > peak_memory_mb:
                            peak_memory_mb = current_mb
                        
                        if current_mb > memory_limit_mb:
                            mle_flag[0] = True
                            process.kill()
                            break
                        time.sleep(0.01)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
            monitor_thread.start()

            try:
                stdout, stderr = process.communicate(input=inp, timeout=timeout_limit)
                
                if mle_flag[0]:
                    status = "❌ MLE"
                    is_passed = False
                else:
                    if "__TIME__:" in stdout:
                        raw_output, time_part = stdout.rsplit("__TIME__:", 1)
                        actual = raw_output.rstrip("\r\n")
                        duration = float(time_part.strip())
                    else:
                        actual = stdout.strip()
                        duration = 0.0

                    if actual == exp:
                        status = "✅ PASS"
                        is_passed = True
                    else:
                        status = "❌ FAIL"
                        is_passed = False

            except subprocess.TimeoutExpired:
                process.kill()
                status = "❌ TLE" if not mle_flag[0] else "❌ MLE"
                duration = timeout_limit
                is_passed = False

        except Exception as e:
            status = "❌ ERROR"
            is_passed = False

        return case_id, status, duration, peak_memory_mb, is_passed

    def run_grader(self, script_name, test_file, timeout_limit, memory_limit_mb):
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            segments = re.findall(r'// input\n(.*?)\n// output\n(.*?)(?=\n// input|\Z)', content, re.DOTALL)
            if not segments:
                self.log("Warning: No test cases found.")
                self._finish_grading()
                return
        except Exception as e:
            self.log(f"Error reading test file: {str(e)}")
            self._finish_grading()
            return

        total_cases = len(segments)
        passed_count = 0
        self.log(f"Target Script: {os.path.basename(script_name)}")
        self.log(f"Time Limit: {timeout_limit}s | Memory Limit: {memory_limit_mb} MB")
        self.log("-" * 65)

        if getattr(sys, 'frozen', False):
            python_exe = "python"
        else:
            python_exe = sys.executable

        env = os.environ.copy()
        if "PYTHONHOME" in env: del env["PYTHONHOME"]
        if "PYTHONPATH" in env: del env["PYTHONPATH"]
        if "_MEI_PATH" in env: del env["_MEI_PATH"]

        runner_code = (
            "import time, sys; "
            "t0 = time.perf_counter(); "
            "exec(open(sys.argv[1], encoding='utf-8').read()); "
            "t1 = time.perf_counter(); "
            "print(f'\\n__TIME__:{t1 - t0:.6f}')"
        )

        max_workers = min(8, os.cpu_count() or 4)
        
        futures = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i, (inp, exp) in enumerate(segments):
                inp, exp = inp.strip(), exp.strip()
                future = executor.submit(
                    self._eval_single_testcase,
                    i + 1, inp, exp, python_exe, runner_code, script_name, timeout_limit, memory_limit_mb, env
                )
                futures.append(future)

            for future in as_completed(futures):
                case_id, status, duration, peak_mem, is_passed = future.result()
                if is_passed:
                    passed_count += 1
                self.log(f"#{case_id:<5} | {status:<8} | {duration:<8.4f}s | Peak Mem: {peak_mem:<6.2f} MB")

        self.log("-" * 65)
        self.log(f"Total Passed: {passed_count}/{total_cases}")

        self._finish_grading()

    def _finish_grading(self):
        self.run_btn.config(state=tk.NORMAL, text="Start Grading")
        self.clear_btn.config(state=tk.NORMAL)
        self.grading = False

if __name__ == "__main__":
    multiprocessing.freeze_support()

    root = tk.Tk()
    app = GraderApp(root)
    root.mainloop()
