# Resonantia Lab — Testing Scenarios

Testing scenarios based on three real user personas from the drug discovery industry.

---

## Persona 1: Beatriz Ferreira Gomes, PhD

**Role:** Product Manager, Drug Discovery at Dewpoint Therapeutics
**Background:** Bridges AI/ML and life sciences. Evaluates tools from a UX/workflow perspective. Translates complex research into purposeful software.
**What she cares about:** Intuitive onboarding, clear value proposition, whether scientists would actually adopt the tool without training.

### B1: First Impressions (Marketing Site)

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Open http://localhost:3000 | Landing page loads with hero "The New Way Labs Work" | |
| 2 | Read the subtitle | Value proposition is clear within 5 seconds — mentions plate mapping, dose-response, sample tracking | |
| 3 | Click "About" in navbar | Navigates to /about with "Built by scientists, for scientists" | |
| 4 | Click "Pricing" in navbar | Navigates to /pricing with three tiers (Free, Pro, Enterprise) | |
| 5 | Click "Blog" in navbar | Navigates to /blog with 5 articles | |
| 6 | Click a blog article | Opens full article with author, date, tags, content | |
| 7 | Navigate back to home, click "Read our vision" | Navigates to /about | |
| 8 | Click "Try Resonantia Lab" | Redirects to Clerk sign-in if not authenticated | |

### B2: Lab Onboarding

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Sign in and land on /lab | Chat interface with greeting: "Hi there," and specific subtitle about capabilities | |
| 2 | Hover over each sidebar icon | Tooltips appear: Chat, Plates, Microscopy, Samples, Processing | |
| 3 | Click "Plates" sidebar icon | Navigates to /lab/plates — Plate Map Designer | |
| 4 | Click "Microscopy" sidebar icon | Navigates to /lab/microscopy — Microscopy Browser | |
| 5 | Click "Samples" sidebar icon | Navigates to /lab/samples — Sample Tracker | |
| 6 | Click "Processing" sidebar icon | Navigates to /lab/processing — Data Processing | |
| 7 | Click "Chat" sidebar icon | Returns to /lab — Chat interface | |

### B3: Feature Discovery via Chat

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Click "+ Skill" button | Dropdown appears with 6 skills (Plate Mapping, Dose-Response Analysis, Sample Lookup, Plate Normalization, Image Analysis, Protocol Design) | |
| 2 | Click "Plate Mapping" skill | Inserts "Design a plate map: " into the text input | |
| 3 | Click "Resource" button | Dropdown with Upload Data File, Plate Maps, Sample Inventory, Microscopy Images, Processing Results | |
| 4 | Click "Plate Maps" in resource dropdown | Navigates to /lab/plates | |
| 5 | Navigate back to /lab, click "Plan mode" | Amber banner appears: "Plan mode active — I'll create a detailed plan before executing" | |
| 6 | Click "Plan mode" again | Banner disappears | |
| 7 | Click the gear icon (Settings) | Modal opens with Model selector, Temperature slider, Max Tokens, System Prompt | |
| 8 | Close the settings modal | Modal closes cleanly | |
| 9 | Click skill bar buttons (Plate Mapping, Data Analysis, etc.) | Each inserts a relevant prompt into the chat input | |

---

## Persona 2: Sangram Parelkar, PhD

**Role:** Associate Director, Head of Cellular Lead Profiling at Takeda
**Background:** 20+ years in HTS, assay development, CRISPR screens. Manages 900K compound libraries. Co-founded UMass screening facility.
**What he cares about:** 384-well plate support, dose-response curve quality, worklist format correctness for Echo/Hamilton, scale.

### S1: Plate Mapping at Scale

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Navigate to /lab/plates | Page loads with Plate Map Designer header | |
| 2 | Check for 384-well toggle | "96" and "384" toggle buttons visible in top-right | |
| 3 | Click "384" toggle | Interface switches to 384-well plate format | |
| 4 | Click "+ New Plate Map" | Modal opens with name input field | |
| 5 | Type "Kinase Screen Round 3" and submit | New plate map appears in the sidebar list | |
| 6 | Click the new plate map | Detail view loads with source-destination plates and mapping controls | |
| 7 | Verify mapping modes available | Cherry Pick, Serial Dilution, Replicate, Randomize tabs visible | |
| 8 | Select "Serial Dilution" mode | Dilution parameters appear (start concentration, dilution factor, points, direction) | |

