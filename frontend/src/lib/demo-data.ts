// Demo data for Sample & Reagent Tracker and Plate Maps

export type SampleType =
  | "antibody"
  | "cell_line"
  | "compound"
  | "media"
  | "buffer"
  | "enzyme"
  | "primer"
  | "plasmid"
  | "reagent";

export type SampleStatus = "active" | "expiring" | "expired" | "low_stock";

export interface Sample {
  id: string;
  name: string;
  barcode: string;
  type: SampleType;
  location: string;
  storageTemp: string;
  lotNumber: string;
  expiryDate: string;
  quantity: number;
  unit: string;
  status: SampleStatus;
  addedDate: string;
  notes?: string;
  supplier?: string;
  catalogNumber?: string;
}

function barcode(n: number): string {
  return `RES-2024-${String(n).padStart(4, "0")}`;
}

function daysFromNow(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().split("T")[0];
}

function daysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split("T")[0];
}

export const DEMO_SAMPLES: Sample[] = [
  {
    id: "s1",
    name: "Anti-GFP Rabbit pAb",
    barcode: barcode(1001),
    type: "antibody",
    location: "Freezer-A / Shelf-2 / Box-3 / A1",
    storageTemp: "-20°C",
    lotNumber: "AB-2024-0391",
    expiryDate: daysFromNow(180),
    quantity: 250,
    unit: "µL",
    status: "active",
    addedDate: daysAgo(45),
    supplier: "Abcam",
    catalogNumber: "ab290",
  },
  {
    id: "s2",
    name: "Anti-mCherry Mouse mAb",
    barcode: barcode(1002),
    type: "antibody",
    location: "Freezer-A / Shelf-2 / Box-3 / A2",
    storageTemp: "-20°C",
    lotNumber: "AB-2024-0412",
    expiryDate: daysFromNow(15),
    quantity: 50,
    unit: "µL",
    status: "expiring",
    addedDate: daysAgo(90),
    supplier: "Thermo Fisher",
    catalogNumber: "M11217",
  },
  {
    id: "s3",
    name: "HEK293T Cells",
    barcode: barcode(1003),
    type: "cell_line",
    location: "LN2 Tank-1 / Rack-B / Box-7 / C3",
    storageTemp: "-196°C",
    lotNumber: "CL-2023-8812",
    expiryDate: daysFromNow(730),
    quantity: 5,
    unit: "vials",
    status: "active",
    addedDate: daysAgo(200),
    supplier: "ATCC",
    catalogNumber: "CRL-3216",
  },
  {
    id: "s4",
    name: "HeLa S3 Cells",
    barcode: barcode(1004),
    type: "cell_line",
    location: "LN2 Tank-1 / Rack-B / Box-7 / C4",
    storageTemp: "-196°C",
    lotNumber: "CL-2023-8844",
    expiryDate: daysFromNow(600),
    quantity: 2,
    unit: "vials",
    status: "low_stock",
    addedDate: daysAgo(300),
    supplier: "ATCC",
    catalogNumber: "CCL-2.2",
  },
  {
    id: "s5",
    name: "Staurosporine",
    barcode: barcode(1005),
    type: "compound",
    location: "Freezer-B / Shelf-1 / Box-1 / D5",
    storageTemp: "-20°C",
    lotNumber: "CP-2024-3321",
    expiryDate: daysFromNow(365),
    quantity: 1,
    unit: "mg",
    status: "active",
    addedDate: daysAgo(30),
    supplier: "Sigma-Aldrich",
    catalogNumber: "S5921",
  },
  {
    id: "s6",
    name: "Rapamycin",
    barcode: barcode(1006),
    type: "compound",
    location: "Freezer-B / Shelf-1 / Box-1 / D6",
    storageTemp: "-20°C",
    lotNumber: "CP-2024-3344",
    expiryDate: daysFromNow(-10),
    quantity: 0.5,
    unit: "mg",
    status: "expired",
    addedDate: daysAgo(400),
    supplier: "Sigma-Aldrich",
    catalogNumber: "R0395",
  },
  {
    id: "s7",
    name: "DMEM + 10% FBS",
    barcode: barcode(1007),
    type: "media",
    location: "Fridge-1 / Shelf-3",
    storageTemp: "4°C",
    lotNumber: "MD-2024-7712",
    expiryDate: daysFromNow(25),
    quantity: 500,
    unit: "mL",
    status: "expiring",
    addedDate: daysAgo(5),
    supplier: "Gibco",
    catalogNumber: "11965092",
  },
  {
    id: "s8",
    name: "RPMI 1640",
    barcode: barcode(1008),
    type: "media",
    location: "Fridge-1 / Shelf-3",
    storageTemp: "4°C",
    lotNumber: "MD-2024-7720",
    expiryDate: daysFromNow(60),
    quantity: 1000,
    unit: "mL",
    status: "active",
    addedDate: daysAgo(10),
    supplier: "Gibco",
    catalogNumber: "11875093",
  },
  {
    id: "s9",
    name: "PBS 1X",
    barcode: barcode(1009),
    type: "buffer",
    location: "Shelf-A / Cabinet-2",
    storageTemp: "RT",
    lotNumber: "BF-2024-5501",
    expiryDate: daysFromNow(300),
    quantity: 2000,
    unit: "mL",
    status: "active",
    addedDate: daysAgo(15),
    supplier: "Corning",
    catalogNumber: "21-040-CV",
  },
  {
    id: "s10",
    name: "Tris-HCl Buffer (pH 7.4)",
    barcode: barcode(1010),
    type: "buffer",
    location: "Shelf-A / Cabinet-2",
    storageTemp: "RT",
    lotNumber: "BF-2024-5520",
    expiryDate: daysFromNow(200),
    quantity: 500,
    unit: "mL",
    status: "active",
    addedDate: daysAgo(20),
    supplier: "Bio-Rad",
  },
  {
    id: "s11",
    name: "T4 DNA Ligase",
    barcode: barcode(1011),
    type: "enzyme",
    location: "Freezer-A / Shelf-1 / Box-2 / E1",
    storageTemp: "-20°C",
    lotNumber: "EN-2024-1102",
    expiryDate: daysFromNow(90),
    quantity: 100,
    unit: "µL",
    status: "active",
    addedDate: daysAgo(60),
    supplier: "NEB",
    catalogNumber: "M0202S",
  },
  {
    id: "s12",
    name: "Taq DNA Polymerase",
    barcode: barcode(1012),
    type: "enzyme",
    location: "Freezer-A / Shelf-1 / Box-2 / E2",
    storageTemp: "-20°C",
    lotNumber: "EN-2024-1130",
    expiryDate: daysFromNow(20),
    quantity: 25,
    unit: "µL",
    status: "expiring",
    addedDate: daysAgo(150),
    supplier: "NEB",
    catalogNumber: "M0273S",
  },
  {
    id: "s13",
    name: "Forward Primer (GFP-F)",
    barcode: barcode(1013),
    type: "primer",
    location: "Freezer-C / Shelf-1 / Box-P1 / A1",
    storageTemp: "-20°C",
    lotNumber: "PR-2024-0010",
    expiryDate: daysFromNow(365),
    quantity: 50,
    unit: "nmol",
    status: "active",
    addedDate: daysAgo(25),
    supplier: "IDT",
    notes: "5'-ATGGTGAGCAAGGGCGAGG-3'",
  },
  {
    id: "s14",
    name: "Reverse Primer (GFP-R)",
    barcode: barcode(1014),
    type: "primer",
    location: "Freezer-C / Shelf-1 / Box-P1 / A2",
    storageTemp: "-20°C",
    lotNumber: "PR-2024-0011",
    expiryDate: daysFromNow(365),
    quantity: 50,
    unit: "nmol",
    status: "active",
    addedDate: daysAgo(25),
    supplier: "IDT",
    notes: "5'-CTTGTACAGCTCGTCCATGC-3'",
  },
  {
    id: "s15",
    name: "pEGFP-N1 Plasmid",
    barcode: barcode(1015),
    type: "plasmid",
    location: "Freezer-A / Shelf-3 / Box-5 / B1",
    storageTemp: "-20°C",
    lotNumber: "PL-2023-4401",
    expiryDate: daysFromNow(500),
    quantity: 20,
    unit: "µg",
    status: "active",
    addedDate: daysAgo(120),
    supplier: "Addgene",
    catalogNumber: "#6085-1",
  },
  {
    id: "s16",
    name: "Lipofectamine 3000",
    barcode: barcode(1016),
    type: "reagent",
    location: "Fridge-2 / Shelf-1",
    storageTemp: "4°C",
    lotNumber: "RG-2024-8801",
    expiryDate: daysFromNow(45),
    quantity: 0.75,
    unit: "mL",
    status: "active",
    addedDate: daysAgo(40),
    supplier: "Thermo Fisher",
    catalogNumber: "L3000015",
  },
  {
    id: "s17",
    name: "DAPI Stain (1 mg/mL)",
    barcode: barcode(1017),
    type: "reagent",
    location: "Freezer-B / Shelf-2 / Box-4 / F1",
    storageTemp: "-20°C",
    lotNumber: "RG-2024-8820",
    expiryDate: daysFromNow(200),
    quantity: 100,
    unit: "µL",
    status: "active",
    addedDate: daysAgo(50),
    supplier: "Invitrogen",
    catalogNumber: "D1306",
  },
  {
    id: "s18",
    name: "Trypsin-EDTA (0.25%)",
    barcode: barcode(1018),
    type: "reagent",
    location: "Fridge-1 / Shelf-2",
    storageTemp: "4°C",
    lotNumber: "RG-2024-8830",
    expiryDate: daysFromNow(-5),
    quantity: 100,
    unit: "mL",
    status: "expired",
    addedDate: daysAgo(180),
    supplier: "Gibco",
    catalogNumber: "25200056",
  },
  {
    id: "s19",
    name: "Fetal Bovine Serum",
    barcode: barcode(1019),
    type: "reagent",
    location: "Freezer-D / Shelf-1 / Box-1 / A1",
    storageTemp: "-20°C",
    lotNumber: "RG-2024-8850",
    expiryDate: daysFromNow(120),
    quantity: 50,
    unit: "mL",
    status: "low_stock",
    addedDate: daysAgo(60),
    supplier: "Gibco",
    catalogNumber: "26140079",
  },
  {
    id: "s20",
    name: "Puromycin (10 mg/mL)",
    barcode: barcode(1020),
    type: "reagent",
    location: "Freezer-B / Shelf-2 / Box-4 / F3",
    storageTemp: "-20°C",
    lotNumber: "RG-2024-8860",
    expiryDate: daysFromNow(250),
    quantity: 500,
    unit: "µL",
    status: "active",
    addedDate: daysAgo(10),
    supplier: "InvivoGen",
    catalogNumber: "ant-pr-1",
  },
  {
    id: "s21",
    name: "Hoechst 33342",
    barcode: barcode(1021),
    type: "reagent",
    location: "Freezer-B / Shelf-2 / Box-4 / F4",
    storageTemp: "-20°C",
    lotNumber: "RG-2024-8870",
    expiryDate: daysFromNow(300),
    quantity: 200,
    unit: "µL",
    status: "active",
    addedDate: daysAgo(35),
    supplier: "Thermo Fisher",
    catalogNumber: "H3570",
  },
  {
    id: "s22",
    name: "CHO-K1 Cells",
    barcode: barcode(1022),
    type: "cell_line",
    location: "LN2 Tank-2 / Rack-A / Box-3 / D1",
    storageTemp: "-196°C",
    lotNumber: "CL-2024-9001",
    expiryDate: daysFromNow(700),
    quantity: 1,
    unit: "vials",
    status: "low_stock",
    addedDate: daysAgo(100),
    supplier: "ATCC",
    catalogNumber: "CCL-61",
  },
];

