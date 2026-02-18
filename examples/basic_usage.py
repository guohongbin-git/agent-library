#!/usr/bin/env python3
"""
Example: How to use Agent Library

This script demonstrates the basic usage of the converter and search.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from converter import PDFConverter
from search import KnowledgeSearch


def example_convert():
    """Example: Convert a PDF to TOON format"""
    print("=" * 60)
    print("Example: PDF Conversion")
    print("=" * 60)
    
    # Initialize converter
    converter = PDFConverter(use_llm=False)
    
    # Example PDF path (you would replace this with your PDF)
    pdf_path = "inputs/example.pdf"
    
    print(f"\n📄 Processing: {pdf_path}")
    
    # Parse PDF
    result = converter.parse_pdf(pdf_path)
    
    if result.get('success'):
        print(f"✅ Parsed using: {result.get('method')}")
        
        # Chunk content
        chunks = converter.chunk_content(result['content'], "Example Book")
        print(f"✅ Created {len(chunks)} chunks")
        
        # Convert to TOON
        toon_content = converter.to_toon(chunks, "Example Book", "Test Author")
        print(f"✅ TOON format generated")
        
        # Show first chunk
        if chunks:
            print(f"\n📖 First chunk preview:")
            print(f"   Title: {chunks[0].title}")
            print(f"   Tokens: {chunks[0].tokens_estimate}")
            print(f"   Keywords: {chunks[0].keywords}")
    else:
        print(f"❌ Error: {result.get('error')}")


def example_search():
    """Example: Search the knowledge base"""
    print("\n" + "=" * 60)
    print("Example: Knowledge Search")
    print("=" * 60)
    
    # Initialize searcher
    searcher = KnowledgeSearch('knowledge')
    
    # Get stats
    stats = searcher.get_stats()
    print(f"\n📊 Knowledge Base Stats:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Total sources: {stats['total_sources']}")
    print(f"   Estimated tokens: {stats['estimated_tokens']:,}")
    
    # Search
    query = "machine learning"
    print(f"\n🔍 Searching for: '{query}'")
    
    results = searcher.search(query, top_k=3)
    
    if results:
        print(f"\n✅ Found {len(results)} results:")
        for i, r in enumerate(results, 1):
            print(f"\n   [{i}] {r.title}")
            print(f"       Score: {r.score:.2f}")
            print(f"       Source: {r.source}")
    else:
        print("   No results found")


def main():
    print("\n📚 Agent Library - Usage Examples\n")
    
    # Note: These examples require actual PDF files
    print("Note: These examples require PDF files in the inputs/ directory.")
    print("Place a PDF in inputs/ and modify the pdf_path in example_convert().")
    
    # You can uncomment these to test with actual files:
    # example_convert()
    # example_search()
    
    print("\n✅ Examples complete!")


if __name__ == '__main__':
    main()
