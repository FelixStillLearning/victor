"""Package entrypoint when invoked via `python -m victor`."""

import sys
from victor.cli.app import main

if __name__ == "__main__":
    sys.exit(main())
