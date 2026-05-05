#!/usr/bin/env python3
"""
HTML Infographic Validation Script

Validates generated HTML infographics against quality checklist.

Usage:
    python3 validate-infographic.py output.html
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple


class InfographicValidator:
    """Validate generated infographics"""
    
    def __init__(self, html_path: str):
        """Initialize validator"""
        self.html_path = html_path
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                self.html = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
        
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
    
    def validate(self) -> bool:
        """Run all validation checks"""
        print("🔍 Validating infographic...\n")
        
        self._check_navigation()
        self._check_content()
        self._check_interactions()
        self._check_metadata()
        self._check_accessibility()
        self._check_performance()
        
        return self._print_results()
    
    def _check_navigation(self):
        """Check navigation panel implementation"""
        section = "Navigation Control"
        
        # Check for floating nav
        if 'floatingNav' in self.html or 'float-nav' in self.html.lower():
            self.results['passed'].append(f"{section}: Found navigation panel")
        else:
            self.results['failed'].append(f"{section}: Navigation panel not found")
        
        # Check for draggable
        if 'mousedown' in self.html and 'mousemove' in self.html:
            self.results['passed'].append(f"{section}: Drag functionality implemented")
        else:
            self.results['warnings'].append(f"{section}: Drag functionality not found")
        
        # Check for close/open logic
        if 'isManuallyClosed' in self.html or 'close' in self.html.lower():
            self.results['passed'].append(f"{section}: Close/open logic found")
        else:
            self.results['warnings'].append(f"{section}: Close/open logic not obvious")
        
        # Check for inactivity timer
        if 'inactivity' in self.html.lower() or '10000' in self.html:
            self.results['passed'].append(f"{section}: Inactivity timer implemented")
        else:
            self.results['warnings'].append(f"{section}: Inactivity timer not found")
        
        # Check for pin marker
        if 'pin' in self.html.lower():
            self.results['passed'].append(f"{section}: Pin marker restoration found")
        else:
            self.results['warnings'].append(f"{section}: Pin marker not obvious")
    
    def _check_content(self):
        """Check content structure"""
        section = "Content Structure"
        
        # Check for multiple entity types
        entity_types = len(re.findall(r'data-entity-type|entity-type|type:', self.html, re.IGNORECASE))
        if entity_types > 3:
            self.results['passed'].append(f"{section}: Multiple entity types represented ({entity_types}+)")
        else:
            self.results['warnings'].append(f"{section}: Limited entity types found")
        
        # Check for acronyms
        if 'acronym' in self.html.lower() or 'abbr' in self.html.lower():
            self.results['passed'].append(f"{section}: Acronym expansion found")
        else:
            self.results['warnings'].append(f"{section}: Acronym expansion not found")
        
        # Check for links
        links = len(re.findall(r'<a[^>]*href=', self.html))
        if links > 5:
            self.results['passed'].append(f"{section}: Entity links implemented ({links} links)")
        else:
            self.results['warnings'].append(f"{section}: Limited links found ({links})")
        
        # Check for section IDs
        section_ids = len(re.findall(r'id="[^"]*"', self.html))
        if section_ids > 5:
            self.results['passed'].append(f"{section}: Section anchors implemented")
        else:
            self.results['warnings'].append(f"{section}: Limited section anchors")
        
        # Check for problem-solution
        if ('problem' in self.html.lower() and 'solution' in self.html.lower()) or \
           ('challenge' in self.html.lower() and 'overcome' in self.html.lower()):
            self.results['passed'].append(f"{section}: Problem-solution framing found")
        else:
            self.results['warnings'].append(f"{section}: Problem-solution framing not obvious")
    
    def _check_interactions(self):
        """Check interactive elements"""
        section = "Interactive Elements"
        
        # Check for accordion
        if 'accordion' in self.html.lower():
            self.results['passed'].append(f"{section}: Accordion component found")
        else:
            self.results['warnings'].append(f"{section}: Accordion not found")
        
        # Check for smooth transitions
        if 'transition' in self.html.lower() or 'cubic-bezier' in self.html:
            self.results['passed'].append(f"{section}: Smooth transitions implemented")
        else:
            self.results['warnings'].append(f"{section}: Smooth transitions not obvious")
        
        # Check for hover effects
        if ':hover' in self.html or 'hover:' in self.html:
            self.results['passed'].append(f"{section}: Hover effects implemented")
        else:
            self.results['warnings'].append(f"{section}: Hover effects not obvious")
        
        # Check for scroll animations
        if 'IntersectionObserver' in self.html or 'intersection' in self.html.lower():
            self.results['passed'].append(f"{section}: Scroll animations with Intersection Observer")
        elif 'scroll' in self.html.lower():
            self.results['warnings'].append(f"{section}: Scroll handling found (may not use Intersection Observer)")
        else:
            self.results['warnings'].append(f"{section}: Scroll animations not found")
        
        # Check for lightbox
        if 'lightbox' in self.html.lower() or 'modal' in self.html.lower():
            self.results['passed'].append(f"{section}: Image lightbox found")
        else:
            self.results['warnings'].append(f"{section}: Image lightbox not found")
        
        # Check responsive design
        if 'media query' in self.html.lower() or '@media' in self.html:
            self.results['passed'].append(f"{section}: Media queries for responsiveness")
        else:
            self.results['warnings'].append(f"{section}: Media queries not obvious")
    
    def _check_metadata(self):
        """Check metadata and SEO"""
        section = "Metadata & SEO"
        
        # Check JSON-LD
        if 'application/ld+json' in self.html:
            self.results['passed'].append(f"{section}: JSON-LD structured data present")
        else:
            self.results['failed'].append(f"{section}: JSON-LD structured data missing")
        
        # Check microdata
        if 'itemscope' in self.html or 'itemprop' in self.html:
            self.results['passed'].append(f"{section}: Microdata annotations present")
        else:
            self.results['warnings'].append(f"{section}: Microdata annotations not found")
        
        # Check Open Graph
        if 'og:' in self.html or 'property="og' in self.html:
            self.results['passed'].append(f"{section}: Open Graph tags present")
        else:
            self.results['warnings'].append(f"{section}: Open Graph tags not found")
        
        # Check meta tags
        meta_tags = len(re.findall(r'<meta[^>]*>', self.html))
        if meta_tags > 5:
            self.results['passed'].append(f"{section}: Comprehensive meta tags ({meta_tags})")
        else:
            self.results['warnings'].append(f"{section}: Limited meta tags ({meta_tags})")
        
        # Check heading hierarchy
        h1_count = len(re.findall(r'<h1[^>]*>', self.html))
        h2_count = len(re.findall(r'<h2[^>]*>', self.html))
        if h1_count == 1 and h2_count > 2:
            self.results['passed'].append(f"{section}: Proper heading hierarchy")
        elif h1_count != 1:
            self.results['failed'].append(f"{section}: Page should have exactly 1 H1 (found {h1_count})")
        else:
            self.results['warnings'].append(f"{section}: Limited H2 tags")
        
        # Check canonical URL
        if 'canonical' in self.html.lower():
            self.results['passed'].append(f"{section}: Canonical URL present")
        else:
            self.results['warnings'].append(f"{section}: Canonical URL not found")
    
    def _check_accessibility(self):
        """Check accessibility features"""
        section = "Accessibility"
        
        # Check alt text
        images = len(re.findall(r'<img[^>]*>', self.html))
        alt_text = len(re.findall(r'<img[^>]*alt="[^"]*"', self.html))
        if alt_text > 0:
            self.results['passed'].append(f"{section}: Alt text on images ({alt_text}/{images})")
        else:
            self.results['warnings'].append(f"{section}: Alt text on images not found")
        
        # Check for focus states
        if 'focus' in self.html.lower():
            self.results['passed'].append(f"{section}: Focus states implemented")
        else:
            self.results['warnings'].append(f"{section}: Focus states not obvious")
        
        # Check language attribute
        if 'lang=' in self.html:
            self.results['passed'].append(f"{section}: Language attribute set")
        else:
            self.results['warnings'].append(f"{section}: Language attribute not found")
        
        # Check for semantic HTML
        semantic_tags = len(re.findall(r'<(article|section|nav|header|footer)[^>]*>', self.html))
        if semantic_tags > 3:
            self.results['passed'].append(f"{section}: Semantic HTML5 tags ({semantic_tags})")
        else:
            self.results['warnings'].append(f"{section}: Limited semantic HTML tags")
        
        # Check for color contrast info (in comments or CSS)
        if 'contrast' in self.html.lower() or '4.5' in self.html or '5.3' in self.html:
            self.results['passed'].append(f"{section}: Color contrast considerations documented")
        else:
            self.results['warnings'].append(f"{section}: Color contrast not documented")
    
    def _check_performance(self):
        """Check performance considerations"""
        section = "Performance"
        
        # Check file size
        file_size_kb = len(self.html) / 1024
        if file_size_kb < 500:
            self.results['passed'].append(f"{section}: Reasonable file size ({file_size_kb:.1f} KB)")
        elif file_size_kb < 1000:
            self.results['warnings'].append(f"{section}: Large file size ({file_size_kb:.1f} KB)")
        else:
            self.results['failed'].append(f"{section}: Very large file size ({file_size_kb:.1f} KB)")
        
        # Check for external resources from CDN
        cdn_resources = len(re.findall(r'https://(cdn\.|[a-z]+\.com/)', self.html))
        if cdn_resources > 0:
            self.results['passed'].append(f"{section}: Using CDN resources ({cdn_resources})")
        else:
            self.results['warnings'].append(f"{section}: Not using CDN resources")
        
        # Check for CSS animations vs JavaScript
        if '@keyframes' in self.html and 'animation:' in self.html:
            self.results['passed'].append(f"{section}: CSS animations used for performance")
        else:
            self.results['warnings'].append(f"{section}: CSS animations not obvious")
        
        # Check for Intersection Observer (performant scrolling)
        if 'IntersectionObserver' in self.html:
            self.results['passed'].append(f"{section}: Intersection Observer for efficient scrolling")
        else:
            self.results['warnings'].append(f"{section}: Scroll handling may not be optimized")
        
        # Check for lazy loading
        if 'lazy' in self.html.lower() or 'data-src' in self.html:
            self.results['passed'].append(f"{section}: Lazy loading implemented")
        else:
            self.results['warnings'].append(f"{section}: Lazy loading not found")
    
    def _print_results(self) -> bool:
        """Print validation results"""
        total = len(self.results['passed']) + len(self.results['failed'])
        passed = len(self.results['passed'])
        
        print("✅ PASSED")
        for item in self.results['passed']:
            print(f"  • {item}")
        
        if self.results['warnings']:
            print("\n⚠️  WARNINGS")
            for item in self.results['warnings']:
                print(f"  • {item}")
        
        if self.results['failed']:
            print("\n❌ FAILED")
            for item in self.results['failed']:
                print(f"  • {item}")
        
        print(f"\n📊 Score: {passed}/{total} checks passed ({100*passed//total}%)")
        
        return len(self.results['failed']) == 0


def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python3 validate-infographic.py <html_file>")
        sys.exit(1)
    
    html_file = sys.argv[1]
    validator = InfographicValidator(html_file)
    success = validator.validate()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
