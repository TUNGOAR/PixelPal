import sys
from pathlib import Path

# 让 src/ 可被 import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
