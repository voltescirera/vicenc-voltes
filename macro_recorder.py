#!/usr/bin/env python3
"""
Robust Macro Recorder Application
A professional-grade macro recorder with accurate timing and screen calibration.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
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
        self.current_file = None
        
        # Listeners and controllers
        self.mouse_listener = None
        self.keyboard_listener = None
        self.global_key_listener = None  # For ESC key detection
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        
        # Queue for thread-safe GUI updates
        self.log_queue = queue.Queue()
        
        # Screen calibration - improved approach
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.offset_x = 0  # Screen offset
        self.offset_y = 0  # Screen offset
        self.scale_factor = 0.79  # Correction factor for coordinate scaling
        self.use_raw_coordinates = True  # Use raw coordinates by default
        
        self.setup_gui()
        self.setup_styles()
        self.setup_global_key_listener()  # Set up global ESC listener
        self.process_log_queue()
        
    def setup_window(self):
        """Configure main window properties"""
        self.root.title("Macro Recorder Pro")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)
        self.root.configure(bg="#f5f5f7")
        
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"900x700+{x}+{y}")
        
        # Make window resizable but maintain aspect
        self.root.resizable(True, True)
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_global_key_listener(self):
        """Set up global key listener for ESC key detection"""
        def on_key_press(key):
            try:
                if key == Key.esc:
                    if self.is_recording:
                        self.log_action("ESC pressed - stopping recording")
                        self.root.after(0, self.stop_recording)
                    elif self.is_playing:
                        self.log_action("ESC pressed - stopping playback")
                        self.root.after(0, self.stop_playback)
            except Exception as e:
                self.log_action(f"Key listener error: {e}")
        
        # Start global key listener in a separate thread
        self.global_key_listener = KeyboardListener(on_press=on_key_press)
        self.global_key_listener.daemon = True
        self.global_key_listener.start()
        
    def on_closing(self):
        """Handle application closing"""
        try:
            if self.global_key_listener:
                self.global_key_listener.stop()
            if self.mouse_listener:
                self.mouse_listener.stop()
            if self.keyboard_listener:
                self.keyboard_listener.stop()
        except:
            pass
        self.root.destroy()
        
    def setup_styles(self):
        """Configure modern Apple-like theme styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main background
        style.configure('Main.TFrame', background='#f5f5f7')
        style.configure('Card.TFrame', background='#ffffff', relief='flat', borderwidth=1)
        
        # Typography - Apple system fonts
        style.configure('Title.TLabel', 
                       background='#f5f5f7', 
                       foreground='#1d1d1f', 
                       font=('SF Pro Display', 28, 'bold'))
        
        style.configure('Subtitle.TLabel', 
                       background='#f5f5f7', 
                       foreground='#86868b', 
                       font=('SF Pro Text', 13))
        
        style.configure('Body.TLabel', 
                       background='#ffffff', 
                       foreground='#1d1d1f', 
                       font=('SF Pro Text', 12))
        
        style.configure('Status.TLabel', 
                       background='#f5f5f7', 
                       foreground='#86868b', 
                       font=('SF Pro Text', 11))
        
        # Buttons - Apple style
        style.configure('Primary.TButton', 
                       background='#007AFF', 
                       foreground='#ffffff',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 12),
                       font=('SF Pro Text', 12, 'bold'))
        style.map('Primary.TButton',
                 background=[('active', '#0056CC'), ('pressed', '#004199')])
        
        style.configure('Secondary.TButton', 
                       background='#f2f2f7', 
                       foreground='#007AFF',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 12),
                       font=('SF Pro Text', 12, 'bold'))
        style.map('Secondary.TButton',
                 background=[('active', '#e5e5ea'), ('pressed', '#d1d1d6')])
        
        style.configure('Danger.TButton', 
                       background='#ff3b30', 
                       foreground='#ffffff',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 12),
                       font=('SF Pro Text', 12, 'bold'))
        style.map('Danger.TButton',
                 background=[('active', '#d70015'), ('pressed', '#a50011')])
        
        style.configure('Success.TButton', 
                       background='#34c759', 
                       foreground='#ffffff',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 12),
                       font=('SF Pro Text', 12, 'bold'))
        style.map('Success.TButton',
                 background=[('active', '#248a3d'), ('pressed', '#1a5f2b')])
        
        # Entry fields
        style.configure('Modern.TEntry', 
                       fieldbackground='#ffffff',
                       borderwidth=1,
                       relief='solid',
                       insertcolor='#007AFF',
                       foreground='#1d1d1f',
                       padding=10,
                       font=('SF Pro Text', 12))
        
    def setup_gui(self):
        """Create the main GUI interface"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        # Header section
        header_frame = ttk.Frame(main_frame, style='Main.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Title and subtitle
        title_label = ttk.Label(header_frame, text="Macro Recorder", style='Title.TLabel')
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(header_frame, 
                                 text="Record and replay mouse and keyboard actions with precision", 
                                 style='Subtitle.TLabel')
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Control panel - Card style
        control_card = ttk.Frame(main_frame, style='Card.TFrame')
        control_card.pack(fill=tk.X, pady=(0, 20))
        
        # Add subtle shadow effect (simulate with border)
        control_card.configure(relief='solid', borderwidth=1)
        
        control_inner = ttk.Frame(control_card, style='Card.TFrame')
        control_inner.pack(fill=tk.X, padx=25, pady=20)
        
        # Primary controls row
        primary_controls = ttk.Frame(control_inner, style='Card.TFrame')
        primary_controls.pack(fill=tk.X, pady=(0, 15))
        
        # Record button
        self.record_btn = ttk.Button(primary_controls, text="⏺ Record", 
                                   command=self.toggle_recording, style='Danger.TButton')
        self.record_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Play button
        self.play_btn = ttk.Button(primary_controls, text="▶ Play", 
                                 command=self.start_playback, style='Success.TButton')
        self.play_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Clear button
        self.clear_btn = ttk.Button(primary_controls, text="🗑 Clear", 
                                  command=self.clear_recording, style='Secondary.TButton')
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Test click button - for debugging coordinates
        self.test_btn = ttk.Button(primary_controls, text="🎯 Test Click", 
                                 command=self.test_click, style='Secondary.TButton')
        self.test_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Calibration button
        self.calibrate_btn = ttk.Button(primary_controls, text="📏 Calibrate", 
                                      command=self.calibrate_screen, style='Secondary.TButton')
        self.calibrate_btn.pack(side=tk.RIGHT)
        
        # Secondary controls row
        secondary_controls = ttk.Frame(control_inner, style='Card.TFrame')
        secondary_controls.pack(fill=tk.X, pady=(0, 15))
        
        # File operations
        file_frame = ttk.Frame(secondary_controls, style='Card.TFrame')
        file_frame.pack(side=tk.LEFT)
        
        self.save_btn = ttk.Button(file_frame, text="💾 Save Recording", 
                                 command=self.save_recording, style='Secondary.TButton')
        self.save_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.load_btn = ttk.Button(file_frame, text="📁 Load Recording", 
                                 command=self.load_recording, style='Secondary.TButton')
        self.load_btn.pack(side=tk.LEFT)
        
        # Repetitions control
        rep_frame = ttk.Frame(secondary_controls, style='Card.TFrame')
        rep_frame.pack(side=tk.RIGHT)
        
        ttk.Label(rep_frame, text="Repetitions:", style='Body.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        self.rep_var = tk.StringVar(value="1")
        self.rep_entry = ttk.Entry(rep_frame, textvariable=self.rep_var, width=8, style='Modern.TEntry')
        self.rep_entry.pack(side=tk.LEFT)
        
        # Status section
        status_card = ttk.Frame(main_frame, style='Card.TFrame')
        status_card.pack(fill=tk.X, pady=(0, 20))
        status_card.configure(relief='solid', borderwidth=1)
        
        status_inner = ttk.Frame(status_card, style='Card.TFrame')
        status_inner.pack(fill=tk.X, padx=25, pady=15)
        
        # Status indicators
        status_top = ttk.Frame(status_inner, style='Card.TFrame')
        status_top.pack(fill=tk.X)
        
        self.status_label = ttk.Label(status_top, text="Ready to record", style='Body.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        self.action_count_label = ttk.Label(status_top, text="Actions: 0", style='Status.TLabel')
        self.action_count_label.pack(side=tk.RIGHT)
        
        # File status and coordinate info
        status_bottom = ttk.Frame(status_inner, style='Card.TFrame')
        status_bottom.pack(fill=tk.X, pady=(5, 0))
        
        self.file_status_label = ttk.Label(status_bottom, text="No file loaded", style='Status.TLabel')
        self.file_status_label.pack(side=tk.LEFT)
        
        self.coordinate_info_label = ttk.Label(status_bottom, text="Raw coordinates mode", style='Status.TLabel')
        self.coordinate_info_label.pack(side=tk.RIGHT)
        
        # Event log section
        log_card = ttk.Frame(main_frame, style='Card.TFrame')
        log_card.pack(fill=tk.BOTH, expand=True)
        log_card.configure(relief='solid', borderwidth=1)
        
        log_inner = ttk.Frame(log_card, style='Card.TFrame')
        log_inner.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        ttk.Label(log_inner, text="Activity Log", style='Body.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # Custom styled text widget
        self.log_text = scrolledtext.ScrolledText(log_inner, 
                                                bg='#fafafa', 
                                                fg='#1d1d1f',
                                                insertbackground='#007AFF',
                                                selectbackground='#007AFF',
                                                selectforeground='#ffffff',
                                                font=('SF Mono', 10),
                                                wrap=tk.WORD,
                                                relief='flat',
                                                borderwidth=0,
                                                padx=15,
                                                pady=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def test_click(self):
        """Test function to click at current mouse position and show coordinates"""
        current_pos = self.mouse_controller.position
        self.log_action(f"Current mouse position: {current_pos}")
        
        # Show what the scaling would do
        scaled_pos = (current_pos[0] * self.scale_factor, current_pos[1] * self.scale_factor)
        self.log_action(f"With scale factor {self.scale_factor}: {current_pos} -> ({scaled_pos[0]:.1f}, {scaled_pos[1]:.1f})")
        
        # Click at current position
        time.sleep(1)  # Give user time to see the message
        self.mouse_controller.click(Button.left)
        self.log_action(f"Test click performed at {current_pos}")
        
    def log_action(self, message):
        """Thread-safe logging to the event log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
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
            
    def save_recording(self):
        """Save the current recording to a file"""
        if not self.recorded_actions:
            messagebox.showwarning("No Recording", "Please record some actions first.")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Save Recording",
            defaultextension=".macro",
            filetypes=[
                ("Macro files", "*.macro"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                recording_data = {
                    'version': '1.0',
                    'created': datetime.now().isoformat(),
                    'actions': self.recorded_actions,
                    'calibration': {
                        'offset_x': self.offset_x,
                        'offset_y': self.offset_y,
                        'scale_factor': self.scale_factor,
                        'use_raw_coordinates': self.use_raw_coordinates
                    },
                    'metadata': {
                        'action_count': len(self.recorded_actions),
                        'duration': self.recorded_actions[-1]['timestamp'] if self.recorded_actions else 0
                    }
                }
                
                with open(filename, 'w') as f:
                    json.dump(recording_data, f, indent=2)
                
                self.current_file = filename
                self.update_file_status()
                self.log_action(f"Recording saved to {os.path.basename(filename)}")
                messagebox.showinfo("Success", f"Recording saved successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save recording:\n{str(e)}")
                self.log_action(f"Save error: {str(e)}")
                
    def load_recording(self):
        """Load a recording from a file"""
        filename = filedialog.askopenfilename(
            title="Load Recording",
            filetypes=[
                ("Macro files", "*.macro"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    recording_data = json.load(f)
                
                # Validate the file format
                if 'actions' not in recording_data:
                    raise ValueError("Invalid macro file format")
                
                self.recorded_actions = recording_data['actions']
                
                # Load calibration if available
                if 'calibration' in recording_data:
                    cal = recording_data['calibration']
                    self.offset_x = cal.get('offset_x', 0)
                    self.offset_y = cal.get('offset_y', 0)
                    self.scale_factor = cal.get('scale_factor', 0.79)
                    self.use_raw_coordinates = cal.get('use_raw_coordinates', True)
                
                self.current_file = filename
                self.update_file_status()
                self.update_action_count()
                self.update_coordinate_info()
                
                # Display metadata if available
                metadata = recording_data.get('metadata', {})
                duration = metadata.get('duration', 0)
                created = recording_data.get('created', 'Unknown')
                
                self.log_action(f"Recording loaded from {os.path.basename(filename)}")
                self.log_action(f"Created: {created[:19] if created != 'Unknown' else 'Unknown'}")
                self.log_action(f"Duration: {duration:.2f}s, Actions: {len(self.recorded_actions)}")
                
                messagebox.showinfo("Success", 
                                  f"Recording loaded successfully!\n"
                                  f"Actions: {len(self.recorded_actions)}\n"
                                  f"Duration: {duration:.2f}s")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load recording:\n{str(e)}")
                self.log_action(f"Load error: {str(e)}")
                
    def update_file_status(self):
        """Update the file status display"""
        if self.current_file:
            filename = os.path.basename(self.current_file)
            self.file_status_label.configure(text=f"File: {filename}")
        else:
            self.file_status_label.configure(text="No file loaded")
            
    def update_coordinate_info(self):
        """Update coordinate information display"""
        if self.use_raw_coordinates:
            info = f"Raw coordinates (scale: {self.scale_factor}, offset: {self.offset_x}, {self.offset_y})"
        else:
            info = f"Calibrated coordinates (scale: {self.scale_factor}, offset: {self.offset_x}, {self.offset_y})"
        self.coordinate_info_label.configure(text=info)
            
    def calibrate_screen(self):
        """Improved screen calibration"""
        cal_window = tk.Toplevel(self.root)
        cal_window.title("Screen Calibration")
        cal_window.geometry("600x500")
        cal_window.configure(bg="#f5f5f7")
        cal_window.transient(self.root)
        cal_window.grab_set()
        
        # Center calibration window
        cal_window.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (500 // 2)
        cal_window.geometry(f"600x500+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(cal_window, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        ttk.Label(main_frame, text="Screen Calibration", 
                 style='Title.TLabel').pack(pady=(0, 20))
        
        instruction_text = """Calibration helps fix coordinate mapping issues.

Choose your calibration method:

1. AUTOMATIC CALIBRATION (Recommended):
   • Uses your current cursor position as reference
   • Quick and usually accurate

2. MANUAL CALIBRATION:
   • Click specific screen corners manually
   • More precise but requires more steps

3. RAW COORDINATES:
   • Uses coordinates exactly as recorded
   • Try this if calibration doesn't help"""
        
        # Instruction card
        instruction_card = ttk.Frame(main_frame, style='Card.TFrame')
        instruction_card.pack(fill=tk.X, pady=(0, 30))
        instruction_card.configure(relief='solid', borderwidth=1)
        
        instruction_inner = ttk.Frame(instruction_card, style='Card.TFrame')
        instruction_inner.pack(fill=tk.X, padx=25, pady=20)
        
        ttk.Label(instruction_inner, text=instruction_text, 
                 style='Body.TLabel', justify=tk.LEFT).pack()
        
        # Button frame
        button_frame = ttk.Frame(main_frame, style='Main.TFrame')
        button_frame.pack(fill=tk.X)
        
        def auto_calibrate():
            """Automatic calibration using current cursor position"""
            current_pos = self.mouse_controller.position
            self.offset_x = 0
            self.offset_y = 0
            self.use_raw_coordinates = True
            self.log_action(f"Auto-calibration: Using raw coordinates from position {current_pos}")
            self.update_coordinate_info()
            cal_window.destroy()
        
        def manual_calibrate():
            """Manual calibration by clicking corners"""
            cal_window.withdraw()
            self.cal_points = []
            self.log_action("Manual calibration started - Click TOP-LEFT corner of your screen")
            
            def on_click(x, y, button, pressed):
                if pressed and button == Button.left:
                    self.cal_points.append((x, y))
                    if len(self.cal_points) == 1:
                        self.log_action(f"Top-left recorded: ({x}, {y}) - Now click BOTTOM-RIGHT corner")
                    elif len(self.cal_points) == 2:
                        self.log_action(f"Bottom-right recorded: ({x}, {y})")
                        self.calculate_manual_calibration()
                        cal_window.destroy()
                        return False
            
            cal_listener = MouseListener(on_click=on_click)
            cal_listener.start()
        
        def use_raw_coordinates():
            """Use raw coordinates without calibration"""
            self.offset_x = 0
            self.offset_y = 0
            self.use_raw_coordinates = True
            self.log_action("Using raw coordinates mode")
            self.update_coordinate_info()
            cal_window.destroy()
            
        def adjust_scale_factor():
            """Allow user to adjust the scale factor"""
            scale_window = tk.Toplevel(cal_window)
            scale_window.title("Adjust Scale Factor")
            scale_window.geometry("400x300")
            scale_window.configure(bg="#f5f5f7")
            scale_window.transient(cal_window)
            scale_window.grab_set()
            
            # Center the window
            scale_window.update_idletasks()
            x = (cal_window.winfo_screenwidth() // 2) - (400 // 2)
            y = (cal_window.winfo_screenheight() // 2) - (300 // 2)
            scale_window.geometry(f"400x300+{x}+{y}")
            
            main_frame = ttk.Frame(scale_window, style='Main.TFrame')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
            
            ttk.Label(main_frame, text="Adjust Scale Factor", style='Title.TLabel').pack(pady=(0, 15))
            
            info_text = f"""Current scale factor: {self.scale_factor}
            
All coordinates are multiplied by this factor.
• 0.79 = coordinates reduced by 21%
• 1.0 = no scaling (original size)
• 1.2 = coordinates increased by 20%

Enter new scale factor:"""
            
            ttk.Label(main_frame, text=info_text, style='Body.TLabel', justify=tk.LEFT).pack(pady=(0, 15))
            
            scale_var = tk.StringVar(value=str(self.scale_factor))
            scale_entry = ttk.Entry(main_frame, textvariable=scale_var, width=10, style='Modern.TEntry')
            scale_entry.pack(pady=(0, 20))
            scale_entry.focus_set()
            
            def apply_scale():
                try:
                    new_scale = float(scale_var.get())
                    if 0.1 <= new_scale <= 5.0:
                        self.scale_factor = new_scale
                        self.log_action(f"Scale factor updated to {self.scale_factor}")
                        self.update_coordinate_info()
                        scale_window.destroy()
                    else:
                        messagebox.showerror("Invalid Value", "Scale factor must be between 0.1 and 5.0")
                except ValueError:
                    messagebox.showerror("Invalid Value", "Please enter a valid number")
            
            button_frame = ttk.Frame(main_frame, style='Main.TFrame')
            button_frame.pack(fill=tk.X)
            
            ttk.Button(button_frame, text="Apply", command=apply_scale, style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="Cancel", command=scale_window.destroy, style='Secondary.TButton').pack(side=tk.LEFT)
        
        # Calibration buttons
        button_row1 = ttk.Frame(button_frame, style='Main.TFrame')
        button_row1.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(button_row1, text="🎯 Auto Calibrate (Recommended)", 
                  command=auto_calibrate, style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(button_row1, text="📏 Manual Calibrate", 
                  command=manual_calibrate, style='Secondary.TButton').pack(side=tk.LEFT, padx=(0, 15))
        
        button_row2 = ttk.Frame(button_frame, style='Main.TFrame')
        button_row2.pack(fill=tk.X)
        
        ttk.Button(button_row2, text="📍 Raw Coordinates", 
                  command=use_raw_coordinates, style='Secondary.TButton').pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(button_row2, text="Cancel", 
                  command=cal_window.destroy, style='Secondary.TButton').pack(side=tk.RIGHT)
        
    def calculate_manual_calibration(self):
        """Calculate calibration from manual corner clicks"""
        if len(self.cal_points) == 2:
            top_left = self.cal_points[0]
            bottom_right = self.cal_points[1]
            
            # Calculate offset based on screen corners
            self.offset_x = top_left[0]
            self.offset_y = top_left[1]
            self.use_raw_coordinates = False
            
            self.log_action(f"Manual calibration complete - Offset: ({self.offset_x}, {self.offset_y})")
            self.update_coordinate_info()
            
    def apply_coordinates(self, x, y):
        """Apply coordinate transformation based on current calibration"""
        # Apply scaling factor first
        scaled_x = x * self.scale_factor
        scaled_y = y * self.scale_factor
        
        if self.use_raw_coordinates:
            # Use coordinates with scaling and optional offset
            return int(scaled_x + self.offset_x), int(scaled_y + self.offset_y)
        else:
            # Apply manual calibration offset with scaling
            return int(scaled_x + self.offset_x), int(scaled_y + self.offset_y)
        
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
        self.current_file = None  # Clear current file as we're creating new recording
        
        self.record_btn.configure(text="⏹ Stop Recording", style='Danger.TButton')
        self.play_btn.configure(state='disabled')
        self.clear_btn.configure(state='disabled')
        self.save_btn.configure(state='disabled')
        self.load_btn.configure(state='disabled')
        self.test_btn.configure(state='disabled')
        self.calibrate_btn.configure(state='disabled')
        self.status_label.configure(text="🔴 Recording in progress... (Press ESC to stop)")
        
        self.log_action("Recording started - Press ESC to stop at any time")
        self.update_file_status()
        
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
        
        # Start keyboard listener (separate from global ESC listener)
        def on_press(key):
            if self.is_recording:
                # Don't record ESC key during recording
                if key == Key.esc:
                    return
                    
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
                # Don't record ESC key during recording
                if key == Key.esc:
                    return
                    
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
            
        self.record_btn.configure(text="⏺ Record", style='Danger.TButton')
        self.play_btn.configure(state='normal')
        self.clear_btn.configure(state='normal')
        self.save_btn.configure(state='normal')
        self.load_btn.configure(state='normal')
        self.test_btn.configure(state='normal')
        self.calibrate_btn.configure(state='normal')
        self.status_label.configure(text="✅ Recording complete")
        
        duration = self.recorded_actions[-1]['timestamp'] if self.recorded_actions else 0
        self.log_action(f"Recording stopped - {len(self.recorded_actions)} actions captured in {duration:.2f}s")
        self.update_action_count()
        
    def start_playback(self):
        """Start playback of recorded actions"""
        if not self.recorded_actions:
            messagebox.showwarning("No Recording", "Please record some actions or load a recording first.")
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
        self.save_btn.configure(state='disabled')
        self.load_btn.configure(state='disabled')
        self.test_btn.configure(state='disabled')
        self.calibrate_btn.configure(state='disabled')
        self.status_label.configure(text=f"▶️ Playing back {repetitions} time(s)... (Press ESC to stop)")
        
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
                    
                if rep < repetitions - 1 and self.is_playing:
                    time.sleep(0.5)  # Brief pause between repetitions
                    
        except Exception as e:
            self.log_action(f"Playback error: {str(e)}")
        finally:
            self.root.after(0, self.playback_finished)
            
    def execute_action(self, action):
        """Execute a single recorded action with improved coordinate handling"""
        try:
            if action['type'] == 'mouse_move':
                # Apply coordinate transformation
                cal_x, cal_y = self.apply_coordinates(action['x'], action['y'])
                self.mouse_controller.position = (cal_x, cal_y)
                
            elif action['type'] == 'mouse_click':
                # Apply coordinate transformation and perform click
                cal_x, cal_y = self.apply_coordinates(action['x'], action['y'])
                
                # Log the coordinate transformation for debugging
                self.log_action(f"Click: original({action['x']}, {action['y']}) -> scaled({action['x']*self.scale_factor:.1f}, {action['y']*self.scale_factor:.1f}) -> final({cal_x}, {cal_y})")
                
                # Force the mouse to the exact position
                self.mouse_controller.position = (cal_x, cal_y)
                time.sleep(0.01)  # Small delay to ensure position is set
                
                button = Button.left if 'left' in action['button'].lower() else Button.right
                
                if action['pressed']:
                    self.mouse_controller.press(button)
                else:
                    self.mouse_controller.release(button)
                    
            elif action['type'] == 'mouse_scroll':
                cal_x, cal_y = self.apply_coordinates(action['x'], action['y'])
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
            self.root.after(0, self.playback_finished)
            
    def playback_finished(self):
        """Clean up after playback"""
        self.is_playing = False
        self.record_btn.configure(state='normal')
        self.play_btn.configure(text="▶ Play", state='normal')
        self.clear_btn.configure(state='normal')
        self.save_btn.configure(state='normal')
        self.load_btn.configure(state='normal')
        self.test_btn.configure(state='normal')
        self.calibrate_btn.configure(state='normal')
        self.status_label.configure(text="✅ Playback finished")
        
    def clear_recording(self):
        """Clear all recorded actions"""
        if messagebox.askyesno("Clear Recording", 
                              "Are you sure you want to clear the recorded actions?\n\n"
                              "This action cannot be undone."):
            self.recorded_actions.clear()
            self.current_file = None
            self.log_text.delete(1.0, tk.END)
            self.log_action("Recording cleared")
            self.update_action_count()
            self.update_file_status()
            
    def update_action_count(self):
        """Update the action count display"""
        count = len(self.recorded_actions)
        self.action_count_label.configure(text=f"Actions: {count}")
        
    def run(self):
        """Start the application"""
        self.log_action("🚀 Macro Recorder Pro started")
        self.log_action("💡 Global ESC key listener is active")
        self.log_action(f"⚙️ Scale factor: {self.scale_factor} (coordinates are scaled by this factor)")
        self.log_action("🎯 Use 'Test Click' to check coordinate accuracy")
        self.log_action("📏 Use 'Calibrate' if clicks are in wrong positions")
        self.log_action("💾 Save recordings to reuse them later")
        self.update_coordinate_info()
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