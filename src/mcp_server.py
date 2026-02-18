#!/usr/bin/env python3
"""
MCP Server for Agent Library

Exposes PDF conversion and search as MCP tools.

Usage:
    python3 mcp_server.py
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# MCP types
class MCPServer:
    """Simple MCP server implementation"""
    
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.tools = {}
        self.resources = {}
    
    def tool(self, name: str, description: str, params_schema: Dict):
        """Register a tool"""
        def decorator(func):
            self.tools[name] = {
                'name': name,
                'description': description,
                'inputSchema': params_schema,
                'handler': func
            }
            return func
        return decorator
    
    def resource(self, uri: str, name: str, description: str):
        """Register a resource"""
        def decorator(func):
            self.resources[uri] = {
                'name': name,
                'description': description,
                'handler': func
            }
            return func
        return decorator
    
    async def handle_request(self, request: Dict) -> Dict:
        """Handle MCP request"""
        method = request.get('method')
        params = request.get('params', {})
        request_id = request.get('id')
        
        if method == 'initialize':
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'protocolVersion': '2024-11-05',
                    'capabilities': {
                        'tools': {},
                        'resources': {}
                    },
                    'serverInfo': {
                        'name': self.name,
                        'version': self.version
                    }
                }
            }
        
        elif method == 'tools/list':
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'tools': [
                        {
                            'name': t['name'],
                            'description': t['description'],
                            'inputSchema': t['inputSchema']
                        }
                        for t in self.tools.values()
                    ]
                }
            }
        
        elif method == 'tools/call':
            tool_name = params.get('name')
            tool_args = params.get('arguments', {})
            
            if tool_name in self.tools:
                try:
                    result = await self.tools[tool_name]['handler'](**tool_args)
                    return {
                        'jsonrpc': '2.0',
                        'id': request_id,
                        'result': {
                            'content': [
                                {'type': 'text', 'text': json.dumps(result, ensure_ascii=False, indent=2)}
                            ]
                        }
                    }
                except Exception as e:
                    return {
                        'jsonrpc': '2.0',
                        'id': request_id,
                        'error': {
                            'code': -32000,
                            'message': str(e)
                        }
                    }
            else:
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'error': {
                        'code': -32601,
                        'message': f'Unknown tool: {tool_name}'
                    }
                }
        
        elif method == 'resources/list':
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'resources': [
                        {
                            'uri': uri,
                            'name': res['name'],
                            'description': res['description']
                        }
                        for uri, res in self.resources.items()
                    ]
                }
            }
        
        elif method == 'resources/read':
            uri = params.get('uri')
            if uri in self.resources:
                try:
                    result = await self.resources[uri]['handler']()
                    return {
                        'jsonrpc': '2.0',
                        'id': request_id,
                        'result': {
                            'contents': [
                                {'uri': uri, 'mimeType': 'text/plain', 'text': result}
                            ]
                        }
                    }
                except Exception as e:
                    return {
                        'jsonrpc': '2.0',
                        'id': request_id,
                        'error': {
                            'code': -32000,
                            'message': str(e)
                        }
                    }
        
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'error': {
                'code': -32601,
                'message': f'Unknown method: {method}'
            }
        }
    
    async def run(self):
        """Run MCP server on stdio"""
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                if not line:
                    break
                
                request = json.loads(line)
                response = await self.handle_request(request)
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                pass
            except Exception as e:
                print(json.dumps({
                    'jsonrpc': '2.0',
                    'error': {'code': -32700, 'message': str(e)}
                }), flush=True)


# Create server instance
server = MCPServer('agent-library', '0.1.0')


# Register tools
@server.tool(
    'convert_pdf',
    'Convert a PDF file to agent-native formats (TOON, Markdown, JSON)',
    {
        'type': 'object',
        'properties': {
            'pdf_path': {
                'type': 'string',
                'description': 'Path to PDF file'
            },
            'output_format': {
                'type': 'string',
                'enum': ['toon', 'markdown', 'json', 'all'],
                'default': 'all',
                'description': 'Output format'
            }
        },
        'required': ['pdf_path']
    }
)
async def convert_pdf(pdf_path: str, output_format: str = 'all'):
    """Convert PDF to agent-native format"""
    from converter import PDFConverter
    
    converter = PDFConverter()
    result = converter.parse_pdf(pdf_path)
    
    if not result.get('success'):
        return {'error': result.get('error', 'Unknown error')}
    
    pdf_name = Path(pdf_path).stem
    chunks = converter.chunk_content(result['content'], pdf_name)
    
    return {
        'success': True,
        'chunks_created': len(chunks),
        'total_tokens': sum(c.tokens_estimate for c in chunks),
        'source': pdf_name
    }


@server.tool(
    'search_knowledge',
    'Search the knowledge base for relevant chunks',
    {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'Search query'
            },
            'top_k': {
                'type': 'integer',
                'default': 5,
                'description': 'Number of results'
            }
        },
        'required': ['query']
    }
)
async def search_knowledge(query: str, top_k: int = 5):
    """Search knowledge base"""
    from search import KnowledgeSearch
    
    searcher = KnowledgeSearch()
    results = searcher.search(query, top_k)
    
    return {
        'query': query,
        'results': [
            {
                'chunk_id': r.chunk_id,
                'title': r.title,
                'score': r.score,
                'source': r.source,
                'content_preview': r.content[:200]
            }
            for r in results
        ]
    }


@server.tool(
    'get_stats',
    'Get knowledge base statistics',
    {
        'type': 'object',
        'properties': {}
    }
)
async def get_stats():
    """Get knowledge base statistics"""
    from search import KnowledgeSearch
    
    searcher = KnowledgeSearch()
    return searcher.get_stats()


# Register resources
@server.resource(
    'mcp://library/stats',
    'Knowledge Base Stats',
    'Statistics about the knowledge base'
)
async def resource_stats():
    from search import KnowledgeSearch
    searcher = KnowledgeSearch()
    return json.dumps(searcher.get_stats(), indent=2)


@server.resource(
    'mcp://library/list',
    'Knowledge Base Contents',
    'List of all books in the knowledge base'
)
async def resource_list():
    knowledge_dir = Path('knowledge')
    files = list(knowledge_dir.glob('*.md')) + list(knowledge_dir.glob('*.toon'))
    return '\n'.join(f.name for f in files)


# Main entry point
if __name__ == '__main__':
    asyncio.run(server.run())
