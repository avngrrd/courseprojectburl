import tkinter as tk
from tkinter import filedialog
import cv2
import time
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import collections
from ffpyplayer.player import MediaPlayer

class FPSMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fps monitor hype version")
        self.root.geometry("1000x650")

        self.video_source = None
        self.cap = None
        self.player = None
        self.is_running = False
        self.prev_time = 0
        
        self.fps_data = collections.deque(maxlen=50) 
        self.frame_indices = collections.deque(maxlen=50)
        self.frame_count = 0

        self._setup_ui()

    def _setup_ui(self):
        control_frame = tk.Frame(self.root, pady=10)
        control_frame.pack(fill=tk.X)

        self.btn_browse = tk.Button(control_frame, text="1. Вибрати файл", command=self.browse_file)
        self.btn_browse.pack(side=tk.LEFT, padx=10)

        self.path_label = tk.Label(control_frame, text="Файл не вибрано", fg="gray")
        self.path_label.pack(side=tk.LEFT, padx=10)

        self.btn_start = tk.Button(control_frame, text="2. Старт", command=self.start_video, state=tk.DISABLED, bg="#ddffdd")
        self.btn_start.pack(side=tk.LEFT, padx=10)

        self.btn_stop = tk.Button(control_frame, text="Стоп", command=self.stop_video, state=tk.DISABLED, bg="#ffdddd")
        self.btn_stop.pack(side=tk.LEFT, padx=10)

        main_content = tk.Frame(self.root)
        main_content.pack(fill=tk.BOTH, expand=True)

        self.video_label = tk.Label(main_content, bg="black")
        self.video_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.graph_frame = tk.Frame(main_content, width=400)
        self.graph_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        self.fig, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.ax.set_title("Динаміка FPS")
        self.ax.set_ylabel("FPS")
        self.line, = self.ax.plot([], [], 'r-')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=(("Video files", "*.mp4 *.avi *.mkv"), ("All files", "*.*")))
        if filename:
            self.video_source = filename
            self.path_label.config(text=f"...{filename[-30:]}")
            self.btn_start.config(state=tk.NORMAL)

    def start_video(self):
        if not self.video_source: return
        
        self.cap = cv2.VideoCapture(self.video_source)
        self.player = MediaPlayer(self.video_source)

        self.is_running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.btn_browse.config(state=tk.DISABLED)
        
        self.prev_time = time.time()
        self.frame_count = 0
        self.fps_data.clear()
        self.frame_indices.clear()
        
        self.update_frame()

    def stop_video(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        
        if self.player:
            self.player.close_player()
            self.player = None

        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_browse.config(state=tk.NORMAL)

    def update_frame(self):
        if not self.is_running or not self.cap.isOpened():
            return

        audio_frame, val = self.player.get_frame()

        if val == 'eof':
            self.stop_video()
            return

        ret, frame = self.cap.read()
        if ret:
            current_time = time.time()
            dt = current_time - self.prev_time
            self.prev_time = current_time
            fps = 1 / dt if dt > 0 else 0
            
            self.frame_count += 1
            self.fps_data.append(fps)
            self.frame_indices.append(self.frame_count)

            self.line.set_data(self.frame_indices, self.fps_data)
            self.ax.set_xlim(min(list(self.frame_indices)), max(list(self.frame_indices)) + 1)
            if max(self.fps_data) > self.ax.get_ylim()[1]:
                self.ax.set_ylim(0, max(self.fps_data) + 10)
            self.canvas.draw_idle()

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (640, 360)) 
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            if val != 'eof' and val is not None:
                delay = int(val * 1000)
                if delay < 1: delay = 1
            else:
                delay = 30 
            
            self.root.after(delay, self.update_frame)
        else:
            self.stop_video()

if __name__ == "__main__":
    root = tk.Tk()
    app = FPSMonitorApp(root)
    root.mainloop()