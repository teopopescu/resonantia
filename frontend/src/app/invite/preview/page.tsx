"use client";

import EmailTemplate from "@/components/email-template";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function EmailPreviewPage() {
  return (
    <div className="min-h-screen bg-cream flex flex-col">
      {/* Top bar */}
      <div className="px-6 py-4 flex items-center justify-between">
        <Link
          href="/invite"
          className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-charcoal transition-colors"
        >
          <ArrowLeft size={16} />
          Back to Invite
        </Link>
        <span className="text-xs font-medium text-muted/60 uppercase tracking-wider">
          Email Template Preview
        </span>
      </div>

      {/* Email preview container */}
      <div className="flex-1 flex items-start justify-center px-4 py-8">
        <div className="w-full max-w-[640px]">
          {/* Mock email client chrome */}
          <div className="bg-white rounded-2xl shadow-lg border border-border overflow-hidden">
            {/* Email header bar */}
            <div className="px-6 py-4 border-b border-border bg-surface">
              <div className="flex items-center gap-3 mb-3">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-400/60" />
                  <div className="w-3 h-3 rounded-full bg-yellow-400/60" />
                  <div className="w-3 h-3 rounded-full bg-green-400/60" />
                </div>
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted/60 w-12">From:</span>
                  <span className="text-xs text-charcoal">
                    noreply@resonantia.app
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted/60 w-12">To:</span>
                  <span className="text-xs text-charcoal">
                    colleague@lab.edu
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted/60 w-12">Subject:</span>
                  <span className="text-xs text-charcoal font-medium">
                    You&apos;ve been invited to Resonantia Lab
                  </span>
                </div>
              </div>
            </div>

            {/* Email body */}
            <div className="max-w-[600px] mx-auto">
              <EmailTemplate inviteUrl="https://resonantia.app/lab" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
