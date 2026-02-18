# TOON Format Specification v0.1

> Token-Oriented Object Notation

## Overview

TOON is a compact data format designed for AI agents. It minimizes token usage while maintaining semantic structure.

## Design Goals

1. **Token Efficiency**: 30-50% fewer tokens than JSON
2. **Human Readable**: Similar to YAML/Markdown
3. **Agent Native**: Optimized for LLM context windows
4. **Schema Optional**: Can work with or without schema

## Format Rules

### 1. Document Header

```
# Document Title
@author Author Name
@created 2026-02-18T00:00:00
@chunks 42
```

### 2. Section Separator

```
---
```

### 3. Chunk Format

```
## chunk_id
  title: Section Title
  tokens: 250
  keywords: keyword1, keyword2, keyword3

Content goes here...

---
```

### 4. Indentation

- 2 spaces for metadata
- No indentation for content

### 5. Metadata Keys

| Key | Description | Example |
|-----|-------------|---------|
| `title` | Section title | `Introduction` |
| `tokens` | Estimated tokens | `250` |
| `keywords` | Comma-separated | `ai, ml, neural` |
| `summary` | Brief summary | `Overview of...` |
| `section` | Parent section | `Chapter 1` |
| `page` | Source page | `42` |

## Comparison

### JSON (312 tokens)
```json
{
  "id": "chunk_0001",
  "title": "Introduction to Machine Learning",
  "content": "Machine learning is a subset of artificial intelligence...",
  "keywords": ["machine learning", "artificial intelligence", "neural networks"],
  "tokens_estimate": 250
}
```

### TOON (187 tokens - 40% savings)
```
## chunk_0001
  title: Introduction to Machine Learning
  tokens: 250
  keywords: machine learning, artificial intelligence, neural networks

Machine learning is a subset of artificial intelligence...

---
```

## File Extension

`.toon`

## MIME Type

`application/x-toon`

## Implementation

```python
def parse_toon(content: str) -> Dict:
    """Parse TOON format to dictionary"""
    doc = {
        'title': '',
        'metadata': {},
        'chunks': []
    }
    
    sections = content.split('---')
    
    # Parse header
    header = sections[0].strip()
    lines = header.split('\n')
    
    if lines[0].startswith('# '):
        doc['title'] = lines[0][2:]
    
    for line in lines[1:]:
        if line.startswith('@'):
            key, value = line[1:].split(' ', 1)
            doc['metadata'][key] = value
    
    # Parse chunks
    for section in sections[1:]:
        if not section.strip():
            continue
        
        chunk = {'metadata': {}, 'content': ''}
        lines = section.strip().split('\n')
        
        if lines[0].startswith('## '):
            chunk['id'] = lines[0][3:]
        
        content_lines = []
        in_content = False
        
        for line in lines[1:]:
            if line.startswith('  ') and ':' in line:
                key, value = line.strip().split(': ', 1)
                chunk['metadata'][key] = value
            else:
                in_content = True
                content_lines.append(line)
        
        chunk['content'] = '\n'.join(content_lines).strip()
        doc['chunks'].append(chunk)
    
    return doc
```

## Version History

- v0.1 (2026-02-18): Initial specification

## License

MIT

---

*Designed for the Agent Age*
