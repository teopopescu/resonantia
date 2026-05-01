// ── Plate Utility Functions ──

export type WellCoords = { row: number; col: number };

export type WellType =
  | "empty"
  | "sample"
  | "control-positive"
  | "control-negative"
  | "compound";

export interface WellData {
  label: string;
  type: WellType;
  compound?: string;
  concentration?: number;
  volume?: number;
}

export interface PlateConfig {
  rows: number;
  cols: number;
  label: string;
}

export const PLATE_CONFIGS: Record<96 | 384, PlateConfig> = {
  96: { rows: 8, cols: 12, label: "96-well" },
  384: { rows: 16, cols: 24, label: "384-well" },
};

const ROW_LETTERS = "ABCDEFGHIJKLMNOP";

/** Generate well labels for a plate: A1, A2, ... H12 */
export function generateWellLabels(rows: number, cols: number): string[] {
  const labels: string[] = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      labels.push(`${ROW_LETTERS[r]}${c + 1}`);
    }
  }
  return labels;
}

/** Convert well label to coordinates: "B3" -> {row: 1, col: 2} */
export function wellToCoords(well: string): WellCoords {
  const match = well.match(/^([A-P])(\d+)$/);
  if (!match) throw new Error(`Invalid well label: ${well}`);
  return {
    row: ROW_LETTERS.indexOf(match[1]),
    col: parseInt(match[2], 10) - 1,
  };
}

/** Convert coordinates to well label: (1, 2) -> "B3" */
export function coordsToWell(row: number, col: number): string {
  return `${ROW_LETTERS[row]}${col + 1}`;
}

/** Get row letter from index */
export function rowLetter(index: number): string {
  return ROW_LETTERS[index];
}

/** Cherry pick mapping: map specific source wells to consecutive destination wells */
export function generateCherryPickMapping(
  sourceWells: string[],
  destStart: string
): Array<{ sourceWell: string; destWell: string }> {
  const start = wellToCoords(destStart);
  const config = start.col < 12 ? PLATE_CONFIGS[96] : PLATE_CONFIGS[384];
  const mappings: Array<{ sourceWell: string; destWell: string }> = [];

  let row = start.row;
  let col = start.col;

  for (const sw of sourceWells) {
    if (row >= config.rows) break;
    mappings.push({ sourceWell: sw, destWell: coordsToWell(row, col) });
    col++;
    if (col >= config.cols) {
      col = 0;
      row++;
    }
  }

  return mappings;
}

/** Serial dilution mapping from a start well in a given direction */
export function generateSerialDilution(
  startWell: string,
  direction: "horizontal" | "vertical",
  steps: number,
  dilutionFactor: number
): Array<{ well: string; dilution: number }> {
  const start = wellToCoords(startWell);
  const result: Array<{ well: string; dilution: number }> = [];

  for (let i = 0; i < steps; i++) {
    const row = direction === "vertical" ? start.row + i : start.row;
    const col = direction === "horizontal" ? start.col + i : start.col;
    if (row > 15 || col > 23) break;
    result.push({
      well: coordsToWell(row, col),
      dilution: Math.pow(1 / dilutionFactor, i),
    });
  }

  return result;
}

/** Well type → fluorescence-channel color (v4 palette).
 *  sample → DAPI cyan, compound → GFP lime, control− → mCherry red,
 *  control+ → brightfield amber, empty → bg-sunk. */
export function wellColor(type: WellType): string {
  switch (type) {
    case "sample":
      return "#1F6CA0"; // DAPI
    case "compound":
      return "#82B82F"; // GFP
    case "control-negative":
      return "#C32A55"; // mCherry
    case "control-positive":
      return "#A6711B"; // brightfield amber
    case "empty":
    default:
      return "#E0E4DA"; // bg-sunk
  }
}

/** Well type display label */
export function wellTypeLabel(type: WellType): string {
  switch (type) {
    case "sample":
      return "Sample";
    case "control-positive":
      return "Control (+)";
    case "control-negative":
      return "Control (-)";
    case "compound":
      return "Compound";
    case "empty":
    default:
      return "Empty";
  }
}

/** Generate Echo CSV worklist */
export function generateEchoCSV(
  mappings: Array<{
    sourceWell: string;
    destWell: string;
    volume: number;
    sourcePlate?: string;
    destPlate?: string;
  }>
): string {
  const header =
    "Source Plate Name,Source Well,Destination Plate Name,Destination Well,Transfer Volume";
  const rows = mappings.map(
    (m) =>
      `${m.sourcePlate || "Source_1"},${m.sourceWell},${m.destPlate || "Dest_1"},${m.destWell},${m.volume}`
  );
  return [header, ...rows].join("\n");
}

/** Generate Hamilton GWL worklist */
export function generateHamiltonGWL(
  mappings: Array<{
    sourceWell: string;
    destWell: string;
    volume: number;
  }>
): string {
  const lines: string[] = [];
  for (const m of mappings) {
    lines.push(`A;Source_1;;;${m.sourceWell};;${m.volume};;;`);
    lines.push(`D;Dest_1;;;${m.destWell};;${m.volume};;;`);
    lines.push("W;");
  }
  return lines.join("\n");
}

/** Generate Opentrons Python protocol */
export function generateOpentronsPython(
  mappings: Array<{
    sourceWell: string;
    destWell: string;
    volume: number;
  }>
): string {
  const transfers = mappings
    .map(
      (m) =>
        `    pipette.transfer(${m.volume}, source_plate['${m.sourceWell}'], dest_plate['${m.destWell}'])`
    )
    .join("\n");

  return `from opentrons import protocol_api

metadata = {
    'protocolName': 'Plate Transfer',
    'author': 'Resonantia Lab',
    'apiLevel': '2.15'
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    source_plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '1')
    dest_plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '2')
    tip_rack = protocol.load_labware('opentrons_96_tiprack_300ul', '3')

    # Load pipette
    pipette = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tip_rack])

    # Transfers
${transfers}
`;
}
