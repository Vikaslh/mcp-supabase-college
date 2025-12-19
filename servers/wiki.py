from mcp.server.fastmcp import FastMCP
import requests
from urllib.parse import quote

mcp = FastMCP("WikiServer")

@mcp.tool()
def add(x: int, y: int) -> int:
    """Add two numbers"""
    return x + y

@mcp.tool()
def wikipedia_summary(title: str, sentences: int = 2) -> str:
    """Return a short summary from Wikipedia for a page title."""
    if not title:
        return "No title provided."
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        extract = data.get("extract")
        if not extract:
            return "No summary available for that page."
        if sentences <= 0:
            return extract
        parts = extract.split(". ")
        summary = ". ".join(parts[:sentences]).strip()
        if not summary.endswith("."):
            summary += "."
        return summary
    except requests.HTTPError as e:
        return f"Wikipedia HTTP error: {e}"
    except Exception as e:
        return f"Error fetching Wikipedia page: {e}"

@mcp.resource("config://app")
def get_config() -> str:
    """Get application configuration"""
    return "App configured!"

if __name__ == "__main__":
    mcp.run()
