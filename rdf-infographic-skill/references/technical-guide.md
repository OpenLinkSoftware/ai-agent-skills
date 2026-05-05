# Technical Implementation Guide

This guide covers JavaScript architecture, state management, and implementation patterns for interactive infographics.

## Architecture Overview

The generated infographic consists of three main layers:

1. **HTML Structure** - Semantic markup with proper heading hierarchy and data attributes
2. **CSS Styling** - Organized by component with media queries for responsiveness
3. **JavaScript Interactions** - Modular, event-driven functionality

## Document Structure

### Semantic Markup

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <!-- Metadata, styles, fonts -->
</head>
<body>
  <nav class="nav-floating" id="floatingNav">
    <!-- Navigation panel -->
  </nav>
  
  <main class="container">
    <section class="hero" id="hero">
      <!-- Hero section -->
    </section>
    
    <section class="overview" id="overview">
      <!-- Problem-solution content -->
    </section>
    
    <!-- Additional sections... -->
  </main>
  
  <footer class="footer">
    <!-- Footer content -->
  </footer>
  
  <script>
    // JavaScript code
  </script>
</body>
</html>
```

## JavaScript Architecture

### Module Pattern

Organize code into logical modules:

```javascript
// Navigation Module
const NavModule = (() => {
  // Private variables
  const state = {
    isOpen: true,
    isManuallyClosed: false,
    inactivityTimer: null
  };
  
  // Private methods
  const _handleInactivity = () => {
    // Implementation
  };
  
  // Public methods
  return {
    init: () => { /* ... */ },
    close: () => { /* ... */ },
    open: () => { /* ... */ }
  };
})();

// Animation Module
const AnimationModule = (() => {
  const _observerCallback = (entries) => {
    // Implementation
  };
  
  return {
    init: () => { /* ... */ }
  };
})();

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
  NavModule.init();
  AnimationModule.init();
});
```

### State Management

Track component state with clear flags:

```javascript
const navigationState = {
  // Visibility states
  isVisible: true,
  isManuallyClosed: false,  // User explicitly closed it
  isHidden: false,           // Auto-hidden due to inactivity
  
  // Position states
  position: { x: 20, y: 20 },
  size: { width: 300, height: 400 },
  
  // Interaction states
  isDragging: false,
  isResizing: false,
  lastActivity: Date.now()
};

// Update state with clear intent
const closeNavigation = () => {
  navigationState.isManuallyClosed = true;
  navigationState.isVisible = false;
  // Only manual action can restore it
};

