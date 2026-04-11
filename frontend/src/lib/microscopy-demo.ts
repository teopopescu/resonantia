// Generates synthetic fluorescence microscopy images using canvas

export interface CellData {
  x: number;
  y: number;
  radius: number;
  nucleusRadius: number;
  brightness: number;
}

export type Channel = "dapi" | "gfp" | "mcherry" | "brightfield" | "phase";

export interface ChannelConfig {
  id: Channel;
  label: string;
  color: string;
  rgb: [number, number, number];
}

export const CHANNELS: ChannelConfig[] = [
  { id: "dapi", label: "DAPI", color: "#4488FF", rgb: [68, 136, 255] },
  { id: "gfp", label: "GFP", color: "#44DD66", rgb: [68, 221, 102] },
  { id: "mcherry", label: "mCherry", color: "#FF4466", rgb: [255, 68, 102] },
  {
    id: "brightfield",
    label: "Brightfield",
    color: "#AAAAAA",
    rgb: [170, 170, 170],
  },
  { id: "phase", label: "Phase", color: "#CCCCCC", rgb: [204, 204, 204] },
];

// Seeded random for reproducible images
function seededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

function generateCells(
  seed: number,
  width: number,
  height: number,
  count: number
): CellData[] {
  const rng = seededRandom(seed);
  const cells: CellData[] = [];
  for (let i = 0; i < count; i++) {
    const radius = 12 + rng() * 20;
    cells.push({
      x: radius + rng() * (width - radius * 2),
      y: radius + rng() * (height - radius * 2),
      radius,
      nucleusRadius: radius * (0.35 + rng() * 0.2),
      brightness: 0.4 + rng() * 0.6,
    });
  }
  return cells;
}

export function renderChannel(
  canvas: HTMLCanvasElement,
  channel: Channel,
  seed: number,
  width = 512,
  height = 512
): void {
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const config = CHANNELS.find((c) => c.id === channel);
  if (!config) return;

  const [r, g, b] = config.rgb;
  const cellCount = 30 + ((seed * 7) % 20);
  const cells = generateCells(seed + CHANNELS.indexOf(config), width, height, cellCount);

  // Background noise
  ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.02)`;
  ctx.fillRect(0, 0, width, height);

  const rng = seededRandom(seed * 3 + CHANNELS.indexOf(config) * 100);
  // Noise specks
  for (let i = 0; i < 200; i++) {
    const nx = rng() * width;
    const ny = rng() * height;
    const alpha = rng() * 0.08;
    ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`;
    ctx.fillRect(nx, ny, 1, 1);
  }

  if (channel === "brightfield" || channel === "phase") {
    // Brightfield / phase: gray cells with ring edges
    ctx.fillStyle =
      channel === "brightfield"
        ? "rgba(140,140,140,0.08)"
        : "rgba(160,160,160,0.06)";
    ctx.fillRect(0, 0, width, height);

    for (const cell of cells) {
      // Cell body (slight contrast)
      const grad = ctx.createRadialGradient(
        cell.x,
        cell.y,
        0,
        cell.x,
        cell.y,
        cell.radius
      );
      if (channel === "brightfield") {
        grad.addColorStop(0, `rgba(180,180,180,${cell.brightness * 0.15})`);
        grad.addColorStop(0.7, `rgba(120,120,120,${cell.brightness * 0.1})`);
        grad.addColorStop(1, `rgba(80,80,80,${cell.brightness * 0.2})`);
      } else {
        grad.addColorStop(0, `rgba(200,200,200,${cell.brightness * 0.12})`);
        grad.addColorStop(0.8, `rgba(140,140,140,${cell.brightness * 0.08})`);
        grad.addColorStop(1, `rgba(100,100,100,${cell.brightness * 0.15})`);
      }
      ctx.beginPath();
      ctx.arc(cell.x, cell.y, cell.radius, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();

      // Edge ring
      ctx.beginPath();
      ctx.arc(cell.x, cell.y, cell.radius, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(80,80,80,${cell.brightness * 0.2})`;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
  } else if (channel === "dapi") {
    // DAPI: nuclei only
    for (const cell of cells) {
      const grad = ctx.createRadialGradient(
        cell.x,
        cell.y,
        0,
        cell.x,
        cell.y,
        cell.nucleusRadius * 1.5
      );
      grad.addColorStop(0, `rgba(${r},${g},${b},${cell.brightness * 0.9})`);
      grad.addColorStop(0.6, `rgba(${r},${g},${b},${cell.brightness * 0.5})`);
      grad.addColorStop(1, `rgba(${r},${g},${b},0)`);
      ctx.beginPath();
      ctx.arc(cell.x, cell.y, cell.nucleusRadius * 1.5, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();
    }
  } else {
    // GFP / mCherry: cytoplasmic with some variation
    for (const cell of cells) {
      // Not all cells express — skip some
      if (cell.brightness < 0.55 && channel === "gfp") continue;
      if (cell.brightness < 0.5 && channel === "mcherry") continue;

      const grad = ctx.createRadialGradient(
        cell.x,
        cell.y,
        cell.nucleusRadius * 0.5,
        cell.x,
        cell.y,
        cell.radius
      );
      const intensity = channel === "gfp" ? cell.brightness * 0.7 : cell.brightness * 0.6;
      grad.addColorStop(0, `rgba(${r},${g},${b},${intensity * 0.3})`);
      grad.addColorStop(0.4, `rgba(${r},${g},${b},${intensity * 0.8})`);
      grad.addColorStop(0.8, `rgba(${r},${g},${b},${intensity * 0.4})`);
      grad.addColorStop(1, `rgba(${r},${g},${b},0)`);
      ctx.beginPath();
      ctx.arc(cell.x, cell.y, cell.radius, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();
    }
  }
}

export function renderComposite(
  canvas: HTMLCanvasElement,
  activeChannels: Channel[],
  seed: number,
  width = 512,
  height = 512
): void {
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, width, height);

  // Render each channel to an offscreen canvas and composite with additive blending
  for (const ch of activeChannels) {
    const offscreen = document.createElement("canvas");
    offscreen.width = width;
    offscreen.height = height;
    renderChannel(offscreen, ch, seed, width, height);
    ctx.globalCompositeOperation = "screen";
    ctx.drawImage(offscreen, 0, 0);
  }
  ctx.globalCompositeOperation = "source-over";
}

// Well labels
export const ROWS = ["A", "B", "C", "D", "E", "F", "G", "H"];
export const COLS = Array.from({ length: 12 }, (_, i) => i + 1);

export function wellLabel(row: number, col: number): string {
  return `${ROWS[row]}${col}`;
}

export function seedForWellFov(
  plateIndex: number,
  row: number,
  col: number,
  fov: number
): number {
  return plateIndex * 10000 + row * 1200 + col * 100 + fov;
}
