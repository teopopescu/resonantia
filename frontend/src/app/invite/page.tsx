"use client";

import { useState } from "react";
import { useUser, useOrganization } from "@clerk/nextjs";
import { RedirectToSignIn } from "@clerk/nextjs";
import Link from "next/link";
import { ArrowLeft, Send, CheckCircle2, AlertCircle } from "lucide-react";

export default function InvitePage() {
  const { isLoaded, isSignedIn } = useUser();
  const { organization } = useOrganization();
  const orgName = organization?.name || "Resonantia Team";
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [message, setMessage] = useState("");

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-amber border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isSignedIn) {
    return <RedirectToSignIn />;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;

    setStatus("loading");
    setMessage("");

    try {
      const res = await fetch("/api/invite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });

      const data = await res.json();

      if (!res.ok) {
        setStatus("error");
        setMessage(data.error || "Something went wrong. Please try again.");
        return;
      }

      setStatus("success");
      setMessage(`Invitation sent to ${email}`);
      setEmail("");
    } catch {
      setStatus("error");
      setMessage("Network error. Please check your connection and try again.");
    }
  }

  return (
    <div className="min-h-screen bg-cream flex flex-col">
      {/* Top bar */}
      <div className="px-6 py-4">
        <Link
          href="/lab"
          className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-charcoal transition-colors"
        >
          <ArrowLeft size={16} />
          Back to Lab
        </Link>
      </div>

      {/* Centered content */}
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-amber text-charcoal font-serif font-bold text-xl mb-4">
              R
            </div>
            <h1 className="font-serif text-3xl font-bold text-charcoal mb-2">
              Invite to Resonantia Lab
            </h1>
            <p className="text-muted text-sm leading-relaxed max-w-sm mx-auto">
              Inviting to: <span className="font-medium text-charcoal">{orgName}</span>
            </p>
            <p className="text-muted text-sm leading-relaxed max-w-sm mx-auto mt-1">
              Resonantia Lab is currently invite-only. Enter an email address to
              send an invitation.
            </p>
          </div>

          {/* Form card */}
          <div className="bg-white rounded-2xl border border-border p-6 shadow-sm">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="email"
                  className="block text-xs font-medium text-charcoal/70 mb-1.5 uppercase tracking-wider"
                >
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (status !== "idle" && status !== "loading")
                      setStatus("idle");
                  }}
                  placeholder="colleague@lab.edu"
                  className="w-full px-4 py-2.5 rounded-xl border border-border bg-surface text-sm text-charcoal placeholder:text-muted/50 focus:outline-none focus:border-amber/40 transition-colors"
                />
              </div>

              <button
                type="submit"
                disabled={status === "loading" || !email.trim()}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-amber text-charcoal font-medium text-sm hover:bg-amber-light transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {status === "loading" ? (
                  <>
                    <div className="w-4 h-4 border-2 border-charcoal/30 border-t-charcoal rounded-full animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send size={16} />
                    Send Invitation
                  </>
                )}
              </button>
            </form>

            {/* Status messages */}
            {status === "success" && (
              <div className="mt-4 flex items-start gap-2 p-3 rounded-lg bg-green-50 border border-green-200">
                <CheckCircle2
                  size={16}
                  className="text-green-600 mt-0.5 shrink-0"
                />
                <p className="text-sm text-green-800">{message}</p>
              </div>
            )}

            {status === "error" && (
              <div className="mt-4 flex items-start gap-2 p-3 rounded-lg bg-red-50 border border-red-200">
                <AlertCircle
                  size={16}
                  className="text-red-600 mt-0.5 shrink-0"
                />
                <p className="text-sm text-red-800">{message}</p>
              </div>
            )}
          </div>

          {/* Footer note */}
          <p className="text-center text-xs text-muted/60 mt-6">
            The recipient will receive an email with a link to join Resonantia
            Lab.
          </p>
        </div>
      </div>
    </div>
  );
}
