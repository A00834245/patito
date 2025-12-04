import sys
from pathlib import Path

# Ensure the project root (the directory that contains entrega4, entrega5, etc.)
# is on sys.path so that `import entrega4...` works inside these tests.
ROOT = Path(__file__).resolve().parents[2]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)
