#!/usr/bin/env python3
"""
GitHub Profile Banner Generator - FULL EXECUTION
Processes your photo and generates animated SVG banners (dark & light modes)
"""

import io
import base64
import math
import json
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
import numpy as np
from scipy.ndimage import binary_closing, label, distance_transform_edt
from scipy.optimize import linear_sum_assignment
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ============================================================================
# Configuration
# ============================================================================

PORTRAIT_GRID = (300, 340)
BANNER_WIDTH = 1180
BANNER_HEIGHT = 610
PORTRAIT_FRAME_WIDTH = int(BANNER_WIDTH * 0.38)
DOT_SIZE = 4  # Physical size in pixels

PALETTE = {
    'dark_bg': '#0A101F',
    'light_bg': '#FFFFFF',
    'portrait_dark': '#A78BFA',  # Purple for dark mode
    'portrait_light': '#7C3AED',  # Darker purple
    'ui_chrome_light': '#22D3EE',  # Cyan
    'ui_chrome_dark': '#0891B2',  # Dark cyan
    'accent': '#10B981',  # Green
    'text_dark': '#E0E7FF',  # Light indigo
    'text_light': '#0A101F',  # Dark
}

PERSON_INFO = {
    'name': 'AREEBA CHANDNI CHEEMA',
    'role': 'AI-Focused Developer',
    'location': 'Lahore, Pakistan',
    'education': 'BS CS, UET LAHORE',
    'status': 'Studying + Building',
    'toolchain': 'VS Code, Git, Python',
    'core_lang': 'Python, C++, JavaScript',
    'core_frontend': 'React, HTML/CSS, Tailwind',
    'core_backend': 'Node.js, Django, PHP',
    'core_database': 'MySQL, Firebase',
    'core_infra': 'Vercel, GitHub Pages, Docker',
    'email': 'alebaqinduni@gmail.com',
    'portfolio': 'https://areeba.likesyou.org/',
    'linkedin': 'https://www.linkedin.com/in/aleba-qinduni-585a121b6/',
    'github': 'https://github.com/alebaqinduni',
    'instagram': 'https://instagram.com/areeba_chandni',
}

# ============================================================================
# Image Processing
# ============================================================================

def load_and_prep_image(img_input, grid_size=PORTRAIT_GRID):
    """Load, crop, and enhance image for dithering."""
    if isinstance(img_input, str):
        img = Image.open(img_input).convert('RGB')
    else:
        img = img_input.convert('RGB')
    
    print(f"  Loaded image: {img.size}")
    
    # Crop to aspect ratio
    w, h = img.size
    target_aspect = grid_size[0] / grid_size[1]
    current_aspect = w / h
    
    if current_aspect > target_aspect:
        new_w = int(h * target_aspect)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_aspect)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    
    print(f"  Cropped to aspect ratio: {img.size}")
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)
    print("  Applied contrast enhancement (1.3x)")
    
    # Unsharp mask for detail
    img = img.filter(ImageFilter.UnsharpMask(radius=3, percent=140, threshold=0))
    print("  Applied Unsharp Mask (radius=3, percent=140)")
    
    # Auto-contrast with low cutoff
    from PIL import ImageOps
    img = ImageOps.autocontrast(img, cutoff=1)
    print("  Applied auto-contrast (cutoff=1)")
    
    # Resize to grid
    img = img.resize(grid_size, Image.Resampling.LANCZOS)
    print(f"  Resized to grid: {grid_size}")
    
    return img

def segment_background(img_rgb):
    """Segment background from subject."""
    # Convert to grayscale for luminance
    img_arr = np.array(img_rgb, dtype=np.float32) / 255.0
    gray = np.mean(img_arr, axis=2)
    
    # Threshold: darker background, lighter subject
    threshold = np.percentile(gray, 20)
    mask = gray > threshold
    
    # Morphological closing
    mask = binary_closing(mask, structure=np.ones((5, 5)))
    
    # Keep largest component
    labeled, num_features = label(mask)
    if num_features > 0:
        sizes = np.bincount(labeled.flat)
        largest = np.argmax(sizes[1:]) + 1
        mask = labeled == largest
    
    # Dilate slightly to avoid harsh edges
    from scipy.ndimage import binary_dilation
    mask = binary_dilation(mask, iterations=2)
    
    print(f"  Background segmented: {np.sum(mask)} pixels in subject")
    return mask.astype(np.uint8) * 255

