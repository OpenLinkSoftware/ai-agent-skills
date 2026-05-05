# Design Patterns for RDF Infographics

This guide covers visual design patterns, component specifications, and CSS frameworks for creating stunning RDF-based infographics.

## Design System

### Color Palette

#### Primary Colors (Headers, Key Elements)
- **Primary**: `#4F46E5` (Indigo) - Main branding
- **Secondary**: `#7C3AED` (Violet) - Accents and highlights
- **Accent**: `#06B6D4` (Cyan) - CTAs, interactive elements

#### Neutral Colors (Backgrounds, Text)
- **White**: `#FFFFFF` - Primary background
- **Light**: `#F8FAFC` (Slate-50) - Secondary background
- **Medium**: `#E2E8F0` (Slate-200) - Borders, dividers
- **Dark**: `#64748B` (Slate-500) - Body text
- **Darker**: `#1E293B` (Slate-900) - Headings, strong text

#### Semantic Colors
- **Success**: `#10B981` (Emerald)
- **Warning**: `#F59E0B` (Amber)
- **Error**: `#EF4444` (Red)
- **Info**: `#3B82F6` (Blue)

#### Gradient Combinations
```css
/* Hero Section - Rich Gradient */
background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #06B6D4 100%);

/* Subtle Background Gradient */
background: linear-gradient(to bottom, #FFFFFF 0%, #F8FAFC 100%);

/* Accent Gradient on Cards */
background: linear-gradient(135deg, #06B6D4 0%, #0891B2 100%);
```

### Typography

#### Font Stack (Google Fonts)
```css
/* Primary Font (Headers, Titles) */
font-family: 'Poppins', 'Inter', system-ui, -apple-system, sans-serif;
font-weight: 600;

/* Secondary Font (Body, Descriptions) */
font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
font-weight: 400;

/* Code Font (Technical Content) */
font-family: 'Fira Code', 'Monaco', 'Courier New', monospace;
font-weight: 500;
```

#### Type Scale
```css
/* H1 - Page Title */
font-size: 3.75rem; /* 60px */
font-weight: 700;
letter-spacing: -0.02em;
line-height: 1.1;
@media (max-width: 768px) { font-size: 2.25rem; } /* 36px */

/* H2 - Section Headers */
font-size: 2.25rem; /* 36px */
font-weight: 600;
letter-spacing: -0.01em;
line-height: 1.2;
@media (max-width: 768px) { font-size: 1.875rem; } /* 30px */

/* H3 - Subsection Headers */
font-size: 1.875rem; /* 30px */
font-weight: 600;
line-height: 1.3;
@media (max-width: 768px) { font-size: 1.5rem; } /* 24px */

/* H4 - Component Headers */
font-size: 1.5rem; /* 24px */
font-weight: 600;
line-height: 1.4;

/* Body */
font-size: 1rem; /* 16px */
font-weight: 400;
line-height: 1.6;

/* Small */
font-size: 0.875rem; /* 14px */
font-weight: 400;
line-height: 1.5;

/* Code */
font-size: 0.875rem; /* 14px */
font-family: monospace;
```

### Spacing System

```css
/* Base unit: 4px */
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-20: 5rem;     /* 80px */
```

**Usage**:
- **Padding**: `--space-6` (24px) inside cards, `--space-4` (16px) inside buttons
- **Margin**: `--space-8` (32px) between sections, `--space-4` between components
- **Whitespace**: Minimum `--space-8` around major content blocks

## Component Specifications

### Card Component

```css
.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1),
              0 1px 2px rgba(0, 0, 0, 0.06);
  border: 1px solid #E2E8F0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1),
              0 10px 10px -5px rgba(0, 0, 0, 0.04);
  transform: translateY(-4px);
  border-color: #06B6D4;
}

.card-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #06B6D4, #0891B2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 8px;
}

.card-description {
  font-size: 0.95rem;
  color: #64748B;
  line-height: 1.6;
}
```

### Hero Section

```css
.hero {
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #06B6D4 100%);
  padding: 120px 24px;
  text-align: center;
  position: relative;
  overflow: hidden;
  min-height: 600px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Decorative elements */
.hero::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 500px;
  height: 500px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  filter: blur(40px);
}

.hero::after {
  content: '';
  position: absolute;
  bottom: -30%;
  left: -5%;
  width: 300px;
  height: 300px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50%;
  filter: blur(30px);
}

.hero-content {
  position: relative;
  z-index: 10;
  color: white;
  max-width: 800px;
}

.hero-title {
  font-size: 3.75rem;
  font-weight: 700;
  margin-bottom: 16px;
  letter-spacing: -0.02em;
}

.hero-tagline {
  font-size: 1.375rem;
  margin-bottom: 32px;
  opacity: 0.95;
  line-height: 1.6;
}

.hero-cta {
  display: inline-flex;
  gap: 16px;
}
```

### Button Component

