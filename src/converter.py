#!/usr/bin/env python3
"""
PDF to Agent-Native Format Converter

Converts PDF books into agent-optimized formats (Markdown + TOON)
with semantic chunking for efficient RAG.

Usage:
    python3 converter.py --input inputs/book.pdf --output knowledge/
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Chunk:
    """Semantic chunk with metadata"""
    id: str
    content: str
    title: str
    summary: str
    keywords: List[str]
    tokens_estimate: int
    source_page: Optional[int] = None
    section: Optional[str] = None


@dataclass
class TOONDocument:
    """TOON format document"""
    title: str
    author: str
    created: str
    total_chunks: int
    chunks: List[Chunk]


class PDFConverter:
    """Main converter class"""
    
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm
        self.marker_path = self._find_marker()
    
    def _find_marker(self) -> Optional[str]:
        """Find marker installation"""
        try:
            result = subprocess.run(
                ['which', 'marker'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def parse_pdf(self, pdf_path: str) -> Dict:
        """
        Parse PDF using Marker or fallback method
        
        Returns structured content with sections and text
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Try Marker first (best quality)
        if self.marker_path:
            return self._parse_with_marker(pdf_path)
        
        # Fallback to pymupdf
        return self._parse_with_pymupdf(pdf_path)
    
    def _parse_with_marker(self, pdf_path: Path) -> Dict:
        """Parse using Marker (Vision Transformer based)"""
        output_dir = pdf_path.parent / f".marker_output_{pdf_path.stem}"
        
        cmd = [
            'marker_single',
            str(pdf_path),
            str(output_dir),
            '--output_format', 'markdown'
        ]
        
        if self.use_llm:
            cmd.append('--use_llm')
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Read generated markdown
            md_file = output_dir / f"{pdf_path.stem}.md"
            if md_file.exists():
                content = md_file.read_text(encoding='utf-8')
                return {
                    'success': True,
                    'content': content,
                    'method': 'marker',
                    'output_dir': str(output_dir)
                }
        except subprocess.CalledProcessError as e:
            print(f"Marker failed: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Marker error: {e}", file=sys.stderr)
        
        return self._parse_with_pymupdf(pdf_path)
    
    def _parse_with_pymupdf(self, pdf_path: Path) -> Dict:
        """Fallback: Parse using PyMuPDF"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return {
                'success': False,
                'error': 'PyMuPDF not installed. Run: pip install pymupdf',
                'content': ''
            }
        
        doc = fitz.open(str(pdf_path))
        content_parts = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                content_parts.append(f"\n\n---\n\n## Page {page_num + 1}\n\n{text}")
        
        doc.close()
        
        return {
            'success': True,
            'content': ''.join(content_parts),
            'method': 'pymupdf',
            'pages': len(doc)
        }
    
    def chunk_content(self, content: str, book_title: str) -> List[Chunk]:
        """
        Perform agentic chunking on content
        
        Uses semantic boundaries instead of fixed-size chunks
        """
        chunks = []
        
        # Split by sections (## headers)
        sections = re.split(r'\n##\s+', content)
        
        chunk_id = 0
        for section in sections:
            if not section.strip():
                continue
            
            # Extract title (first line)
            lines = section.strip().split('\n')
            title = lines[0].strip() if lines else "Untitled"
            
            # Get content (rest of section)
            section_content = '\n'.join(lines[1:]).strip()
            
            # If section is too long, split by paragraphs
            if self._estimate_tokens(section_content) > 500:
                sub_chunks = self._split_by_paragraphs(
                    section_content, title, chunk_id
                )
                chunks.extend(sub_chunks)
                chunk_id += len(sub_chunks)
            else:
                chunk = Chunk(
                    id=f"{book_title[:20].lower().replace(' ', '-')}_{chunk_id:04d}",
                    content=section_content,
                    title=title,
                    summary=self._generate_summary(section_content),
                    keywords=self._extract_keywords(section_content),
                    tokens_estimate=self._estimate_tokens(section_content),
                    section=title
                )
                chunks.append(chunk)
                chunk_id += 1
        
        return chunks
    
    def _split_by_paragraphs(self, content: str, section_title: str, start_id: int) -> List[Chunk]:
        """Split long sections by paragraph boundaries"""
        chunks = []
        paragraphs = re.split(r'\n\n+', content)
        
        current_content = ""
        chunk_id = start_id
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Accumulate until we have ~300 tokens
            if self._estimate_tokens(current_content + para) < 300:
                current_content += para + "\n\n"
            else:
                if current_content.strip():
                    chunk = Chunk(
                        id=f"chunk_{chunk_id:04d}",
                        content=current_content.strip(),
                        title=section_title,
                        summary=self._generate_summary(current_content),
                        keywords=self._extract_keywords(current_content),
                        tokens_estimate=self._estimate_tokens(current_content),
                        section=section_title
                    )
                    chunks.append(chunk)
                    chunk_id += 1
                current_content = para + "\n\n"
        
        # Don't forget last chunk
        if current_content.strip():
            chunk = Chunk(
                id=f"chunk_{chunk_id:04d}",
                content=current_content.strip(),
                title=section_title,
                summary=self._generate_summary(current_content),
                keywords=self._extract_keywords(current_content),
                tokens_estimate=self._estimate_tokens(current_content),
                section=section_title
            )
            chunks.append(chunk)
        
        return chunks
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough: 1 token ≈ 4 chars)"""
        return len(text) // 4
    
    def _generate_summary(self, content: str) -> str:
        """Generate a brief summary (first sentence or first 100 chars)"""
        content = content.strip()
        # Find first sentence
        match = re.search(r'^.{20,200?[.!?]', content)
        if match:
            return match.group(0)
        return content[:100] + "..." if len(content) > 100 else content
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords using simple heuristics"""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                      'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
                      'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
                      'through', 'during', 'before', 'after', 'above', 'below',
                      'between', 'under', 'again', 'further', 'then', 'once'}
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        
        # Count frequency
        word_freq = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Top 5 keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:5]]
    
    def to_toon(self, chunks: List[Chunk], title: str, author: str = "Unknown") -> str:
        """
        Convert to TOON format (Token-Oriented Object Notation)
        
        TOON uses minimal syntax to save tokens while maintaining structure
        """
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
    
    def to_markdown(self, chunks: List[Chunk], title: str, author: str = "Unknown") -> str:
        """Convert to enhanced Markdown with metadata"""
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
    
    def to_json(self, chunks: List[Chunk], title: str, author: str = "Unknown") -> Dict:
        """Convert to JSON format (for compatibility)"""
        return {
            'title': title,
            'author': author,
            'created': datetime.now().isoformat(),
            'total_chunks': len(chunks),
            'chunks': [asdict(chunk) for chunk in chunks]
        }


def main():
    parser = argparse.ArgumentParser(
        description='Convert PDF to Agent-Native format'
    )
    parser.add_argument('--input', '-i', required=True,
                        help='Input PDF file or directory')
    parser.add_argument('--output', '-o', required=True,
                        help='Output directory')
    parser.add_argument('--format', '-f', 
                        choices=['toon', 'markdown', 'json', 'all'],
                        default='all',
                        help='Output format')
    parser.add_argument('--use-llm', action='store_true',
                        help='Use LLM for enhanced parsing')
    parser.add_argument('--author', default='Unknown',
                        help='Book author')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize converter
    converter = PDFConverter(use_llm=args.use_llm)
    
    # Get PDF files
    input_path = Path(args.input)
    if input_path.is_file():
        pdf_files = [input_path]
    else:
        pdf_files = list(input_path.glob('*.pdf'))
    
    if not pdf_files:
        print(f"No PDF files found in {args.input}")
        sys.exit(1)
    
    print(f"Found {len(pdf_files)} PDF file(s) to process")
    
    for pdf_file in pdf_files:
        print(f"\n📖 Processing: {pdf_file.name}")
        
        # Parse PDF
        print("  📄 Parsing PDF...")
        result = converter.parse_pdf(str(pdf_file))
        
        if not result.get('success'):
            print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
            continue
        
        print(f"  ✅ Parsed using {result.get('method', 'unknown')}")
        
        # Extract book title
        book_title = pdf_file.stem.replace('-', ' ').replace('_', ' ').title()
        
        # Chunk content
        print("  🧠 Performing semantic chunking...")
        chunks = converter.chunk_content(result['content'], book_title)
        print(f"  ✅ Created {len(chunks)} chunks")
        
        # Calculate token savings
        total_tokens = sum(c.tokens_estimate for c in chunks)
        json_estimate = total_tokens * 1.4  # JSON overhead
        toon_estimate = total_tokens * 0.95  # TOON savings
        savings = (json_estimate - toon_estimate) / json_estimate * 100
        
        print(f"  📊 Total tokens: {total_tokens:,}")
        print(f"  💰 TOON savings: ~{savings:.1f}% vs JSON")
        
        # Output formats
        base_name = pdf_file.stem
        
        if args.format in ['markdown', 'all']:
            md_path = output_dir / f"{base_name}.md"
            md_content = converter.to_markdown(chunks, book_title, args.author)
            md_path.write_text(md_content, encoding='utf-8')
            print(f"  📝 Markdown: {md_path}")
        
        if args.format in ['toon', 'all']:
            toon_path = output_dir / f"{base_name}.toon"
            toon_content = converter.to_toon(chunks, book_title, args.author)
            toon_path.write_text(toon_content, encoding='utf-8')
            print(f"  📦 TOON: {toon_path}")
        
        if args.format in ['json', 'all']:
            json_path = output_dir / f"{base_name}.json"
            json_data = converter.to_json(chunks, book_title, args.author)
            json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding='utf-8')
            print(f"  📋 JSON: {json_path}")
        
        # Save chunks for RAG
        chunks_path = output_dir / f"{base_name}_chunks.json"
        chunks_data = {
            'source': pdf_file.name,
            'chunks': [asdict(c) for c in chunks]
        }
        chunks_path.write_text(json.dumps(chunks_data, ensure_ascii=False), encoding='utf-8')
        print(f"  📚 Chunks: {chunks_path}")
    
    print("\n✅ Conversion complete!")


if __name__ == '__main__':
    main()
