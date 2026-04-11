import Link from "next/link";
import { notFound } from "next/navigation";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { contentfulClient } from "@/lib/contentful";
import { demoPosts, type BlogPost } from "@/lib/blog-data";

async function getPost(slug: string): Promise<BlogPost | null> {
  // Try Contentful first
  try {
    const entries = await contentfulClient.getEntries({
      content_type: "blogPost",
      "fields.slug": slug,
      limit: 1,
    });

    if (entries.items.length > 0) {
      const item: any = entries.items[0];
      return {
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
      };
    }
  } catch {
    // fall through to demo data
  }

  // Fallback to demo posts
  return demoPosts.find((p) => p.slug === slug) || null;
}

export async function generateStaticParams() {
  return demoPosts.map((post) => ({ slug: post.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = await getPost(slug);
  if (!post) return { title: "Post Not Found — Resonantia" };
  return {
    title: `${post.title} — Resonantia Blog`,
    description: post.excerpt,
  };
}

export default async function BlogPostPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = await getPost(slug);

  if (!post) {
    notFound();
  }

  // Split content into paragraphs
  const paragraphs = post.content
    .split("\n\n")
    .filter((p) => p.trim().length > 0);

  return (
    <>
      <Navbar />

      <main className="min-h-screen pt-32 pb-24 bg-cream">
        <article className="max-w-3xl mx-auto px-6 lg:px-8">
          {/* Back link */}
          <Link
            href="/blog"
            className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-charcoal transition-colors duration-300 mb-10"
          >
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
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Back to blog
          </Link>

          {/* Tags */}
          <div className="flex flex-wrap gap-2 mb-6">
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
          <h1 className="font-serif text-3xl md:text-4xl lg:text-5xl font-semibold text-charcoal leading-tight mb-6">
            {post.title}
          </h1>

          {/* Meta */}
          <div className="flex items-center gap-3 text-sm text-muted mb-10">
            {/* Author avatar placeholder */}
            <div className="w-8 h-8 rounded-full bg-amber/20 flex items-center justify-center text-amber-dark font-serif text-sm font-semibold">
              {post.author
                .split(" ")
                .map((n) => n[0])
                .join("")}
            </div>
            <span>{post.author}</span>
            <span className="text-border">&middot;</span>
            <span>{post.date}</span>
          </div>

          {/* Divider */}
          <div className="w-16 h-px bg-amber mb-10" />

          {/* Content */}
          <div className="prose-resonantia">
            {paragraphs.map((paragraph, i) => (
              <p
                key={i}
                className="text-base md:text-lg text-charcoal/85 leading-relaxed mb-6"
              >
                {paragraph}
              </p>
            ))}
          </div>

          {/* Bottom divider */}
          <div className="mt-16 pt-10 border-t border-border">
            <Link
              href="/blog"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-amber-dark hover:gap-2.5 transition-all duration-300"
            >
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
                  d="M15 19l-7-7 7-7"
                />
              </svg>
              All articles
            </Link>
          </div>
        </article>
      </main>

      <Footer />
    </>
  );
}