export interface PlateMapEntry {
  id: string;
  name: string;
  format: "96-well" | "384-well";
  createdDate: string;
  description: string;
  wells: number;
}

export const DEMO_PLATES: PlateMapEntry[] = [
  {
    id: "p1",
    name: "Drug Screen Plate A",
    format: "96-well",
    createdDate: daysAgo(3),
    description: "Dose-response for staurosporine in HEK293T",
    wells: 96,
  },
  {
    id: "p2",
    name: "Drug Screen Plate B",
    format: "96-well",
    createdDate: daysAgo(3),
    description: "Dose-response for rapamycin in HeLa",
    wells: 96,
  },
  {
    id: "p3",
    name: "Transfection Plate 1",
    format: "96-well",
    createdDate: daysAgo(7),
    description: "pEGFP-N1 transfection efficiency test",
    wells: 96,
  },
  {
    id: "p4",
    name: "HCS Assay Plate",
    format: "384-well",
    createdDate: daysAgo(1),
    description: "High-content screening morphology assay",
    wells: 384,
  },
  {
    id: "p5",
    name: "Viability Plate 2024-04",
    format: "96-well",
    createdDate: daysAgo(14),
    description: "CellTiter-Glo viability assay",
    wells: 96,
  },
  {
    id: "p6",
    name: "Compound Library Screen",
    format: "384-well",
    createdDate: daysAgo(2),
    description: "Primary screen of 320 compounds",
    wells: 384,
  },
];

export const SAMPLE_TYPE_LABELS: Record<SampleType, string> = {
  antibody: "Antibody",
  cell_line: "Cell Line",
  compound: "Compound",
  media: "Media",
  buffer: "Buffer",
  enzyme: "Enzyme",
  primer: "Primer",
  plasmid: "Plasmid",
  reagent: "Reagent",
};

export const STATUS_CONFIG: Record<
  SampleStatus,
  { label: string; bg: string; text: string; dot: string }
> = {
  active: {
    label: "Active",
    bg: "bg-emerald-50",
    text: "text-emerald-700",
    dot: "bg-emerald-500",
  },
  expiring: {
    label: "Expiring",
    bg: "bg-yellow-50",
    text: "text-yellow-700",
    dot: "bg-yellow-500",
  },
  expired: {
    label: "Expired",
    bg: "bg-red-50",
    text: "text-red-700",
    dot: "bg-red-500",
  },
  low_stock: {
    label: "Low Stock",
    bg: "bg-orange-50",
    text: "text-orange-700",
    dot: "bg-orange-500",
  },
};
