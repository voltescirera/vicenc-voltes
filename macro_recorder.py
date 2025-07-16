#!/usr/bin/env python3
"""
Robust Macro Recorder Application
A professional-grade macro recorder with accurate timing and screen calibration.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
from datetime import datetime
from pynput import mouse, keyboard
from pynput.mouse import Button, Listener as MouseListener
from pynput.keyboard import Key, Listener as KeyboardListener
import queue
import sys
import os


class MacroRecorder:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        
        # Recording state
        self.is_recording = False
        self.is_playing = False
        self.recorded_actions = []
        self.start_time = None
        
        # Listeners and controllers
        self.mouse_listener = None
        self.keyboard_listener = None
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        
        # Queue for thread-safe GUI updates
        self.log_queue = queue.Queue()
        
        # Screen calibration
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.calibration_factor_x = 1.0
        self.calibration_factor_y = 1.0
        
        self.setup_gui()
        self.setup_styles()
        self.process_log_queue()
        
    def setup_window(self):
        """Configure main window properties"""
        self.root.title("Macro Recorder Pro")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        self.root.configure(bg="#1e1e1e")
        
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"800x600+{x}+{y}")
        
    def setup_styles(self):
        """Configure modern dark theme styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles for dark theme
        style.configure('Dark.TFrame', background='#1e1e1e')
        style.configure('Dark.TLabel', background='#1e1e1e', foreground='#ffffff', font=('SF Pro Display', 10))
        style.configure('Title.TLabel', background='#1e1e1e', foreground='#ffffff', font=('SF Pro Display', 16, 'bold'))
        style.configure('Dark.TButton', 
                       background='#007AFF', 
                       foreground='#ffffff',
                       borderwidth=0,
                       focuscolor='none',
                       font=('SF Pro Display', 10, 'bold'))
        style.map('Dark.TButton',
                 background=[('active', '#0056CC'), ('pressed', '#004199')])
        
        style.configure('Record.TButton', 
                       background='#FF3B30', 
                       foreground='#ffffff',
                       borderwidth=0,
                       focuscolor='none',
                       font=('SF Pro Display', 10, 'bold'))
        style.map('Record.TButton',
                 background=[('active', '#D70015'), ('pressed', '#A50011')])
        
        style.configure('Success.TButton', 
                       background='#34C759', 
                       foreground='#ffffff',
                       borderwidth=0,
                       focuscolor='none',
                       font=('SF Pro Display', 10, 'bold'))
        style.map('Success.TButton',
                 background=[('active', '#248A3D'), ('pressed', '#1A5F2B')])
        
        style.configure('Dark.TEntry', 
                       fieldbackground='#2c2c2e',
                       borderwidth=1,
                       insertcolor='#ffffff',
                       foreground='#ffffff')
        
    def setup_gui(self):
        """Create the main GUI interface"""
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="Macro Recorder Pro", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Control panel
        control_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Record button
        self.record_btn = ttk.Button(control_frame, text="● Record", 
                                   command=self.toggle_recording, style='Record.TButton')
        self.record_btn.pack(side=tk.LEFT, padx=(0, 10), ipady=8, ipadx=15)
        
        # Play button
        self.play_btn = ttk.Button(control_frame, text="▶ Play", 
                                 command=self.start_playback, style='Success.TButton')
        self.play_btn.pack(side=tk.LEFT, padx=(0, 10), ipady=8, ipadx=15)
        
        # Clear button
        self.clear_btn = ttk.Button(control_frame, text="🗑 Clear", 
                                  command=self.clear_recording, style='Dark.TButton')
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 20), ipady=8, ipadx=15)
        
        # Repetitions
        rep_frame = ttk.Frame(control_frame, style='Dark.TFrame')
        rep_frame.pack(side=tk.LEFT)
        
        ttk.Label(rep_frame, text="Repetitions:", style='Dark.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        self.rep_var = tk.StringVar(value="1")
        self.rep_entry = ttk.Entry(rep_frame, textvariable=self.rep_var, width=5, style='Dark.TEntry')
        self.rep_entry.pack(side=tk.LEFT)
        
        # Calibration button
        self.calibrate_btn = ttk.Button(control_frame, text="🎯 Calibrate", 
                                      command=self.calibrate_screen, style='Dark.TButton')
        self.calibrate_btn.pack(side=tk.RIGHT, ipady=8, ipadx=15)
        
        # Status frame
        status_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Ready to record", style='Dark.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        self.action_count_label = ttk.Label(status_frame, text="Actions: 0", style='Dark.TLabel')
        self.action_count_label.pack(side=tk.RIGHT)
        
        # Event log
        log_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(log_frame, text="Event Log:", style='Dark.TLabel').pack(anchor=tk.W, pady=(0, 5))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                bg='#2c2c2e', 
                                                fg='#ffffff',
                                                insertbackground='#ffffff',
                                                selectbackground='#007AFF',
                                                selectforeground='#ffffff',
                                                font=('Monaco', 9),
                                                wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Bind escape key globally
        self.root.bind('<Escape>', self.stop_playback)
        self.root.focus_set()
        
    def log_action(self, message):
        """Thread-safe logging to the event log"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] {message}\n"
        self.log_queue.put(formatted_message)
        
    def process_log_queue(self):
        """Process log messages from the queue"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message)
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self.process_log_queue)
            
    def calibrate_screen(self):
        """Screen calibration to ensure accurate coordinate mapping"""
        cal_window = tk.Toplevel(self.root)
        cal_window.title("Screen Calibration")
        cal_window.geometry("400x300")
        cal_window.configure(bg="#1e1e1e")
        cal_window.transient(self.root)
        cal_window.grab_set()
        
        # Center calibration window
        cal_window.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (300 // 2)
        cal_window.geometry(f"400x300+{x}+{y}")
        
        ttk.Label(cal_window, text="Screen Calibration", 
                 style='Title.TLabel').pack(pady=20)
        
        instruction_text = """
        To calibrate screen coordinates:
        
        1. Click 'Start Calibration'
        2. Click on the TOP-LEFT corner of your primary monitor
        3. Click on the BOTTOM-RIGHT corner of your primary monitor
        4. The system will calculate calibration factors
        
        This ensures accurate coordinate mapping.
        """
        
        ttk.Label(cal_window, text=instruction_text, 
                 style='Dark.TLabel', justify=tk.CENTER).pack(pady=20, padx=20)
        
        self.cal_points = []
        self.cal_listener = None
        
        def start_calibration():
            cal_window.withdraw()
            self.cal_points.clear()
            self.log_action("Calibration started - Click TOP-LEFT corner")
            
            def on_click(x, y, button, pressed):
                if pressed and button == Button.left:
                    self.cal_points.append((x, y))
                    if len(self.cal_points) == 1:
                        self.log_action(f"Top-left recorded: ({x}, {y}) - Now click BOTTOM-RIGHT corner")
                    elif len(self.cal_points) == 2:
                        self.log_action(f"Bottom-right recorded: ({x}, {y})")
                        self.calculate_calibration()
                        cal_window.destroy()
                        return False
            
            self.cal_listener = MouseListener(on_click=on_click)
            self.cal_listener.start()
        
        ttk.Button(cal_window, text="Start Calibration", 
                  command=start_calibration, style='Dark.TButton').pack(pady=20)
        
        ttk.Button(cal_window, text="Cancel", 
                  command=cal_window.destroy, style='Dark.TButton').pack()
        
    def calculate_calibration(self):
        """Calculate calibration factors based on calibration points"""
        if len(self.cal_points) == 2:
            top_left = self.cal_points[0]
            bottom_right = self.cal_points[1]
            
            # Calculate screen dimensions based on calibration
            cal_width = bottom_right[0] - top_left[0]
            cal_height = bottom_right[1] - top_left[1]
            
            # Update calibration factors
            self.calibration_factor_x = cal_width / self.screen_width
            self.calibration_factor_y = cal_height / self.screen_height
            
            self.log_action(f"Calibration complete - Factors: X={self.calibration_factor_x:.3f}, Y={self.calibration_factor_y:.3f}")
            
    def apply_calibration(self, x, y):
        """Apply calibration to coordinates"""
        cal_x = int(x * self.calibration_factor_x)
        cal_y = int(y * self.calibration_factor_y)
        return cal_x, cal_y
        
    def toggle_recording(self):
        """Start or stop recording"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        """Begin recording user actions"""
        self.is_recording = True
        self.recorded_actions.clear()
        self.start_time = time.time()
        
        self.record_btn.configure(text="⏹ Stop Recording", style='Record.TButton')
        self.play_btn.configure(state='disabled')
        self.clear_btn.configure(state='disabled')
        self.status_label.configure(text="Recording in progress...")
        
        self.log_action("Recording started")
        
        # Start mouse listener
        def on_move(x, y):
            if self.is_recording:
                timestamp = time.time() - self.start_time
                self.recorded_actions.append({
                    'type': 'mouse_move',
                    'x': x,
                    'y': y,
                    'timestamp': timestamp
                })
                
        def on_click(x, y, button, pressed):
            if self.is_recording:
                timestamp = time.time() - self.start_time
                action = {
                    'type': 'mouse_click',
                    'x': x,
                    'y': y,
                    'button': str(button),
                    'pressed': pressed,
                    'timestamp': timestamp
                }
                self.recorded_actions.append(action)
                
                if pressed:
                    button_name = "Left" if button == Button.left else "Right"
                    self.log_action(f"{button_name} click at ({x}, {y})")
                    
        def on_scroll(x, y, dx, dy):
            if self.is_recording:
                timestamp = time.time() - self.start_time
                self.recorded_actions.append({
                    'type': 'mouse_scroll',
                    'x': x,
                    'y': y,
                    'dx': dx,
                    'dy': dy,
                    'timestamp': timestamp
                })
                self.log_action(f"Scroll at ({x}, {y}): dx={dx}, dy={dy}")
        
        self.mouse_listener = MouseListener(
            on_move=on_move,
            on_click=on_click,
            on_scroll=on_scroll
        )
        self.mouse_listener.start()
        
        # Start keyboard listener
        def on_press(key):
            if self.is_recording:
                timestamp = time.time() - self.start_time
                key_name = str(key).replace("'", "")
                self.recorded_actions.append({
                    'type': 'key_press',
                    'key': key_name,
                    'timestamp': timestamp
                })
                self.log_action(f"Key pressed: {key_name}")
                
        def on_release(key):
            if self.is_recording:
                timestamp = time.time() - self.start_time
                key_name = str(key).replace("'", "")
                self.recorded_actions.append({
                    'type': 'key_release',
                    'key': key_name,
                    'timestamp': timestamp
                })
        
        self.keyboard_listener = KeyboardListener(
            on_press=on_press,
            on_release=on_release
        )
        self.keyboard_listener.start()
        
        self.update_action_count()
        
    def stop_recording(self):
        """Stop recording"""
        self.is_recording = False
        
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            
        self.record_btn.configure(text="● Record", style='Record.TButton')
        self.play_btn.configure(state='normal')
        self.clear_btn.configure(state='normal')
        self.status_label.configure(text="Recording stopped")
        
        self.log_action(f"Recording stopped - {len(self.recorded_actions)} actions captured")
        self.update_action_count()
        
    def start_playback(self):
        """Start playback of recorded actions"""
        if not self.recorded_actions:
            messagebox.showwarning("No Recording", "Please record some actions first.")
            return
            
        try:
            repetitions = int(self.rep_var.get())
            if repetitions <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of repetitions.")
            return
            
        self.is_playing = True
        self.record_btn.configure(state='disabled')
        self.play_btn.configure(text="⏸ Playing...", state='disabled')
        self.clear_btn.configure(state='disabled')
        self.status_label.configure(text=f"Playing back {repetitions} time(s)...")
        
        # Start playback in a separate thread
        playback_thread = threading.Thread(target=self.playback_actions, args=(repetitions,))
        playback_thread.daemon = True
        playback_thread.start()
        
    def playback_actions(self, repetitions):
        """Execute the recorded actions"""
        try:
            for rep in range(repetitions):
                if not self.is_playing:
                    break
                    
                self.log_action(f"Starting repetition {rep + 1}/{repetitions}")
                
                last_timestamp = 0
                for action in self.recorded_actions:
                    if not self.is_playing:
                        break
                        
                    # Wait for the correct timing
                    wait_time = action['timestamp'] - last_timestamp
                    if wait_time > 0:
                        time.sleep(wait_time)
                    last_timestamp = action['timestamp']
                    
                    # Execute the action
                    self.execute_action(action)
                    
                if rep < repetitions - 1:
                    time.sleep(0.5)  # Brief pause between repetitions
                    
        except Exception as e:
            self.log_action(f"Playback error: {str(e)}")
        finally:
            self.root.after(0, self.playback_finished)
            
    def execute_action(self, action):
        """Execute a single recorded action"""
        try:
            if action['type'] == 'mouse_move':
                # Apply calibration and force mouse position
                cal_x, cal_y = self.apply_calibration(action['x'], action['y'])
                self.mouse_controller.position = (cal_x, cal_y)
                
            elif action['type'] == 'mouse_click':
                # Apply calibration and perform click
                cal_x, cal_y = self.apply_calibration(action['x'], action['y'])
                self.mouse_controller.position = (cal_x, cal_y)
                
                button = Button.left if 'left' in action['button'].lower() else Button.right
                
                if action['pressed']:
                    self.mouse_controller.press(button)
                else:
                    self.mouse_controller.release(button)
                    
            elif action['type'] == 'mouse_scroll':
                cal_x, cal_y = self.apply_calibration(action['x'], action['y'])
                self.mouse_controller.position = (cal_x, cal_y)
                self.mouse_controller.scroll(action['dx'], action['dy'])
                
            elif action['type'] == 'key_press':
                key = self.parse_key(action['key'])
                if key:
                    self.keyboard_controller.press(key)
                    
            elif action['type'] == 'key_release':
                key = self.parse_key(action['key'])
                if key:
                    self.keyboard_controller.release(key)
                    
        except Exception as e:
            self.log_action(f"Action execution error: {str(e)}")
            
    def parse_key(self, key_str):
        """Parse key string back to pynput key object"""
        try:
            # Handle special keys
            if key_str.startswith('Key.'):
                key_name = key_str.replace('Key.', '')
                return getattr(Key, key_name)
            elif len(key_str) == 1:
                return key_str
            else:
                # Try to get the key from keyboard module
                return getattr(Key, key_str, key_str)
        except:
            return None
            
    def stop_playback(self, event=None):
        """Stop playback (ESC key handler)"""
        if self.is_playing:
            self.is_playing = False
            self.log_action("Playback stopped by user (ESC)")
            self.root.after(0, self.playback_finished)
            
    def playback_finished(self):
        """Clean up after playback"""
        self.is_playing = False
        self.record_btn.configure(state='normal')
        self.play_btn.configure(text="▶ Play", state='normal')
        self.clear_btn.configure(state='normal')
        self.status_label.configure(text="Playback finished")
        
    def clear_recording(self):
        """Clear all recorded actions"""
        if messagebox.askyesno("Clear Recording", "Are you sure you want to clear the recorded actions?"):
            self.recorded_actions.clear()
            self.log_text.delete(1.0, tk.END)
            self.log_action("Recording cleared")
            self.update_action_count()
            
    def update_action_count(self):
        """Update the action count display"""
        count = len(self.recorded_actions)
        self.action_count_label.configure(text=f"Actions: {count}")
        
    def run(self):
        """Start the application"""
        self.log_action("Macro Recorder Pro started")
        self.log_action("Press ESC during playback to stop")
        self.log_action("Use 'Calibrate' for accurate coordinate mapping")
        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = MacroRecorder()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)