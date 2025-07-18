import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
from PIL import Image, ImageTk, ImageEnhance
import cv2
import os
import threading
import numpy as np
import time

class ImageVideoEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Image and Video Processing App")
        self.root.geometry("1000x700") 
        self.root.resizable(True, True)

        self.image = None
        self.original_image = None
        self.photo = None
        self.video_path = None
        self.video_fps = 30
        self.processed_frames = []
        self.undo_stack = []
        self.video_undo_stack = []
        self.video_paused = False
        self.stop_playback = False

        self.gradient_canvas = tk.Canvas(self.root, width=1000, height=700, highlightthickness=0)
        self.gradient_canvas.pack(fill="both", expand=True)
        self.draw_gradient()

        self.gradient_frame = tk.Frame(self.gradient_canvas)
        self.gradient_frame.place(relwidth=1, relheight=1)

        self.top_frame = tk.Frame(self.gradient_frame)
        self.top_frame.pack(side="top", fill="x", pady=10)

        self.content_frame = tk.Frame(self.gradient_frame)
        self.content_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.image_frame = tk.Frame(self.content_frame, bg="#ffffff", bd=2, relief="groove")
        self.image_frame.pack(side="left", expand=True, fill="both", padx=(0, 10))

        self.button_frame = tk.Frame(self.content_frame)
        self.button_frame.pack(side="right", fill="y")

        self.preview_label = tk.Label(self.image_frame, bg="white")
        self.preview_label.pack(expand=True)

        self.start_menu()

        self.loading_bar = Progressbar(self.root, length=300, mode="indeterminate", maximum=100)
        # self.loading_bar.place(relx=0.5, rely=0.9, anchor="center")

    def draw_gradient(self):
        for i in range(700):
            color = "#%02x%02x%02x" % (255 - i//3, 180 - i//4, 255 - i//3)
            self.gradient_canvas.create_line(0, i, 1000, i, fill=color)

    def clear_buttons(self):
        for widget in self.button_frame.winfo_children():
            widget.destroy()

    def add_button(self, text, command, width=25, pady=10, font_size=12):
        btn = tk.Button(
            self.button_frame, text=text, command=command, width=width, pady=pady,
            font=("Helvetica", font_size), bg="#9370DB", fg="white",
            activebackground="#8A2BE2", bd=0, cursor="hand2"
        )
        btn.pack(pady=7)

    def start_menu(self):
        self.clear_buttons()
        self.add_button("🖼️ Image Processing", self.main_menu, width=30, pady=20, font_size=14)
        self.add_button("🎬 Video Processing", self.video_menu, width=30, pady=20, font_size=14)

    def main_menu(self):
        self.clear_buttons()
        self.add_button("Open Image", self.open_image)
        self.add_button("Sharpen Image", self.sharpen_menu)
        self.add_button("Resize Image", self.resize_menu)
        self.add_button("Color Effects", self.color_menu)
        self.add_button("Convert to Grayscale", self.convert_to_grayscale)
        self.add_button("Save Image", self.save_image)
        self.add_button("Undo", self.undo_image)
        self.add_button("🏠 Home", self.start_menu)

    def video_menu(self):
        self.clear_buttons()
        self.add_button("Open Video", self.open_video)
        self.add_button("Play Video", self.play_video)
        self.add_button("Pause Video", self.pause_video)
        self.add_button("Resume Video", self.resume_video)
        self.add_button("Video Effects", self.video_effects_menu)
        self.add_button("Save Processed Video", self.save_processed_video)
        self.add_button("Undo Video", self.undo_video)
        self.add_button("🏠 Home", self.start_menu)

    def sharpen_menu(self):
        self.clear_buttons()
        self.add_button("Sharpen Image", self.sharpen_image)
        self.add_button("Undo", self.undo_image)
        self.add_button("⬅️ Back", self.main_menu)

    def resize_menu(self):
        self.clear_buttons()
        self.add_button("Resize Bigger", lambda: self.resize_image(1.5))
        self.add_button("Resize Smaller", lambda: self.resize_image(0.5))
        self.add_button("Undo", self.undo_image)
        self.add_button("⬅️ Back", self.main_menu)

    def color_menu(self):
        self.clear_buttons()
        self.add_button("Enhance Colors", self.enhance_color)
        self.add_button("Undo", self.undo_image)
        self.add_button("⬅️ Back", self.main_menu)

    def video_effects_menu(self):
        self.clear_buttons()
        self.add_button("Apply Grayscale", self.vid_grayscale)
        self.add_button("Resize Bigger", lambda: self.vid_resize(1.5))
        self.add_button("Resize Smaller", lambda: self.vid_resize(0.5))
        self.add_button("Enhance Colors", lambda: self.vid_color(1.5))
        self.add_button("Sharpen Video", self.vid_sharpen)
        self.add_button("Apply Cartoonish Effect", self.vid_cartoon)
        # self.add_button("Apply Bloom Effect", self.vid_bloom)
        self.add_button("Apply Sketch Effect", self.vid_sketch)
        self.add_button("Undo", self.undo_video)
        self.add_button("⬅️ Back", self.video_menu)

    # def vid_bloom(self):
    #     def bloom_effect(frame):
    #         # Convert to grayscale and threshold
    #         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    #         _, thresholded = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    #         # Use the threshold to create a glowing effect
    #         frame = cv2.addWeighted(frame, 1.5, thresholded, 0.5, 0)
    #         return frame
    #     self.process_video(bloom_effect)

    def vid_cartoon(self):
        def cartoonize(frame):
            # Apply bilateral filter to smoothen the image
            color = cv2.bilateralFilter(frame, 9, 300, 300)
            # Convert to grayscale and apply median blur
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 7)
            # Detect edges using adaptive thresholding
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY, 9, 9)
            # Combine the color image with edges
            cartoon = cv2.bitwise_and(color, color, mask=edges)
            return cartoon

        self.process_video(cartoonize)

    def vid_sketch(self):
        def sketch(frame):
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Invert the image
            inverted = cv2.bitwise_not(gray)
            # Blur the inverted image
            blurred = cv2.GaussianBlur(inverted, (21, 21), 0)
            # Invert the blurred image
            inverted_blurred = cv2.bitwise_not(blurred)
            # Create the sketch effect by blending the grayscale and inverted blurred image
            sketch = cv2.divide(gray, inverted_blurred, scale=256.0)
            return cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)

        self.process_video(sketch)


    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if path:
            self.image = Image.open(path)
            self.undo_stack = [self.image.copy()]
            self.display_image(self.image)

    def save_image(self):
        if self.image:
            path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")])
            if path:
                self.image.save(path)

    def display_image(self, img):
        img.thumbnail((600, 600))
        self.photo = ImageTk.PhotoImage(img)
        self.preview_label.configure(image=self.photo)

    def sharpen_image(self):
        if self.image:
            self.undo_stack.append(self.image.copy())
            enhancer = ImageEnhance.Sharpness(self.image)
            self.image = enhancer.enhance(2.0)
            self.display_image(self.image)

    def resize_image(self, scale):
        if self.image:
            self.undo_stack.append(self.image.copy())
            w, h = self.image.size
            self.image = self.image.resize((int(w * scale), int(h * scale)))
            self.display_image(self.image)

    def enhance_color(self):
        if self.image:
            self.undo_stack.append(self.image.copy())
            enhancer = ImageEnhance.Color(self.image)
            self.image = enhancer.enhance(1.5)
            self.display_image(self.image)

    def convert_to_grayscale(self):
        if self.image:
            self.undo_stack.append(self.image.copy())
            self.image = self.image.convert("L")
            self.display_image(self.image)

    def undo_image(self):
        if len(self.undo_stack) > 1:
            self.undo_stack.pop()
            self.image = self.undo_stack[-1].copy()
            self.display_image(self.image)

    def open_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mov")])
        if path:
            self.video_path = path
            cap = cv2.VideoCapture(path)
            self.video_fps = cap.get(cv2.CAP_PROP_FPS) or 30
            self.processed_frames = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                self.processed_frames.append(frame)
            cap.release()
            self.video_undo_stack = [self.processed_frames.copy()]
            frame_rgb = cv2.cvtColor(self.processed_frames[0], cv2.COLOR_BGR2RGB)
            self.display_image(Image.fromarray(frame_rgb))

    def play_video(self):
        if not self.processed_frames:
            return
        self.stop_playback = False

        def play():
            while not self.stop_playback:
                for frame in self.processed_frames:
                    if self.stop_playback:
                        break
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    self.display_image(img)
                    time.sleep(1.0 / self.video_fps)

        threading.Thread(target=play, daemon=True).start()

    def pause_video(self):
        self.stop_playback = True

    def resume_video(self):
        self.play_video()

    def process_video(self, func):
        if not self.processed_frames:
            return
        self.pause_video()
        new_frames = []
        for frame in self.processed_frames:
            out = func(frame)
            if out.ndim == 2:
                out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
            new_frames.append(out)
        self.video_undo_stack.append(self.processed_frames.copy())
        self.processed_frames = new_frames
        frame_rgb = cv2.cvtColor(self.processed_frames[0], cv2.COLOR_BGR2RGB)
        self.display_image(Image.fromarray(frame_rgb))

    def vid_grayscale(self):
        self.process_video(lambda frame: cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

    def vid_resize(self, scale):
        self.process_video(lambda frame: cv2.resize(frame, (0, 0), fx=scale, fy=scale))

    def vid_color(self, factor):
        def enhance(frame):
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(float)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255)
            return cv2.cvtColor(hsv.astype('uint8'), cv2.COLOR_HSV2BGR)
        self.process_video(enhance)

    def vid_sharpen(self):
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        self.process_video(lambda frame: cv2.filter2D(frame, -1, kernel))

    def undo_video(self):
        if len(self.video_undo_stack) > 1:
            self.video_undo_stack.pop()
            self.processed_frames = self.video_undo_stack[-1].copy()
            frame_rgb = cv2.cvtColor(self.processed_frames[0], cv2.COLOR_BGR2RGB)
            self.display_image(Image.fromarray(frame_rgb))

    def save_processed_video(self):
        if not self.processed_frames:
            return
        path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
        if path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            h, w = self.processed_frames[0].shape[:2]
            out = cv2.VideoWriter(path, fourcc, self.video_fps, (w, h))
            for frame in self.processed_frames:
                out.write(frame)
            out.release()
            messagebox.showinfo("Success", "Video saved successfully.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageVideoEditor(root)
    root.mainloop()