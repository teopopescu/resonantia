"use client";

import Link from "next/link";
import { motion } from "framer-motion";

/* ── Live 4PL dose-response panel — the hero "instrument" ───────── */

function ScopePanel() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, delay: 0.5 }}
      className="relative bg-surface border border-line rounded-md p-5 lg:p-6 flex flex-col min-h-[460px]"
    >
      <span className="reg" style={{ top: -7, left: -7 }} />
      <span className="reg" style={{ top: -7, right: -7 }} />
      <span className="reg" style={{ bottom: -7, left: -7 }} />
      <span className="reg" style={{ bottom: -7, right: -7 }} />

      {/* Head */}
      <div className="flex justify-between items-center pb-3 border-b border-dashed border-line mb-2 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted">
        <span>
          CH-1 · 4PL FIT · <b className="text-ink font-semibold">STAUROSPORINE</b>
        </span>
        <span className="inline-flex items-center gap-1.5 text-brand">
          <span className="inline-block w-[7px] h-[7px] rounded-full bg-brand pulse-led" />
          LIVE
        </span>
      </div>

      {/* Curve */}
      <div className="flex-1 relative">
        <svg
          viewBox="0 0 600 360"
          preserveAspectRatio="none"
          className="absolute inset-0 w-full h-full"
          aria-hidden="true"
        >
          {/* grid */}
          <g stroke="#CFD3C6" strokeWidth="0.6">
            <line x1="0" y1="60" x2="600" y2="60" />
            <line x1="0" y1="120" x2="600" y2="120" />
            <line x1="0" y1="180" x2="600" y2="180" />
            <line x1="0" y1="240" x2="600" y2="240" />
            <line x1="0" y1="300" x2="600" y2="300" />
            <line x1="120" y1="0" x2="120" y2="360" />
            <line x1="240" y1="0" x2="240" y2="360" />
            <line x1="360" y1="0" x2="360" y2="360" />
            <line x1="480" y1="0" x2="480" y2="360" />
          </g>

          {/* axis labels */}
          <g
            fontFamily="var(--font-jetbrains-mono), JetBrains Mono, monospace"
            fontSize="9"
            fill="#828776"
            letterSpacing="0.5"
          >
            <text x="2" y="58">100%</text>
            <text x="2" y="178">50%</text>
            <text x="2" y="298">0%</text>
            <text x="116" y="350">−9</text>
            <text x="236" y="350">−8</text>
            <text x="356" y="350">−7</text>
            <text x="476" y="350">−6</text>
            <text x="556" y="350">log[M]</text>
          </g>

          {/* replicate scatter */}
          <g fill="#1F4D3A" opacity="0.35">
            <circle cx="60" cy="84" r="3" />
            <circle cx="120" cy="92" r="3" />
            <circle cx="180" cy="106" r="3" />
            <circle cx="240" cy="146" r="3" />
            <circle cx="300" cy="208" r="3" />
            <circle cx="360" cy="258" r="3" />
            <circle cx="420" cy="284" r="3" />
            <circle cx="480" cy="294" r="3" />
            <circle cx="540" cy="298" r="3" />
          </g>

          {/* main scatter */}
          <g fill="#1F4D3A">
            <circle cx="60" cy="78" r="3.5" />
            <circle cx="120" cy="86" r="3.5" />
            <circle cx="180" cy="98" r="3.5" />
            <circle cx="240" cy="138" r="3.5" />
            <circle cx="300" cy="200" r="3.5" />
            <circle cx="360" cy="248" r="3.5" />
            <circle cx="420" cy="278" r="3.5" />
            <circle cx="480" cy="290" r="3.5" />
            <circle cx="540" cy="296" r="3.5" />
          </g>

          {/* 4PL curve, drawn with a stroke-dash animation */}
          <motion.path
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.6, delay: 0.9, ease: "easeOut" }}
            d="M 0,80 C 80,80 140,84 200,110 C 260,150 300,210 360,250 C 420,278 480,290 600,295"
            fill="none"
            stroke="#1F4D3A"
            strokeWidth="2.4"
            strokeLinecap="round"
          />

          {/* IC50 crosshair */}
          <g>
            <line x1="300" y1="0" x2="300" y2="360" stroke="#1F6CA0" strokeWidth="1" strokeDasharray="3 4" />
            <line x1="0" y1="200" x2="600" y2="200" stroke="#1F6CA0" strokeWidth="1" strokeDasharray="3 4" />
            <circle cx="300" cy="200" r="5" fill="#FFFFFF" stroke="#1F6CA0" strokeWidth="2" />
            <text
              x="308" y="196"
              fontFamily="var(--font-jetbrains-mono), monospace"
              fontSize="9"
              fill="#1F6CA0"
            >
              IC₅₀
            </text>
          </g>
        </svg>
      </div>

      {/* Foot */}
      <div className="grid grid-cols-3 gap-3 pt-3 border-t border-dashed border-line">
        <ScopeStat k="IC₅₀" v="42.3" suffix="nM" highlight />
        <ScopeStat k="Hill slope" v="−1.18" />
        <ScopeStat k="Z′" v="0.71" />
      </div>
    </motion.div>
  );
}