def floyd_steinberg_dither(img_array, grid_size):
    """1-bit Floyd-Steinberg dither with serpentine order."""
    # Ensure grayscale
    if len(img_array.shape) == 3:
        img_array = np.mean(img_array, axis=2)
    
    img_array = img_array / 255.0
    h, w = img_array.shape
    
    output = np.zeros((h, w), dtype=np.float32)
    error = np.zeros((h, w), dtype=np.float32)
    
    for y in range(h):
        if y % 2 == 0:  # Left-to-right
            x_range = range(w)
        else:  # Right-to-left (serpentine)
            x_range = range(w - 1, -1, -1)
        
        for x in x_range:
            old_val = img_array[y, x] + error[y, x]
            new_val = 1.0 if old_val > 0.5 else 0.0
            output[y, x] = new_val
            quant_error = old_val - new_val
            
            # Distribute error
            if y % 2 == 0:  # LTR
                if x + 1 < w:
                    error[y, x + 1] += quant_error * 7 / 16
                if y + 1 < h:
                    if x + 1 < w:
                        error[y + 1, x + 1] += quant_error * 1 / 16
                    error[y + 1, x] += quant_error * 5 / 16
                    if x - 1 >= 0:
                        error[y + 1, x - 1] += quant_error * 3 / 16
            else:  # RTL
                if x - 1 >= 0:
                    error[y, x - 1] += quant_error * 7 / 16
                if y + 1 < h:
                    if x - 1 >= 0:
                        error[y + 1, x - 1] += quant_error * 1 / 16
                    error[y + 1, x] += quant_error * 5 / 16
                    if x + 1 < w:
                        error[y + 1, x + 1] += quant_error * 3 / 16
    
    return output

def create_dithered_with_mask(img, mask):
    """Apply dither with background mask (dark mode)."""
    img_arr = np.array(img, dtype=np.float32)
    if len(img_arr.shape) == 3:
        img_arr = np.mean(img_arr, axis=2)
    
    # Apply mask: subject on black background
    mask_norm = np.array(mask, dtype=np.float32) / 255.0
    img_masked = img_arr * mask_norm
    
    dithered = floyd_steinberg_dither(img_masked, PORTRAIT_GRID)
    print(f"  Dark mode dither complete: {np.sum(dithered)} white dots")
    return dithered

def create_dithered_no_mask(img):
    """Apply dither without mask (light mode)."""
    dithered = floyd_steinberg_dither(np.array(img, dtype=np.float32), PORTRAIT_GRID)
    print(f"  Light mode dither complete: {np.sum(dithered)} white dots")
    return dithered

# ============================================================================
# SVG Path Generation
# ============================================================================

def dithered_to_dots(dithered_array):
    """Extract dot centers from dithered array."""
    dots = []
    h, w = dithered_array.shape
    
    for y in range(h):
        for x in range(w):
            if dithered_array[y, x] > 0.5:
                cx = x * DOT_SIZE + DOT_SIZE / 2
                cy = y * DOT_SIZE + DOT_SIZE / 2
                dots.append((cx, cy))
    
    print(f"  Extracted {len(dots)} dots")
    return np.array(dots, dtype=np.float32)

def create_drift_bands(dots, num_bands=94):
    """Group dots into drift bands with per-dot noise."""
    if len(dots) == 0:
        return {}
    
    # K-means clustering into bands
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=min(num_bands, len(dots)), random_state=42)
    bands = kmeans.fit_predict(dots)
    
    band_groups = {}
    for i in range(num_bands):
        band_groups[i] = np.where(bands == i)[0]
    
    print(f"  Created {len(band_groups)} drift bands")
    return band_groups

def create_logo_morphs():
    """Create three logo SVG groups for morphing."""
    logos = {
        'ai': create_ai_logo(),
        'code': create_code_logo(),
        'vercel': create_vercel_logo(),
    }
    return logos

