# SPEC: Dose-Response Curve Fit Integration

**ID:** P1.2
**Phase:** 1 — Killer Workflow
**Branch:** `feat/dose-response-integration`
**Priority:** P1
**Effort:** 3 days
**Dependencies:** P1.1 (storage + CSV upload)

---

## Problem Statement

The `fit_dose_response` tool handler exists in `data_processor.py` with real scipy 4PL curve fitting, but:
- It doesn't generate a visual plot (scientists need to see the curve)
- Results aren't persisted to the Experiment model
- The tool response doesn't include confidence intervals
- No inline plot rendering in chat

---

## Scope

### In Scope
- Generate matplotlib figure (sigmoidal curve + data points + IC50 line)
- Save figure via storage abstraction, return URL
- Persist fit results to Experiment model
- Return structured results with confidence intervals
- Render plot inline in chat

### Out of Scope
- Multi-compound overlay plots (defer)
- Interactive plot (static PNG is sufficient)
- Custom plot styling beyond standard scientific presentation

---

## Architecture

### Tool Response Schema

```python
class DoseResponseResult(BaseModel):
    ic50: float
    ic50_ci_lower: float  # 95% CI
    ic50_ci_upper: float
    hill_slope: float
    r_squared: float
    z_prime: float | None  # If controls provided
    top: float  # Upper asymptote
    bottom: float  # Lower asymptote
    outliers: list[dict]  # { well, concentration, response, residual }
    plot_url: str  # URL to generated PNG
    experiment_id: str  # Created/linked experiment
    n_points: int
    n_replicates: int
```

### Plot Generation

```python
# Generate publication-quality dose-response plot
# - X axis: log10(concentration) with nM/μM labels
# - Y axis: Response (%)
# - Blue dots: data points (with error bars if replicates)
# - Red line: fitted 4PL curve
# - Dashed vertical line at IC50
# - Shaded band: 95% CI around IC50
# - Text annotation: IC50 = X nM, Hill = Y, R² = Z
# - Figure size: 6x4 inches, 150 DPI (good for inline chat display)
```

---

## Implementation

### Step 1: Enhance data_processor.py (day 1)
- Add confidence interval calculation (bootstrap or asymptotic)
- Add Z-prime calculation when control wells are provided
- Add outlier detection (>3 SD from fitted curve)

### Step 2: Plot generation (day 1-2)
- matplotlib figure with scientific styling
- Save as PNG via storage abstraction
- Return plot URL in tool result

### Step 3: Persist to Experiment (day 2)
- Create Experiment record if none exists for this analysis
- Store fit parameters in `results` JSON field
- Link to source file (file_upload_id)

### Step 4: Wire tool handler (day 2-3)
- Update `fit_dose_response` handler in tool_executor to use enhanced processor
- Return full `DoseResponseResult` as tool output
- Agent renders: summary text + inline plot image

### Step 5: Frontend inline plot (day 3)
- Chat message renderer: when tool result contains `plot_url`, render as `<img>`
- Responsive sizing (max-width within chat bubble)

---

## Expected Behavior

| Input | Output |
|-------|--------|
| CSV with Compound, Concentration, Response columns | IC50, Hill slope, R², Z', 95% CI, plot URL, experiment_id |
| 10-point staurosporine dose-response, 3 replicates | IC50 ~42 nM, Hill ~-1.18, R² >0.99, publication-quality plot |
| Data with outliers at high concentration | Outliers flagged in result, visible as red points on plot |
| Data with poor fit (R² < 0.8) | Warning in agent response: "Poor fit quality — consider removing outliers" |

---

## Acceptance Criteria

- [ ] `fit_dose_response` tool returns: IC50, Hill slope, R², Z' (if controls), 95% CI, plot URL
- [ ] Plot PNG generated and accessible via URL (survives restart)
- [ ] Plot shows: data points, fitted curve, IC50 line, CI band, annotation text
- [ ] Results persisted to Experiment model in database
- [ ] Experiment linked to source file (file_upload_id)
- [ ] Chat renders plot inline (img tag with plot URL)
- [ ] Outliers identified and reported (>3 SD from curve)
- [ ] Seed CSV produces reproducible IC50 ~42 nM for staurosporine
- [ ] Agent summarizes results in natural language alongside plot
