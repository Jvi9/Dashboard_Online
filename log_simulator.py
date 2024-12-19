# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 13:40:45 2024

@author: Jhon
"""

# =============================================================================
# SIMULATION OF LOG FILE
# =============================================================================
import time
import threading
import tkinter as tk
from tkinter import filedialog


class LogSimulator:
    def __init__(self, root):
        self.root = root
        self.running = False
        self.paused = False
        self.thread = None

        # Set window size and title
        self.root.title("Log Simulator")
        self.root.geometry("600x400")
        self.root.resizable(True, True)  # Allow resizing in both width and height

        # Create GUI components
        self.label = tk.Label(root, text="Log Simulator", font=("Helvetica", 16))
        self.label.pack(pady=10)

        # Input file selection
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(pady=5)
        tk.Label(self.input_frame, text="Input Log File:").grid(row=0, column=0, padx=5)
        self.input_path = tk.Entry(self.input_frame, width=40)
        self.input_path.grid(row=0, column=1, padx=5)
        tk.Button(self.input_frame, text="Browse", command=self.select_input_file).grid(row=0, column=2, padx=5)

        # Output file selection
        self.output_frame = tk.Frame(root)
        self.output_frame.pack(pady=5)
        tk.Label(self.output_frame, text="Output Log File:").grid(row=0, column=0, padx=5)
        self.output_path = tk.Entry(self.output_frame, width=40)
        self.output_path.grid(row=0, column=1, padx=5)
        tk.Button(self.output_frame, text="Browse", command=self.select_output_file).grid(row=0, column=2, padx=5)

        # Control buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=10)
        
        self.start_button = tk.Button(self.button_frame, text="Start", command=self.start_simulation, bg="green", fg="white", width=10)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.pause_button = tk.Button(self.button_frame, text="Pause", command=self.toggle_pause, bg="blue", fg="white", state=tk.DISABLED, width=10)
        self.pause_button.grid(row=0, column=1, padx=5)
        
        self.stop_button = tk.Button(self.button_frame, text="Stop", command=self.stop_simulation, bg="red", fg="white", state=tk.DISABLED, width=10)
        self.stop_button.grid(row=0, column=2, padx=5)
        
        self.quit_button = tk.Button(self.button_frame, text="Quit", command=self.quit_program, width=10)
        self.quit_button.grid(row=0, column=3, padx=5)

        # Log display area
        self.text = tk.Text(root, height=20, width=120)
        self.text.pack(pady=10)

    def log_simulation(self):
        input_file = self.input_path.get()
        output_file = self.output_path.get()
        try:
            with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
                for line in infile:
                    if not self.running:  # Stop if running is set to False
                        break

                    while self.paused:  # Pause logic
                        time.sleep(0.1)

                    outfile.write(line)
                    outfile.flush()
                    self.text.insert(tk.END, f"Simulated log line: {line.strip()}\n")
                    self.text.see(tk.END)  # Auto-scroll
                    time.sleep(0.05)  # Simulate delay
        except Exception as e:
            self.text.insert(tk.END, f"Error: {e}\n")
        finally:
            self.running = False
            self.update_buttons()

    def start_simulation(self):
        input_file = self.input_path.get()
        output_file = self.output_path.get()
        if not input_file or not output_file:
            self.text.insert(tk.END, "Please select both input and output files.\n")
            return

        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.log_simulation, daemon=True)
            self.thread.start()
            self.update_buttons()

    def toggle_pause(self):
        if self.paused:
            self.paused = False
            self.pause_button.config(text="Pause", bg="blue")
        else:
            self.paused = True
            self.pause_button.config(text="Resume", bg="orange")

    def stop_simulation(self):
        self.running = False
        self.paused = False
        self.update_buttons()

    def quit_program(self):
        self.running = False  # Signal the thread to stop
        self.paused = False   # Ensure it isn't stuck in a paused state
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)  # Wait for the thread to terminate safely
        self.root.quit()  # Close the mainloop
        self.root.destroy()  # Destroy the window

    def select_input_file(self):
        input_file = filedialog.askopenfilename(title="Select Input Log File", filetypes=[("Text Files", "*.txt")])
        if input_file:
            self.input_path.delete(0, tk.END)
            self.input_path.insert(0, input_file)

    def select_output_file(self):
        output_file = filedialog.asksaveasfilename(title="Select Output Log File", defaultextension=".txt",
                                                   filetypes=[("Text Files", "*.txt")])
        if output_file:
            self.output_path.delete(0, tk.END)
            self.output_path.insert(0, output_file)

    def update_buttons(self):
        if self.running:
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED, text="Pause", bg="blue")
            self.stop_button.config(state=tk.DISABLED)


# Create the GUI application
if __name__ == "__main__":
    root = tk.Tk()
    app = LogSimulator(root)
    root.mainloop()