```css
.btn {
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-primary {
  background: linear-gradient(135deg, #4F46E5, #7C3AED);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(79, 70, 229, 0.3);
}

.btn-secondary {
  background: white;
  color: #4F46E5;
  border: 2px solid #4F46E5;
}

.btn-secondary:hover {
  background: #F8FAFC;
}

.btn-outline {
  background: transparent;
  color: white;
  border: 2px solid white;
}

.btn-outline:hover {
  background: rgba(255, 255, 255, 0.1);
}
```

### Glassmorphism Effect (Navigation Panel)

```css
.glass-panel {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
}

.glass-panel:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(255, 255, 255, 0.25);
}
```

### Accordion Component

```css
.accordion-item {
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
}

.accordion-header {
  background: white;
  padding: 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #1E293B;
  transition: background-color 0.2s ease;
}

.accordion-header:hover {
  background: #F8FAFC;
}

.accordion-header.active {
  background: linear-gradient(135deg, #F0F4FF, #F3E8FF);
  color: #4F46E5;
}

.accordion-chevron {
  transition: transform 0.3s ease;
  color: #06B6D4;
}

.accordion-chevron.open {
  transform: rotate(180deg);
}

.accordion-content {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease, padding 0.3s ease;
  background: #F8FAFC;
}

.accordion-content.open {
  max-height: 500px;
  padding: 16px;
}

.accordion-text {
  color: #64748B;
  line-height: 1.7;
}
```

### Grid Layouts

#### Feature Grid (3 Columns)
```css
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin: 48px 0;
}

@media (max-width: 768px) {
  .feature-grid {
    grid-template-columns: 1fr;
  }
}
```

#### Timeline/Step Layout
```css
.timeline {
  position: relative;
  padding: 20px 0;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 24px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(to bottom, #4F46E5, transparent);
}

.timeline-item {
  margin-bottom: 32px;
  padding-left: 80px;
  position: relative;
}

.timeline-dot {
  position: absolute;
  left: 0;
  top: 0;
  width: 48px;
  height: 48px;
  background: white;
  border: 3px solid #4F46E5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: #4F46E5;
}

.timeline-content {
  background: #F8FAFC;
  padding: 16px;
  border-radius: 8px;
  border-left: 3px solid #06B6D4;
}
```

### Icon Styles

```css
.icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.icon-small { width: 24px; height: 24px; }
.icon-medium { width: 32px; height: 32px; }
.icon-large { width: 48px; height: 48px; }
.icon-xl { width: 64px; height: 64px; }

.icon-primary { color: #4F46E5; }
.icon-secondary { color: #7C3AED; }
.icon-accent { color: #06B6D4; }
.icon-success { color: #10B981; }
.icon-warning { color: #F59E0B; }
.icon-error { color: #EF4444; }
```

## Animation Specifications

### Scroll Animations

```css
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in-up {
  animation: fadeInUp 0.6s ease-out forwards;
}

.fade-in-up-delay-1 { animation-delay: 0.1s; }
.fade-in-up-delay-2 { animation-delay: 0.2s; }
.fade-in-up-delay-3 { animation-delay: 0.3s; }
```

### Hover Animations

```css
@keyframes scaleIn {
  from {
    transform: scale(0.95);
  }
  to {
    transform: scale(1);
  }
}

.hover-scale {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.hover-scale:hover {
  transform: scale(1.05);
}
```

### Rotation Animations

```css
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.spinner {
  animation: spin 1s linear infinite;
}
```

## Responsive Design

### Breakpoints
```css
/* Mobile First Approach */
/* Base: Mobile (< 640px) */
/* sm: 640px */
@media (min-width: 640px) { }

/* md: 768px */
@media (min-width: 768px) { }

/* lg: 1024px */
@media (min-width: 1024px) { }

/* xl: 1280px */
@media (min-width: 1280px) { }

/* 2xl: 1536px */
@media (min-width: 1536px) { }
```

### Container Queries
```css
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 16px;
}

@media (max-width: 640px) {
  .container { padding: 0 12px; }
}
```

## Accessibility Considerations

### Color Contrast
- Primary text on white: `#1E293B` (ratio 11.9:1)
- Secondary text on white: `#64748B` (ratio 6.5:1)
- Links on white: `#4F46E5` (ratio 5.3:1)

### Focus States
```css
button:focus,
a:focus {
  outline: 2px solid #4F46E5;
  outline-offset: 2px;
}
```

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Dark Mode Support (Optional)

```css
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #0F172A;
    --bg-secondary: #1E293B;
    --text-primary: #F1F5F9;
    --text-secondary: #CBD5E1;
  }
  
  body {
    background: var(--bg-primary);
    color: var(--text-primary);
  }
}
```

## Best Practices

1. **Whitespace**: Use generous margins and padding (min 24px between sections)
2. **Visual Hierarchy**: Use size, weight, and color to guide attention
3. **Consistency**: Apply same spacing/sizing rules across all sections
4. **Performance**: Use CSS transforms for animations (no layout thrashing)
5. **Accessibility**: Ensure 4.5:1 contrast for body text, 3:1 for larger text
6. **Mobile First**: Design for mobile, enhance for desktop
7. **Emphasis**: Use color sparingly; draw attention through contrast
8. **Typography**: Limit to 2-3 font families maximum
