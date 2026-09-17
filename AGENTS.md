# Blog Project Instructions

This is the source repository for grahamdumpleton.me, a personal technical blog built with Eleventy (11ty).

## Writing Blog Content

When planning, writing or editing blog content, use the `/personal-blogging` skill which provides detailed writing style guidance, front matter conventions, and topic context.

Blog posts are standalone content — each new post covers a new topic. When creating a new post, do NOT explore or read old blog posts. The `/personal-blogging` skill already provides all the style, voice, and convention guidance needed. Only reference or cross-link previous posts if explicitly asked, such as when extending a topic from an earlier post.

## Scratch Directory

The `scratch/` directory is not part of the git repo (its `.gitignore` excludes everything but itself). It holds temporary working files for use by AI agents, such as reference material given to an agent, plans for a post or series of posts an agent is asked to generate, and example scripts used to validate code in a draft. Its contents come and go, so never reference `scratch/` files by name from posts, templates or other files that will be committed.

## Validating a Build

The user often has the dev server (`npm run dev`) running while working on a post. It serves the `_site` directory from disk, and draft posts are only included in listings when the site is built by the dev server. A plain `npm run build` writes to the same `_site` directory without drafts, so running it while the dev server is up makes draft posts vanish from the home page and post listings until the next rebuild.

When validating that a draft builds, always build into the scratch directory instead:

```
npx eleventy --output=scratch/_site
```

Never run `npm run build` to check a draft.

## Git Conventions

- Do not include Claude Code session URLs (e.g., `https://claude.ai/code/...`) in commit messages or pull request bodies.
- Never include a `Co-Authored-By` line (or any other co-author attribution) in commit messages.

## Quick Reference

- **Build**: `npm run build`
- **Dev server**: `npm run dev`
- **Posts**: `src/posts/YYYY/MM/post-slug/index.md`
- **Guides**: `src/guides/guide-name/index.md`
- **Layouts**: `src/_layouts/` (base, post, guide)
