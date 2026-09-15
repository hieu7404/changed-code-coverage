"""Support ``python -m tc1`` using the same CLI as the console script."""

from tc1.cli import main

raise SystemExit(main())
