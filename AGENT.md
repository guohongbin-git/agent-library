# Agent Instruction Manual (AIM)

@meta
id: agent-library
version: 1.2.0
type: knowledge_ingestion
entrypoint: src/converter.py

@capabilities
[
  "pdf_parsing",
  "semantic_chunking",
  "format_conversion"
]

@formats
input: [.pdf]
output: [.toon, .md, .json]

@interface
## CLI: Convert Book
`python3 src/converter.py --input <path> --output <dir> --format toon`

## CLI: Search Knowledge
`python3 src/search.py --query <text>`

@data_structure
## TOON Format (.toon)
- Header: `@meta` tags
- Chunks: Separated by `---`
- Fields: `title`, `tokens`, `keywords`, `content`

@dependencies
- marker-pdf (optional, for high-fidelity)
- pymupdf (fallback)
