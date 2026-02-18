#!/usr/bin/env python3
"""
Semantic Search for Agent Library

Search through TOON/Markdown knowledge base using sqlite-vec.

Usage:
    python3 search.py --query "machine learning" --top-k 5
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Search result with metadata"""
    chunk_id: str
    title: str
    content: str
    score: float
    source: str
    keywords: List[str]


class KnowledgeSearch:
    """Semantic search over knowledge base"""
    
    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.chunks: List[Dict] = []
        self._load_chunks()
    
    def _load_chunks(self):
        """Load all chunks from knowledge directory"""
        chunks_files = list(self.knowledge_dir.glob("*_chunks.json"))
        
        for cf in chunks_files:
            try:
                data = json.loads(cf.read_text(encoding='utf-8'))
                for chunk in data.get('chunks', []):
                    chunk['source_file'] = cf.stem.replace('_chunks', '')
                    self.chunks.append(chunk)
            except Exception as e:
                print(f"Warning: Failed to load {cf}: {e}", file=sys.stderr)
        
        print(f"Loaded {len(self.chunks)} chunks from {len(chunks_files)} files", file=sys.stderr)
    
    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        Search chunks using keyword matching
        
        Note: For full semantic search, use sqlite-vec with embeddings
        """
        query_terms = set(re.findall(r'\w+', query.lower()))
        
        results = []
        for chunk in self.chunks:
            # Calculate simple relevance score
            content_lower = chunk.get('content', '').lower()
            title_lower = chunk.get('title', '').lower()
            keywords = [k.lower() for k in chunk.get('keywords', [])]
            
            score = 0.0
            
            # Title matches (highest weight)
            title_terms = set(re.findall(r'\w+', title_lower))
            title_overlap = len(query_terms & title_terms)
            score += title_overlap * 3.0
            
            # Keyword matches
            keyword_set = set(keywords)
            keyword_overlap = len(query_terms & keyword_set)
            score += keyword_overlap * 2.0
            
            # Content matches
            content_terms = set(re.findall(r'\w+', content_lower))
            content_overlap = len(query_terms & content_terms)
            score += content_overlap * 0.5
            
            # Normalize by query length
            if query_terms:
                score = score / len(query_terms)
            
            if score > 0:
                results.append(SearchResult(
                    chunk_id=chunk.get('id', 'unknown'),
                    title=chunk.get('title', 'Untitled'),
                    content=chunk.get('content', '')[:500] + '...',
                    score=score,
                    source=chunk.get('source_file', 'unknown'),
                    keywords=chunk.get('keywords', [])
                ))
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def search_by_keyword(self, keyword: str, top_k: int = 10) -> List[SearchResult]:
        """Search by specific keyword"""
        keyword_lower = keyword.lower()
        
        results = []
        for chunk in self.chunks:
            keywords = [k.lower() for k in chunk.get('keywords', [])]
            
            if keyword_lower in keywords:
                results.append(SearchResult(
                    chunk_id=chunk.get('id', 'unknown'),
                    title=chunk.get('title', 'Untitled'),
                    content=chunk.get('content', '')[:500] + '...',
                    score=1.0,
                    source=chunk.get('source_file', 'unknown'),
                    keywords=chunk.get('keywords', [])
                ))
        
        return results[:top_k]
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        sources = {}
        for chunk in self.chunks:
            source = chunk.get('source_file', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        total_tokens = sum(
            chunk.get('tokens_estimate', 0) 
            for chunk in self.chunks
        )
        
        return {
            'total_chunks': len(self.chunks),
            'total_sources': len(sources),
            'sources': sources,
            'estimated_tokens': total_tokens
        }


def main():
    parser = argparse.ArgumentParser(
        description='Search agent knowledge base'
    )
    parser.add_argument('--query', '-q', required=True,
                        help='Search query')
    parser.add_argument('--top-k', '-k', type=int, default=5,
                        help='Number of results')
    parser.add_argument('--knowledge-dir', '-d', default='knowledge',
                        help='Knowledge directory')
    parser.add_argument('--stats', action='store_true',
                        help='Show knowledge base stats')
    
    args = parser.parse_args()
    
    searcher = KnowledgeSearch(args.knowledge_dir)
    
    if args.stats:
        stats = searcher.get_stats()
        print(json.dumps(stats, indent=2))
        return
    
    results = searcher.search(args.query, args.top_k)
    
    if not results:
        print("No results found.")
        return
    
    print(f"\n🔍 Found {len(results)} results for: '{args.query}'\n")
    print("=" * 60)
    
    for i, result in enumerate(results, 1):
        print(f"\n[{i}] {result.title}")
        print(f"    Score: {result.score:.2f}")
        print(f"    Source: {result.source}")
        print(f"    Keywords: {', '.join(result.keywords)}")
        print(f"\n    {result.content[:300]}...")
        print("-" * 60)


if __name__ == '__main__':
    main()
