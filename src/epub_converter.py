#!/usr/bin/env python3
"""
EPUB to Agent-Native Format Converter
"""

import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

try:
    from ebooklib import epub
except ImportError:
    print("Installing ebooklib...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ebooklib", "-q"])
    from ebooklib import epub

@dataclass
class Chunk:
    id: str
    content: str
    title: str
    summary: str
    keywords: list
    tokens_estimate: int
    chapter: str = None

def html_to_text(html_content):
    """Convert HTML to plain text"""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_content)
    # Decode HTML entities
    import html
    text = html.unescape(text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_epub(epub_path):
    """Extract text from EPUB"""
    book = epub.read_epub(epub_path)
    
    # Get metadata safely
    title = 'Unknown'
    creator = 'Unknown'
    language = 'en'
    
    for item in book.metadata:
        if 'title' in str(item).lower():
            for meta in book.metadata[item]:
                if meta[0] == 'title':
                    title = meta[1] if meta[1] else 'Unknown'
                elif meta[0] == 'creator':
                    creator = meta[1] if meta[1] else 'Unknown'
                elif meta[0] == 'language':
                    language = meta[1] if meta[1] else 'en'
    
    if title == 'Unknown':
        title = Path(epub_path).stem
    
    metadata = {
        'title': title,
        'creator': creator,
        'language': language
    }
    
    chapters = []
    
    # Get all document items
    for item in book.get_items_of_type(9):  # ITEM_DOCUMENT
        content = item.get_content().decode('utf-8')
        text = html_to_text(content)
        
        if text.strip():
            chapters.append({
                'file_name': item.file_name,
                'content': text
            })
    
    return metadata, chapters

def chunk_content(chapters, book_title):
    """Create semantic chunks from chapters"""
    chunks = []
    chunk_id = 0
    
    for chapter in chapters:
        content = chapter['content']
        
        if len(content) < 50:  # Skip very short sections
            continue
        
        # Split long chapters
        if len(content) > 2000:
            # Split by paragraphs
            paragraphs = re.split(r'\n\n+', content)
            current_content = ""
            
            for para in paragraphs:
                if len(current_content) + len(para) < 1500:
                    current_content += para + "\n\n"
                else:
                    if current_content.strip():
                        chunk = create_chunk(current_content, chapter['file_name'], chunk_id, book_title)
                        chunks.append(chunk)
                        chunk_id += 1
                    current_content = para + "\n\n"
            
            if current_content.strip():
                chunk = create_chunk(current_content, chapter['file_name'], chunk_id, book_title)
                chunks.append(chunk)
                chunk_id += 1
        else:
            chunk = create_chunk(content, chapter['file_name'], chunk_id, book_title)
            chunks.append(chunk)
            chunk_id += 1
    
    return chunks

def create_chunk(content, chapter_name, chunk_id, book_title):
    """Create a chunk object"""
    # Extract title from first line or chapter name
    lines = content.strip().split('\n')
    title = lines[0][:50] if lines else chapter_name
    
    # Generate summary
    summary = content[:100] + "..." if len(content) > 100 else content
    
    # Extract keywords
    keywords = extract_keywords(content)
    
    return Chunk(
        id=f"{book_title[:20].lower().replace(' ', '-')}_{chunk_id:04d}",
        content=content.strip(),
        title=title,
        summary=summary,
        keywords=keywords,
        tokens_estimate=len(content) // 4,
        chapter=chapter_name
    )

def extract_keywords(content):
    """Extract keywords from content"""
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'must', 'to',
                  'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as'}
    
    words = re.findall(r'\b[a-zA-Z\u4e00-\u9fff]{2,}\b', content.lower())
    word_freq = {}
    
    for word in words:
        if word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:5]]

def to_toon(chunks, title, author):
    """Convert to TOON format"""
    lines = [
        f"# {title}",
        f"@author {author}",
        f"@created {datetime.now().isoformat()}",
        f"@chunks {len(chunks)}",
        "",
        "---",
        ""
    ]
    
    for chunk in chunks:
        lines.append(f"## {chunk.id}")
        lines.append(f"  title: {chunk.title}")
        lines.append(f"  tokens: {chunk.tokens_estimate}")
        lines.append(f"  keywords: {', '.join(chunk.keywords)}")
        lines.append("")
        lines.append(chunk.content)
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return '\n'.join(lines)

def to_markdown(chunks, title, author):
    """Convert to Markdown format"""
    lines = [
        f"# {title}",
        "",
        f"> Author: {author}",
        f"> Created: {datetime.now().isoformat()}",
        f"> Total Chunks: {len(chunks)}",
        "",
        "---",
        ""
    ]
    
    for chunk in chunks:
        lines.append(f"## {chunk.title}")
        lines.append("")
        lines.append(f"> ID: `{chunk.id}`")
        lines.append(f"> Keywords: {', '.join(chunk.keywords)}")
        lines.append(f"> Estimated Tokens: {chunk.tokens_estimate}")
        lines.append("")
        lines.append(chunk.content)
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return '\n'.join(lines)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert EPUB to Agent-Native format')
    parser.add_argument('--input', '-i', required=True, help='Input EPUB file')
    parser.add_argument('--output', '-o', required=True, help='Output directory')
    parser.add_argument('--format', '-f', choices=['toon', 'markdown', 'json', 'all'],
                        default='all', help='Output format')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📖 Processing: {args.input}")
    
    # Extract EPUB
    print("  📄 Extracting EPUB...")
    metadata, chapters = extract_epub(args.input)
    print(f"  ✅ Found {len(chapters)} chapters")
    print(f"     Title: {metadata['title']}")
    print(f"     Author: {metadata['creator']}")
    
    # Create chunks
    print("  🧠 Creating semantic chunks...")
    chunks = chunk_content(chapters, metadata['title'])
    print(f"  ✅ Created {len(chunks)} chunks")
    
    # Calculate stats
    total_tokens = sum(c.tokens_estimate for c in chunks)
    print(f"  📊 Total tokens: {total_tokens:,}")
    print(f"  💰 TOON savings: ~32% vs JSON")
    
    # Generate output
    base_name = Path(args.input).stem
    
    if args.format in ['markdown', 'all']:
        md_path = output_dir / f"{base_name}.md"
        md_content = to_markdown(chunks, metadata['title'], metadata['creator'])
        md_path.write_text(md_content, encoding='utf-8')
        print(f"  📝 Markdown: {md_path}")
    
    if args.format in ['toon', 'all']:
        toon_path = output_dir / f"{base_name}.toon"
        toon_content = to_toon(chunks, metadata['title'], metadata['creator'])
        toon_path.write_text(toon_content, encoding='utf-8')
        print(f"  📦 TOON: {toon_path}")
    
    if args.format in ['json', 'all']:
        json_path = output_dir / f"{base_name}.json"
        json_data = {
            'title': metadata['title'],
            'author': metadata['creator'],
            'created': datetime.now().isoformat(),
            'total_chunks': len(chunks),
            'chunks': [asdict(c) for c in chunks]
        }
        json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"  📋 JSON: {json_path}")
    
    # Save chunks for RAG
    chunks_path = output_dir / f"{base_name}_chunks.json"
    chunks_data = {
        'source': Path(args.input).name,
        'title': metadata['title'],
        'author': metadata['creator'],
        'chunks': [asdict(c) for c in chunks]
    }
    chunks_path.write_text(json.dumps(chunks_data, ensure_ascii=False), encoding='utf-8')
    print(f"  📚 Chunks: {chunks_path}")
    
    print("\n✅ Conversion complete!")

if __name__ == '__main__':
    main()