function ScopeStat({
  k,
  v,
  suffix,
  highlight,
}: {
  k: string;
  v: string;
  suffix?: string;
  highlight?: boolean;
}) {
  return (
    <div>
      <div className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-ink-subtle">
        {k}
      </div>
      <div className="font-mono text-[18px] mt-0.5 text-ink font-medium">
        <span className={highlight ? "text-brand font-semibold" : ""}>{v}</span>
        {suffix && <span className="text-ink-muted ml-1">{suffix}</span>}
      </div>
    </div>
  );
}

/* ── Hero ────────────────────────────────────────────────────────── */

export function Hero() {
  return (
    <section className="relative pt-28 lg:pt-32 pb-16 lg:pb-20">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-[1.15fr_1fr] gap-12 lg:gap-14 items-stretch relative">
          <span className="reg hidden lg:block" style={{ top: 56, left: -22 }} />
          <span className="reg hidden lg:block" style={{ top: 56, right: -22 }} />

          {/* Left — copy */}
          <div>
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="inline-flex items-center gap-2.5 mb-9 font-mono text-[11px] uppercase tracking-[0.06em] text-ink-muted"
            >
              <span className="font-semibold text-brand bg-brand-soft border border-brand/40 rounded-[2px] px-1.5 py-0.5">
                01
              </span>
              <span>System overview · v0.7 · research preview</span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, delay: 0.2 }}
              className="text-[56px] sm:text-[72px] lg:text-[96px] xl:text-[104px] leading-[0.96] tracking-[-0.045em] text-ink"
            >
              <span className="font-light">The wet lab,</span>
              <br />
              <span className="relative inline-block font-bold text-brand">
                <span className="relative z-10">instrumented.</span>
                <span
                  aria-hidden="true"
                  className="absolute left-0 right-0 bottom-[2px] h-[6px] bg-brand-soft -z-0"
                />
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, delay: 0.35 }}
              className="mt-8 max-w-xl text-[16.5px] leading-[1.55] text-ink-muted"
            >
              Resonantia is the agent-native console for plate mapping,
              microscopy, and inventory.{" "}
              <strong className="text-ink font-medium">
                One surface for the whole bench
              </strong>{" "}
              — your samples, your scope, your data — listening in real time,
              writing back to your notebook.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, delay: 0.5 }}
              className="mt-9 flex flex-col sm:flex-row gap-3"
            >
              <Link
                href="/lab"
                className="inline-flex items-center justify-center gap-2.5 px-[18px] py-3 bg-brand text-white text-[13.5px] font-medium rounded-[3px] hover:bg-brand-strong transition-colors"
                style={{ boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.06)" }}
              >
                Open the console
                <span className="font-mono text-[14px] leading-none">→</span>
              </Link>
              <a
                href="#features"
                className="inline-flex items-center justify-center gap-2.5 px-[18px] py-3 text-[13.5px] font-medium text-ink border border-line-strong rounded-[3px] hover:border-ink hover:bg-surface transition-colors"
              >
                See it run
                <span className="font-mono text-[14px] leading-none">↗</span>
              </a>
            </motion.div>

            {/* Hero meta strip */}
            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.65 }}
              className="mt-14 grid grid-cols-2 sm:grid-cols-4 gap-5 pt-5 border-t border-dashed border-line-strong"
            >
              <HeroStat k="Tools wired" v={<><em className="text-brand not-italic">32</em> / live</>} />
              <HeroStat k="Liquid handlers" v="Echo · STAR · OT-2" />
              <HeroStat k="Channels" v="DAPI · GFP · mCh · BF" />
              <HeroStat k="Compliance" v="SOC 2 · 21 CFR" />
            </motion.div>
          </div>

          {/* Right — live scope panel */}
          <ScopePanel />
        </div>

        {/* Trust strip below the hero */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.9 }}
          className="mt-16 grid grid-cols-2 lg:grid-cols-5 border-t border-b border-line"
        >
          <TrustCell k="Worklists" v={<><em className="text-brand not-italic">3</em> liquid handlers</>} />
          <TrustCell k="Tests passing" v={<><em className="text-brand not-italic">108</em> / 108</>} />
          <TrustCell k="Auth" v="SAML · OIDC · SCIM" />
          <TrustCell k="Hosting" v="EU · US · self-host" />
          <TrustCell k="Compliance" v="SOC 2 · 21 CFR · GDPR" />
        </motion.div>
      </div>
    </section>
  );
}

function HeroStat({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div>
      <div className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
        {k}
      </div>
      <div className="mt-1 text-[15px] font-semibold tracking-[-0.01em] text-ink">
        {v}
      </div>
    </div>
  );
}

function TrustCell({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="px-5 py-5 border-r border-line last:border-r-0">
      <div className="font-mono text-[11px] uppercase tracking-[0.06em] text-ink-subtle">
        {k}
      </div>
      <div className="mt-1.5 text-[15px] font-medium tracking-[-0.01em] text-ink">
        {v}
      </div>
    </div>
  );
}
