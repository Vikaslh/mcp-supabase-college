# College Database MCP Server (Supabase Edition)

This project provides Model Context Protocol (MCP) servers for managing a college database (backed by Supabase) and a simple Wikipedia tool.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) (for Python dependency management)
- Node.js & npm (for the MCP Inspector)
- A Supabase project with credentials

## Setup

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Environment Configuration**:
   Create a `.env` file in the root directory with your Supabase credentials:
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

3. **Database Initialization**:
   If starting from scratch, create the tables in your Supabase SQL Editor using `setup_database.sql`, then populate the data:
   ```bash
   uv run upload_data.py
   ```

## Available Servers

### 1. College Database Server (Supabase)
Manages students, teachers, subjects, and marks.

**Run locally:**
```bash
uv run servers/college_supabase.py
```

**Features:**
- **Students**: List, add, and query students.
- **Teachers**: List and analyze teacher performance.
- **Subjects**: List subjects and view statistics.
- **Marks**: Update grades and generate report cards.
- **Resources**: `college://students`, `college://teachers`, `college://subjects`.

### 2. Wiki Server (Demo)
A simple tool to fetch Wikipedia summaries.

**Run locally:**
```bash
uv run servers/wiki.py
```

## Testing with MCP Inspector

You can inspect and test the tools interactively using the MCP Inspector:

```bash
npx -y @modelcontextprotocol/inspector uv run servers/college_supabase.py
```

## Configuration for Claude Desktop

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "CollegeSupabase": {
      "command": "/path/to/uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-server-demo",
        "run",
        "servers/college_supabase.py"
      ]
    },
    "WikiServer": {
      "command": "/path/to/uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-server-demo",
        "run",
        "servers/wiki.py"
      ]
    }
  }
}
```
*Note: Replace `/path/to/uv` and `/absolute/path/to/...` with your actual paths.*
