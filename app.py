import sys
from pathlib import Path
import runpy

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

target_app = PROJECT_ROOT / "src" / "resume_shortlister" / "ui" / "streamlit_app.py"
runpy.run_path(str(target_app), run_name="__main__")
