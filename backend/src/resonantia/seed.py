"""Seed the database with demo data for first-run experience."""

import logging
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from resonantia.models.eln_entry import ELNAppendix, ELNEntry
from resonantia.models.experiment import Experiment
from resonantia.models.plate import PlateMap
from resonantia.models.protocol import Protocol, ProtocolStep
from resonantia.models.sample import Sample

logger = logging.getLogger(__name__)

_today = date.today()


async def seed_if_empty(session: AsyncSession) -> None:
    """Seed the database only if it's empty."""
    count = await session.scalar(select(func.count()).select_from(Sample))
    if count and count > 0:
        logger.info("Database already has %d samples, skipping seed", count)
        return

    logger.info("Empty database detected, seeding demo data...")
    await _seed_samples(session)
    await _seed_plates(session)
    await _seed_experiments(session)
    await _seed_eln_entries(session)
    await _seed_protocols(session)
    await session.commit()
    logger.info("Database seeded successfully")


async def _seed_samples(session: AsyncSession) -> None:
    """Seed realistic lab samples."""
    samples = [
        # ── Antibodies ──────────────────────────────────────────────
        Sample(
            name="Anti-EGFR (Rabbit)",
            barcode="RES-2024-1001",
            sample_type="antibody",
            location="Freezer-A / Shelf-1 / Box-3 / A1",
            storage_temp=-20.0,
            lot_number="AB-2024-4421",
            expiry_date=_today + timedelta(days=180),
            quantity=250,
            unit="µL",
            metadata_extra={
                "host": "Rabbit",
                "clonality": "Polyclonal",
                "target": "EGFR",
            },
        ),
        Sample(
            name="Anti-β-actin (Mouse)",
            barcode="RES-2024-1002",
            sample_type="antibody",
            location="Freezer-A / Shelf-1 / Box-3 / A2",
            storage_temp=-20.0,
            lot_number="AB-2024-4422",
            expiry_date=_today + timedelta(days=365),
            quantity=500,
            unit="µL",
            metadata_extra={
                "host": "Mouse",
                "clonality": "Monoclonal",
                "target": "β-actin",
            },
        ),
        Sample(
            name="Anti-HER2 (Rabbit)",
            barcode="RES-2024-1003",
            sample_type="antibody",
            location="Freezer-A / Shelf-1 / Box-3 / B1",
            storage_temp=-20.0,
            lot_number="AB-2024-4423",
            expiry_date=_today + timedelta(days=15),  # Expiring soon
            quantity=100,
            unit="µL",
            metadata_extra={"host": "Rabbit", "target": "HER2"},
        ),
        Sample(
            name="Anti-GFP (Rabbit pAb)",
            barcode="RES-2024-1015",
            sample_type="antibody",
            location="Freezer-A / Shelf-2 / Box-1 / C1",
            storage_temp=-20.0,
            lot_number="AB-2024-6601",
            expiry_date=_today + timedelta(days=20),
            quantity=200,
            unit="µL",
            metadata_extra={"host": "Rabbit", "clonality": "Polyclonal"},
        ),
        # ── Cell lines ──────────────────────────────────────────────
        Sample(
            name="HeLa S3",
            barcode="RES-2024-1004",
            sample_type="cell_line",
            location="LN2 Tank-1 / Rack-A / Box-2 / C1",
            storage_temp=-196.0,
            lot_number="CL-2024-0012",
            expiry_date=_today + timedelta(days=730),
            quantity=5,
            unit="vials",
            metadata_extra={"organism": "Human", "tissue": "Cervix"},
        ),
        Sample(
            name="HEK293T",
            barcode="RES-2024-1005",
            sample_type="cell_line",
            location="LN2 Tank-1 / Rack-A / Box-2 / C2",
            storage_temp=-196.0,
            lot_number="CL-2024-0013",
            expiry_date=_today + timedelta(days=730),
            quantity=10,
            unit="vials",
            metadata_extra={"organism": "Human", "tissue": "Kidney"},
        ),
        Sample(
            name="MCF-7",
            barcode="RES-2024-1006",
            sample_type="cell_line",
            location="LN2 Tank-1 / Rack-B / Box-1 / A1",
            storage_temp=-196.0,
            lot_number="CL-2024-0014",
            expiry_date=_today + timedelta(days=730),
            quantity=2,
            unit="vials",
            metadata_extra={"organism": "Human", "tissue": "Breast"},
        ),
        # ── Compounds ───────────────────────────────────────────────
        Sample(
            name="Staurosporine",
            barcode="RES-2024-1007",
            sample_type="compound",
            location="Freezer-B / Shelf-2 / Box-4 / D1",
            storage_temp=-20.0,
            lot_number="CP-2024-8810",
            expiry_date=_today + timedelta(days=365),
            quantity=1,
            unit="mg",
            metadata_extra={"mw": 466.53, "cas": "62996-74-1"},
        ),
        Sample(
            name="Rapamycin",
            barcode="RES-2024-1008",
            sample_type="compound",
            location="Freezer-B / Shelf-2 / Box-4 / D2",
            storage_temp=-20.0,
            lot_number="CP-2024-8811",
            expiry_date=_today - timedelta(days=10),  # Expired
            quantity=0.5,
            unit="mg",
            metadata_extra={"mw": 914.17, "cas": "53123-88-9"},
        ),
        Sample(
            name="Doxorubicin",
            barcode="RES-2024-1009",
            sample_type="compound",
            location="Freezer-B / Shelf-2 / Box-4 / D3",
            storage_temp=-20.0,
            lot_number="CP-2024-8812",
            expiry_date=_today + timedelta(days=200),
            quantity=2,
            unit="mg",
            metadata_extra={"mw": 543.52, "cas": "25316-40-9"},
        ),
        # ── Media ───────────────────────────────────────────────────
        Sample(
            name="DMEM + 10% FBS",
            barcode="RES-2024-1010",
            sample_type="media",
            location="Fridge-1 / Shelf-3",
            storage_temp=4.0,
            lot_number="MD-2024-7712",
            expiry_date=_today + timedelta(days=25),  # Expiring
            quantity=500,
            unit="mL",
            metadata_extra={"supplements": "10% FBS, 1% P/S"},
        ),
        Sample(
            name="RPMI 1640",
            barcode="RES-2024-1011",
            sample_type="media",
            location="Fridge-1 / Shelf-3",
            storage_temp=4.0,
            lot_number="MD-2024-7720",
            expiry_date=_today + timedelta(days=60),
            quantity=500,
            unit="mL",
            metadata_extra={"supplements": "None"},
        ),
        # ── Buffers ─────────────────────────────────────────────────
        Sample(
            name="PBS 1X",
            barcode="RES-2024-1012",
            sample_type="buffer",
            location="Shelf-A / Cabinet-2",
            storage_temp=22.0,  # Room temperature
            lot_number="BF-2024-5501",
            expiry_date=_today + timedelta(days=300),
            quantity=1000,
            unit="mL",
            metadata_extra={},
        ),
        Sample(
            name="Lysis Buffer (RIPA)",
            barcode="RES-2024-1013",
            sample_type="buffer",
            location="Fridge-1 / Shelf-2",
            storage_temp=4.0,
            lot_number="BF-2024-5502",
            expiry_date=_today + timedelta(days=90),
            quantity=50,
            unit="mL",
            metadata_extra={
                "composition": "50mM Tris, 150mM NaCl, 1% NP-40",
            },
        ),
        # ── Reagents ────────────────────────────────────────────────
        Sample(
            name="Lipofectamine 3000",
            barcode="RES-2024-1014",
            sample_type="reagent",
            location="Fridge-1 / Shelf-1 / Box-1",
            storage_temp=4.0,
            lot_number="RG-2024-3301",
            expiry_date=_today + timedelta(days=120),
            quantity=0.75,
            unit="mL",
            metadata_extra={"supplier": "Thermo Fisher"},
        ),
        Sample(
            name="FBS (Heat Inactivated)",
            barcode="RES-2024-1016",
            sample_type="reagent",
            location="Freezer-A / Shelf-3 / Box-2",
            storage_temp=-20.0,
            lot_number="RG-2024-3302",
            expiry_date=_today + timedelta(days=180),
            quantity=50,
            unit="mL",
            metadata_extra={"supplier": "Gibco", "origin": "Brazil"},
        ),
    ]

    session.add_all(samples)
    logger.info("Seeded %d samples", len(samples))