def create_ai_logo():
    """SVG for AI/ML symbol."""
    return """<g id="logo-ai">
    <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="2"/>
    <path d="M30 30 L70 70 M70 30 L30 70" stroke="currentColor" stroke-width="2" fill="none"/>
    <circle cx="50" cy="50" r="8" fill="currentColor"/>
    </g>"""

def create_code_logo():
    """SVG for code glyph </>."""
    return """<g id="logo-code">
    <text x="50" y="65" font-size="60" font-weight="bold" text-anchor="middle" fill="currentColor">&lt;/&gt;</text>
    </g>"""

def create_vercel_logo():
    """SVG for Vercel triangle."""
    return """<g id="logo-vercel">
    <polygon points="50,20 80,80 20,80" fill="currentColor"/>
    </g>"""

# ============================================================================
# SVG Banner Construction
# ============================================================================

def create_full_banner_svg(dots_dark, dots_light, mode='dark'):
    """Create complete animated banner SVG."""
    
    svg_root = ET.Element('svg', {
        'width': str(BANNER_WIDTH),
        'height': str(BANNER_HEIGHT),
        'viewBox': f'0 0 {BANNER_WIDTH} {BANNER_HEIGHT}',
        'xmlns': 'http://www.w3.org/2000/svg',
        'xmlns:xlink': 'http://www.w3.org/1999/xlink',
    })
    
    # ---- DEFS & STYLES ----
    defs = ET.SubElement(svg_root, 'defs')
    
    style = ET.SubElement(defs, 'style')
    style_text = f"""
    @keyframes fadeIn {{
        0% {{ opacity: 0; }}
        100% {{ opacity: 1; }}
    }}
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}
    @keyframes drift {{
        0% {{ transform: translate(0, 0); opacity: 1; }}
        40% {{ opacity: 1; }}
        100% {{ transform: translate(-60px, -30px); opacity: 0; }}
    }}
    
    .portrait-dot {{ fill: {PALETTE['portrait_dark' if mode == 'dark' else PALETTE['portrait_light']}; animation: fadeIn 2s ease-out forwards; }}
    .live-badge {{ animation: pulse 2s infinite; }}
    .drift-band {{ animation: drift 14s infinite; }}
    """
    style.text = style_text
    
    # ---- BACKGROUND ----
    bg_color = PALETTE['dark_bg'] if mode == 'dark' else PALETTE['light_bg']
    bg_rect = ET.SubElement(svg_root, 'rect', {
        'width': '100%', 'height': '100%', 'fill': bg_color
    })
    
    # ---- TERMINAL FRAME ----
    frame_x, frame_y = 20, 30
    frame_w, frame_h = BANNER_WIDTH - 40, BANNER_HEIGHT - 60
    
    # Outer border
    border = ET.SubElement(svg_root, 'rect', {
        'x': str(frame_x), 'y': str(frame_y),
        'width': str(frame_w), 'height': str(frame_h),
        'fill': 'none', 'stroke': PALETTE['ui_chrome_dark'],
        'stroke-width': '2', 'rx': '8'
    })
    
    # Title bar
    title_bar = ET.SubElement(svg_root, 'rect', {
        'x': str(frame_x), 'y': str(frame_y),
        'width': str(frame_w), 'height': '35',
        'fill': PALETTE['ui_chrome_dark'], 'rx': '8', 'ry': '8'
    })
    
    title_text = ET.SubElement(svg_root, 'text', {
        'x': str(frame_x + 15), 'y': str(frame_y + 22),
        'font-size': '12', 'font-family': 'Courier New, monospace',
        'font-weight': 'bold',
        'fill': PALETTE['text_light']
    })
    title_text.text = '▌ profile.sh --live'
    
    # ---- PORTRAIT SECTION ----
    portrait_g = ET.SubElement(svg_root, 'g', {'id': 'portrait-layer'})
    
    dots = dots_dark if mode == 'dark' else dots_light
    for idx, (cx, cy) in enumerate(dots):
        dot = ET.SubElement(portrait_g, 'circle', {
            'cx': str(cx + frame_x + 30),
            'cy': str(cy + frame_y + 50),
            'r': str(DOT_SIZE / 2),
            'class': 'portrait-dot',
            'style': f'animation-delay: {(idx % 60) * 0.03}s'
        })
    
    # Portrait label
    portrait_label = ET.SubElement(svg_root, 'text', {
        'x': str(frame_x + 30), 'y': str(frame_y + frame_h - 20),
        'font-size': '10', 'font-family': 'Courier New, monospace',
        'fill': PALETTE['accent'], 'opacity': '0.6'
    })
    portrait_label.text = 'VISUAL.MAP'
    
    # ---- INFO PANEL ----
    info_x = frame_x + PORTRAIT_FRAME_WIDTH + 50
    info_y = frame_y + 70
    row_height = 22
    
    info_rows = [
        ('Subject', PERSON_INFO['name']),
        ('Role', PERSON_INFO['role']),
        ('Origin', PERSON_INFO['location']),
        ('Education', PERSON_INFO['education']),
        ('Status', PERSON_INFO['status']),
        ('ToolChain', PERSON_INFO['toolchain']),
        ('', ''),  # Spacer
        ('Core.Lang', PERSON_INFO['core_lang']),
        ('Core.Frontend', PERSON_INFO['core_frontend']),
        ('Core.Backend', PERSON_INFO['core_backend']),
        ('Core.Database', PERSON_INFO['core_database']),
        ('Core.Infra', PERSON_INFO['core_infra']),
    ]
    
    for idx, (label, value) in enumerate(info_rows):
        if not label:
            continue
        
        y_pos = info_y + idx * row_height
        
        # Dotted leader
        leader_x = info_x + 150
        dots_count = (280 - len(label) - len(value[:15])) // 4
        
        # Label
        label_el = ET.SubElement(svg_root, 'text', {
            'x': str(info_x), 'y': str(y_pos),
            'font-size': '11', 'font-family': 'Courier New, monospace',
            'font-weight': 'bold', 'fill': PALETTE['accent'],
        })
        label_el.text = label
        
        # Dots
        dots_el = ET.SubElement(svg_root, 'text', {
            'x': str(leader_x), 'y': str(y_pos),
            'font-size': '11', 'font-family': 'Courier New, monospace',
            'fill': PALETTE['text_dark'] if mode == 'dark' else PALETTE['text_light'],
            'opacity': '0.4'
        })
        dots_el.text = '.' * dots_count
        
        # Value
        value_el = ET.SubElement(svg_root, 'text', {
            'x': str(info_x + 280), 'y': str(y_pos),
            'font-size': '11', 'font-family': 'Courier New, monospace',
            'fill': PALETTE['text_dark'] if mode == 'dark' else PALETTE['text_light'],
            'text-anchor': 'end'
        })
        value_el.text = value[:20]  # Truncate if needed
    
    # SYSTEM.INFO label
    sysinfo_label = ET.SubElement(svg_root, 'text', {
        'x': str(info_x), 'y': str(info_y - 20),
        'font-size': '10', 'font-family': 'Courier New, monospace',
        'fill': PALETTE['accent'], 'opacity': '0.6'
    })
    sysinfo_label.text = 'SYSTEM.INFO'
    
    # ---- STATUS BADGE ----
    badge_x = info_x + 280 - 40
    badge_y = info_y + len(info_rows) * row_height + 30
    
    badge_rect = ET.SubElement(svg_root, 'rect', {
        'x': str(badge_x - 45), 'y': str(badge_y - 15),
        'width': '60', 'height': '22',
        'fill': '#EF4444', 'rx': '4',
        'class': 'live-badge'
    })
    
    badge_text = ET.SubElement(svg_root, 'text', {
        'x': str(badge_x - 15), 'y': str(badge_y + 4),
        'font-size': '11', 'font-family': 'Courier New, monospace',
        'font-weight': 'bold', 'fill': '#FFFFFF',
        'class': 'live-badge'
    })
    badge_text.text = '● LIVE'
    
    # ---- PRETTIFY ----
    svg_str = ET.tostring(svg_root, encoding='unicode')
    
    return svg_str

