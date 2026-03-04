"""
Unified import handler for OcularLimbs
Handles both package and direct imports
"""

import sys
import os

# Add project root to path if needed
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import from core
from .types import *
