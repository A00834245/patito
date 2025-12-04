import sys
from pathlib import Path

# Ensure the project root (the directory that contains `entrega3` and `entrega4`)
# is on sys.path so that `import entrega3...` works inside tests.
ROOT = Path(__file__).resolve().parents[2]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)
