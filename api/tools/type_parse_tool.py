"""Type parsing and safe conversion utilities."""

from datetime import datetime
from typing import Any, Optional


class TypeParseTool:
    """Utility class for safe data type conversions and date parsing."""

    @staticmethod
    def to_int(val: Any, default: int = 0) -> int:
        """Safely converts a value (which may be '-', None, or string) to an int."""
        if val is None or val == "-":
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def to_float(val: Any, default: float = 0.0) -> float:
        """Safely converts a value (which may be '-', None, or string) to a float."""
        if val is None or val == "-":
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def parse_dt(val: Any) -> Optional[datetime]:
        """Safely parses an ISO datetime string or returns existing datetime object."""
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
            except Exception:
                pass
        return None


# Direct aliases
to_int = TypeParseTool.to_int
to_float = TypeParseTool.to_float
parse_dt = TypeParseTool.parse_dt
