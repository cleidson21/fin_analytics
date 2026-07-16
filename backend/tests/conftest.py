import sys
from unittest.mock import MagicMock

# Mock yfinance globally for all tests to avoid C++ build errors with pandas
sys.modules['yfinance'] = MagicMock()
