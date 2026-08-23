# Phase 3: Contribution Snake Setup Guide

## 📋 Manual Setup Instructions

Since I cannot directly create files in the `.github` folder, you need to manually copy the workflow file.

---

## 🐍 Workflow File Content

**Copy this entire block and paste it as `.github/workflows/snake.yml`**

```yaml
name: Generate Contribution Snake

on:
  schedule:
    # Run every 12 hours
    - cron: '0 */12 * * *'
  # Allow manual trigger
  workflow_dispatch:
  # Run on push to main
  push:
    branches:
      - main

permissions:
  contents: write

jobs:
  generate-snake:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Generate snake SVG (Dark Mode)
        uses: Platane/snk/svg-only@v3
        with:
          github_user_name: alebaqinduni
          outputs: |
            dist/snake-dark.svg?palette=dark&color_dots=0A101F,10B981,0891B2,A78BFA,E0E7FF

      - name: Generate snake SVG (Light Mode)
        uses: Platane/snk/svg-only@v3
        with:
          github_user_name: alebaqinduni
          outputs: |
            dist/snake-light.svg?palette=light&color_dots=FFFFFF,10B981,0891B2,A78BFA,0A101F

      - name: Push to output branch
        uses: crazy-max/ghaction-github-pages@v3.1.0
        with:
          target_branch: output
          build_dir: dist
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## ✅ Step-by-Step Setup

### **Step 1: Create the Workflow File**

1. Open GitHub: https://github.com/alebaqinduni/projects
2. Click **"Add file"** (green button) → **"Create new file"**
3. In the **filename field**, type exactly:
   ```
   .github/workflows/snake.yml
   ```
4. Paste the **Workflow File Content** (above) into the editor
5. Click **"Commit changes"** at the bottom
6. Add commit message: `Phase 3: Add contribution snake workflow`
7. Click **"Commit directly to the main branch"**

### **Step 2: Enable Workflow Permissions**

1. Go to: https://github.com/alebaqinduni/projects/settings/actions
2. Scroll to **"Workflow permissions"** section
3. Select radio button: **"Read and write permissions"**
4. Click **"Save"**

### **Step 3: Trigger the Workflow Manually**

1. Go to: https://github.com/alebaqinduni/projects/actions
2. Click on **"Generate Contribution Snake"** (on the left sidebar)
3. Click **"Run workflow"** (blue button on the right)
4. Select branch: **main**
5. Click **"Run workflow"**
6. Watch the progress! 🐍

### **Step 4: Check the Output**

After ~2-3 minutes:
1. Go to: https://github.com/alebaqinduni/projects/branches
2. Find the **"output"** branch
3. Inside it, you should see:
   - `snake-dark.svg`
   - `snake-light.svg`

---

## 📝 Add to Your README

Once the workflow completes successfully, add this to your README:

```markdown
## 🐍 Contribution Graph

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/alebaqinduni/projects/output/snake-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/alebaqinduni/projects/output/snake-light.svg">
  <img alt="Contribution snake" src="https://raw.githubusercontent.com/alebaqinduni/projects/output/snake-dark.svg">
</picture>
```

---

## 🔄 Workflow Schedule

- **Automatic:** Runs every 12 hours
- **Manual:** Anytime from the Actions tab
- **On Push:** Runs when you push to `main`

---

## 🎨 Color Palette (Configured)

| Mode | Background | Accent | Highlight |
|------|------------|--------|-----------|
| Dark | #0A101F | #10B981 | #A78BFA |
| Light | #FFFFFF | #10B981 | #0891B2 |

---

## ⚠️ Troubleshooting

If the workflow fails:

1. **Check permissions:** Settings → Actions → "Read and write"
2. **Check branch:** Workflow is configured for `main` branch
3. **Check output branch:** https://github.com/alebaqinduni/projects/branches
4. **View logs:** Go to Actions tab → Click the failed run → View details

---

## ✨ Next: Phase 4

Once verified working:
- [ ] Workflow runs successfully (green ✅)
- [ ] `output` branch created with SVGs
- [ ] README updated with snake image

**Tell me when complete and we'll move to Phase 4: Social Badges!** 🚀
