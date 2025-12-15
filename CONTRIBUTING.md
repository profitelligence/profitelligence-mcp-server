# Contributing to Profitelligence MCP Server

Thank you for your interest in contributing! This document provides guidelines for contributing to the Profitelligence MCP Server.

## Code of Conduct

Be respectful, inclusive, and constructive. We're building tools for the financial intelligence community, and we welcome contributors from all backgrounds.

## Getting Started

### Prerequisites

- Python 3.10+
- Docker (optional, for containerized development)
- A Profitelligence API key (get one at [profitelligence.com/account/api-keys](https://profitelligence.com/account/api-keys))

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/profitelligence/mcp-server.git
cd mcp-server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env with your API key

# Run the server
python -m src.server
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_tools.py -v
```

## How to Contribute

### Reporting Issues

Before creating an issue:
1. Search existing issues to avoid duplicates
2. Use the issue templates when available
3. Include reproduction steps for bugs

**Bug Reports Should Include:**
- Python version and OS
- MCP client being used (Claude Desktop, Claude Code, etc.)
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or error messages

### Suggesting Features

We welcome feature suggestions! Please:
1. Check if the feature is already on our [Roadmap](README.md#roadmap)
2. Open a discussion or issue describing:
   - The problem you're trying to solve
   - Your proposed solution
   - Alternative approaches you've considered

### Submitting Pull Requests

1. **Fork and Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

2. **Write Quality Code**
   - Follow PEP 8 style guidelines
   - Add type hints to function signatures
   - Write docstrings for public functions
   - Keep changes focused and atomic

3. **Test Your Changes**
   ```bash
   # Run tests
   pytest

   # Check formatting
   ruff check src/
   ruff format --check src/
   ```

4. **Commit with Clear Messages**
   ```
   feat: add new insider clustering tool
   fix: handle empty API response in FRED tool
   docs: update authentication section
   refactor: simplify cache key generation
   ```

5. **Open a Pull Request**
   - Reference any related issues
   - Describe what changes you made and why
   - Include testing instructions
   - Add screenshots for UI changes (if applicable)

## Development Guidelines

### Project Structure

```
mcp/
├── src/
│   ├── server.py           # FastMCP server entry point
│   ├── tools/              # MCP tool implementations
│   │   ├── mcp_tools.py    # Current tool definitions (v3)
│   │   └── market_data.py  # Legacy tools (v1)
│   ├── data_sources/       # API client wrappers
│   ├── intelligence/       # Analysis modules
│   └── utils/              # Shared utilities
├── tests/                  # Test files
└── docs/                   # Documentation
```

### Adding a New Tool

1. **Define the tool in `src/tools/mcp_tools.py`:**
   ```python
   @mcp.tool()
   async def my_new_tool(
       param1: str,
       param2: int = 10
   ) -> str:
       """
       Brief description of what the tool does.

       Args:
           param1: Description of param1
           param2: Description of param2 (default: 10)

       Returns:
           Description of return value

       Note: Include any disclaimers or usage notes
       """
       # Implementation
       pass
   ```

2. **Add data source if needed** in `src/data_sources/`

3. **Write tests** in `tests/`

4. **Update README.md** with tool documentation

### Code Style

- **Type hints**: Use them for all function parameters and returns
- **Docstrings**: Google style, include Args, Returns, and Raises sections
- **Error handling**: Use specific exceptions, provide helpful error messages
- **Logging**: Use the configured logger, appropriate log levels

### API Response Handling

Our backend returns:
- **CSV** (pipe-delimited): For tabular data (OHLC, insider trades, etc.)
- **JSON**: For complex nested structures (analytics, 8K summaries)

Always handle both formats appropriately and provide clear error messages for API failures.

## Release Process

Releases are managed by maintainers:

1. Version bump in `pyproject.toml`
2. Update CHANGELOG.md
3. Create GitHub release with tag
4. Docker image published automatically via CI

## Getting Help

- **Documentation**: [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/profitelligence/mcp-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/profitelligence/mcp-server/discussions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
