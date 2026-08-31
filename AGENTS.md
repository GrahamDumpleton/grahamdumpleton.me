# Blog Project Instructions

This is the source repository for grahamdumpleton.me, a personal technical blog built with Eleventy (11ty).

## Writing Blog Content

When planning, writing or editing blog content, use the `/personal-blogging` skill which provides detailed writing style guidance, front matter conventions, and topic context.

Blog posts are standalone content — each new post covers a new topic. When creating a new post, do NOT explore or read old blog posts. The `/personal-blogging` skill already provides all the style, voice, and convention guidance needed. Only reference or cross-link previous posts if explicitly asked, such as when extending a topic from an earlier post.

## Scratch Directory

The `scratch/` directory is not part of the git repo (its `.gitignore` excludes everything but itself). It holds temporary working files for use by AI agents, such as reference material given to an agent, plans for a post or series of posts an agent is asked to generate, and example scripts used to validate code in a draft. Its contents come and go, so never reference `scratch/` files by name from posts, templates or other files that will be committed.

## Git Conventions

- Do not include Claude Code session URLs (e.g., `https://claude.ai/code/...`) in commit messages or pull request bodies.
- Never include a `Co-Authored-By` line (or any other co-author attribution) in commit messages.

## Quick Reference

- **Build**: `npm run build`
- **Dev server**: `npm run dev`
- **Posts**: `src/posts/YYYY/MM/post-slug/index.md`
- **Guides**: `src/guides/guide-name/index.md`
- **Layouts**: `src/_layouts/` (base, post, guide)
