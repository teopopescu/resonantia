# SPEC: Partner-Specific Workflow Templates

**ID:** P4.3
**Phase:** 4 — Multi-Agent + Observability
**Branch:** `feat/partner-workflows`
**Priority:** P3
**Effort:** 3 days
**Dependencies:** P3.3 (org admin)

---

## Problem Statement

Different design partners have different workflows. A condensate biology lab (Dewpoint) needs HCI → follow-up. A screening lab needs dose-response → hit confirmation. Configurable workflow templates let us adapt without custom code per partner.

---

## Scope

### In Scope
- Template system: per-org workflow configuration
- 2 starter templates: "Dose-Response Screening" and "High-Content Imaging"
- Templates configure: enabled tools, default plate format, preferred analysis methods
- Org admin selects template in settings

### Out of Scope
- Custom template editor (admin picks from predefined list)
- Template marketplace
- Per-user template assignment

---

## Architecture

### Template Definition

```python
class WorkflowTemplate(BaseModel):
    id: str
    name: str
    description: str
    enabled_tools: list[str]  # Subset of all tools
    defaults: dict  # { "plate_type": 384, "analysis_method": "4pl", ... }
    system_prompt_additions: str  # Extra context for the agent
    
TEMPLATES = {
    "dose_response_screening": WorkflowTemplate(
        name="Dose-Response Screening",
        description="IC50 determination, hit confirmation, worklist export",
        enabled_tools=["fit_dose_response", "normalize_plate", "calculate_z_prime", 
                       "create_plate_map", "generate_worklist", "create_eln_entry", ...],
        defaults={"plate_type": 384, "analysis_method": "4pl"},
        system_prompt_additions="Focus on dose-response analysis, IC50 determination, and hit follow-up..."
    ),
    "high_content_imaging": WorkflowTemplate(
        name="High-Content Imaging",
        description="Microscopy analysis, FOV navigation, image-based assay QC",
        enabled_tools=["browse_microscopy", "generate_montage", "normalize_plate",
                       "create_eln_entry", ...],
        defaults={"plate_type": 96, "channels": ["DAPI", "GFP", "mCherry"]},
        system_prompt_additions="Focus on microscopy workflows, cell counting, phenotype analysis..."
    ),
}
```

---

## Acceptance Criteria

- [ ] At least 2 workflow templates available
- [ ] Org admin can select a template in settings
- [ ] Selected template configures: which tools the agent offers, default plate format
- [ ] Agent system prompt includes template-specific context
- [ ] Switching templates takes effect on next conversation (no restart)
- [ ] Orgs without a template get all tools (default behavior unchanged)
