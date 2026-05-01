"use client";

import { useEffect, useRef } from "react";
import { renderComposite, type Channel } from "@/lib/microscopy-demo";
import { seedForWellFov } from "@/lib/microscopy-demo";

interface Props {
  plateIndex: number;
  row: number;
  col: number;
  activeFov: number;
  totalFov: number;
  activeChannels: Channel[];
  onSelectFov: (fov: number) => void;
}

function Thumbnail({
  seed,
  active,
  fov,
  channels,
  onClick,
}: {
  seed: number;
  active: boolean;
  fov: number;
  channels: Channel[];
  onClick: () => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    renderComposite(canvas, channels.length > 0 ? channels : ["dapi"], seed, 96, 96);
  }, [seed, channels]);

  return (
    <button
      onClick={onClick}
      className={`relative shrink-0 rounded-[3px] overflow-hidden transition-all duration-150 ${
        active
          ? "ring-2 ring-brand ring-offset-2 ring-offset-ink scale-105"
          : "ring-1 ring-white/10 hover:ring-white/30 opacity-70 hover:opacity-100"
      }`}
    >
      <canvas ref={canvasRef} className="w-16 h-16 object-cover" />
      <span className="absolute bottom-0 inset-x-0 text-center text-[9px] font-mono text-white/80 bg-black/55 py-0.5 tracking-[0.04em] uppercase">
        FOV {fov}
      </span>
    </button>
  );
}

export default function ThumbnailStrip({
  plateIndex,
  row,
  col,
  activeFov,
  totalFov,
  activeChannels,
  onSelectFov,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll active thumbnail into view
    if (containerRef.current) {
      const active = containerRef.current.querySelector("[data-active='true']");
      active?.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
    }
  }, [activeFov]);

  return (
    <div className="bg-ink border-t border-line/10 px-4 py-3">
      <div
        ref={containerRef}
        className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin"
      >
        {Array.from({ length: totalFov }, (_, i) => {
          const fov = i + 1;
          const seed = seedForWellFov(plateIndex, row, col, fov);
          return (
            <div key={fov} data-active={fov === activeFov ? "true" : undefined}>
              <Thumbnail
                seed={seed}
                active={fov === activeFov}
                fov={fov}
                channels={activeChannels}
                onClick={() => onSelectFov(fov)}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
