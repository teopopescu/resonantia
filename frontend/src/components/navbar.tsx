"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";

const navLinks = [
  { label: "About", href: "/about" },
  { label: "Features", href: "/#features" },
  { label: "Pricing", href: "/pricing" },
  { label: "Blog", href: "/blog" },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-500",
        scrolled
          ? "bg-cream/80 backdrop-blur-xl border-b border-border shadow-sm"
          : "bg-transparent"
      )}
    >
      <nav className="max-w-7xl mx-auto px-6 lg:px-8 h-18 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="relative w-8 h-8">
            {/* DNA helix / wave icon */}
            <svg
              viewBox="0 0 32 32"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="w-full h-full"
            >
              <path
                d="M8 4C8 4 12 10 16 16C20 22 24 28 24 28"
                stroke="#D4A843"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M24 4C24 4 20 10 16 16C12 22 8 28 8 28"
                stroke="#1A1A1A"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <circle cx="11" cy="10" r="1.5" fill="#D4A843" />
              <circle cx="21" cy="10" r="1.5" fill="#1A1A1A" />
              <circle cx="16" cy="16" r="2" fill="#D4A843" opacity="0.6" />
              <circle cx="11" cy="22" r="1.5" fill="#1A1A1A" />
              <circle cx="21" cy="22" r="1.5" fill="#D4A843" />
            </svg>
          </div>
          <span className="font-serif text-xl font-semibold tracking-tight text-charcoal">
            Resonantia
          </span>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-sm text-muted hover:text-charcoal transition-colors duration-300 relative group"
            >
              {link.label}
              <span className="absolute -bottom-0.5 left-0 w-0 h-px bg-amber group-hover:w-full transition-all duration-300" />
            </a>
          ))}
        </div>

        {/* Auth + CTA */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            href="/lab"
            className="text-sm text-muted hover:text-charcoal transition-colors duration-300"
          >
            Sign in
          </Link>
          <Link
            href="/lab"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-charcoal text-cream text-sm font-medium rounded-full hover:bg-charcoal-light transition-colors duration-300"
          >
            Get started
          </Link>
        </div>

        {/* Mobile menu button */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="md:hidden p-2 text-charcoal"
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </nav>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="md:hidden bg-cream/95 backdrop-blur-xl border-b border-border overflow-hidden"
          >
            <div className="px-6 py-6 flex flex-col gap-4">
              {navLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="text-base text-muted hover:text-charcoal transition-colors"
                >
                  {link.label}
                </a>
              ))}
              <Link
                href="/lab"
                onClick={() => setMobileOpen(false)}
                className="text-base text-muted hover:text-charcoal transition-colors"
              >
                Sign in
              </Link>
              <Link
                href="/lab"
                onClick={() => setMobileOpen(false)}
                className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-charcoal text-cream text-sm font-medium rounded-full mt-2"
              >
                Get started
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
