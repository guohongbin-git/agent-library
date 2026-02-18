# Agent Library 📚

> PDF to Agent-Native Format Conversion Pipeline

Transform PDF books into Agent-native formats (TOON/Markdown) for efficient AI learning.

## What This Does

```
PDF Books → High-Fidelity Parsing → Semantic Chunking → TOON Format → Agent Knowledge Base
```

## Project Structure

```
agent-library/
├── inputs/          # PDF files to process
├── src/             # Conversion scripts
├── knowledge/       # Generated TOON/Markdown files
├── memory/          # Learning logs
└── .github/workflows/ # Agentic automation
```

## Quick Start

```bash
# 1. Add PDF to inputs
cp your-book.pdf inputs/

# 2. Run conversion
python3 src/converter.py --input inputs/your-book.pdf --output knowledge/

# 3. Search knowledge
python3 src/search.py --query "concept from book"
```

## Features

- 📖 **PDF Parsing**: Marker-based high-fidelity extraction
- 🧠 **Semantic Chunking**: Agentic chunking for 25-40% better retrieval
- 📦 **TOON Format**: 30-50% token savings vs JSON
- 🔍 **Local RAG**: SQLite + sqlite-vec for fast search
- 🤖 **MCP Compatible**: Expose as MCP tools

## Tech Stack

| Component | Technology |
|-----------|------------|
| PDF Parser | Marker / MinerU |
| Format | TOON / Markdown |
| Chunking | Agentic (LLM-based) |
| Vector DB | SQLite + sqlite-vec |
| Protocol | MCP (Model Context Protocol) |

## Status

🚧 Under active development

## Author

**money-maker-ai** - Building knowledge infrastructure for agents

## License

MIT
