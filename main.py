import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import threading
import time
import numpy as np
from datetime import datetime

from frequencies import STATIONS, ALL_FREQS
from wefax_decoder import decode_wefax_wav


class FaxSpotterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fax Spotter Network")
        self.geometry("980x720")
        self.minsize(800, 600)

        self.current_image = None
        self.photo = None
        self.listening = False
        self.scanning = False
        self.scan_thread = None
        self.stop_event = threading.Event()
        self.spinner_chars = ["|", "/", "-", "\\"]
        self.spinner_index = 0
        self.spinner_job = None
        self.current_freq = None
        self.current_station = None
        self.allow_audio = False

        self._build_ui()
        self._show_static()

    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(top, text="KiwiSDR host:").pack(side=tk.LEFT)
        self.host_var = tk.StringVar(value="pb8w.proxy.kiwisdr.com")
        ttk.Entry(top, textvariable=self.host_var, width=28).pack(side=tk.LEFT, padx=4)

        ttk.Label(top, text="Port:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value="8073")
        ttk.Entry(top, textvariable=self.port_var, width=6).pack(side=tk.LEFT, padx=4)

        ttk.Label(top, text="  Current:").pack(side=tk.LEFT)
        self.freq_label = ttk.Label(top, text="None", foreground="#0066cc")
        self.freq_label.pack(side=tk.LEFT, padx=4)

        btn_frame = ttk.Frame(self, padding=6)
        btn_frame.pack(fill=tk.X)

        self.btn_start = ttk.Button(btn_frame, text="Start Listening", command=self.start_listening)
        self.btn_start.pack(side=tk.LEFT, padx=3)

        self.btn_stop = ttk.Button(btn_frame, text="Stop Listening", command=self.stop_listening, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=3)

        self.btn_scan = ttk.Button(btn_frame, text="Scan", command=self.start_scan)
        self.btn_scan.pack(side=tk.LEFT, padx=3)

        ttk.Button(btn_frame, text="Clear Output", command=self._show_static).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Download Current Output", command=self.download_image).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Test Audio File", command=self.test_audio_file).pack(side=tk.LEFT, padx=3)

        self.btn_audio = ttk.Button(btn_frame, text="Allow Audio: OFF", command=self.toggle_audio)
        self.btn_audio.pack(side=tk.LEFT, padx=8)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X, side=tk.BOTTOM)

        main = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        left = ttk.Frame(main)
        main.add(left, weight=3)

        self.canvas = tk.Canvas(left, bg="#1a1a1a", highlightthickness=1, highlightbackground="#555")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        right = ttk.Frame(main)
        main.add(right, weight=1)

        ttk.Label(right, text="Known WeFAX Stations  (double-click to tune)", font=("", 10, "bold")).pack(anchor=tk.W)
        self.tree = ttk.Treeview(right, columns=("freq",), show="tree headings", height=25)
        self.tree.heading("#0", text="Station / Frequency")
        self.tree.heading("freq", text="kHz")
        self.tree.column("#0", width=260)
        self.tree.column("freq", width=70)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        for station, freqs in STATIONS.items():
            parent = self.tree.insert("", "end", text=station, open=False, values=("",))
            for f, mode in freqs:
                self.tree.insert(parent, "end", text=f"{f} {mode}", values=(f,))

    def toggle_audio(self):
        self.allow_audio = not self.allow_audio
        if self.allow_audio:
            self.btn_audio.config(text="Allow Audio: ON")
            self.status_var.set("Audio playback enabled")
        else:
            self.btn_audio.config(text="Allow Audio: OFF")
            self.status_var.set("Audio playback disabled")

    def _generate_static(self, size=512):
        noise = np.random.randint(0, 256, (size, size), dtype=np.uint8)
        return Image.fromarray(noise, mode="L")

    def _show_static(self):
        img = self._generate_static()
        self._show_image(img)
        self.status_var.set("Static (no signal)")

    def _on_canvas_resize(self, event=None):
        if self.current_image:
            self._show_image(self.current_image)

    def _show_image(self, pil_img: Image.Image):
        self.current_image = pil_img
        w = self.canvas.winfo_width() or 400
        h = self.canvas.winfo_height() or 400
        side = min(w, h) - 40
        side = max(side, 200)
        display = pil_img.resize((side, side), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(display)
        self.canvas.delete("all")
        self.canvas.create_image(w // 2, h // 2, image=self.photo, anchor=tk.CENTER)

    def download_image(self):
        if not self.current_image:
            messagebox.showinfo("Download", "No image to save.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG image", "*.png"), ("All files", "*.*")],
            initialfile=f"wefax_{datetime.now():%Y%m%d_%H%M%S}.png"
        )
        if path:
            self.current_image.save(path)
            self.status_var.set(f"Saved → {path}")

    def test_audio_file(self):
        path = filedialog.askopenfilename(
            title="Select WeFAX audio file",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )
        if not path:
            url = simpledialog.askstring("Test Audio", "Or paste a direct WAV URL:")
            if not url:
                return
            import requests
            import tempfile
            try:
                r = requests.get(url, timeout=30)
                r.raise_for_status()
                tmp = tempfile.mktemp(suffix=".wav")
                with open(tmp, "wb") as f:
                    f.write(r.content)
                path = tmp
            except Exception as e:
                messagebox.showerror("Download failed", str(e))
                return

        self.status_var.set("Decoding audio file…")
        self.update_idletasks()

        def worker():
            try:
                img = decode_wefax_wav(path)
                self.after(0, lambda: self._show_image(img))
                self.after(0, lambda: self.status_var.set("Decode complete"))
            except Exception as e:
                self.after(0, lambda: self._show_static())
                self.after(0, lambda: messagebox.showerror("Decode error", str(e)))
                self.after(0, lambda: self.status_var.set("Decode failed - showing static"))

        threading.Thread(target=worker, daemon=True).start()

    def on_tree_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, "values")
        if values and values[0]:
            try:
                freq = float(values[0])
                parent = self.tree.parent(item)
                station = self.tree.item(parent, "text") if parent else "Unknown"
                self.current_freq = freq
                self.current_station = station
                self.freq_label.config(text=f"{freq} kHz  ({station})")
                self.status_var.set(f"Tuned to {freq} kHz ({station})")
                if self.listening:
                    self.status_var.set(f"Listening on {freq} kHz ({station})")
            except ValueError:
                pass

    def start_spinner(self, base_text):
        self.spinner_index = 0
        def animate():
            if not self.scanning and not self.listening:
                return
            char = self.spinner_chars[self.spinner_index % 4]
            self.status_var.set(f"{base_text} {char}")
            self.spinner_index += 1
            self.spinner_job = self.after(150, animate)
        animate()

    def stop_spinner(self):
        if self.spinner_job:
            self.after_cancel(self.spinner_job)
            self.spinner_job = None

    def start_listening(self):
        host = self.host_var.get().strip()
        if not host:
            messagebox.showwarning("Missing host", "Enter a KiwiSDR hostname first.")
            return
        if self.current_freq is None:
            messagebox.showinfo("No frequency", "Double-click a frequency in the list first.")
            return
        self.listening = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.btn_scan.config(state=tk.DISABLED)
        audio_state = " + audio" if self.allow_audio else ""
        base = f"Listening {self.current_freq} kHz on {host}{audio_state}"
        self.start_spinner(base)
        self._show_static()

    def stop_listening(self):
        self.listening = False
        self.scanning = False
        self.stop_event.set()
        self.stop_spinner()
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_scan.config(state=tk.NORMAL)
        self.status_var.set("Stopped")
        self._show_static()

    def start_scan(self):
        if self.scanning:
            return
        host = self.host_var.get().strip()
        if not host:
            messagebox.showwarning("Missing host", "Enter a KiwiSDR hostname first.")
            return
        self.scanning = True
        self.stop_event.clear()
        self.btn_start.config(state=tk.DISABLED)
        self.btn_scan.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.start_spinner("Scanning")
        self.scan_thread = threading.Thread(target=self._scan_worker, daemon=True)
        self.scan_thread.start()

    def _scan_worker(self):
        for entry in ALL_FREQS:
            if self.stop_event.is_set() or not self.scanning:
                break
            freq = entry["freq"]
            station = entry["station"]
            self.current_freq = freq
            self.current_station = station
            self.after(0, lambda f=freq, s=station: self.freq_label.config(text=f"{f} kHz  ({s})"))
            self.after(0, lambda: self._show_static())
            time.sleep(2.5)
        self.after(0, self._finish_scan)

    def _finish_scan(self):
        self.scanning = False
        self.stop_spinner()
        self.btn_start.config(state=tk.NORMAL)
        self.btn_scan.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.status_var.set("Scan finished")
        self._show_static()


if __name__ == "__main__":
    app = FaxSpotterApp()
    app.mainloop()
