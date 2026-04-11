export interface BlogPost {
  slug: string;
  title: string;
  author: string;
  date: string;
  tags: string[];
  excerpt: string;
  content: string;
}

export const demoPosts: BlogPost[] = [
  {
    slug: "integrated-lab-environment",
    title:
      "The Integrated Lab Environment: Why Scientists Deserve Better Tools",
    author: "Teodor Popescu",
    date: "April 10, 2026",
    tags: ["Vision", "Lab Informatics"],
    excerpt:
      "The average lab scientist spends 45 minutes wrangling data for every 15 minutes of actual science. Plate maps in Excel, instrument exports copied between folders, results manually entered into notebooks...",
    content: `The average lab scientist spends 45 minutes wrangling data for every 15 minutes of actual science. Plate maps in Excel, instrument exports copied between folders, results manually entered into notebooks. We have sequenced the human genome, engineered proteins with atomic precision, and built microscopes that resolve individual molecules — yet the informatics layer connecting all of this work remains stuck in the early 2000s.

I spent years at QuantumBlack building ML infrastructure for the pharmaceutical industry, and later at Dewpoint Therapeutics watching world-class biologists wrestle with file-system archaeology just to find their own data. The pattern was always the same: brilliant scientists doing tedious, error-prone busywork because no one had built the connective tissue between their instruments, their analysis, and their decisions.

Resonantia exists to close that gap. We believe the lab deserves an operating system — not another point solution bolted onto the side. An environment where you describe what you need in natural language, and intelligent agents handle the plumbing: plate mapping, data ingestion, curve fitting, image browsing, report generation. The scientist stays in the science; the software stays out of the way.

This is not a LIMS replacement. It is not another ELN. It is the agentic layer that sits above all of them, orchestrating workflows that currently live in your head, your email, and a dozen disconnected spreadsheets. We are building it in the open, one feature at a time, and we invite the community to shape what comes next.`,
  },
  {
    slug: "automating-plate-mapping",
    title:
      "Automating Plate Mapping: From Excel Hell to Intelligent Worklists",
    author: "Teodor Popescu",
    date: "April 8, 2026",
    tags: ["Plate Mapping", "Automation"],
    excerpt:
      "Every screening lab does plate mapping. And almost every screening lab does it in Excel. We built a better way — conversational plate design with automatic worklist generation for Echo, Hamilton, and Opentrons...",
    content: `Every screening lab does plate mapping. And almost every screening lab does it in Excel. The ritual is always the same: copy a template, fill in compound IDs, assign concentrations, double-check the layout, then manually translate the whole thing into a CSV that your liquid handler can understand. One transposed row and you have wasted a week of reagents.

We built a better way. In Resonantia, you describe your plate layout conversationally: "8-point dose-response, half-log dilution from 10 micromolar, triplicate, DMSO controls in columns 1 and 12." The system generates an interactive plate map you can inspect, edit, and approve. When you are satisfied, it exports machine-ready worklists for Echo, Hamilton, Opentrons, or any custom format you define.

The real power is in the feedback loop. Because Resonantia tracks both your plate design and your downstream results, it can flag layout problems before they cost you an experiment. Compounds that consistently show edge effects? The system will suggest moving them inward. Dose ranges that never reach a plateau? It will recommend extending the titration. Over time, the platform learns the patterns of your assay and makes each new experiment a little smarter than the last.

We have already seen labs cut plate-setup time from two hours to ten minutes — and eliminate the transcription errors that used to plague one in every five experiments. That is the kind of leverage we think every scientist deserves.`,
  },
  {
    slug: "ai-dose-response-analysis",
    title: "How AI Agents Can Transform Dose-Response Analysis",
    author: "Teodor Popescu",
    date: "April 5, 2026",
    tags: ["Data Processing", "AI"],
    excerpt:
      "Fitting a 4-parameter logistic curve to dose-response data shouldn't require a statistics degree. With Resonantia's agentic data processing, you describe what you need in plain English and get publication-ready IC50 curves in seconds...",
    content: `Fitting a 4-parameter logistic curve to dose-response data should not require a statistics degree. Yet in most labs, the analysis pipeline looks something like this: export raw plate-reader data, open GraphPad Prism, paste values, configure the model, run the fit, export the figure, paste it into a slide deck, then repeat for every plate. If a colleague asks "what was the IC50 for compound X?" two months later, you are digging through folders named "final_v3_REAL".

With Resonantia's agentic data processing, you describe what you need in plain English: "Fit 4PL curves for all compounds on plate HTS-042, flag any with Hill slope outside 0.5 to 2, and generate a summary table with IC50 and R-squared." Seconds later you have publication-ready figures, a structured results table, and a persistent record linked to the original plate map and raw instrument file.

Under the hood, the agent selects the right statistical model, applies sensible constraints, handles outlier detection, and formats the output according to your lab's style guide. If the fit looks unusual — an incomplete curve, ambiguous asymptote, or biphasic behaviour — the system surfaces a clear explanation and suggests next steps rather than silently returning a questionable number.

Because every analysis is recorded as a reproducible pipeline, any team member can re-run it months later with a single click. No more archaeology, no more "which version of the script did we use?" Just transparent, traceable science from raw data to decision.`,
  },
  {
    slug: "open-instrument-integration",
    title: "Building an Open Platform for Lab Instrument Integration",
    author: "Teodor Popescu",
    date: "April 2, 2026",
    tags: ["Instruments", "Integration"],
    excerpt:
      "The biggest pain point in lab informatics isn't the software — it's the data formats. Every instrument vendor has their own proprietary export format. We're building a universal ingestion layer...",
    content: `The biggest pain point in lab informatics is not the software — it is the data formats. Every instrument vendor has their own proprietary export format. Your plate reader exports XML. Your mass spec exports a binary blob. Your microscope writes OME-TIFF with custom metadata extensions. Your liquid handler logs CSV with vendor-specific headers. Getting all of these into one coherent picture of an experiment is an exercise in frustration that consumes far too much of a scientist's time.

We are building a universal ingestion layer inside Resonantia. The principle is simple: point the system at a file or a folder, and it figures out what it is. We maintain a growing library of parsers for common instruments — BMG, Tecan, PerkinElmer, Molecular Devices, Yokogawa, Thermo Fisher, and more — and an extensible plugin architecture so that any lab can add support for their own niche hardware.

Once data is ingested, it is normalised into a common schema and linked to the experiment that produced it. That means you can query across instruments: "show me all IC50 values for compound ABC-123 from both the EnVision and the Synergy reads" without ever thinking about file formats. The data just flows.

The long-term vision is a community-maintained registry of instrument adapters, where a parser written by one lab automatically benefits every other lab using the same hardware. Open formats, open parsers, open science. That is the infrastructure the field has needed for a decade, and we intend to build it.`,
  },
  {
    slug: "microscopy-data-at-scale",
    title: "Microscopy Data at Scale: Browsing Terabytes Without the Pain",
    author: "Teodor Popescu",
    date: "March 28, 2026",
    tags: ["Microscopy", "Data Management"],
    excerpt:
      "High-content screening generates terabytes of imaging data per experiment. Finding the right FOV of the right well from the right plate shouldn't require memorizing file paths. Resonantia's microscopy browser lets you navigate by plate, well, channel, and field of view...",
    content: `High-content screening generates terabytes of imaging data per experiment. A single 384-well plate imaged across five channels at nine fields of view produces over 17,000 individual images. Scale that to a weekly screening campaign and you are managing millions of files. Finding the right field of view of the right well from the right plate should not require memorising file paths or writing custom scripts — but in most labs, it does.

Resonantia's microscopy browser changes the paradigm. You navigate by biology, not by file system: select a plate, click a well, choose a channel, step through fields of view. Overlays, brightness and contrast adjustments, and channel composites are available instantly. The viewer streams tiled pyramidal images so that even multi-gigabyte acquisitions load in milliseconds, regardless of your network speed.

Beyond browsing, the system integrates with your analysis pipeline. Annotate regions of interest, flag wells for re-imaging, or launch a CellProfiler pipeline directly from the viewer. Every annotation is stored with full provenance — who marked it, when, and in what context — so that downstream machine-learning models can train on curated, traceable ground truth.

We built this because we lived the alternative. At Dewpoint, finding the right image to show in a project meeting could take longer than the meeting itself. The data was there; the access layer was not. Resonantia makes imaging data a first-class citizen in the lab informatics stack, not an afterthought buried in a network drive.`,
  },
];
