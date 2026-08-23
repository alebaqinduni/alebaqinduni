# Phase 2: GitHub Stats Cards Configuration
# Self-hosted instance ready at: https://github-readme-stats-one-jade-66.vercel.app

## Stats Cards Block (Ready to add to README)

This block includes:
1. Streak Card (100% width)
2. GitHub Stats Card (49% width)
3. Top Languages Card (49% width)

All themed to your custom palette:
- Primary: #A78BFA (Purple)
- Accent: #10B981 (Green)
- Background: #0A101F (Dark)
- UI Chrome: #0891B2 (Cyan)

---

## 📈 Markdown Block (Copy & Paste to README)

```markdown
## 📊 GitHub Statistics

![GitHub Streak](https://github-readme-stats-one-jade-66.vercel.app/api/streak-stats?user=alebaqinduni&theme=dark&hide_border=true&background=0A101F&stroke=0891B2&ring=A78BFA&fire=10B981&currStreakLabel=E0E7FF)

<div align="center">
  <img src="https://github-readme-stats-one-jade-66.vercel.app/api?username=alebaqinduni&show_icons=true&hide_rank=true&theme=dark&bg_color=0A101F&title_color=A78BFA&text_color=E0E7FF&icon_color=10B981&border_color=0891B2&hide_border=true" alt="Areeba's GitHub Stats" width="49%" />
  <img src="https://github-readme-stats-one-jade-66.vercel.app/api/top-langs/?username=alebaqinduni&layout=compact&theme=dark&bg_color=0A101F&title_color=A78BFA&text_color=E0E7FF&border_color=0891B2&hide_border=true" alt="Top Languages" width="49%" />
</div>
```

---

## 🎨 Color Palette Explanation

| Element | Color | Hex | Purpose |
|---------|-------|-----|---------|
| Primary Title | Purple | #A78BFA | Matches portrait dither color |
| Background | Dark | #0A101F | GitHub dark mode background |
| UI Chrome | Cyan | #0891B2 | Border, accent elements |
| Accent | Green | #10B981 | Highlights, icons |
| Text | Light Indigo | #E0E7FF | Main text color |

---

## ℹ️ Why `hide_rank=true`?

The GitHub rank is weighted heavily by **star count**, which:
- Favors prolific repo creators
- Misleads for newer accounts
- Doesn't reflect skill or contribution quality

For your profile as a student + builder, hiding rank shows your **actual stats** (contributions, languages, streak) without the popularity bias.

---

## ✅ Next Steps

1. **Copy the markdown block** above (the full code fence)
2. **Paste it** into your `projects` README.md (after the banner section)
3. **Test in browser** to verify colors render correctly
4. **Commit & push** to your repo

Once approved, move to **Phase 3: Contribution Snake** 🐍

---

## 🔧 Customization Notes

If you want to tweak:
- **Colors:** Change any hex code in the URLs
- **Layout:** Try `layout=waffle` or `layout=pie` for top-langs
- **Theme:** Use theme names like `dark`, `dracula`, `synthwave` (but custom colors override)

Example variations:
- Streak only: `![Streak](https://github-readme-stats-one-jade-66.vercel.app/api/streak-stats?user=alebaqinduni&theme=dark)`
- Stats + heatmap: Add `&type=calendar` parameter
- Icons: `&show_icons=true` (already included)
