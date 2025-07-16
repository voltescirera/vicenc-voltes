#!/usr/bin/env python3
"""
Simple test script for the Macro Recorder application
"""

try:
    print("Testing imports...")
    import tkinter as tk
    print("✅ tkinter imported successfully")
    
    import pynput
    print("✅ pynput imported successfully")
    
    from macro_recorder import MacroRecorder
    print("✅ MacroRecorder imported successfully")
    
    print("\n🎉 All dependencies are working correctly!")
    print("The Macro Recorder application is ready to use.")
    print("\nTo run the application, execute:")
    print("python3 macro_recorder.py")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install missing dependencies using:")
    print("pip install --break-system-packages pynput")
    
except Exception as e:
    print(f"❌ Error: {e}")