### S2: Worklist Generation

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | With a plate map open, scroll to Worklist Generator | Section visible with export options | |
| 2 | Verify Echo CSV option | "Echo CSV" button present — this is critical for acoustic dispensing | |
| 3 | Verify Hamilton GWL option | "Hamilton GWL" button present | |
| 4 | Verify Opentrons Python option | "Opentrons Python" button present | |
| 5 | Check for generic exports | "Export CSV" and "Export JSON" buttons present | |
| 6 | Click "Echo CSV" with mappings | Downloads or previews an Echo-compatible CSV file | |

### S3: Dose-Response Analysis

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Navigate to /lab/processing | Three analysis cards visible | |
| 2 | Click "Dose-Response Curve Fitting" | Card expands with description and "Run Analysis" button | |
| 3 | Verify terminology | Description mentions 4PL, IC50/EC50, Hill coefficients, confidence intervals | |
| 4 | Click "Run Analysis" | Simulated analysis runs (loading → complete) | |
| 5 | Check recent runs table | Shows runs with status (Completed, Running, Failed, Queued) | |
| 6 | Verify a completed run entry | Shows experiment name, plate, timestamp, and duration | |

### S4: Sample Tracking for Large Libraries

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Navigate to /lab/samples | Dashboard cards visible: Total, Expiring, Low Stock, Added This Week | |
| 2 | Check type filter dropdown | Options include: Antibody, Cell Line, Compound, Media, Buffer, Enzyme, Primer, Plasmid, Reagent | |
| 3 | Select "Compound" filter | Table filters to show only compounds | |
| 4 | Search for "Staurosporine" | Search results show Staurosporine entry | |
| 5 | Check table columns | Name, Barcode, Type, Location, Temp, Lot #, Expiry, Qty, Status all present | |
| 6 | Click "+ Add Sample" | Slide-over panel opens with full form | |
| 7 | Fill in sample details | Fields: Name, Barcode, Type, Location, Storage Temp, Lot Number, Expiry, Quantity+Unit | |
| 8 | Save the sample | New sample appears in the table | |

### S5: Chat Agent — HTS Query

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Navigate to /lab | Chat interface loads | |
| 2 | Type "What is the Z-prime factor for my latest screen?" | Text appears in input | |
| 3 | Press Enter or click Send | Message appears in chat thread, assistant responds | |
| 4 | Verify response | Response acknowledges the HTS query (demo mode shows placeholder response) | |
| 5 | Type "Design an 8-point dose-response with 3-fold dilution from 10 uM" | Text appears in input | |
| 6 | Send the message | Response in chat thread | |

---

## Persona 3: John Manteiga, PhD

**Role:** Principal Scientist at Dewpoint Therapeutics
**Background:** Hands-on bench scientist in cell biology, HTS, target discovery/validation. 5+ years drug discovery. Pragmatic problem solver.
**What he cares about:** Quick experiment setup, reagent tracking, microscopy data access, file uploads.

### J1: Quick Plate Map Setup

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Navigate to /lab/plates | Plate Map Designer loads | |
| 2 | Click first plate map ("HTS Screen — Round 1") | Detail view loads with source plate visualization | |
| 3 | Verify well color coding | Legend shows: Empty (gray), Sample (blue), Control+ (green), Control- (red), Compound (purple) | |
| 4 | Select "Cherry Pick" mode | Cherry pick interface active | |
| 5 | Click wells on source plate | Wells highlight with amber border (selected) | |
| 6 | Click wells on destination plate | Destination wells highlight | |
| 7 | Click "Apply" | Mappings appear in the table below | |
| 8 | Check mapping table | Columns: Source Well → Dest Well → Compound → Concentration → Volume | |

### J2: Reagent Tracking

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Navigate to /lab/samples | Dashboard loads with summary cards | |
| 2 | Check "Expiring Soon" card | Shows count of items expiring within 30 days (should be 3) | |
| 3 | Check "Low Stock" card | Shows count of low-stock items (should be 3) | |
| 4 | Click "Status" dropdown, select "Expiring" | Table filters to show only expiring items | |
| 5 | Click "+ Add Sample" | Form opens | |
| 6 | Fill: Name="Anti-EGFR rabbit pAb", Type=Antibody, Location="Freezer-A/Shelf-1/Box-2", Temp=-20C | Fields populated | |
| 7 | Save | New antibody appears in the table | |
| 8 | Click "Scanner" button | Barcode scanner UI opens | |

