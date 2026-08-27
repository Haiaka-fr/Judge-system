import subprocess
import re
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import sys

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
        self.root.title("程式評分系統")
        self.root.geometry("9000x950")
        self.root.configure(bg=COLORS["bg"])
        self.grading = False
        
        self.default_font = ("Microsoft JhengHei", 12)
        self.title_font = ("Microsoft JhengHei", 14, "bold")
        
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
        tk.Label(header, text="程式評分系統", bg=COLORS["primary"], 
                 fg="white", font=("Microsoft JhengHei", 16, "bold"), pady=15).pack()

        container = tk.Frame(self.root, bg=COLORS["bg"], padx=30, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        # 檔案路徑設定
        self._create_section(container, "資源路徑設定", [
            ("測試資料 (.md):", "test_path", "瀏覽", lambda: self.browse_file(self.test_path, [("Markdown files", "*.md")])),
            ("目標程式 (.py):", "script_path", "瀏覽", lambda: self.browse_file(self.script_path, [("Python files", "*.py")]))
        ])

        # 競賽參數設定
        settings_frame = tk.LabelFrame(container, text="競賽參數", bg=COLORS["bg"], 
                                      font=self.title_font, padx=15, pady=15, fg=COLORS["primary"])
        settings_frame.pack(fill=tk.X, pady=10)

        tk.Label(settings_frame, text="執行限時 (秒):").grid(row=0, column=0, sticky="w", pady=5)
        self.time_limit_entry = tk.Entry(settings_frame, width=10, font=self.default_font)
        self.time_limit_entry.insert(0, "10.0")
        self.time_limit_entry.grid(row=0, column=1, padx=10, sticky="w")

        tk.Label(settings_frame, text="顯示標題:").grid(row=1, column=0, sticky="w", pady=5)
        self.Title = tk.Entry(settings_frame, width=40, font=self.default_font)
        self.Title.insert(0, "Title")
        self.Title.grid(row=1, column=1, padx=10, sticky="w")

        # 控制按鈕
        btn_frame = tk.Frame(container, bg=COLORS["bg"])
        btn_frame.pack(fill=tk.X, pady=15)

        self.run_btn = tk.Button(btn_frame, text="開始評分 (Start)", bg=COLORS["primary"], fg="white",
                                 font=self.title_font, relief="flat", padx=30, pady=10, 
                                 cursor="hand2", command=self.start_grading_thread)
        self.run_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = tk.Button(btn_frame, text="清空日誌", bg="#95a5a6", fg="white",
                                   font=self.title_font, relief="flat", padx=20, pady=10, 
                                   cursor="hand2", command=self.clear_log_area)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # 輸出日誌區
        report_frame = tk.LabelFrame(container, text="評分輸出診斷", bg=COLORS["bg"], 
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
            limit = float(self.time_limit_entry.get())
            if limit <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("錯誤", "無效的時間限制！請輸入正數。")
            return

        if not os.path.exists(script) or not os.path.exists(test_file):
            messagebox.showerror("錯誤", "檔案路徑不正確！")
            return
        
        self.run_btn.config(state=tk.DISABLED, text="評分中...")
        self.clear_btn.config(state=tk.DISABLED)
        self.log_area.delete(1.0, tk.END)
        self.grading = True
        threading.Thread(target=self.run_grader, args=(script, test_file, limit), daemon=True).start()
    
    def clear_log_area(self):
        if not self.grading:
            self.log_area.delete(1.0, tk.END)

    def run_grader(self, script_name, test_file, timeout_limit):
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            segments = re.findall(r'// input\n(.*?)\n// output\n(.*?)(?=\n// input|\Z)', content, re.DOTALL)
            if not segments:
                self.log("警告：找不到任何測試資料。")
                self._finish_grading()
                return
        except Exception as e:
            self.log(f"讀取測試檔錯誤: {str(e)}")
            self._finish_grading()
            return

        total_cases = len(segments)
        passed_count = 0
        self.log(f"測試對象: {os.path.basename(script_name)}")
        self.log(f"時間限制: {timeout_limit}s")
        self.log("-" * 60)

        for i, (inp, exp) in enumerate(segments):
            inp, exp = inp.strip(), exp.strip()
            status = ""
            actual = ""
            duration = 0.0

            try:
                process = subprocess.Popen([sys.executable, script_name], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                start_time = time.perf_counter()
                try:
                    stdout, stderr = process.communicate(input=inp, timeout=timeout_limit)
                    duration = time.perf_counter() - start_time
                    actual = stdout.strip()
                    
                    if actual == exp:
                        status = "✅ PASS"
                        passed_count += 1
                    else:
                        status = "❌ FAIL"
                except subprocess.TimeoutExpired:
                    process.kill()
                    status = "❌ TIMEOUT"
                    duration = timeout_limit
                    actual = "Execution Timed Out"
            except Exception as e:
                status = "❌ ERROR"
                actual = str(e)

            self.log(f"#{i+1:<7} | {status:<10} | {duration:<10.4f}s")

        self.log("-" * 60)
        self.log(f"總計通過: {passed_count}/{total_cases}")

        self._finish_grading()

    def _finish_grading(self):
        self.run_btn.config(state=tk.NORMAL, text="開始評分 (Start)")
        self.clear_btn.config(state=tk.NORMAL)
        self.grading = False

if __name__ == "__main__":
    root = tk.Tk()
    app = GraderApp(root)
    root.mainloop()