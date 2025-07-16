# Macro Recorder Pro

A professional-grade macro recorder application with a modern Apple-like interface. Record and replay mouse and keyboard actions with precision timing and accurate coordinate mapping.

![Macro Recorder Pro](https://img.shields.io/badge/Python-3.6+-blue.svg) ![Platform](https://img.shields.io/badge/Platform-Linux-green.svg) ![License](https://img.shields.io/badge/License-MIT-red.svg)

## ✨ Features

### 🎯 Core Functionality
- **Precise Recording**: Captures all mouse movements, clicks, and keyboard inputs with exact timing
- **Accurate Playback**: Replays actions with forced cursor positioning for consistent results
- **Screen Calibration**: Ensures accurate coordinate mapping across different screen configurations
- **Multi-Repetition**: Run recorded sequences multiple times with a single click

### 💾 File Management
- **Save Recordings**: Export your macros to `.macro` files for future use
- **Load Recordings**: Import previously saved macro files
- **Metadata Storage**: Automatically saves creation date, duration, and action count

### 🎨 Modern Interface
- **Apple-like Design**: Clean, modern interface inspired by Apple's design language
- **Dark/Light Theme**: Beautiful light theme with card-based layout
- **Real-time Feedback**: Live activity log with timestamps and status updates
- **Responsive Layout**: Resizable window with proper scaling

### ⚡ Advanced Controls
- **ESC to Stop**: Press ESC at any time to stop recording or playback
- **Thread-Safe**: All operations run safely in background threads
- **Error Handling**: Comprehensive error handling with user-friendly messages

## 🚀 Installation

### Prerequisites
- Python 3.6 or higher
- Linux operating system (tested on Ubuntu)

### Quick Setup

1. **Clone or download the files**:
   ```bash
   # Download the macro_recorder.py file to your desired directory
   ```

2. **Install system dependencies**:
   ```bash
   sudo apt update
   sudo apt install -y python3-tk python3-pip
   ```

3. **Install Python dependencies**:
   ```bash
   pip install --break-system-packages pynput
   ```

4. **Test the installation**:
   ```bash
   python3 test_app.py
   ```

5. **Run the application**:
   ```bash
   python3 macro_recorder.py
   ```

## 📖 Usage Guide

### Getting Started

1. **Launch the Application**:
   ```bash
   python3 macro_recorder.py
   ```

2. **Calibrate Your Screen** (Recommended):
   - Click the "🎯 Calibrate" button
   - Follow the on-screen instructions
   - Click the top-left and bottom-right corners of your screen
   - This ensures accurate coordinate mapping

### Recording Actions

1. **Start Recording**:
   - Click the "⏺ Record" button
   - The interface will show "🔴 Recording in progress..."
   - All mouse movements, clicks, and keyboard inputs will be captured

2. **Stop Recording**:
   - Click the "⏹ Stop Recording" button, OR
   - Press the **ESC** key at any time

### Playing Back Recordings

1. **Set Repetitions**:
   - Enter the desired number of repetitions in the "Repetitions" field
   - Default is 1

2. **Start Playback**:
   - Click the "▶ Play" button
   - The status will show "▶️ Playing back..."

3. **Stop Playback**:
   - Press the **ESC** key to stop playback immediately

### Saving and Loading

1. **Save a Recording**:
   - After recording actions, click "💾 Save Recording"
   - Choose a location and filename (`.macro` extension recommended)
   - The file includes all actions, timing, and calibration data

2. **Load a Recording**:
   - Click "📁 Load Recording"
   - Select a previously saved `.macro` file
   - The recording will be loaded and ready for playback

### Other Controls

- **🗑 Clear**: Removes all recorded actions (with confirmation)
- **Activity Log**: Shows real-time updates of all operations
- **Status Indicators**: Display current file, action count, and system status

## 🔧 Advanced Features

### Screen Calibration
The calibration feature solves coordinate mapping issues by:
- Recording your actual screen boundaries
- Calculating scaling factors
- Ensuring recorded mouse positions are accurate during playback

### File Format
Saved recordings use JSON format with the following structure:
```json
{
  "version": "1.0",
  "created": "2024-01-01T12:00:00",
  "actions": [...],
  "calibration": {
    "factor_x": 1.0,
    "factor_y": 1.0
  },
  "metadata": {
    "action_count": 150,
    "duration": 30.5
  }
}
```

### Keyboard Shortcuts
- **ESC**: Stop recording or playback immediately
- Global key detection works even when the application is not focused

## 🛠 Troubleshooting

### Common Issues

1. **Permission Errors**:
   ```bash
   # Run with proper permissions for input access
   sudo python3 macro_recorder.py
   ```

2. **Import Errors**:
   ```bash
   # Reinstall dependencies
   pip install --break-system-packages pynput
   sudo apt install python3-tk
   ```

3. **Coordinate Issues**:
   - Use the calibration feature before recording
   - Ensure you're recording on the same screen setup where you'll play back

4. **ESC Key Not Working**:
   - Make sure the application window has focus
   - Try clicking on the application window first

### Performance Tips
- For long recordings, ensure adequate disk space
- Close unnecessary applications during recording for better performance
- Use calibration for best coordinate accuracy

## 🎯 Best Practices

1. **Always Calibrate**: Run calibration before important recordings
2. **Test First**: Record a short test sequence before long recordings
3. **Save Regularly**: Save important recordings to avoid losing work
4. **Use Descriptive Names**: Name your macro files descriptively
5. **Clean Environment**: Record in a clean desktop environment for best results

## 🐛 Known Limitations

- Currently supports Linux systems (X11 environments)
- Requires proper permissions for input device access
- Some applications may block programmatic input
- Screen resolution changes require re-calibration

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Feel free to fork, modify, and improve this application. Submit pull requests for any enhancements or bug fixes.

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Ensure all dependencies are properly installed
3. Try running the test script: `python3 test_app.py`
4. Check the activity log for error messages

---

**Enjoy using Macro Recorder Pro!** 🎉