### J3: Microscopy Data Access

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Navigate to /lab/microscopy | Microscopy Browser loads with viewer | |
| 2 | Verify plate dropdown | Shows available plates (Drug Screen Plate A, etc.) | |
| 3 | Click well B3 in the well grid | Viewer updates to show B3 data, info overlay shows "B3 · FOV 1" | |
| 4 | Uncheck DAPI channel | Blue (nuclear) signal disappears from composite | |
| 5 | Check mCherry channel | Red signal appears in composite | |
| 6 | Click FOV 4 in the FOV grid | Viewer shows FOV 4, thumbnail strip highlights FOV 4 | |
| 7 | Click a thumbnail in the strip | Viewer updates to that FOV | |
| 8 | Check scale bar | Shows "100 um" (or similar) | |
| 9 | Use zoom controls (+/-) | Image zooms in/out, zoom percentage updates | |

### J4: File Upload and Download

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Navigate to /lab | Chat interface | |
| 2 | Click paperclip (attach) button | File chooser dialog opens | |
| 3 | Select a CSV file | File appears as attachment chip with name and size | |
| 4 | Type "Analyze this plate data" | Text appears in input alongside attachment | |
| 5 | Click Send | Message sent with attachment, uploads file to backend | |
| 6 | Verify message in thread | Shows file as clickable download link with filename and size | |
| 7 | Click the download link | File downloads | |
| 8 | Attach multiple files | Multiple chips appear, all sent with the message | |

### J5: Quick Skills

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | On /lab, click "Plate Mapping" in skill bar | Input populates with "Help me design a plate map for " | |
| 2 | Click "Sample Tracking" in skill bar | Input changes to "Look up information about sample " | |
| 3 | Click "+ Skill", then "Dose-Response Analysis" | Input changes to "Analyze dose-response data: " | |
| 4 | Type additional context after the prompt | Text appends to the inserted prompt | |
| 5 | Send the message | Full message (prompt + context) sent to chat | |

---

## Cross-Cutting Scenarios

### X1: Authentication Flow

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Open http://localhost:3000 while signed out | Marketing site loads without auth requirement | |
| 2 | Click "About", "Pricing", "Blog" | All pages accessible without sign-in | |
| 3 | Click "Try Resonantia Lab" or navigate to /lab | Redirected to Clerk sign-in page | |
| 4 | Sign in with Google | Redirected to /lab after authentication | |
| 5 | Navigate between /lab/* pages | All pages accessible without re-authentication | |
| 6 | Visit /invite | Invite page loads (requires auth) | |

### X2: Invite Flow

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | Click invite icon in sidebar (UserPlus) | Navigates to /invite | |
| 2 | Enter a valid email address | Email validated, button enabled | |
| 3 | Click "Send Invitation" | Success message shown, Clerk sends invitation email | |
| 4 | Check recipient's inbox | Branded invitation email received | |
| 5 | Recipient clicks "Accept Invitation" | Redirected to sign-up flow, then to /lab | |

### X3: Responsive Design

| Step | Action | Expected Result | Pass/Fail |
|------|--------|-----------------|-----------|
| 1 | View marketing site on mobile (375px width) | Layout adapts, hamburger menu appears | |
| 2 | View /lab on tablet (768px width) | Sidebar collapses, task panel adjustable | |
| 3 | View /lab/plates on desktop (1440px) | Full three-panel layout with room for plate visualization | |

---

## How to Run These Tests

### Manual Testing
1. Start the frontend: `cd frontend && npm run dev`
2. Start the backend: `cd backend && uv run uvicorn resonantia.main:app --reload`
3. Open http://localhost:3000 in your browser
4. Walk through each scenario table, marking Pass/Fail
5. Note any unexpected behavior in the comments column

### Automated Testing
- **Backend unit tests:** `cd backend && uv run pytest tests/ -v` (55 tests)
- **Frontend unit tests:** `cd frontend && npx vitest run` (46 tests)
- **Build verification:** `cd frontend && npm run build`

### Playwright Testing
For automated E2E tests using the scenarios above:
```bash
# Ensure the app is running, then use Playwright MCP
# Navigate to each URL and verify elements exist
npx playwright test  # (when E2E test suite is created)
```