const autoHideNavigation = () => {
  navigationState.isHidden = true;
  navigationState.isVisible = false;
  // Can be restored by inactivity timer
};
```

## Key Interactions

### 1. Floating Navigation Panel

```javascript
const FloatingNav = (() => {
  const state = {
    isVisible: true,
    isManuallyClosed: false,
    isHidden: false,
    inactivityTimer: null,
    lastMouseMove: 0,
    isDragging: false,
    dragOffset: { x: 0, y: 0 }
  };

  const panel = document.getElementById('floatingNav');
  const closeBtn = panel.querySelector('.nav-close');
  const pinBtn = document.getElementById('navPin');

  // Dragging functionality
  const _setupDragging = () => {
    let header = panel.querySelector('.nav-header');
    
    header.addEventListener('mousedown', (e) => {
      state.isDragging = true;
      state.dragOffset = {
        x: e.clientX - panel.offsetLeft,
        y: e.clientY - panel.offsetTop
      };
    });

    document.addEventListener('mousemove', (e) => {
      if (!state.isDragging) return;
      
      panel.style.left = (e.clientX - state.dragOffset.x) + 'px';
      panel.style.top = (e.clientY - state.dragOffset.y) + 'px';
      _resetInactivityTimer();
    });

    document.addEventListener('mouseup', () => {
      state.isDragging = false;
    });
  };

  // Manual close (respects user preference)
  const _setupCloseButton = () => {
    closeBtn.addEventListener('click', () => {
      state.isManuallyClosed = true;
      state.isVisible = false;
      panel.style.display = 'none';
      
      // Show pin marker
      pinBtn.style.display = 'flex';
      
      // Clear timers
      clearTimeout(state.inactivityTimer);
    });
  };

  // Pin marker restoration
  const _setupPinButton = () => {
    pinBtn.addEventListener('click', () => {
      state.isManuallyClosed = false;
      state.isVisible = true;
      state.isHidden = false;
      panel.style.display = 'block';
      pinBtn.style.display = 'none';
      _resetInactivityTimer();
    });
  };

  // Inactivity fade (10 seconds)
  const _resetInactivityTimer = () => {
    // Don't override manual close
    if (state.isManuallyClosed) return;
    
    clearTimeout(state.inactivityTimer);
    state.isHidden = false;
    panel.classList.remove('inactive');
    
    state.inactivityTimer = setTimeout(() => {
      if (!state.isManuallyClosed) {
        state.isHidden = true;
        panel.classList.add('inactive');
        pinBtn.style.display = 'flex';
      }
    }, 10000);
  };

  // Track user activity
  const _setupActivityTracking = () => {
    ['mousemove', 'click', 'scroll'].forEach(event => {
      document.addEventListener(event, _resetInactivityTimer, true);
    });
  };

  return {
    init: () => {
      _setupDragging();
      _setupCloseButton();
      _setupPinButton();
      _setupActivityTracking();
    }
  };
})();
```

### 2. Scroll-Triggered Animations

```javascript
const ScrollAnimations = (() => {
  const _setupIntersectionObserver = () => {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observerCallback = (entries) => {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          // Add staggered delay for multiple items
          entry.target.style.animationDelay = (index * 0.1) + 's';
          entry.target.classList.add('animate-in');
          observer.unobserve(entry.target);
        }
      });
    };

    const observer = new IntersectionObserver(observerCallback, observerOptions);
    
    // Observe all elements with animation class
    document.querySelectorAll('[data-animate]').forEach(el => {
      observer.observe(el);
    });
  };

  return {
    init: () => _setupIntersectionObserver()
  };
})();
```

### 3. Accordion Component

```javascript
const AccordionModule = (() => {
  const _setupAccordions = () => {
    const headers = document.querySelectorAll('.accordion-header');
    
    headers.forEach(header => {
      header.addEventListener('click', () => {
        const item = header.parentElement;
        const content = item.querySelector('.accordion-content');
        const chevron = header.querySelector('.accordion-chevron');
        const isOpen = item.classList.contains('open');
        
        // Close all others in same accordion
        item.parentElement.querySelectorAll('.accordion-item.open').forEach(el => {
          if (el !== item) {
            el.classList.remove('open');
            el.querySelector('.accordion-content').classList.remove('open');
            el.querySelector('.accordion-chevron').classList.remove('open');
          }
        });
        
        // Toggle current
        if (!isOpen) {
          item.classList.add('open');
          content.classList.add('open');
          chevron.classList.add('open');
        } else {
          item.classList.remove('open');
          content.classList.remove('open');
          chevron.classList.remove('open');
        }
      });
    });
  };

  return {
    init: () => _setupAccordions()
  };
})();
```

### 4. Section Anchors with Copy

```javascript
const SectionAnchorsModule = (() => {
  const _setupAnchors = () => {
    const headers = document.querySelectorAll('h2, h3, h4');
    
    headers.forEach(header => {
      if (!header.id) return; // Skip headers without IDs
      
      // Create anchor icon
      const anchorIcon = document.createElement('span');
      anchorIcon.className = 'section-anchor';
      anchorIcon.textContent = '🔗';
      anchorIcon.style.display = 'none';
      
      header.appendChild(anchorIcon);
      
      // Show on hover
      header.addEventListener('mouseenter', () => {
        anchorIcon.style.display = 'inline';
      });
      header.addEventListener('mouseleave', () => {
        anchorIcon.style.display = 'none';
      });
      
      // Copy on click
      anchorIcon.addEventListener('click', () => {
        const url = window.location.origin + window.location.pathname + '#' + header.id;
        navigator.clipboard.writeText(url);
        
        // Show confirmation
        const originalText = anchorIcon.textContent;
        anchorIcon.textContent = '✓ Copied!';
        setTimeout(() => {
          anchorIcon.textContent = originalText;
        }, 2000);
      });
    });
  };

  return {
    init: () => _setupAnchors()
  };
})();
```

### 5. Entity Linking

```javascript
const EntityLinkingModule = (() => {
  // Map of entity labels to IRIs
  const entityMap = {};
  
  const _buildEntityMap = () => {
    // Extract from data attributes on entity elements
    document.querySelectorAll('[data-entity-iri]').forEach(el => {
      const label = el.textContent;
      const iri = el.getAttribute('data-entity-iri');
      entityMap[label] = iri;
    });
  };

  const _linkifyText = (node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      let text = node.nodeValue;
      let htmlContent = text;
      
      // Replace entity labels with links (first occurrence only)
      Object.entries(entityMap).forEach(([label, iri]) => {
        if (!htmlContent.includes(`<a href`)) { // Check if not already linked
          const regex = new RegExp(`\\b${label}\\b`, 'g');
          const encodedIri = encodeURIComponent(iri);
          const link = `<a href="https://linkeddata.uriburner.com/describe/?uri=${encodedIri}" target="_blank" class="entity-link">${label}</a>`;
          
          htmlContent = htmlContent.replace(regex, link);
        }
      });
      
      if (htmlContent !== text) {
        const span = document.createElement('span');
        span.innerHTML = htmlContent;
        node.parentNode.replaceChild(span, node);
      }
    } else if (node.nodeType === Node.ELEMENT_NODE && !['SCRIPT', 'STYLE', 'A'].includes(node.tagName)) {
      node.childNodes.forEach(_linkifyText);
    }
  };

  return {
    init: () => {
      _buildEntityMap();
      _linkifyText(document.body);
    }
  };
})();
```

### 6. Image Lightbox

```javascript
const LightboxModule = (() => {
  const _createLightbox = () => {
    const lightbox = document.createElement('div');
    lightbox.id = 'lightbox';
    lightbox.className = 'lightbox';
    lightbox.innerHTML = `
      <div class="lightbox-content">
        <img id="lightbox-image" src="" alt="">
        <button class="lightbox-close">&times;</button>
      </div>
    `;
    document.body.appendChild(lightbox);
    return lightbox;
  };

  const _setupImageClicks = (lightbox) => {
    document.querySelectorAll('img[data-lightbox]').forEach(img => {
      img.style.cursor = 'pointer';
      img.addEventListener('click', () => {
        const lightboxImg = lightbox.querySelector('#lightbox-image');
        lightboxImg.src = img.src;
        lightbox.classList.add('active');
      });
    });
  };

  const _setupClose = (lightbox) => {
    const closeBtn = lightbox.querySelector('.lightbox-close');
    closeBtn.addEventListener('click', () => {
      lightbox.classList.remove('active');
    });
    
    lightbox.addEventListener('click', (e) => {
      if (e.target === lightbox) {
        lightbox.classList.remove('active');
      }
    });
  };

  return {
    init: () => {
      const lightbox = _createLightbox();
      _setupImageClicks(lightbox);
      _setupClose(lightbox);
    }
  };
})();
```

## Metadata & SEO Implementation

### JSON-LD Structure

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Thing",
  "name": "OPAL - OpenLink AI Layer",
  "description": "AI-powered semantic data integration platform",
  "url": "https://example.com/infographic",
  "image": "https://example.com/image.jpg",
  "creator": {
    "@type": "Organization",
    "name": "OpenLink Software",
    "url": "https://www.openlinksw.com"
  },
  "datePublished": "2025-01-15",
  "keywords": ["semantic web", "RDF", "knowledge graph", "data integration"]
}
</script>
```

