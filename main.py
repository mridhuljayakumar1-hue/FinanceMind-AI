import os
import sys
import subprocess
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Path to streamlit UI script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "ui", "streamlit_app.py")
    
    # Check if app path exists
    if not os.path.exists(app_path):
        print(f"Error: UI script not found at {app_path}")
        sys.exit(1)
        
    print("==================================================")
    print("      Launching FinanceMind AI Dashboard          ")
    print("==================================================")
    print(f"Running Streamlit app at: {app_path}")
    print("Press Ctrl+C to stop the server.")
    
    try:
        # Run streamlit as a module inside the current python executable
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])
    except KeyboardInterrupt:
        print("\nStopping FinanceMind AI Dashboard...")

if __name__ == "__main__":
    main()
