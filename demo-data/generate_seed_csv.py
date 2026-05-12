"""Generate reproducible seed CSV for the killer workflow demo.

Uses a fixed random seed for noise so the file is deterministic.
Run: python generate_seed_csv.py
Produces: dose_response_staurosporine_HEK293T.csv
"""

import csv
import numpy as np
import os

# Fixed seed for reproducibility
RNG = np.random.default_rng(seed=42)

# 4-parameter logistic model (inhibition convention)
# Response = Bottom + (Top - Bottom) / (1 + (Concentration / IC50)^n)
# where n > 0 means response decreases as concentration increases
# When fitting with negative Hill convention: hill = -n
def four_pl(conc, bottom, top, ic50, hill_abs):
    """Generate response for inhibition curve.

    hill_abs is the absolute Hill coefficient (positive value).
    High concentration -> response approaches bottom.
    """
    return bottom + (top - bottom) / (1.0 + (conc / ic50) ** hill_abs)


# Compound definitions: (name, IC50_nM, Hill_abs, Bottom, Top)
# hill_abs is positive (inhibition convention: response goes DOWN at high conc)
COMPOUNDS = [
    ("Staurosporine", 42.0, 1.2, 3.0, 98.0),
    ("Rapamycin", 180.0, 1.0, 5.0, 95.0),
    ("Imatinib", 2500.0, 0.8, 8.0, 92.0),
    ("Dasatinib", 15.0, 1.4, 2.0, 97.0),
    ("Sorafenib", 90.0, 1.1, 4.0, 96.0),
    ("Erlotinib", 500.0, 0.9, 6.0, 94.0),
    ("Compound_F", 50000.0, 0.3, 75.0, 100.0),  # Inactive (flat curve, IC50 way above range)
    ("Compound_G", 8.0, 1.5, 1.0, 99.0),  # Most potent
]

# 10 concentrations: 3-fold dilution from 10000 nM
START_CONC = 10000.0
DILUTION_FACTOR = 3.0
NUM_POINTS = 10
REPLICATES = 3

concentrations = [START_CONC / (DILUTION_FACTOR ** i) for i in range(NUM_POINTS)]

# Well assignment: 96-well plate layout
# 8 compounds x 10 concentrations x 3 replicates = 240 wells
# Layout: each compound gets 3 rows (replicates), 10 columns (concentrations)
# But since 8 compounds x 3 replicates = 24 rows > 8 rows in a 96-well plate,
# we'll use a 384-well plate or just assign well labels sequentially.
# For simplicity, use row-based assignment in multiple plates or a 384-well plate.
# Actually the spec just says "Well" column - use standard plate notation.

ROWS = "ABCDEFGHIJKLMNOPQRSTUVWX"  # 24 rows (enough for 8 compounds x 3 replicates)


def generate_well_label(compound_idx, replicate, conc_idx):
    """Generate well label: each compound gets 3 consecutive rows."""
    row_idx = compound_idx * REPLICATES + replicate
    col = conc_idx + 1
    return f"{ROWS[row_idx]}{col}"


def generate_data():
    rows = []
    for comp_idx, (name, ic50, hill, bottom, top) in enumerate(COMPOUNDS):
        for conc_idx, conc in enumerate(concentrations):
            ideal_response = four_pl(conc, bottom, top, ic50, hill)
            for rep in range(REPLICATES):
                # Add realistic noise: ±5-10% relative noise
                noise_pct = RNG.normal(0, 0.07)  # ~7% CV
                noisy_response = ideal_response * (1 + noise_pct)
                # Clamp to [0, 110] - biological data can't go below 0
                noisy_response = max(0.0, min(110.0, noisy_response))
                well = generate_well_label(comp_idx, rep, conc_idx)
                rows.append({
                    "Compound": name,
                    "Concentration_nM": round(conc, 4),
                    "Response_Pct": round(noisy_response, 2),
                    "Well": well,
                    "Replicate": rep + 1,
                })
    return rows


def main():
    data = generate_data()
    output_path = os.path.join(os.path.dirname(__file__), "dose_response_staurosporine_HEK293T.csv")

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Compound", "Concentration_nM", "Response_Pct", "Well", "Replicate"])
        writer.writeheader()
        writer.writerows(data)

    print(f"Generated {len(data)} rows -> {output_path}")

    # Verify staurosporine IC50
    from scipy.optimize import curve_fit

    stauro_data = [(r["Concentration_nM"], r["Response_Pct"]) for r in data if r["Compound"] == "Staurosporine"]
    concs = [d[0] for d in stauro_data]
    resps = [d[1] for d in stauro_data]

    def fit_4pl(x, bottom, top, ec50, hill):
        return bottom + (top - bottom) / (1.0 + (np.array(x) / ec50) ** hill)

    popt, _ = curve_fit(fit_4pl, concs, resps, p0=[3.0, 98.0, 42.0, -1.2], maxfev=10000)
    fitted_ic50 = popt[2]
    print(f"Staurosporine fitted IC50: {fitted_ic50:.2f} nM (target: ~42 nM)")

    # Compute R²
    fitted_vals = fit_4pl(np.array(concs), *popt)
    ss_res = np.sum((np.array(resps) - fitted_vals) ** 2)
    ss_tot = np.sum((np.array(resps) - np.mean(resps)) ** 2)
    r_squared = 1 - ss_res / ss_tot
    print(f"Staurosporine R²: {r_squared:.4f} (target: ~0.99)")
    print(f"Staurosporine Hill slope: {popt[3]:.3f} (target: ~-1.2)")


if __name__ == "__main__":
    main()
