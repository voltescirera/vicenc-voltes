#!/bin/bash
# Macro Recorder Pro Launcher Script

echo "🚀 Starting Macro Recorder Pro..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if required dependencies are available
if ! python3 -c "import tkinter, pynput" &> /dev/null; then
    echo "❌ Missing dependencies. Installing..."
    echo "📦 Installing tkinter and pynput..."
    
    # Install system dependencies
    sudo apt update && sudo apt install -y python3-tk python3-pip
    
    # Install Python dependencies
    pip install --break-system-packages pynput
    
    echo "✅ Dependencies installed successfully!"
fi

# Run the application
echo "🎯 Launching Macro Recorder Pro..."
python3 macro_recorder.py

echo "👋 Macro Recorder Pro closed."