async def _seed_plates(session: AsyncSession) -> None:
    """Seed demo plate maps."""
    plates = [
        PlateMap(
            name="HTS Screen — Round 1",
            plate_type="96",
            description="Primary cytotoxicity screen of kinase inhibitor panel",
            source_plates={"plates": [{"name": "Compound Library Plate A", "barcode": "SRC-001"}]},
            destination_plate={"barcode": "DEST-001", "type": "96"},
            well_mappings=[
                {"source": "A1", "dest": "A1", "compound": "Staurosporine", "conc": 10.0},
                {"source": "A2", "dest": "A2", "compound": "Staurosporine", "conc": 3.33},
                {"source": "A3", "dest": "A3", "compound": "Staurosporine", "conc": 1.11},
                {"source": "B1", "dest": "B1", "compound": "Rapamycin", "conc": 10.0},
                {"source": "B2", "dest": "B2", "compound": "Rapamycin", "conc": 3.33},
            ],
            worklist_data=None,
        ),
        PlateMap(
            name="Kinase Inhibitor Dose-Response",
            plate_type="96",
            description="8-point dose-response for 4 kinase inhibitors",
            source_plates={"plates": [{"name": "Kinase Inhibitor Panel", "barcode": "SRC-002"}]},
            destination_plate={"barcode": "DEST-002", "type": "96"},
            well_mappings=[],
            worklist_data=None,
        ),
        PlateMap(
            name="Replicate QC Plate",
            plate_type="384",
            description="Quality control replicate for validation",
            source_plates={"plates": [{"name": "Compound Library Plate A", "barcode": "SRC-001"}, {"name": "Compound Library Plate B", "barcode": "SRC-003"}]},
            destination_plate={"barcode": "DEST-003", "type": "384"},
            well_mappings=[],
            worklist_data=None,
        ),
    ]
    session.add_all(plates)
    logger.info("Seeded %d plate maps", len(plates))


