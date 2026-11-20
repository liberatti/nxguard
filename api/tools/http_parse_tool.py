"""HTTP parsing, header filtering, status code resolution, and user agent extraction utilities."""

from functools import lru_cache
from typing import Any, Dict, List, Optional

try:
    from user_agents import parse as ua_parse
except ImportError:
    ua_parse = None

from config import MASKED_HEADERS_SET, UA_REGEX
from api.tools.type_parse_tool import to_int


class HttpParseTool:
    """Utility class for parsing HTTP headers, user agents, and status codes."""

    @staticmethod
    @lru_cache(maxsize=100)
    def resolve_status_code(code: Any) -> str:
        """Categorizes HTTP status codes into action categories (blocked, warn, allowed)."""
        c = to_int(code, default=200)
        if c == 403:
            return "blocked"
        elif c in (404, 401, 500, 502, 503, 504):
            return "warn"
        elif c in (200, 201, 204, 301, 302, 304):
            return "allowed"
        return "allowed"

    @staticmethod
    @lru_cache(maxsize=4096)
    def parse_agent(user_agent_str: Optional[str]) -> Dict[str, Any]:
        """Parses user agent string with LRU caching for high performance."""
        if not user_agent_str or user_agent_str == "-":
            return {"family": "Unknown", "major": 0, "minor": 0}

        if ua_parse is not None:
            try:
                ua = ua_parse(user_agent_str)
                return {
                    "family": ua.browser.family or "Unknown",
                    "major": (
                        int(ua.browser.version[0])
                        if ua.browser.version and len(ua.browser.version) > 0
                        else 0
                    ),
                    "minor": (
                        int(ua.browser.version[1])
                        if ua.browser.version and len(ua.browser.version) > 1
                        else 0
                    ),
                }
            except Exception:
                pass

        try:
            family = "Unknown"
            major = 0
            minor = 0
            match = UA_REGEX.search(user_agent_str)
            if match:
                family = match.group(1)
                major = int(match.group(2))
                minor = int(match.group(3)) if match.group(3) else 0
            elif "Mozilla" in user_agent_str:
                family = "Mozilla"
            return {"family": family, "major": major, "minor": minor}
        except Exception:
            return {"family": "Unknown", "major": 0, "minor": 0}

    @staticmethod
    def parse_headers(headers: Any) -> List[Dict[str, str]]:
        """Parses, normalizes, and filters masked sensitive headers into an array of name-content mappings."""
        if not headers:
            return []
        if isinstance(headers, dict):
            return [
                {"name": str(k), "content": str(v)}
                for k, v in headers.items()
                if str(k).lower() not in MASKED_HEADERS_SET
            ]
        if isinstance(headers, list):
            result = []
            for h in headers:
                if isinstance(h, dict):
                    name = str(h.get("name", ""))
                    if name.lower() not in MASKED_HEADERS_SET:
                        content = str(h.get("content") or h.get("value") or "")
                        result.append({"name": name, "content": content})
            return result
        return []


# Direct aliases
resolve_status_code = HttpParseTool.resolve_status_code
parse_agent = HttpParseTool.parse_agent
parse_headers = HttpParseTool.parse_headers
