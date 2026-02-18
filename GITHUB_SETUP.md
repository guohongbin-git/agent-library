# GitHub Setup Instructions

## Create Repository

Run these commands to publish to GitHub:

```bash
# Navigate to project
cd ~/agent-library

# Create GitHub repo (requires GitHub CLI: gh)
gh repo create agent-library --public --source=. --remote=origin --push

# Or manual setup:
# 1. Go to https://github.com/new
# 2. Create repo named "agent-library"
# 3. Run:
git remote add origin https://github.com/YOUR_USERNAME/agent-library.git
git push -u origin master
```

## Repository Description

```
📚 PDF to Agent-Native Format Converter - Transform books into AI-optimized TOON/Markdown with semantic chunking
```

## Topics (Tags)

```
ai, llm, pdf, rag, knowledge-base, semantic-search, openclaw, agent, mcp, toon-format
```

## Post-Creation

1. **Add sample PDF** (optional):
   ```bash
   # Add a small test PDF to inputs/
   # Run conversion
   python3 src/converter.py -i inputs/sample.pdf -o knowledge/
   git add knowledge/
   git commit -m "docs: add sample conversion"
   git push
   ```

2. **Enable GitHub Pages** (optional):
   - Settings → Pages → Source: main branch
   - Access docs at: https://YOUR_USERNAME.github.io/agent-library/

3. **Add badges to README**:
   ```markdown
   ![GitHub stars](https://img.shields.io/github/stars/YOUR_USERNAME/agent-library)
   ![GitHub license](https://img.shields.io/github/license/YOUR_USERNAME/agent-library)
   ```

## Share

Once published, share:
- On Moltbook: Post about the project
- On Twitter/X: Share with #AI #LLM #OpenSource
- On Discord: OpenClaw community

---

*Happy publishing! 🦞*
