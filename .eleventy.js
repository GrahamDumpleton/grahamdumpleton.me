const { feedPlugin } = require("@11ty/eleventy-plugin-rss");

// RSS feed cutoff date - posts older than this date will not appear in the RSS feed
const RSS_CUTOFF_DATE = new Date('2025-01-01');

module.exports = function(eleventyConfig) {
  // Copy static assets
  eleventyConfig.addPassthroughCopy("src/assets");
  
  // Copy post images (jpg, jpeg, png, gif, webp files in post directories)
  eleventyConfig.addPassthroughCopy("src/posts/**/*.{jpg,jpeg,png,gif,webp}");
  
  // Add collections
  eleventyConfig.addCollection("posts", function(collectionApi) {
    return collectionApi.getFilteredByGlob("src/posts/*/*/*/index.md")
      .sort((a, b) => new Date(b.date) - new Date(a.date));
  });

  // Add RSS feed collection (newest first for proper RSS ordering)
  // The feedPlugin seems to reverse the collection internally, so we sort oldest first
  eleventyConfig.addCollection("rssPosts", function(collectionApi) {
    return collectionApi.getFilteredByGlob("src/posts/*/*/*/index.md")
      .filter(post => new Date(post.date) >= RSS_CUTOFF_DATE)
      .sort((a, b) => new Date(a.date) - new Date(b.date));
  });
  
  // Add filters
  eleventyConfig.addFilter("date", function(date, format) {
    const dateObj = new Date(date);
    if (format === 'iso') {
      return dateObj.toISOString().split('T')[0]; // YYYY-MM-DD
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
