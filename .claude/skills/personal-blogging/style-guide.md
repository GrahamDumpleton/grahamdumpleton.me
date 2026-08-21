# Writing Style Guide

This guide captures the distinctive voice and patterns of Graham Dumpleton's blog posts, derived from analysing the actual blog content.

## Voice and Tone

- **First person dominant.** Uses "I" extensively: "I thought", "I found", "I added". This is a personal blog and should read as one person sharing their experience.
- **Formal yet conversational.** Professional and technically precise, but not stiff or academic. Reads like a knowledgeable colleague explaining something over coffee.
- **Honest and reflective.** Willing to admit uncertainty, limitations, or mistakes. Doesn't present everything as clean or polished: "I haven't given up, but I also don't want to delay the next release any further."
- **Slightly self-deprecating humour**, used sparingly. Examples: "rather than spending an obsessive amount of time watching anime", "my age is probably showing here."
- **Direct and pragmatic.** States opinions clearly. Doesn't hedge excessively or bury the point.
- **No emojis in prose.** The blog does not use emojis.

## Post Titles

- Sentence case (not Title Case): "Back from the dead", "Lazy imports using wrapt", "Detecting object wrappers"
- Direct statements or declarations, not questions or clickbait
- Often names the specific technology or concept: "Wrapping immutable objects", "Wrapt version 2.0.0"
- Reflective posts may use more evocative titles: "Back from the dead", "Developer Advocacy in 2026"

## Post Structure

- **Opening paragraph**: Sets context or establishes the problem. Often starts with a personal angle or the motivation behind the post. Never opens with "In this post I will..." or similar meta-framing. Dives straight into the subject.
- **Section headings**: Uses `##` for major sections, `###` for subsections. Headings are descriptive and informative, not generic. Good: "Object proxy hierarchy", "What's to be learned". Bad: "Introduction", "Details", "Conclusion".
- **Closing section**: Typically summarises takeaways or signals next steps. Often titled "What's next", "What's to be learned", or "Initial Reflections". Not always present in shorter posts.
- **Paragraphs**: Moderate length. Each paragraph develops one idea. Good flow between paragraphs with natural transitions.

## Transitions and Characteristic Phrases

These phrases appear naturally throughout the blog. Use them when appropriate but don't force them:

- "That said, ..." for introducing a qualification or counterpoint
- "Either way, ..." for moving past a branching discussion
- "Just to complicate things even more, ..." for adding complexity to an explanation
- "Anyway, ..." for transitioning or wrapping up a tangent
- "The end result is that..." for summarising an outcome
- "Fingers crossed" for cautious optimism
- Frequent parenthetical asides for brief additional context
- "The reason for this is that..." for explaining causation

## Code Examples

- Python is the primary language. Use ` ```python ` for syntax-highlighted blocks when writing new posts, though many existing posts use plain ` ``` `.
- **Progressive complexity**: Start with a simple example, then build up to the complex case. Layer on nuance.
- **Explanation first, then code**: Introduce the concept or problem in prose before showing the code block.
- **Output shown separately**: When showing code output, use a separate code block, often preceded by "Running this the output is:" or "The result being that..." or "verifying that..."
- Code examples should be realistic and runnable, not pseudocode.
- Uses backticks liberally for inline code references: `wrapt`, `ObjectProxy`, `__init__()`, `sys.modules`.

## Post Length by Type

- **Announcements** (~300 to 500 words): Brief and to the point. States what happened, why it matters, links to details. No deep technical explanation. Example: "Wrapt version 2.0.0".
- **Personal/reflective posts** (~800 to 1500 words): More narrative, tells a story. Sets up personal context, reflects honestly on challenges or industry observations. Example: "Back from the dead", "Developer Advocacy in 2026".
- **Technical deep dives** (~1500 to 3000 words): Extensive code examples, progressive problem exploration. Builds from simple case to edge cases to solution. Example: "Wrapping immutable objects", "Lazy imports using wrapt".

Length should match topic complexity, not an arbitrary target.

## Addressing the Reader

- Second person ("you") used sparingly and directly: "if you try and access...", "you might be thinking..."
- Does not overuse "we" as a false inclusive. Occasionally used to create community feeling: "we like to recite".
- Assumes the reader has technical knowledge (Python experience, familiarity with software development concepts) but doesn't assume deep expertise in the specific topic being discussed.

## Links and References

- Links strategically to relevant resources: PEPs, PyPI packages, GitHub repos, ReadTheDocs
- Frequently cross-links to own previous blog posts when building on earlier work
- Sparse on images, most posts are text-and-code dominant
- When discussing external ideas or feedback, properly attributes them

## Things to Avoid

### AI-generated text indicators

Be especially vigilant about punctuation, syntax, and stylistic patterns that are known markers of AI-generated content:

- **No em dashes.** Do not use the em dash character (—). Graham does not use em dashes in his writing. Use commas, semicolons, parentheses, or restructure the sentence instead.
- **No en dashes in prose.** Do not use en dashes (–) as punctuation. Use hyphens (-) for compound words and "to" for ranges (e.g., "2019 to 2025" not "2019–2025").
- **No AI filler phrases.** Never use: "Let's dive in", "In this comprehensive guide", "Without further ado", "In this blog post, we will explore", "Let's get started", "It's worth noting that", "Interestingly enough". These are dead giveaways of AI-generated content.
- **No formulaic sentence openers.** Avoid starting consecutive sentences or paragraphs with the same structure. Do not open paragraphs with "Additionally, ...", "Furthermore, ...", "Moreover, ...", "Importantly, ..." or similar adverbial openers that AI tends to overuse.
- **No excessive bold for emphasis.** Do not bold phrases mid-paragraph for emphasis. Graham uses bold sparingly and only in structured contexts (like the "What the AI told me:" / "My take:" labels in the developer advocacy post). In regular prose, let the words carry the weight.
- **No colon-heavy listing patterns.** Avoid the AI pattern of "Topic: explanation. Topic: explanation." within prose paragraphs.
- **No sycophantic or overly enthusiastic tone.** Do not use "fantastic", "excellent", "powerful", "incredibly", "absolutely" or similar amplifiers that AI defaults to.
- **No artificial parallelism.** Do not construct lists of three or more items that all follow an identical grammatical template. Vary sentence structure naturally.

### Content and structure anti-patterns

- **No bullet-point-driven prose.** Bullet lists are for guides listing related posts. Blog post body text uses flowing paragraphs.
- **No clickbait titles.** No "You Won't Believe..." or "The Ultimate Guide to..."
- **No marketing language or hype.** No "game-changing", "revolutionary", "next-level".
- **No unnecessary images or diagrams** unless specifically relevant and requested.
- **No over-use of headings** in short posts. An announcement or short reflection may have zero or one heading.
- **No excessive hedging.** State things directly rather than padding with "It might be worth considering that perhaps..."