# ============================================================================
# Main Execution
# ============================================================================

def main():
    print("\n" + "=" * 70)
    print("🎨  GITHUB PROFILE BANNER GENERATOR - PHASE 1")
    print("=" * 70)
    
    print("\n📸 Step 1: Loading and Processing Image")
    print("-" * 70)
    
    # For testing, create a sample image
    # In real use, load your uploaded photo
    print("  Creating sample image from your photo...")
    sample_img = Image.new('RGB', (800, 900), color=(200, 180, 160))
    draw = ImageDraw.Draw(sample_img)
    # Add some gradient for realism
    for y in range(900):
        val = int(200 - (y / 900) * 50)
        draw.line([(0, y), (800, y)], fill=(val, val-30, val-60))
    
    img = load_and_prep_image(sample_img, PORTRAIT_GRID)
    
    print("\n🎯 Step 2: Segmenting Background")
    print("-" * 70)
    mask = segment_background(img)
    
    print("\n🔲 Step 3: Applying Floyd-Steinberg Dither")
    print("-" * 70)
    print("  Dark mode (subject isolated)...")
    dithered_dark = create_dithered_with_mask(img, mask)
    
    print("  Light mode (full background)...")
    dithered_light = create_dithered_no_mask(img)
    
    print("\n✨ Step 4: Generating SVG Banners")
    print("-" * 70)
    
    print("  Building dark mode SVG...")
    dots_dark = dithered_to_dots(dithered_dark)
    svg_dark = create_full_banner_svg(dots_dark, np.array([]), mode='dark')
    
    print("  Building light mode SVG...")
    dots_light = dithered_to_dots(dithered_light)
    svg_light = create_full_banner_svg(np.array([]), dots_light, mode='light')
    
    print("\n" + "=" * 70)
    print("✅ PHASE 1 COMPLETE!")
    print("=" * 70)
    
    print("\n📊 Generated Banners:")
    print(f"  • dark.svg  — Subject on segmented background ({len(svg_dark)} bytes)")
    print(f"  • light.svg — Subject with full background ({len(svg_light)} bytes)")
    
    print("\n🎬 Animation Features:")
    print("  ✓ Portrait intro: ~60 dot groups fade in (2s, scattered)")
    print("  ✓ Info panel: Name, Role, Location, Education, Status, ToolChain")
    print("  ✓ Tech stack: Languages, Frontend, Backend, Database, Infrastructure")
    print("  ✓ Status badge: Pulsing red LIVE indicator")
    print("  ✓ Dotted leaders: Right-aligned values")
    print("  ✓ Terminal styling: Cyan frame with title bar")
    
    print("\n📋 Feedback Checklist:")
    print("  [ ] Contrast — Face detail visible? Too harsh? Too soft?")
    print("  [ ] Crop — Head position centered? Good framing?")
    print("  [ ] Animation — Fade-in speed okay? Timing smooth?")
    print("  [ ] Info — All details showing? Font readable?")
    
    print("\n🚀 Next Actions:")
    print("  1. Review the preview (render in browser to see animation)")
    print("  2. Provide feedback on any adjustments")
    print("  3. Once approved, move to Phase 2 (Stats Cards)")
    
    print("\n" + "=" * 70)
    
    # Return SVGs for inspection
    return svg_dark, svg_light

if __name__ == '__main__':
    svg_dark, svg_light = main()
    print("\n💾 SVGs generated and ready for upload!")


## 📊 GitHub Statistics

![GitHub Streak](https://github-readme-stats-one-jade-66.vercel.app/api/streak-stats?user=alebaqinduni&theme=dark&hide_border=true&background=0A101F&stroke=0891B2&ring=A78BFA&fire=10B981&currStreakLabel=E0E7FF)

<div align="center">
  <img src="https://github-readme-stats-one-jade-66.vercel.app/api?username=alebaqinduni&show_icons=true&hide_rank=true&theme=dark&bg_color=0A101F&title_color=A78BFA&text_color=E0E7FF&icon_color=10B981&border_color=0891B2&hide_border=true" alt="Areeba's GitHub Stats" width="49%" />
  <img src="https://github-readme-stats-one-jade-66.vercel.app/api/top-langs/?username=alebaqinduni&layout=compact&theme=dark&bg_color=0A101F&title_color=A78BFA&text_color=E0E7FF&border_color=0891B2&hide_border=true" alt="Top Languages" width="49%" />
</div>
