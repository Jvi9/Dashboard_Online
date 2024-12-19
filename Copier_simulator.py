# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 16:47:42 2024

@author: Jhon
"""
import os
import shutil
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import queue

class ImageCopierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Copier")
        self.root.geometry("500x400")  # Adjusted size for the queue and buttons

        # Source folder selection
        tk.Label(root, text="Source Folder:").pack(pady=5)
        self.source_path = tk.Entry(root, width=50)
        self.source_path.pack(pady=5)
        tk.Button(root, text="Browse", command=self.select_source_folder).pack(pady=5)

        # Destination folder selection
        tk.Label(root, text="Destination Folder:").pack(pady=5)
        self.dest_path = tk.Entry(root, width=50)
        self.dest_path.pack(pady=5)
        tk.Button(root, text="Browse", command=self.select_dest_folder).pack(pady=5)

        # Delay selection
        tk.Label(root, text="Delay (seconds):").pack(pady=5)
        self.delay_entry = tk.Entry(root, width=10)
        self.delay_entry.insert(0, "1")  # Default 1 second delay
        self.delay_entry.pack(pady=5)

        # Start Button (Green)
        self.start_button = tk.Button(root, text="Start Copying", command=self.start_copying, bg="green", fg="white")
        self.start_button.pack(pady=10)

        # Pause/Resume Button (Red)
        self.pause_button = tk.Button(root, text="Pause", command=self.toggle_pause, bg="red", fg="white")
        self.pause_button.pack(pady=5)

        # Image Queue Listbox to show copied images
        tk.Label(root, text="Copied Images:").pack(pady=5)
        self.image_queue = tk.Listbox(root, width=50, height=10)
        self.image_queue.pack(pady=10)

        # Initialize variables
        self.is_paused = False
        self.is_copying = False
        self.current_index = 0
        self.files_to_copy = []
        self.queue = queue.Queue()  # Queue to communicate between threads

        # Event to handle pause/resume
        self.pause_event = threading.Event()
        self.pause_event.set()  # Initially set the event, allowing copying to continue

        # Start a thread that checks the queue for updates
        self.check_queue_thread = threading.Thread(target=self.check_queue, daemon=True)
        self.check_queue_thread.start()

    def select_source_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.source_path.delete(0, tk.END)
            self.source_path.insert(0, folder)

    def select_dest_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_path.delete(0, tk.END)
            self.dest_path.insert(0, folder)

    def start_copying(self):
        source_folder = self.source_path.get()
        dest_folder = self.dest_path.get()
        delay = self.delay_entry.get()

        if not source_folder or not dest_folder:
            messagebox.showerror("Error", "Please select both source and destination folders.")
            return

        if not os.path.exists(source_folder):
            messagebox.showerror("Error", "Source folder does not exist.")
            return

        try:
            delay = float(delay)
        except ValueError:
            messagebox.showerror("Error", "Invalid delay value. Enter a valid number.")
            return

        # Initialize the files to copy
        self.files_to_copy = sorted(os.listdir(source_folder))
        self.is_copying = True
        self.current_index = 0

        # Clear the queue before starting
        self.image_queue.delete(0, tk.END)

        # Start copying images in a separate thread
        threading.Thread(target=self.copy_images_with_delay, args=(source_folder, dest_folder, delay), daemon=True).start()

    def toggle_pause(self):
        """ Toggle pause/resume functionality """
        if self.is_copying:
            if self.is_paused:
                self.is_paused = False
                self.pause_event.set()  # Allow copying to resume
                self.pause_button.config(text="Pause", bg="red")  # Keep red for pause
            else:
                self.is_paused = True
                self.pause_event.clear()  # Block copying until resumed
                self.pause_button.config(text="Resume", bg="green")  # Change to green for resume

    def check_queue(self):
        """ This function checks the queue for any updates from the copying thread """
        while True:
            try:
                # Get item from the queue, if available
                file_name = self.queue.get(timeout=1)
                # Insert at the top of the list (i.e., most recent copied image at the top)
                self.image_queue.insert(0, file_name)
            except queue.Empty:
                continue

    def copy_images_with_delay(self, source_folder, destination_folder, delay):
        # Ensure destination folder exists
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        # Supported image extensions (case insensitive)
        image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", 
                            ".JPG", ".JPEG", ".PNG", ".BMP", ".GIF", ".TIFF"}

        copied_count = 0
        while self.current_index < len(self.files_to_copy) and self.is_copying:
            file = self.files_to_copy[self.current_index]
            file_path = os.path.join(source_folder, file)

            if os.path.isfile(file_path) and os.path.splitext(file)[1] in image_extensions:
                # Wait for the pause event if the process is paused
                self.pause_event.wait()

                # Copy the file to destination
                shutil.copy(file_path, destination_folder)
                self.queue.put(file)  # Put image name in the queue to update the listbox
                copied_count += 1

                # Update the index
                self.current_index += 1

                # Pause if needed
                time.sleep(delay)

        if self.current_index >= len(self.files_to_copy):
            messagebox.showinfo("Success", f"Copied {copied_count} images to the destination folder.")

# Main Application
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCopierApp(root)
    root.mainloop()
