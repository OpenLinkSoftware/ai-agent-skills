/**
 * HTML Infographic Validation Script — TypeScript edition (Node.js ≥ 18, no npm deps).
 * Identical behavior to validate-infographic.py.
 *
 * Usage:
 *   npx tsx validate-infographic.ts output.html
 */

import { readFileSync } from "node:fs";

interface Results {
  passed: string[];
  failed: string[];
  warnings: string[];
}

class InfographicValidator {
  private readonly html: string;
  private readonly results: Results = { passed: [], failed: [], warnings: [] };

  constructor(htmlPath: string) {
    try {
      this.html = readFileSync(htmlPath, "utf-8");
    } catch (err) {
      process.stderr.write(`Error reading file: ${(err as Error).message}\n`);
      process.exit(1);
    }
  }

  validate(): boolean {
    console.log("Validating infographic...\n");
    this.checkNavigation();
    this.checkContent();
    this.checkInteractions();
    this.checkMetadata();
    this.checkAccessibility();
    this.checkPerformance();
    return this.printResults();
  }

  private pass(msg: string): void { this.results.passed.push(msg); }
  private fail(msg: string): void { this.results.failed.push(msg); }
  private warn(msg: string): void { this.results.warnings.push(msg); }

  private checkNavigation(): void {
    const s = "Navigation Control";
    const html = this.html;

    if (html.includes("floatingNav") || html.toLowerCase().includes("float-nav"))
      this.pass(`${s}: Found navigation panel`);
    else this.fail(`${s}: Navigation panel not found`);

    if (html.includes("mousedown") && html.includes("mousemove"))
      this.pass(`${s}: Drag functionality implemented`);
    else this.warn(`${s}: Drag functionality not found`);

    if (html.includes("isManuallyClosed") || html.toLowerCase().includes("close"))
      this.pass(`${s}: Close/open logic found`);
    else this.warn(`${s}: Close/open logic not obvious`);

    if (html.toLowerCase().includes("inactivity") || html.includes("10000"))
      this.pass(`${s}: Inactivity timer implemented`);
    else this.warn(`${s}: Inactivity timer not found`);

    if (html.toLowerCase().includes("pin"))
      this.pass(`${s}: Pin marker restoration found`);
    else this.warn(`${s}: Pin marker not obvious`);
  }

