from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo")

@mcp.tool()
def add(x: int, y: int) -> int:
    """Add two numbers"""
    return x + y

@mcp.resource("config://app")
def get_config() -> str:
    """Get application configuration"""
    return "App configured!"

if __name__ == "__main__":
    mcp.run()
