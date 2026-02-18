# Agent Library CI/CD Pipeline

This workflow automatically processes PDF files and maintains the knowledge base.

## Trigger

- On push to `inputs/` directory
- On schedule (daily at 00:00 UTC)
- Manual dispatch

## Steps

1. **Detect new PDFs**: Scan inputs/ for new files
2. **Convert**: Run converter.py on each PDF
3. **Index**: Update vector index
4. **Commit**: Push generated files to knowledge/
5. **Report**: Generate daily status report

## Configuration

Set these secrets in repository settings:

- `OPENAI_API_KEY` (optional, for LLM-enhanced parsing)
- `ANTHROPIC_API_KEY` (optional, for semantic chunking)

## Manual Trigger

```bash
gh workflow run agent-pipeline.yml
```
