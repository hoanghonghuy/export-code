import sys

# For backward compatibility: delegate to core.__main__
from .__main__ import main

if __name__ == "__main__":
    sys.exit(main())
