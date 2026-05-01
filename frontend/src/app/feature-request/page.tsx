"use client";

import { useState } from "react";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { CheckCircle2 } from "lucide-react";

const roles = ["Scientist", "Lab Manager", "Bioinformatician", "Other"];
const priorities = ["Nice to have", "Important", "Critical"];

export default function FeatureRequestPage() {
  const [submitted, setSubmitted] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("Important");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // For now, just show success state. Will wire to backend later.
    setSubmitted(true);
  }

  const inputClass =
    "w-full px-4 py-3 rounded-xl border border-border bg-surface text-sm text-charcoal focus:outline-none focus:border-amber/60 focus:ring-1 focus:ring-amber/20 transition-colors";

  return (
    <div className="min-h-screen bg-cream flex flex-col">
      <Navbar />

      <main className="flex-1 flex items-start justify-center px-6 py-20 lg:py-28">
        <div className="w-full max-w-xl">
          {/* Heading */}
          <div className="text-center mb-10">
            <h1 className="font-serif text-3xl sm:text-4xl font-semibold text-charcoal mb-3">
              Request a Feature
            </h1>
            <p className="text-base text-muted leading-relaxed max-w-md mx-auto">
              Help us shape the future of Resonantia Lab. Tell us what you need.
            </p>
          </div>

          {submitted ? (
            /* Success state */
            <div className="rounded-2xl border border-border bg-surface p-10 text-center">
              <div className="mx-auto w-14 h-14 rounded-full bg-emerald-50 flex items-center justify-center mb-5">
                <CheckCircle2 size={28} className="text-emerald-500" />
              </div>
              <h2 className="font-serif text-2xl font-semibold text-charcoal mb-2">
                Thank you!
              </h2>
              <p className="text-sm text-muted leading-relaxed">
                We&apos;ve received your request. Our team will review it and follow up
                if we need more details.
              </p>
            </div>
          ) : (
            /* Form */
            <form
              onSubmit={handleSubmit}
              className="rounded-2xl border border-border bg-surface p-8 space-y-5"
            >
              {/* Name */}
              <div>
                <label className="block text-xs font-medium text-charcoal mb-1.5">
                  Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  className={inputClass}
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-xs font-medium text-charcoal mb-1.5">
                  Email
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className={inputClass}
                />
              </div>

              {/* Role */}
              <div>
                <label className="block text-xs font-medium text-charcoal mb-1.5">
                  Role
                </label>
                <select
                  required
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className={`${inputClass} ${!role ? "text-muted/60" : ""}`}
                >
                  <option value="" disabled>
                    Select your role
                  </option>
                  {roles.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>

              {/* Feature description */}
              <div>
                <label className="block text-xs font-medium text-charcoal mb-1.5">
                  Feature Description
                </label>
                <textarea
                  required
                  rows={6}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the feature you'd like to see..."
                  className={`${inputClass} resize-none`}
                />
              </div>

              {/* Priority */}
              <div>
                <label className="block text-xs font-medium text-charcoal mb-2">
                  Priority
                </label>
                <div className="flex items-center gap-4">
                  {priorities.map((p) => (
                    <label
                      key={p}
                      className="flex items-center gap-2 cursor-pointer"
                    >
                      <input
                        type="radio"
                        name="priority"
                        value={p}
                        checked={priority === p}
                        onChange={() => setPriority(p)}
                        className="accent-amber-500 w-3.5 h-3.5"
                      />
                      <span className="text-sm text-charcoal">{p}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Submit */}
              <button
                type="submit"
                className="w-full py-3 rounded-xl text-sm font-medium bg-amber text-charcoal hover:bg-amber-light transition-colors shadow-sm"
              >
                Submit Request
              </button>
            </form>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