  private checkContent(): void {
    const s = "Content Structure";
    const html = this.html;

    const entityTypes = (html.match(/data-entity-type|entity-type|type:/gi) ?? []).length;
    if (entityTypes > 3) this.pass(`${s}: Multiple entity types represented (${entityTypes}+)`);
    else this.warn(`${s}: Limited entity types found`);

    if (html.toLowerCase().includes("acronym") || html.toLowerCase().includes("abbr"))
      this.pass(`${s}: Acronym expansion found`);
    else this.warn(`${s}: Acronym expansion not found`);

    const links = (html.match(/<a[^>]*href=/g) ?? []).length;
    if (links > 5) this.pass(`${s}: Entity links implemented (${links} links)`);
    else this.warn(`${s}: Limited links found (${links})`);

    const sectionIds = (html.match(/id="[^"]*"/g) ?? []).length;
    if (sectionIds > 5) this.pass(`${s}: Section anchors implemented`);
    else this.warn(`${s}: Limited section anchors`);

    const lc = html.toLowerCase();
    if ((lc.includes("problem") && lc.includes("solution")) ||
        (lc.includes("challenge") && lc.includes("overcome")))
      this.pass(`${s}: Problem-solution framing found`);
    else this.warn(`${s}: Problem-solution framing not obvious`);
  }

  private checkInteractions(): void {
    const s = "Interactive Elements";
    const html = this.html;
    const lc = html.toLowerCase();

    if (lc.includes("accordion")) this.pass(`${s}: Accordion component found`);
    else this.warn(`${s}: Accordion not found`);

    if (lc.includes("transition") || html.includes("cubic-bezier"))
      this.pass(`${s}: Smooth transitions implemented`);
    else this.warn(`${s}: Smooth transitions not obvious`);

    if (html.includes(":hover") || html.includes("hover:"))
      this.pass(`${s}: Hover effects implemented`);
    else this.warn(`${s}: Hover effects not obvious`);

    if (html.includes("IntersectionObserver") || lc.includes("intersection"))
      this.pass(`${s}: Scroll animations with Intersection Observer`);
    else if (lc.includes("scroll"))
      this.warn(`${s}: Scroll handling found (may not use Intersection Observer)`);
    else this.warn(`${s}: Scroll animations not found`);

    if (lc.includes("lightbox") || lc.includes("modal"))
      this.pass(`${s}: Image lightbox found`);
    else this.warn(`${s}: Image lightbox not found`);

    if (lc.includes("media query") || html.includes("@media"))
      this.pass(`${s}: Media queries for responsiveness`);
    else this.warn(`${s}: Media queries not obvious`);
  }

  private checkMetadata(): void {
    const s = "Metadata & SEO";
    const html = this.html;

    if (html.includes("application/ld+json"))
      this.pass(`${s}: JSON-LD structured data present`);
    else this.fail(`${s}: JSON-LD structured data missing`);

    if (html.includes("itemscope") || html.includes("itemprop"))
      this.pass(`${s}: Microdata annotations present`);
    else this.warn(`${s}: Microdata annotations not found`);

    if (html.includes("og:") || html.includes('property="og'))
      this.pass(`${s}: Open Graph tags present`);
    else this.warn(`${s}: Open Graph tags not found`);

    const metaTags = (html.match(/<meta[^>]*>/g) ?? []).length;
    if (metaTags > 5) this.pass(`${s}: Comprehensive meta tags (${metaTags})`);
    else this.warn(`${s}: Limited meta tags (${metaTags})`);

    const h1Count = (html.match(/<h1[^>]*>/g) ?? []).length;
    const h2Count = (html.match(/<h2[^>]*>/g) ?? []).length;
    if (h1Count === 1 && h2Count > 2) this.pass(`${s}: Proper heading hierarchy`);
    else if (h1Count !== 1) this.fail(`${s}: Page should have exactly 1 H1 (found ${h1Count})`);
    else this.warn(`${s}: Limited H2 tags`);

    if (html.toLowerCase().includes("canonical"))
      this.pass(`${s}: Canonical URL present`);
    else this.warn(`${s}: Canonical URL not found`);
  }

  private checkAccessibility(): void {
    const s = "Accessibility";
    const html = this.html;

    const images = (html.match(/<img[^>]*>/g) ?? []).length;
    const altText = (html.match(/<img[^>]*alt="[^"]*"/g) ?? []).length;
    if (altText > 0) this.pass(`${s}: Alt text on images (${altText}/${images})`);
    else this.warn(`${s}: Alt text on images not found`);

    if (html.toLowerCase().includes("focus"))
      this.pass(`${s}: Focus states implemented`);
    else this.warn(`${s}: Focus states not obvious`);

    if (html.includes("lang="))
      this.pass(`${s}: Language attribute set`);
    else this.warn(`${s}: Language attribute not found`);

    const semanticTags = (html.match(/<(article|section|nav|header|footer)[^>]*>/g) ?? []).length;
    if (semanticTags > 3) this.pass(`${s}: Semantic HTML5 tags (${semanticTags})`);
    else this.warn(`${s}: Limited semantic HTML tags`);

    if (html.toLowerCase().includes("contrast") || html.includes("4.5") || html.includes("5.3"))
      this.pass(`${s}: Color contrast considerations documented`);
    else this.warn(`${s}: Color contrast not documented`);
  }

  private checkPerformance(): void {
    const s = "Performance";
    const html = this.html;

    const fileSizeKb = html.length / 1024;
    if (fileSizeKb < 500) this.pass(`${s}: Reasonable file size (${fileSizeKb.toFixed(1)} KB)`);
    else if (fileSizeKb < 1000) this.warn(`${s}: Large file size (${fileSizeKb.toFixed(1)} KB)`);
    else this.fail(`${s}: Very large file size (${fileSizeKb.toFixed(1)} KB)`);

    const cdnResources = (html.match(/https:\/\/(cdn\.|[a-z]+\.com\/)/g) ?? []).length;
    if (cdnResources > 0) this.pass(`${s}: Using CDN resources (${cdnResources})`);
    else this.warn(`${s}: Not using CDN resources`);

    if (html.includes("@keyframes") && html.includes("animation:"))
      this.pass(`${s}: CSS animations used for performance`);
    else this.warn(`${s}: CSS animations not obvious`);

    if (html.includes("IntersectionObserver"))
      this.pass(`${s}: Intersection Observer for efficient scrolling`);
    else this.warn(`${s}: Scroll handling may not be optimized`);

    if (html.toLowerCase().includes("lazy") || html.includes("data-src"))
      this.pass(`${s}: Lazy loading implemented`);
    else this.warn(`${s}: Lazy loading not found`);
  }

  private printResults(): boolean {
    const total = this.results.passed.length + this.results.failed.length;
    const passed = this.results.passed.length;

    console.log("PASSED");
    for (const item of this.results.passed) console.log(`  - ${item}`);

    if (this.results.warnings.length) {
      console.log("\nWARNINGS");
      for (const item of this.results.warnings) console.log(`  - ${item}`);
    }

    if (this.results.failed.length) {
      console.log("\nFAILED");
      for (const item of this.results.failed) console.log(`  - ${item}`);
    }

    const pct = total > 0 ? Math.floor((100 * passed) / total) : 0;
    console.log(`\nScore: ${passed}/${total} checks passed (${pct}%)`);
    return this.results.failed.length === 0;
  }
}

function main(): void {
  const argv = process.argv.slice(2);
  if (!argv.length) {
    process.stderr.write("Usage: npx tsx validate-infographic.ts <html_file>\n");
    process.exit(1);
  }
  const validator = new InfographicValidator(argv[0]);
  const success = validator.validate();
  process.exit(success ? 0 : 1);
}

main();
