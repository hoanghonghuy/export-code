import sys

# For backward compatibility: delegate to core.__main__
from core.__main__ import main

# Note: DEFAULT_EXCLUDE_DIRS is now managed in core/utils.py

if __name__ == "__main__":
    sys.exit(main())
