import os
import sys

# Attempt to ensure the project root (containing `core/`) is on sys.path
# when the console script is invoked (especially in editable installs),
# because the Windows launcher sometimes runs before .pth files are read.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from .__main__ import main

def cli():
    sys.exit(main())
