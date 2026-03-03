import os
import sys

# Attempt to ensure the project root (containing `core/`) is on sys.path
# when the console script is invoked, which may run via a bundled .exe that
# doesn't process editable .pth files.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Delegate to the real entry point in core
from core.__main__ import main

def cli():
    sys.exit(main())
