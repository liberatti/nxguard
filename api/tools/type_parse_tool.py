"""Type parsing and safe conversion utilities."""

from datetime import datetime
from typing import Any, Optional
from config import COMMON_LOG_FORMATS


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

    @staticmethod
    def parse_logtime(time_str: Optional[str]) -> datetime:
        """Parses timestamp strings into datetime objects with fast-path ISO 8601 support."""
        if not time_str:
            return datetime.now()

        # Fast path for ISO 8601 strings (standard in Nginx/ModSecurity JSON logs)
        if "T" in time_str or (
            len(time_str) >= 10 and time_str[4] == "-" and time_str[7] == "-"
        ):
            try:
                clean_str = time_str.replace("Z", "+00:00")
                return datetime.fromisoformat(clean_str)
            except (ValueError, TypeError):
                pass

        for fmt in COMMON_LOG_FORMATS:
            try:
                return datetime.strptime(time_str, fmt)
            except (ValueError, TypeError):
                continue
        return datetime.now()


# Direct aliases
to_int = TypeParseTool.to_int
to_float = TypeParseTool.to_float
parse_dt = TypeParseTool.parse_dt
parse_logtime = TypeParseTool.parse_logtime

