import tkinter as tk
from tkinter import ttk, scrolledtext, font
import os
import glob
import threading
import subprocess
import sys
import time  # <--- EKSİK OLAN VE HATAYI ÇÖZEN SATIR
from PIL import Image, ImageTk, ImageDraw, ImageFont

class ScriptRunnerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Soru Olusturma Otomasyonu")
        self.root.geometry("1100x700")

        # Stil ayarları
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')
        self.style.configure("TButton", padding=6, relief="flat", font=('Helvetica', 10, 'bold'))
        self.style.configure("RunAll.TButton", foreground="white", background="#2a75bb")
        self.style.configure("TFrame", background="#2e2e2e")
        self.style.configure("TLabel", background="#2e2e2e", foreground="white", font=('Helvetica', 12, 'bold'))
        self.style.configure("Vertical.TScrollbar", background='#555', troughcolor='#333', bordercolor='#555', arrowcolor='white')

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame, width=250)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        self.run_all_button = ttk.Button(left_frame, text="Tümünü Sırayla 1 Kez Çalıştır", style="RunAll.TButton", command=self.start_run_all_scripts)
        self.run_all_button.pack(fill=tk.X, pady=(5, 10))
        ttk.Separator(left_frame, orient='horizontal').pack(fill='x', pady=5)
        
        ttk.Label(left_frame, text="Tek Tek Çalıştır").pack(pady=(0, 10), anchor='w')
        
        scroll_container = ttk.Frame(left_frame)
        scroll_container.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(scroll_container, borderwidth=0, background="#2e2e2e", highlightthickness=0)
        self.scripts_frame = ttk.Frame(self.canvas, padding=5)
        self.scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=self.canvas.yview, style="Vertical.TScrollbar")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scripts_frame, anchor="nw")
        self.scripts_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind('<Enter>', self._bind_mouse)
        self.canvas.bind('<Leave>', self._unbind_mouse)
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        image_frame = ttk.Frame(right_frame, height=300)
        image_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        image_frame.pack_propagate(False)
        ttk.Label(image_frame, text="Önizleme").pack(pady=(0, 10), anchor='w')
        self.image_label = ttk.Label(image_frame, background="#1e1e1e", anchor=tk.CENTER)
        self.image_label.pack(fill=tk.BOTH, expand=True)

        console_frame = ttk.Frame(right_frame)
        console_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        ttk.Label(console_frame, text="Çıktı Konsolu").pack(pady=(0, 10), anchor='w')
        self.output_text = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, bg="#1e1e1e", fg="white", font=("Consolas", 10), insertbackground="white", borderwidth=0, relief=tk.FLAT)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        self.buttons = []
        self.placeholder_image = self.create_placeholder_image((600, 280))
        self.on_button_leave()
        self.populate_scripts()
        
    def _execute_single_script(self, script_path):
        """Tek bir betiği çalıştıran ve çıktısını yazan çekirdek fonksiyon."""
        script_name = os.path.basename(script_path)
        script_dir = os.path.dirname(script_path)
        
        self.root.after(0, lambda: self.on_button_hover(None, script_path))
        self.safe_insert_text(f"\n▶ Başlatılıyor: {script_name}\n" + "-"*50 + "\n")
        
        command = [sys.executable, script_path]
        try:
            my_env = os.environ.copy()
            my_env["PYTHONIOENCODING"] = "utf-8"
            
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace', cwd=script_dir,
                env=my_env, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            for line in process.stdout:
                self.safe_insert_text(line)
            
            process.wait()

            if process.returncode == 0:
                self.safe_insert_text("-" * 50 + f"\n✔ Başarıyla Tamamlandı: {script_name} (Çıkış Kodu: 0)\n")
            else:
                self.safe_insert_text("-" * 50 + f"\n❌ HATA ile Tamamlandı: {script_name} (Çıkış Kodu: {process.returncode})\n")
        except Exception as e:
            self.safe_insert_text(f"\n--- HATA: {script_name} çalıştırılamadı! ---\n{str(e)}\n")

    def safe_insert_text(self, text):
        """Thread'ler arası güvenli bir şekilde metin kutusuna yazı ekler."""
        if self.root.winfo_exists():
            self.output_text.insert(tk.END, text)
            self.output_text.see(tk.END)

    def run_all_scripts_thread(self):
        try:
            script_dir = os.path.join(os.path.dirname(__file__), 'scripts'); script_files = sorted(glob.glob(os.path.join(script_dir, '*.py')))
            total_scripts = len(script_files)
            for idx, script_path in enumerate(script_files):
                if not self.root.winfo_exists(): break
                self.safe_insert_text(f"\n{'='*80}\nGENEL İLERLEME: {idx+1}/{total_scripts}\n{'='*80}")
                self._execute_single_script(script_path)
                time.sleep(1)
            if self.root.winfo_exists(): self.safe_insert_text(f"\n{'*'*80}\nTÜM İŞLEMLER BAŞARIYLA TAMAMLANDI!\n{'*'*80}\n")
        finally:
            if self.root.winfo_exists(): self.set_buttons_state(tk.NORMAL); self.root.after(0, self.on_button_leave)
            
    def start_run_all_scripts(self):
        self.set_buttons_state(tk.DISABLED); self.output_text.delete('1.0', tk.END)
        thread = threading.Thread(target=self.run_all_scripts_thread); thread.daemon = True; thread.start()

    def run_script_thread(self, script_path):
        try: self._execute_single_script(script_path)
        finally:
            if self.root.winfo_exists(): self.set_buttons_state(tk.NORMAL); self.root.after(0, self.on_button_leave)

    def start_script_run(self, script_path):
        self.on_button_hover(None, script_path); self.set_buttons_state(tk.DISABLED)
        self.output_text.delete('1.0', tk.END)
        thread = threading.Thread(target=self.run_script_thread, args=(script_path,)); thread.daemon = True; thread.start()
        
    def create_placeholder_image(self, size):
        img = Image.new('RGB', size, color = '#3c3c3c'); d = ImageDraw.Draw(img)
        try: fnt = ImageFont.truetype("arial.ttf", 24)
        except IOError: fnt = ImageFont.load_default()
        d.text((size[0]/2, size[1]/2), "Önizleme Yok", font=fnt, fill=(200, 200, 200), anchor='mm')
        return ImageTk.PhotoImage(img)

    def load_and_resize_image(self, path, size):
        try:
            img = Image.open(path); img.thumbnail(size, Image.Resampling.LANCZOS); return ImageTk.PhotoImage(img)
        except Exception: return self.placeholder_image

    def on_button_hover(self, event, script_path):
        script_name = os.path.basename(script_path); image_name = script_name.replace('.py', '.png')
        image_path = os.path.join(os.path.dirname(__file__), 'images', image_name)
        if os.path.exists(image_path): photo = self.load_and_resize_image(image_path, (600, 280))
        else: photo = self.placeholder_image
        self.image_label.config(image=photo); self.image_label.image = photo

    def on_button_leave(self, event=None):
        self.image_label.config(image=self.placeholder_image); self.image_label.image = self.placeholder_image

    def populate_scripts(self):
        for widget in self.scripts_frame.winfo_children(): widget.destroy()
        self.buttons = []
        script_dir = os.path.join(os.path.dirname(__file__), 'scripts')
        if not os.path.exists(script_dir): self.output_text.insert(tk.END, f"HATA: 'scripts' klasörü bulunamadı!\n"); return
        script_files = glob.glob(os.path.join(script_dir, '*.py'))
        for script_path in sorted(script_files):
            script_name = os.path.basename(script_path)
            button_text = script_name.replace('.py', '').replace('Grid-', 'Grid: ').replace('TopDown', 'Tepeden ').replace('Perspective', ' Perspektif')
            button = ttk.Button(self.scripts_frame, text=button_text, width=30, command=lambda p=script_path: self.start_script_run(p))
            button.pack(fill=tk.X, pady=2, anchor='w')
            button.bind("<Enter>", lambda e, p=script_path: self.on_button_hover(e, p))
            button.bind("<Leave>", self.on_button_leave)
            self.buttons.append(button)
        self.root.after(100, self.on_frame_configure)

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _bind_mouse(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mouse(self, event=None):
        self.canvas.unbind_all("<MouseWheel>")

    def set_buttons_state(self, state):
        self.run_all_button.config(state=state)
        for button in self.buttons:
            button.config(state=state)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptRunnerApp(root)
    root.mainloop()