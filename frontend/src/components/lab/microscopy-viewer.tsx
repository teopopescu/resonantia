"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  ChevronLeft,
  ChevronRight,
  Layers,
  Info,
} from "lucide-react";
import {
  CHANNELS,
  renderChannel,
  renderComposite,
  type Channel,
} from "@/lib/microscopy-demo";

interface Props {
  seed: number;
  wellLabel: string;
  plateName: string;
  fov: number;
  totalFov: number;
  onPrevFov: () => void;
  onNextFov: () => void;
}

const IMG_SIZE = 512;

export default function MicroscopyViewer({
  seed,
  wellLabel,
  plateName,
  fov,
  totalFov,
  onPrevFov,
  onNextFov,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [activeChannels, setActiveChannels] = useState<Channel[]>([
    "dapi",
    "gfp",
  ]);
  const [compositeMode, setCompositeMode] = useState(true);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [showInfo, setShowInfo] = useState(false);

  // Render canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    if (compositeMode) {
      renderComposite(canvas, activeChannels, seed, IMG_SIZE, IMG_SIZE);
    } else {
      // Show first active channel
      const ch = activeChannels[0] || "dapi";
      renderChannel(canvas, ch, seed, IMG_SIZE, IMG_SIZE);
    }
  }, [seed, activeChannels, compositeMode]);

  const toggleChannel = (ch: Channel) => {
    setActiveChannels((prev) =>
      prev.includes(ch) ? prev.filter((c) => c !== ch) : [...prev, ch]
    );
  };

  const handleZoomIn = () => setZoom((z) => Math.min(z * 1.3, 8));
  const handleZoomOut = () => {
    setZoom((z) => {
      const next = Math.max(z / 1.3, 1);
      if (next <= 1) setPan({ x: 0, y: 0 });
      return next;
    });
  };
  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleWheel = useCallback(
    (e: React.WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      setZoom((z) => {
        const next = Math.max(1, Math.min(z * delta, 8));
        if (next <= 1) setPan({ x: 0, y: 0 });
        return next;
      });
    },
    []
  );

  const handleMouseDown = (e: React.MouseEvent) => {
    if (zoom <= 1) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };
  const handleMouseUp = () => setIsDragging(false);

  return (
    <div className="flex flex-col h-full">
      {/* Channel bar */}
      <div className="flex items-center gap-1.5 px-4 py-2 bg-bg border-b border-line">
        <button
          onClick={() => setCompositeMode(!compositeMode)}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-[3px] font-mono text-[11px] uppercase tracking-[0.04em] transition-colors ${
            compositeMode
              ? "bg-brand-soft text-brand border border-brand/30"
              : "bg-surface text-ink-muted border border-line hover:border-line-strong hover:text-ink"
          }`}
        >
          <Layers size={12} />
          composite
        </button>
        <div className="w-px h-4 bg-line mx-1" />
        {CHANNELS.map((ch) => (
          <button
            key={ch.id}
            onClick={() => toggleChannel(ch.id)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-[3px] font-mono text-[11px] uppercase tracking-[0.04em] transition-all ${
              activeChannels.includes(ch.id) ? "" : "opacity-50 hover:opacity-80"
            }`}
            style={{
              backgroundColor: activeChannels.includes(ch.id)
                ? `${ch.color}1F`
                : undefined,
              color: activeChannels.includes(ch.id) ? ch.color : "var(--color-ink-muted)",
              boxShadow: activeChannels.includes(ch.id)
                ? `inset 0 0 0 1px ${ch.color}`
                : "inset 0 0 0 1px var(--color-line)",
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ backgroundColor: ch.color }}
            />
            {ch.label}
          </button>
        ))}

        <div className="flex-1" />

        {/* Zoom controls */}
        <div className="flex items-center gap-0.5">
          <button
            onClick={handleZoomOut}
            className="p-1.5 rounded-[3px] hover:bg-bg-sunk text-ink-muted hover:text-ink transition-colors"
          >
            <ZoomOut size={14} />
          </button>
          <span className="font-mono text-[11px] tracking-[0.02em] text-ink-subtle w-11 text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={handleZoomIn}
            className="p-1.5 rounded-[3px] hover:bg-bg-sunk text-ink-muted hover:text-ink transition-colors"
          >
            <ZoomIn size={14} />
          </button>
          <button
            onClick={handleResetZoom}
            className="p-1.5 rounded-[3px] hover:bg-bg-sunk text-ink-muted hover:text-ink transition-colors"
          >
            <Maximize2 size={14} />
          </button>
          <div className="w-px h-4 bg-line mx-1" />
          <button
            onClick={() => setShowInfo(!showInfo)}
            className={`p-1.5 rounded-[3px] transition-colors ${
              showInfo
                ? "bg-brand-soft text-brand"
                : "hover:bg-bg-sunk text-ink-muted hover:text-ink"
            }`}
          >
            <Info size={14} />
          </button>
        </div>
      </div>

      {/* Image viewport */}
      <div className="flex-1 relative overflow-hidden bg-black/90">
        <div
          ref={containerRef}
          className="w-full h-full flex items-center justify-center"
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          style={{ cursor: zoom > 1 ? (isDragging ? "grabbing" : "grab") : "default" }}
        >
          <canvas
            ref={canvasRef}
            className="max-w-full max-h-full"
            style={{
              transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
              transformOrigin: "center center",
              imageRendering: zoom > 2 ? "pixelated" : "auto",
            }}
          />
        </div>

        {/* FOV Navigation arrows */}
        <button
          onClick={onPrevFov}
          disabled={fov <= 1}
          className="absolute left-3 top-1/2 -translate-y-1/2 p-2 rounded-[3px] bg-black/55 text-white/80 hover:bg-black/75 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all backdrop-blur-sm"
        >
          <ChevronLeft size={18} />
        </button>
        <button
          onClick={onNextFov}
          disabled={fov >= totalFov}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-[3px] bg-black/55 text-white/80 hover:bg-black/75 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all backdrop-blur-sm"
        >
          <ChevronRight size={18} />
        </button>

        {/* Scale bar */}
        <div className="absolute bottom-4 left-4 flex flex-col items-start">
          <div className="w-20 h-0.5 bg-white" />
          <span className="text-white/70 text-[10px] font-mono mt-1 tracking-[0.04em] uppercase">
            100 µm
          </span>
        </div>

        {/* Info overlay */}
        {showInfo && (
          <div className="absolute top-4 left-4 bg-black/65 backdrop-blur-md rounded-[3px] p-3 text-white/90 font-mono text-[11px] space-y-1 min-w-[200px]">
            <div className="text-brand font-semibold text-[10.5px] uppercase tracking-[0.06em] mb-1.5">
              <span className="text-brand">›</span> acquisition
            </div>
            {[
              ["plate", plateName],
              ["well", wellLabel],
              ["fov", `${fov} / ${totalFov}`],
              ["objective", "20×"],
              ["exposure", "200 ms"],
              ["gain", "1.0"],
              ["pixels", "512 × 512"],
              ["scale", "0.65 µm/px"],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between gap-3">
                <span className="text-white/45 uppercase tracking-[0.04em]">{k}</span>
                <span>{v}</span>
              </div>
            ))}
          </div>
        )}

        {/* Well / FOV badge */}
        <div className="absolute top-4 right-4 bg-black/55 backdrop-blur-sm rounded-[3px] px-2.5 py-1 text-white/90 font-mono text-[11px] tracking-[0.04em] uppercase">
          {wellLabel} · FOV {fov}
        </div>
      </div>
    </div>
  );
}
