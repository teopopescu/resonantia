import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { contentfulClient } from "@/lib/contentful";
import { demoPosts, type BlogPost } from "@/lib/blog-data";

async function getBlogPosts(): Promise<BlogPost[]> {
  try {
    const entries = await contentfulClient.getEntries({
      content_type: "blogPost",
      order: ["-sys.createdAt"],
    });

    if (entries.items.length > 0) {
      return entries.items.map((item: any) => ({
        slug: item.fields.slug as string,
        title: item.fields.title as string,
        author: (item.fields.author as string) || "Teodor Popescu",
        date: new Date(
          (item.fields.date as string) || item.sys.createdAt
        ).toLocaleDateString("en-US", {
          year: "numeric",
          month: "long",
          day: "numeric",
        }),
        tags: (item.fields.tags as string[]) || [],
        excerpt: (item.fields.excerpt as string) || "",
        content: (item.fields.content as string) || "",
      }));
    }
  } catch {
    // Contentful unavailable or no matching content type — fall through to demo
  }

  return demoPosts;
}

export const metadata = {
  title: "Blog — Resonantia",
  description:
    "Insights on lab informatics, automation, and AI from the Resonantia team.",
};

export default async function BlogPage() {
  const posts = await getBlogPosts();

  return (
    <>
      <Navbar />

      <main className="min-h-screen pt-32 pb-24 bg-cream">
        {/* Header */}
        <div className="max-w-3xl mx-auto px-6 lg:px-8 mb-16 text-center">
          <h1 className="font-serif text-4xl md:text-5xl font-semibold text-charcoal mb-4">
            Blog
          </h1>
          <p className="text-lg text-muted max-w-xl mx-auto">
            Insights on lab informatics, automation, and AI
          </p>
          <div className="mt-6 w-16 h-px bg-amber mx-auto" />
        </div>

        {/* Post list */}
        <div className="max-w-3xl mx-auto px-6 lg:px-8 flex flex-col gap-10">
          {posts.map((post) => (
            <Link
              key={post.slug}
              href={`/blog/${post.slug}`}
              className="group block bg-surface border border-border rounded-2xl p-8 hover:border-amber/40 hover:shadow-md transition-all duration-300"
            >
              {/* Tags */}
              <div className="flex flex-wrap gap-2 mb-4">
                {post.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-block text-xs font-medium tracking-wide uppercase px-3 py-1 rounded-full bg-amber/10 text-amber-dark"
                  >
                    {tag}
                  </span>
                ))}
              </div>

              {/* Title */}
              <h2 className="font-serif text-xl md:text-2xl font-semibold text-charcoal mb-3 group-hover:text-amber-dark transition-colors duration-300">
                {post.title}
              </h2>

              {/* Meta */}
              <p className="text-sm text-muted mb-4">
                {post.author} &middot; {post.date}
              </p>

              {/* Excerpt */}
              <p className="text-base text-muted leading-relaxed mb-5">
                {post.excerpt}
              </p>

              {/* Read more */}
              <span className="inline-flex items-center text-sm font-medium text-amber-dark group-hover:gap-2 gap-1 transition-all duration-300">
                Read more
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </span>
            </Link>
          ))}
        </div>
      </main>

      <Footer />
    </>
  );
}