### Open Graph Tags

```html
<meta property="og:title" content="OPAL - OpenLink AI Layer">
<meta property="og:description" content="AI-powered semantic data integration platform">
<meta property="og:image" content="https://example.com/image.jpg">
<meta property="og:url" content="https://example.com/infographic">
<meta property="og:type" content="website">
```

### Twitter Cards

```html
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="OPAL - OpenLink AI Layer">
<meta name="twitter:description" content="AI-powered semantic data integration platform">
<meta name="twitter:image" content="https://example.com/image.jpg">
```

### Microdata

```html
<article itemscope itemtype="https://schema.org/Article">
  <h1 itemprop="headline">Understanding RDF Data Integration</h1>
  <p itemprop="description">Learn how RDF and semantic web technologies enable better data integration</p>
  <span itemprop="author" itemscope itemtype="https://schema.org/Organization">
    <span itemprop="name">OpenLink Software</span>
  </span>
</article>
```

## Performance Optimization

### Lazy Loading Images

```javascript
const LazyLoadModule = (() => {
  const _setupLazyLoad = () => {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
          imageObserver.unobserve(img);
        }
      });
    });
    
    images.forEach(img => imageObserver.observe(img));
  };

  return {
    init: () => _setupLazyLoad()
  };
})();
```

### CSS Performance