async def _seed_experiments(session: AsyncSession) -> None:
    """Seed demo experiments."""
    experiments = [
        Experiment(
            name="Staurosporine IC50 — HEK293T",
            description="Dose-response curve fitting for Staurosporine in HEK293T cells",
            protocol="4PL curve fitting, 8-point serial dilution, triplicate",
            status="completed",
            results={
                "ec50": 0.042,
                "hill_slope": 1.23,
                "r_squared": 0.994,
                "top": 100.2,
                "bottom": 3.1,
            },
        ),
        Experiment(
            name="HCS Plate Z-score Normalization",
            description="High-content screening plate normalization using Z-score method",
            protocol="Z-score normalization, columns 1+12 as controls",
            status="completed",
            results={
                "method": "z-score",
                "z_prime": 0.72,
                "plate_count": 1,
            },
        ),
        Experiment(
            name="Kinase Panel Screening",
            description="Primary screen of kinase inhibitor panel",
            protocol="Single-point screening at 10 µM, CellTiter-Glo readout",
            status="draft",
            results=None,
        ),
    ]
    session.add_all(experiments)
    logger.info("Seeded %d experiments", len(experiments))


async def _seed_eln_entries(session: AsyncSession) -> None:
    """Seed demo ELN entries."""
    entries = [
        ELNEntry(
            title="Staurosporine IC50 Determination — HEK293T",
            entry_number="ELN-2026-0001",
            content_markdown="""# Staurosporine IC50 Determination — HEK293T

## Objective
Determine the IC50 of Staurosporine in HEK293T cells using a CellTiter-Glo viability assay.

## Protocol
- 4-parameter logistic (4PL) curve fitting
- 8-point serial dilution (1:3), starting at 10 µM
- Triplicate wells per concentration
- 48-hour compound incubation

## Materials
| Reagent | Lot | Quantity |
|---------|-----|----------|
| Staurosporine | CP-2024-8810 | 1 mg |
| DMEM + 10% FBS | MD-2024-7712 | 50 mL |
| CellTiter-Glo | CTG-2026-001 | 10 mL |

## Results
| Parameter | Value |
|-----------|-------|
| EC50 | 0.042 µM |
| Hill slope | 1.23 |
| R² | 0.994 |
| Top | 100.2% |
| Bottom | 3.1% |

## Conclusions
Staurosporine shows potent cytotoxicity in HEK293T cells with an EC50 of 42 nM, consistent with published literature values (30-100 nM range).
""",
            summary="IC50 determination of Staurosporine in HEK293T cells. EC50 = 0.042 µM.",
            status="submitted",
            version=1,
            author_id="demo-user",
            tags=["cytotoxicity", "dose-response", "staurosporine"],
            linked_references={"experiments": [], "samples": [], "plates": []},
        ),
        ELNEntry(
            title="HCS Plate Normalization — Z-score Method",
            entry_number="ELN-2026-0002",
            content_markdown="""# HCS Plate Normalization

## Objective
Normalize high-content screening plate data using Z-score method to identify hits.

## Method
Z-score normalization using columns 1 and 12 as positive and negative controls respectively.

## Results
- Z-prime factor: 0.72 (excellent assay quality)
- Hit threshold: Z-score < -3
- Hits identified: 12 out of 80 compounds

## Notes
Plate edge effects were minimal. Controls showed consistent separation.
""",
            summary="Z-score normalization of HCS plate. Z-prime = 0.72.",
            status="draft",
            version=1,
            author_id="demo-user",
            tags=["normalization", "hcs", "z-score"],
        ),
    ]
    session.add_all(entries)
    logger.info("Seeded %d ELN entries", len(entries))


