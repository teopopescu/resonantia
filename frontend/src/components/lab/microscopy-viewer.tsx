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
      <div className="flex items-center gap-2 px-4 py-2.5 bg-surface border-b border-border">
        <button
          onClick={() => setCompositeMode(!compositeMode)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            compositeMode
              ? "bg-charcoal text-white"
              : "bg-cream-dark text-charcoal hover:bg-border"
          }`}
        >
          <Layers size={14} />
          Composite
        </button>
        <div className="w-px h-5 bg-border mx-1" />
        {CHANNELS.map((ch) => (
          <button
            key={ch.id}
            onClick={() => toggleChannel(ch.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeChannels.includes(ch.id)
                ? "ring-1 ring-offset-1 ring-offset-surface"
                : "opacity-50 hover:opacity-80"
            }`}
            style={{
              backgroundColor: activeChannels.includes(ch.id)
                ? `${ch.color}20`
                : undefined,
              color: activeChannels.includes(ch.id)
                ? ch.color
                : "var(--color-muted)",
              boxShadow: activeChannels.includes(ch.id)
                ? `0 0 0 1px ${ch.color}`
                : undefined,
            }}
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: ch.color }}
            />
            {ch.label}
          </button>
        ))}

        <div className="flex-1" />

        {/* Zoom controls */}
        <div className="flex items-center gap-1">
          <button
            onClick={handleZoomOut}
            className="p-1.5 rounded-md hover:bg-cream-dark text-muted hover:text-charcoal transition-colors"
          >
            <ZoomOut size={16} />
          </button>
          <span className="text-xs font-mono text-muted w-12 text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={handleZoomIn}
            className="p-1.5 rounded-md hover:bg-cream-dark text-muted hover:text-charcoal transition-colors"
          >
            <ZoomIn size={16} />
          </button>
          <button
            onClick={handleResetZoom}
            className="p-1.5 rounded-md hover:bg-cream-dark text-muted hover:text-charcoal transition-colors"
          >
            <Maximize2 size={16} />
          </button>
          <div className="w-px h-5 bg-border mx-1" />
          <button
            onClick={() => setShowInfo(!showInfo)}
            className={`p-1.5 rounded-md transition-colors ${
              showInfo
                ? "bg-amber/20 text-amber"
                : "hover:bg-cream-dark text-muted hover:text-charcoal"
            }`}
          >
            <Info size={16} />
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
          className="absolute left-3 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black/50 text-white/80 hover:bg-black/70 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all backdrop-blur-sm"
        >
          <ChevronLeft size={20} />
        </button>
        <button
          onClick={onNextFov}
          disabled={fov >= totalFov}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black/50 text-white/80 hover:bg-black/70 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all backdrop-blur-sm"
        >
          <ChevronRight size={20} />
        </button>

        {/* Scale bar */}
        <div className="absolute bottom-4 left-4 flex items-end gap-2">
          <div className="flex flex-col items-start">
            <div className="w-20 h-0.5 bg-white" />
            <span className="text-white/70 text-[10px] font-mono mt-0.5">
              100 um
            </span>
          </div>
        </div>

        {/* Info overlay */}
        {showInfo && (
          <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-md rounded-lg p-3 text-white/90 text-xs font-mono space-y-1 min-w-[180px]">
            <div className="text-amber font-semibold text-[11px] mb-1.5">
              Acquisition Info
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Plate</span>
              <span>{plateName}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Well</span>
              <span>{wellLabel}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">FOV</span>
              <span>
                {fov} / {totalFov}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Objective</span>
              <span>20x</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Exposure</span>
              <span>200 ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Gain</span>
              <span>1.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Pixels</span>
              <span>512 x 512</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/50">Scale</span>
              <span>0.65 um/px</span>
            </div>
          </div>
        )}

        {/* Well / FOV badge */}
        <div className="absolute top-4 right-4 bg-black/50 backdrop-blur-sm rounded-md px-3 py-1.5 text-white/90 text-xs font-mono">
          {wellLabel} &middot; FOV {fov}
        </div>
      </div>
    </div>
  );
}
