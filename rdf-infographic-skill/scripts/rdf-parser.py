#!/usr/bin/env python3
"""
RDF Parser Utility for Infographic Generation

Parses RDF data in multiple formats (Turtle, RDF/XML, JSON-LD, N-Triples)
and extracts key information for infographic generation.

Usage:
    python3 rdf-parser.py input.ttl
    python3 rdf-parser.py input.rdf --format rdf-xml
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

try:
    from rdflib import Graph, Namespace, RDF, RDFS, Literal
    HAS_RDFLIB = True
except ImportError:
    HAS_RDFLIB = False
    print("Warning: rdflib not installed. Install with: pip install rdflib", file=sys.stderr)

class RDFParser:
    """Parse RDF data and extract infographic information"""
    
    COMMON_NAMESPACES = {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'owl': 'http://www.w3.org/2002/07/owl#',
        'dct': 'http://purl.org/dc/terms/',
        'foaf': 'http://xmlns.com/foaf/0.1/',
        'schema': 'https://schema.org/',
    }
    
    def __init__(self, rdf_data: str, format: str = 'turtle'):
        """Initialize parser with RDF data"""
        self.format = self._detect_format(rdf_data, format)
        self.graph = None
        self.entities = {}
        self.entity_types = {}
        self.relationships = []
        self.acronyms = {}
        
        if HAS_RDFLIB:
            self._parse_with_rdflib(rdf_data)
        else:
            self._parse_manual(rdf_data)
    
    def _detect_format(self, data: str, provided_format: str) -> str:
        """Detect RDF format from data"""
        if provided_format != 'turtle':
            return provided_format
        
        data_lower = data.lower()
        if data_lower.startswith('<?xml'):
            return 'xml'
        elif data_lower.startswith('{'):
            return 'json-ld'
        elif data_lower.startswith('@prefix'):
            return 'turtle'
        else:
            return 'nt'
    
    def _parse_with_rdflib(self, rdf_data: str):
        """Parse RDF using rdflib"""
        self.graph = Graph()
        try:
            self.graph.parse(data=rdf_data, format=self.format)
            self._extract_from_graph()
        except Exception as e:
            print(f"Error parsing RDF: {e}", file=sys.stderr)
    
    def _extract_from_graph(self):
        """Extract entities and relationships from parsed graph"""
        RDFS_ns = Namespace('http://www.w3.org/2000/01/rdf-schema#')
        RDF_ns = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        
        # Extract entities
        for subject in self.graph.subjects():
            entity_iri = str(subject)
            
            # Get entity type
            entity_types = list(self.graph.objects(subject, RDF_ns.type))
            entity_type = str(entity_types[0]) if entity_types else 'Thing'
            
            # Get label
            labels = list(self.graph.objects(subject, RDFS_ns.label))
            label = str(labels[0]) if labels else entity_iri.split('/')[-1]
            
            # Get description
            descriptions = list(self.graph.objects(subject, RDFS_ns.comment))
            description = str(descriptions[0]) if descriptions else ''
            
            # Store entity
            self.entities[entity_iri] = {
                'iri': entity_iri,
                'type': entity_type,
                'label': label,
                'description': description,
                'properties': {}
            }
            
            # Track entity types
            if entity_type not in self.entity_types:
                self.entity_types[entity_type] = []
            self.entity_types[entity_type].append(entity_iri)
            
            # Extract acronyms from labels
            self._extract_acronym(label)
        
        # Extract relationships
        for subject, predicate, obj in self.graph.triples((None, None, None)):
            subj_iri = str(subject)
            pred_iri = str(predicate)
            obj_iri = str(obj)
            
            if isinstance(obj, Literal):
                # Store property on entity
                if subj_iri in self.entities:
                    prop_name = pred_iri.split('#')[-1] or pred_iri.split('/')[-1]
                    self.entities[subj_iri]['properties'][prop_name] = str(obj)
            else:
                # Track relationship
                self.relationships.append({
                    'source': subj_iri,
                    'predicate': pred_iri,
                    'target': obj_iri
                })
    
    def _parse_manual(self, rdf_data: str):
        """Fallback manual parsing when rdflib is not available"""
        # Simple regex-based extraction for Turtle format
        import re
        
        lines = rdf_data.split('\n')
        for line in lines:
            # Simple label extraction
            if 'rdfs:label' in line or 'dcterms:title' in line:
                match = re.search(r'"([^"]+)"', line)
                if match:
                    label = match.group(1)
                    self._extract_acronym(label)
    
    def _extract_acronym(self, text: str):
        """Extract acronym from text"""
        # Look for parenthetical acronyms: "OpenLink AI Layer (OPAL)"
        import re
        match = re.search(r'\(([A-Z]{2,})\)', text)
        if match:
            acronym = match.group(1)
            self.acronyms[acronym] = text.replace(f'({acronym})', '').strip()
        else:
            # Infer from capitals
            capitals = ''.join([c for c in text if c.isupper()])
            if 2 <= len(capitals) <= 5:
                self.acronyms[capitals] = text
    
    def get_entities(self) -> Dict:
        """Get all extracted entities"""
        return self.entities
    
    def get_entity_types(self) -> Dict:
        """Get entities grouped by type"""
        return self.entity_types
    
    def get_acronyms(self) -> Dict:
        """Get all extracted acronyms"""
        return self.acronyms
    
    def get_relationships(self) -> List:
        """Get all relationships"""
        return self.relationships
    
    def get_keywords(self, limit: int = 10) -> List[str]:
        """Extract keywords from labels and descriptions"""
        from collections import Counter
        
        words = []
        for entity in self.entities.values():
            # Extract from label
            label = entity['label'].lower()
            words.extend(label.split())
            
            # Extract from description
            description = entity['description'].lower()
            # Simple tokenization
            import re
            words.extend(re.findall(r'\b\w{4,}\b', description))
        
        # Count and filter
        counter = Counter(words)
        # Remove common words
        stop_words = {'the', 'and', 'for', 'with', 'from', 'that', 'this', 'data'}
        keywords = [w for w, _ in counter.most_common(limit) if w not in stop_words]
        return keywords[:limit]
    
    def generate_json_ld(self) -> Dict:
        """Generate JSON-LD structured data"""
        graph_data = {
            '@context': {
                '@vocab': 'http://schema.org/',
                'rdf': self.COMMON_NAMESPACES['rdf'],
                'rdfs': self.COMMON_NAMESPACES['rdfs']
            },
            '@graph': []
        }
        
        for entity_iri, entity in self.entities.items():
            entity_json = {
                '@id': entity_iri,
                '@type': entity['type'],
                'name': entity['label'],
                'description': entity['description']
            }
            graph_data['@graph'].append(entity_json)
        
        return graph_data
    
    def to_infographic_config(self) -> Dict:
        """Generate infographic configuration from parsed RDF"""
        entity_types = list(self.entity_types.keys())[:10]  # Top 10 types
        
        config = {
            'ENTITY_TYPES': entity_types,
            'KEY_ACRONYMS': self.acronyms,
            'DOMAIN_KEYWORDS': self.get_keywords(),
            'ENTITIES_COUNT': len(self.entities),
            'RELATIONSHIPS_COUNT': len(self.relationships),
            'ENTITY_SAMPLES': {
                type_name: [
                    self.entities[iri]['label']
                    for iri in self.entity_types.get(type_name, [])[:3]
                ]
                for type_name in entity_types
            }
        }
        
        return config


def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python3 rdf-parser.py <input_file> [--format FORMAT]")
        print("Supported formats: turtle, xml (rdf-xml), json-ld, nt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    format = 'turtle'
    
    if '--format' in sys.argv:
        format_idx = sys.argv.index('--format')
        if format_idx + 1 < len(sys.argv):
            format = sys.argv[format_idx + 1]
    
    # Read file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            rdf_data = f.read()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Parse
    parser = RDFParser(rdf_data, format)
    
    # Output
    config = parser.to_infographic_config()
    print(json.dumps(config, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