async def _seed_protocols(session: AsyncSession) -> None:
    """Seed demo protocols with steps."""
    # Protocol 1: Cytotoxicity assay
    cyto_protocol = Protocol(
        name="CellTiter-Glo Cytotoxicity Assay",
        description="Standard cytotoxicity assay using CellTiter-Glo luminescent viability reagent for IC50 determination.",
        version=1,
        status="published",
        is_template=True,
        author_id="demo-user",
        tags=["cytotoxicity", "viability", "dose-response"],
    )
    session.add(cyto_protocol)
    await session.flush()

    cyto_steps = [
        ProtocolStep(
            protocol_id=cyto_protocol.id,
            step_order=1,
            title="Cell Seeding",
            description="Seed HEK293T cells at 5,000 cells/well in 100 µL DMEM + 10% FBS into a white 96-well plate.",
            duration_minutes=30,
            temperature_celsius=37.0,
            equipment="Biosafety Cabinet, Incubator",
            reagents=[
                {"name": "DMEM + 10% FBS", "volume": 100, "unit": "uL"},
                {"name": "HEK293T", "volume": 1, "unit": "vials"},
            ],
        ),
        ProtocolStep(
            protocol_id=cyto_protocol.id,
            step_order=2,
            title="Overnight Incubation",
            description="Incubate at 37°C, 5% CO2 for 24 hours to allow cell attachment.",
            duration_minutes=1440,
            temperature_celsius=37.0,
            equipment="CO2 Incubator",
        ),
        ProtocolStep(
            protocol_id=cyto_protocol.id,
            step_order=3,
            title="Compound Treatment",
            description="Add 8-point 1:3 serial dilution of compound starting at 10 µM. Triplicate wells per concentration.",
            duration_minutes=60,
            temperature_celsius=22.0,
            equipment="Echo 555 Liquid Handler",
            reagents=[
                {"name": "Staurosporine", "volume": 0.1, "unit": "uL"},
            ],
        ),
        ProtocolStep(
            protocol_id=cyto_protocol.id,
            step_order=4,
            title="48-Hour Incubation",
            description="Incubate plates with compound for 48 hours at 37°C, 5% CO2.",
            duration_minutes=2880,
            temperature_celsius=37.0,
            equipment="CO2 Incubator",
        ),
        ProtocolStep(
            protocol_id=cyto_protocol.id,
            step_order=5,
            title="CellTiter-Glo Readout",
            description="Add 100 µL CellTiter-Glo reagent per well. Shake 2 min, incubate 10 min at RT, read luminescence.",
            duration_minutes=30,
            temperature_celsius=22.0,
            equipment="Plate Reader (EnVision)",
            reagents=[
                {"name": "CellTiter-Glo", "volume": 100, "unit": "uL"},
            ],
        ),
        ProtocolStep(
            protocol_id=cyto_protocol.id,
            step_order=6,
            title="Data Analysis",
            description="Fit 4PL dose-response curve using Resonantia processing pipeline. Calculate IC50, Hill slope, R².",
            duration_minutes=60,
        ),
    ]
    session.add_all(cyto_steps)

    # Protocol 2: Transfection
    transfection_protocol = Protocol(
        name="Lipofectamine 3000 Transfection",
        description="Standard lipofection protocol for transient transfection of adherent mammalian cells.",
        version=1,
        status="draft",
        is_template=True,
        author_id="demo-user",
        tags=["transfection", "lipofection"],
    )
    session.add(transfection_protocol)
    await session.flush()

    transfection_steps = [
        ProtocolStep(
            protocol_id=transfection_protocol.id,
            step_order=1,
            title="Cell Seeding",
            description="Seed cells at 60-70% confluency in 24-well plates, 500 µL/well.",
            duration_minutes=30,
            temperature_celsius=37.0,
            equipment="Biosafety Cabinet",
            reagents=[
                {"name": "DMEM + 10% FBS", "volume": 500, "unit": "uL"},
            ],
        ),
        ProtocolStep(
            protocol_id=transfection_protocol.id,
            step_order=2,
            title="Prepare Lipid-DNA Complexes",
            description="Dilute 1 µg DNA in 25 µL Opti-MEM + P3000. Dilute 1.5 µL Lipofectamine 3000 in 25 µL Opti-MEM. Combine and incubate 15 min.",
            duration_minutes=25,
            temperature_celsius=22.0,
            reagents=[
                {"name": "Lipofectamine 3000", "volume": 1.5, "unit": "uL"},
            ],
        ),
        ProtocolStep(
            protocol_id=transfection_protocol.id,
            step_order=3,
            title="Transfect Cells",
            description="Add 50 µL DNA-lipid complexes dropwise to each well.",
            duration_minutes=15,
            temperature_celsius=22.0,
            equipment="Biosafety Cabinet",
        ),
        ProtocolStep(
            protocol_id=transfection_protocol.id,
            step_order=4,
            title="Post-Transfection Incubation",
            description="Incubate 24-48 hours at 37°C, 5% CO2.",
            duration_minutes=1440,
            temperature_celsius=37.0,
            equipment="CO2 Incubator",
        ),
    ]
    session.add_all(transfection_steps)
    logger.info("Seeded 2 protocols with steps")
