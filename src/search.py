#!/usr/bin/env python3
"""
Semantic Search for Agent Library
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class SearchResult:
    chunk_id: str
    title: str
    content: str
    score: float
    source: str
    keywords: List[str]


class KnowledgeSearch:
    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.chunks: List[Dict] = []
        self._load_chunks()
    
    def _load_chunks(self):
        chunks_files = list(self.knowledge_dir.glob("*_chunks.json"))
        for cf in chunks_files:
            try:
                data = json.loads(cf.read_text(encoding='utf-8'))
                for chunk in data.get('chunks', []):
                    chunk['source_file'] = cf.stem.replace('_chunks', '')
                    self.chunks.append(chunk)
            except Exception as e:
                print(f"Warning: {cf}: {e}", file=sys.stderr)
        print(f"Loaded {len(self.chunks)} chunks", file=sys.stderr)
    
    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        query_terms = set(re.findall(r'\w+', query.lower()))
        results = []
        
        for chunk in self.chunks:
            content = chunk.get('content', '').lower()
            title = chunk.get('title', '').lower()
            keywords = [k.lower() for k in chunk.get('keywords', [])]
            
            score = 0.0
            score += len(query_terms & set(re.findall(r'\w+', title))) * 3.0
            score += len(query_terms & set(keywords)) * 2.0
            score += len(query_terms & set(re.findall(r'\w+', content))) * 0.5
            
            if query_terms:
                score /= len(query_terms)
            
            if score > 0:
                results.append(SearchResult(
                    chunk_id=chunk.get('id', 'unknown'),
                    title=title,
                    content=chunk.get('content', '')[:500],
                    score=score,
                    source=chunk.get('source_file', 'unknown'),
                    keywords=keywords
                ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def get_stats(self) -> Dict:
        sources = {}
        for chunk in self.chunks:
            src = chunk.get('source_file', 'unknown')
            sources[src] = sources.get(src, 0) + 1
        
        return {
            'total_chunks': len(self.chunks),
            'total_sources': len(sources),
            'sources': sources,
            'estimated_tokens': sum(c.get('tokens_estimate', 0) for c in self.chunks)
        }


def main():
    parser = argparse.ArgumentParser(description='Search knowledge base')
    parser.add_argument('-q', '--query', default='', help='Search query')
    parser.add_argument('-k', '--top-k', type=int, default=5)
    parser.add_argument('-d', '--dir', default='knowledge')
    parser.add_argument('--stats', action='store_true')
    
    args = parser.parse_args()
    searcher = KnowledgeSearch(args.dir)
    
    if args.stats:
        print(json.dumps(searcher.get_stats(), indent=2))
        return
    
    if not args.query:
        print("Use -q for query or --stats")
        sys.exit(1)
    
    results = searcher.search(args.query, args.top_k)
    
    print(f"\n🔍 Found {len(results)} for: '{args.query}'\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r.title} (score: {r.score:.2f})")
        print(f"    {r.content[:200]}...\n")


if __name__ == '__main__':
    main()
