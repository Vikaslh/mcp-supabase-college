# College Database MCP Server

This is an MCP server for managing a college database, including students, teachers, subjects, and marks.

## Prerequisites

- Python 3.12+
- `uv` package manager

## Installation

1. Install dependencies:
   ```bash
   uv sync
   ```

## Running the Server

To start the College Database server, run:

```bash
uv run servers/college_db.py
```

## Inspector

To test the server with the MCP Inspector:

```bash
npx -y @modelcontextprotocol/inspector uv run servers/college_db.py
```

## Features

- **Students**: List, add, and query students.
- **Teachers**: List and analyze teacher performance.
- **Subjects**: List subjects and view statistics.
- **Marks**: Manage student grades and generate report cards.
