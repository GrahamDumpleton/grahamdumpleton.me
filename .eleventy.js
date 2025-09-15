const { feedPlugin } = require("@11ty/eleventy-plugin-rss");

// RSS feed cutoff date - posts older than this date will not appear in the RSS feed
const RSS_CUTOFF_DATE = new Date('2025-01-01');

module.exports = function(eleventyConfig) {
  // Copy static assets
  eleventyConfig.addPassthroughCopy("src/assets");
  
  // Copy post images (jpg, jpeg, png, gif, webp files in post directories)
  eleventyConfig.addPassthroughCopy("src/posts/**/*.{jpg,jpeg,png,gif,webp}");
  
  // Copy page images (jpg, jpeg, png, gif, webp files in page directories)
  eleventyConfig.addPassthroughCopy("src/guides/**/*.{jpg,jpeg,png,gif,webp}");
  
  // Add posts collections
  eleventyConfig.addCollection("posts", function(collectionApi) {
    return collectionApi.getFilteredByGlob("src/posts/*/*/*/index.md")
      .filter(post => !post.data.draft) // Exclude draft posts
      .sort((a, b) => new Date(b.date) - new Date(a.date));
  });

  // Add guides collection
  eleventyConfig.addCollection("guides", function(collectionApi) {
    return collectionApi.getFilteredByGlob("src/guides/*/index.md")
      .filter(guide => !guide.data.draft) // Exclude draft guides
      .sort((a, b) => a.data.title.localeCompare(b.data.title));
  });

  // Add RSS feed collection (newest first for proper RSS ordering)
  // The feedPlugin seems to reverse the collection internally, so we sort oldest first
  eleventyConfig.addCollection("rssPosts", function(collectionApi) {
    return collectionApi.getFilteredByGlob("src/posts/*/*/*/index.md")
      .filter(post => !post.data.draft) // Exclude draft posts
      .filter(post => new Date(post.date) >= RSS_CUTOFF_DATE)
      .sort((a, b) => new Date(a.date) - new Date(b.date));
  });
  
  // Add filters
  eleventyConfig.addFilter("date", function(date, format) {
    if (format === 'iso') {
      // If the date is already in YYYY-MM-DD format, return it directly
      if (typeof date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(date)) {
        return date;
      }
      // Otherwise, try to convert to ISO date format
      const dateObj = new Date(date);
      if (isNaN(dateObj.getTime())) {
        // If date is invalid, return the original string or a fallback
        return typeof date === 'string' ? date : '1970-01-01';
      }
      return dateObj.toISOString().split('T')[0]; // YYYY-MM-DD
    }
    const dateObj = new Date(date);
    if (isNaN(dateObj.getTime())) {
      // If date is invalid, return a fallback
      return 'Invalid Date';
    }
    return dateObj.toLocaleDateString('en-AU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  });

  eleventyConfig.addFilter("excerpt", function(content) {
    return content.split('\n').slice(0, 3).join(' ');
  });

  // Add limit filter for arrays
  eleventyConfig.addFilter("limit", function(array, limit) {
    return array.slice(0, limit);
  });

  // Add safe filter for Liquid (equivalent to Nunjucks safe filter)
  eleventyConfig.addLiquidFilter("safe", function(content) {
    return content;
  });

  // Add absolute_url filter for Liquid
  eleventyConfig.addLiquidFilter("absolute_url", function(url) {
    return url;
  });

  // Add length filter for Liquid
  eleventyConfig.addLiquidFilter("length", function(array) {
    return array ? array.length : 0;
  });

  // Add GitHub Open Graph URL cache busting filter
  eleventyConfig.addLiquidFilter("github_og_cache_bust", function(url) {
    if (!url || typeof url !== 'string') return url;
    
    // Check if it's a GitHub Open Graph URL
    const githubOgPattern = /^(https:\/\/opengraph\.githubassets\.com\/)([^\/]+)(\/.+)$/;
    const match = url.match(githubOgPattern);
    
    if (match) {
      const crypto = require('crypto');
      // Generate a random hash for cache busting
      const randomHash = crypto.createHash('md5')
        .update(Date.now().toString() + Math.random().toString())
        .digest('hex')
        .substring(0, 8);
      
      // Replace the hash component with our random hash
      return `${match[1]}${randomHash}${match[3]}`;
    }
    
    // Return original URL if it's not a GitHub Open Graph URL
    return url;
  });

  // Add markdown filter that renders markdown but disables links
  eleventyConfig.addLiquidFilter("markdown_no_links", function(content) {
    if (!content) return '';
    
    // Import markdown-it
    const MarkdownIt = require('markdown-it');
    const md = new MarkdownIt({
      html: false,
      linkify: false,
      breaks: true
    });
    
    // Custom renderer to disable links
    const originalLinkOpen = md.renderer.rules.link_open || function(tokens, idx, options, env, renderer) {
      return renderer.renderToken(tokens, idx, options);
    };
    
    md.renderer.rules.link_open = function(tokens, idx, options, env, renderer) {
      // Replace link with just the text content
      return '';
    };
    
    md.renderer.rules.link_close = function(tokens, idx, options, env, renderer) {
      return '';
    };
    
    return md.render(content);
  });

  // Enable indented code blocks (disabled by default in Eleventy v2.0+)
  eleventyConfig.amendLibrary("md", (mdLib) => mdLib.enable("code"));

  eleventyConfig.addPlugin(feedPlugin, {
		type: "rss", // or "atom", "json"
		outputPath: "/feed.xml",
		collection: {
			name: "rssPosts",
			limit: 10,
		},
		metadata: {
			language: "en",
			title: "Graham Dumpleton",
			subtitle: "Technical blog posts about Python, web development, WSGI, mod_wsgi, and more",
			base: "https://grahamdumpleton.me/",
			author: {
				name: "Graham Dumpleton"
			}
		}
	});

  return {
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
      layouts: "_layouts"
    },
    templateFormats: ["md", "liquid", "njk", "html"],
    markdownTemplateEngine: "liquid",
    htmlTemplateEngine: "liquid",
    // 11ty v3 configuration
    markdown: {
      // Enable syntax highlighting if you want to add it later
      code: false
    }
  };
};
