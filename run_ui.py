import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    app_path = Path(__file__).parent / "src" / "resume_shortlister" / "ui" / "streamlit_app.py"
    print(f"Launching Streamlit Shortlisting Dashboard from {app_path} ...")
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    subprocess.run(cmd)