- Use `transform` and `opacity` for animations (GPU accelerated)
- Avoid animating `width`, `height`, `left`, `top` (triggers layout recalculation)
- Use `will-change` sparingly for heavy animations

```css
/* Good - hardware accelerated */
transform: translateY(-4px);
opacity: 0.8;

/* Bad - triggers layout thrashing */
top: -4px;
margin-top: -4px;
```

## Browser Compatibility

### Feature Detection

```javascript
const browserFeatures = {
  hasBackdropFilter: CSS.supports('backdrop-filter', 'blur(10px)'),
  hasIntersectionObserver: 'IntersectionObserver' in window,
  hasClipboard: 'clipboard' in navigator
};

// Apply fallbacks if needed
if (!browserFeatures.hasBackdropFilter) {
  // Use solid background instead of glassmorphism
  panel.style.background = 'rgba(255, 255, 255, 0.95)';
}
```

## Debugging Tips

### Console Logging for State

```javascript
// Log state changes
const logState = (moduleName, state) => {
  console.log(`[${moduleName}]`, state);
};

// Example: Log navigation state changes
const closeNavigation = () => {
  navigationState.isManuallyClosed = true;
  navigationState.isVisible = false;
  logState('Navigation', navigationState);
};
```

### Performance Monitoring

```javascript
// Measure script execution time
console.time('InitializeModules');
NavModule.init();
AnimationModule.init();
console.timeEnd('InitializeModules');

// Monitor layout thrashing
const observer = new PerformanceObserver((list) => {
  list.getEntries().forEach(entry => {
    console.log(`Performance: ${entry.name} - ${entry.duration.toFixed(2)}ms`);
  });
});
observer.observe({ entryTypes: ['measure'] });
```

## Testing Checklist

- [ ] Navigation drag/resize works smoothly
- [ ] Manual close prevents auto-reopen
- [ ] Pin marker restores panel correctly
- [ ] Accordion opens/closes without janky animation
- [ ] Scroll animations trigger at correct viewport
- [ ] Entity links point to correct URIs
- [ ] Images open in lightbox on click
- [ ] Metadata renders correctly in social shares
- [ ] Mobile responsive on 375px+ widths
- [ ] No console errors in DevTools
- [ ] Performance: Initial load < 2s, interactions < 100ms
