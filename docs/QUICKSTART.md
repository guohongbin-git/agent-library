# Agent Library - Quick Start Guide

## Installation

```bash
# Clone repository
git clone https://github.com/your-username/agent-library.git
cd agent-library

# Install dependencies
pip install -r requirements.txt

# Optional: Install Marker for better PDF parsing
# pip install marker-pdf
```

## Basic Usage

### 1. Convert a PDF

```bash
# Add your PDF
cp ~/my-book.pdf inputs/

# Convert to all formats
python3 src/converter.py --input inputs/my-book.pdf --output knowledge/

# Or specify format
python3 src/converter.py -i inputs/my-book.pdf -o knowledge/ -f toon
```

### 2. Search Knowledge

```bash
# Search for concepts
python3 src/search.py --query "machine learning" --top-k 5

# View stats
python3 src/search.py --stats
```

### 3. Use with MCP

```python
# In Claude Desktop or other MCP client
# Add to config:
{
  "mcpServers": {
    "agent-library": {
      "command": "python3",
      "args": ["/path/to/agent-library/src/mcp_server.py"]
    }
  }
}
```

## Output Formats

### TOON (Recommended)
- 30-50% token savings vs JSON
- Optimized for LLM context windows
- Best for large documents

### Markdown
- Human readable
- Good for debugging
- Git-friendly

### JSON
- Standard format
- Easy integration
- Full metadata

## Project Structure

```
agent-library/
├── inputs/          # Put PDFs here
├── src/
│   ├── converter.py # PDF conversion
│   ├── search.py    # Knowledge search
│   └── mcp_server.py # MCP interface
├── knowledge/       # Generated files
├── memory/          # Logs
├── docs/
│   └── TOON_SPEC.md # Format spec
└── examples/        # Usage examples
```

## Tips

1. **Use descriptive filenames** for PDFs
2. **Check chunk count** after conversion
3. **Review generated TOON** files
4. **Run search --stats** to monitor growth

## Troubleshooting

### PDF won't parse
- Try `--use-llm` flag for complex layouts
- Check if PDF is password-protected
- Ensure file is not corrupted

### Search returns nothing
- Run `--stats` to verify chunks exist
- Check knowledge directory for files
- Verify JSON format is valid

### Token estimates seem wrong
- Estimates are approximate (4 chars ≈ 1 token)
- Actual usage varies by model
- Use TOON for best efficiency

---

*Need help? Open an issue on GitHub!*
