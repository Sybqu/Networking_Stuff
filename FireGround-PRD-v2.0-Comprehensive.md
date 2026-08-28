# FireGround — Product Requirements Document

**Product:** Offline Ground Verification & Response Triage for Forest Fire Alerts
**Version:** 2.0 (Comprehensive — Core Spec + Operational Hardening)
**Context:** MAHE Internal Smart India Hackathon 2026
**Team:** 6 students
**Status:** Proposed pivot from ResQNet

---

# 0. Executive Summary

**FireGround is an offline-first field verification and response-triage system for forest fire operations.**

India already has a strong satellite-based forest fire detection infrastructure. Forest Survey of India (FSI) receives MODIS and SNPP-VIIRS thermal detections, processes them, and disseminates near-real-time fire alerts to State Forest Departments and registered users. FSI itself notes an important limitation: satellite detections are thermal anomalies, the number of detections does not necessarily equal the number of real fire incidents on the ground, and the same physical fire can be detected repeatedly on successive satellite passes.

The missing operational layer is **what happens after an alert reaches the field**.

A Parliamentary Committee report published on **7 August 2026** identified poor network connectivity in forest and hill terrain, weak integration with frontline firefighting response, and the absence of a robust ground feedback/verification loop as problems affecting Uttarakhand's fire-alert application's ground-level utility. It recommended improved GIS monitoring, field-level verification and stronger integration with response teams.

FireGround targets that gap.

A satellite detection, a photograph from a beat guard, another observation from a fire watcher and a second satellite pass should not automatically appear as four separate fires.

FireGround resolves noisy observations into **physical fire incidents**, estimates how strongly each incident has been corroborated, and produces an explainable ranked queue showing:

> **Which fire needs the first available response team?**

```text
SATELLITE ALERTS
       +
FIELD OBSERVATIONS
       ↓
OFFLINE STRUCTURED EVIDENCE
       ↓
EVENT RESOLUTION
"Which observations describe the same fire?"
       ↓
CROSS-SOURCE CORROBORATION
"How much evidence supports this incident?"
       ↓
FIRE PRIORITY ENGINE
"Which incident needs attention first?"
       ↓
RANGE / DIVISION OFFICER
human verifies → dispatches → resolves
```

FireGround **does not detect forest fires from scratch**, replace FSI, predict fire spread, automatically dispatch firefighters, or tell civilians that an area is safe.

It sits between **detection and response allocation**.

**This version (2.0)** folds in operational hardening across ten areas that a real Forest Department pilot or a sharp judge panel would immediately probe: language/literacy design, multi-device conflict resolution, device identity lifecycle, clock-drift handling, a false-positive taxonomy, governance/data-ownership framing, field onboarding, power constraints, scale-out posture, and a concrete QA strategy for the deterministic core. These are integrated into the relevant sections below, not bolted on as an appendix — the intent is that reading this document top to bottom gives a complete and honest picture of the project as it should actually be built.

---

# 1. Product Definition

## 1.1 One-line pitch

> **Satellite systems tell the Forest Department where a possible fire is. FireGround determines which observations describe the same real fire, collects ground verification even where networks fail, and tells officers which incident deserves the first response team.**

## 1.2 The problem

India's forest-fire monitoring infrastructure already performs large-scale satellite detection and alert dissemination. FSI uses remote sensing for near-real-time fire monitoring and maintains the Van Agni forest-fire information system.

The remaining field problem:

```text
                 CURRENT PIPELINE

SATELLITE
    ↓
THERMAL DETECTION
    ↓
FSI ALERT
    ↓
STATE FOREST DEPARTMENT
    ↓
──────────────────────────────────
        THE MESSY PART
──────────────────────────────────
    ↓
Who verifies it?
Is there network coverage?
Was this already reported?
Is this the same fire as another alert?
Is this an active fire or controlled activity?
Is it growing?
Are settlements threatened?
Which incident gets the first crew?
    ↓
FIELD RESPONSE
```

FSI explicitly states that the number of satellite detections can differ from the number of actual ground fire incidents and that the same fire can produce detections on successive days because of satellite repeat coverage.

That makes **alert-to-incident resolution** an actual operational data problem.

---

# 2. Product Thesis

FireGround is **not an AI forest-fire detector**.

> **The scarce resource is not another fire-detection model. It is reliable, structured, ground-verified information that lets a forest officer turn noisy alerts into a response queue under poor connectivity.**

The system optimises for five things:

1. **Offline evidence capture**
2. **Opportunistic synchronization**
3. **Observation-to-incident resolution**
4. **Independent and cross-source corroboration**
5. **Explainable response prioritization**

This preserves the strongest technical concept from ResQNet: resolve transmissions and observations into real-world events before ranking them, rather than treating every report as a new incident.

---

# 3. Deployment Owner and Users

## 3.1 Primary deployment owner

**State Forest Department.** Pilot deployment should be scoped at:

```text
ONE FOREST DIVISION
        ↓
2–4 RANGES
        ↓
BEATS / PATROL TEAMS
```

FSI remains the upstream satellite-alert provider. The State Forest Department owns field verification, incident confirmation, response prioritization, crew deployment, and incident closure. FireGround is not intended initially as a nationwide consumer application.

## 3.2 Personas

| Persona | Situation | Need | FireGround role |
|---|---|---|---|
| **Fire Watcher / Patrol Staff** | Deep inside forest, weak/no signal | Record what is visible quickly | Capture observations |
| **Beat Guard** | Moving across beat, may encounter alerts or fires | Verify alerts and report conditions | Reporter + verifier |
| **Patrol Vehicle / Mobile Team** | Moves between disconnected field staff | Carry accumulated observations | Opportunistic gateway |
| **Range Officer** | Several possible incidents, limited teams | Decide where to respond first | Primary decision user |
| **Division Control Room** | Multiple ranges | Maintain operational picture; resolve conflicts | Dashboard user + arbiter |
| **System Administrator** | Before fire season | Provision devices/maps/configuration; manage device registry | Configuration |

**Realism note:** fire watchers and beat guards are frequently regional-language speakers with variable literacy, working under low light and time pressure. The interface design in §11 reflects this — it is not designed for a hackathon judge's reading comfort, it is designed for a guard's ten-second decision window.

## 3.3 Core job to be done

> **When several possible forest fires are being reported and network coverage is unreliable, help me determine which observations describe real distinct fires, what evidence supports each one, and where I should send the next available team.**

---

# 4. Current Workflow vs FireGround

## 4.1 Current simplified workflow

```text
FSI ALERT → SMS/portal/departmental channel → officer/guard receives alert
   → someone travels toward location → phone call/message/manual feedback
   → control room manually reconciles information → response decision
```

The 2026 Parliamentary Committee report specifically identified poor mobile connectivity, weak integration with frontline response and insufficient ground feedback/verification as problems in Uttarakhand's implementation.

## 4.2 FireGround workflow

```text
FSI / SATELLITE ALERT
        ↓
cached onto relevant range devices
        ↓
GUARD ENTERS LOW-CONNECTIVITY AREA → opens cached alert
        ↓
captures photograph + structured ground observation
        ↓
ON DEVICE: GPS, timestamp, image quality, visual fingerprint, embedding, signature
        ↓
LOCAL STORE
        ↓
encounters another FireGround device → OFFLINE SYNCHRONIZATION
        ↓
observation stores reconcile
        ↓
EVENT RESOLUTION ENGINE → 6 observations → 2 physical fire incidents
        ↓
PRIORITY ENGINE → #1 FIRE A — priority 87  |  #2 FIRE B — priority 54
        ↓
RANGE OFFICER REVIEWS → VERIFY / REJECT / DISPATCH / RESOLVE
```

---

# 5. Scope

## 5.1 MVP

- Android field application
- Cached satellite/fire-alert markers
- Fully offline observation capture (GPS, photos, structured status)
- On-device visual preprocessing
- Signed device identity (with revocation list — §17.3)
- SQLite local store
- Offline map
- Nearby Connections synchronization between phones
- Store-and-forward synchronization
- Observation deduplication, incident association, independent-device counting
- Satellite + field evidence fusion
- Explainable priority score
- Range-officer incident queue with conflict-state handling (§16)
- Verification states
- Local simulator
- Completely internet-free live demo
- Icon-first, multilingual primary observation flow (§11)

## 5.2 Explicit non-goals

Automatic wildfire detection from continuous camera feeds; drone surveillance; live satellite imagery processing; a proprietary satellite fire-detection algorithm; autonomous dispatch; autonomous evacuation advice; fire-spread simulation; weather forecasting; controlled-burn classification from photographs alone; exact fire-perimeter estimation; citizen social network; public chat; nationwide deployment; iOS; custom radio hardware; LoRa; full BLE epidemic flooding; complex routing across hundreds of phones; facial recognition; responder tracking; automated claims that an area is safe; real-time (online) device revocation; cross-division backend federation; formal legal compliance certification.

These exclusions are intentional and stated explicitly to judges (§75–80).

---

# 6. The Key Pivot from ResQNet

ResQNet had an elaborate epidemic mesh because the assumed network consisted of arbitrary disaster victims and bystanders. FireGround has a **known, provisioned operational population**:

```text
fire watcher ↕ beat guard ↕ patrol team ↕ range officer ↕ division
```

Therefore the transport problem gets dramatically simpler.

**Keep:** offline-first Android architecture; SQLite; PMTiles/offline mapping; Nearby Connections abstraction; store-and-forward; cryptographic report identity; image fingerprints; event resolution; independent-device evidence; scoring engine; verification states; simulator; ranked operational dashboard.

**Remove or downgrade:** random TTL; origin-location privacy tricks; dense-network flood suppression; fanout optimisation; anonymous-civilian Sybil defence; hundreds-of-node epidemic flooding; complex courier budgets; class-tiered radio scheduling; message-level mesh novelty.

**New philosophy:**

> **P2P is transportation, not the project.**

If Nearby behaves badly, the product remains useful through `offline capture → later internet upload`. Nearby simply improves the time at which evidence escapes disconnected areas.

---

# 7. High-Level Architecture

```text
┌────────────────────── FIELD ANDROID DEVICE ──────────────────────┐
│ ALERT CACHE — cached FSI-like hotspots · beat/range map · tiles  │
│       ↓                                                          │
│ CAPTURE — alert verification · new fire observation · photo · GPS│
│       ↓                                                          │
│ STRUCTURE — smoke/flame state · spread observation · exposure    │
│       ↓                                                          │
│ ON-DEVICE VISION — quality check · pHash · embedding · CV assist │
│       ↓                                                          │
│ SIGN — Ed25519 device key → signed observation                   │
│       ↓                                                          │
│ STORE — SQLite: alerts · observations · incidents · sync state   │
│       ↓                                                          │
│ LOCAL EVENT ENGINE — dedup · incident association · priority     │
│       ↓                                                          │
│ OFFLINE MAP — hotspots · field reports · resolved incidents      │
│       ↓                                                          │
│ NEARBY SYNC — device encounter, duty-cycled discovery (§21.3)    │
│   exchange IDs → missing records → status → optional thumbnails  │
└─────────────────────────┬────────────────────────────────────────┘
                          │ connectivity eventually exists
                          ↓
┌──────────────────────── BACKEND ─────────────────────────────────┐
│ ALERT INGEST → SIGNATURE VALIDATION (checks revocation list)     │
│       ↓                                                          │
│ DIVISION-WIDE EVENT RESOLUTION → FIRE PRIORITY ENGINE            │
│       ↓                                                          │
│ PostgreSQL + PostGIS → DASHBOARD                                 │
│   map · ranked incidents · timeline · evidence · verification    │
│   · conflict-reconciliation queue · device registry              │
└──────────────────────────────────────────────────────────────────┘
```

---

# 8. Architectural Invariant

**The cloud must not be necessary to capture or preserve a field observation.**

For the SIH demo, **event resolution and priority ranking must also be executable locally on the Range Officer device.**

```text
NO INTERNET → capture works, map works, vision works, sync works,
              event fusion works, priority works, officer review works
```

The backend provides a larger divisional picture, persistence and integration. It is not the brain required to make the demo work.

---

# 9. Input Model

## 9.1 Satellite Detection

```json
{
  "source": "SATELLITE",
  "alert_id": "...",
  "detected_at": "...",
  "latitude": 0.0,
  "longitude": 0.0,
  "sensor": "...",
  "provider": "FSI_LIKE"
}
```

The hackathon implementation uses a **seeded FSI-like alert dataset**, not a fake claim of official API integration. Production integration would require authorization/data-feed agreements appropriate to the State Forest Department.

## 9.2 Field Observation

```text
observation_id
origin_device_id
observer_role

observed_at              (device clock)
observed_at_gps          (GPS-derived time, when available — see §17.4)
time_uncertain           (bool — set when device/GPS time disagree beyond threshold)

latitude / longitude / gps_accuracy

linked_alert_id[]        optional

visual_state    → SMOKE_VISIBLE | FLAME_VISIBLE | BOTH | NO_FIRE_VISIBLE | UNCERTAIN
spread_state    → NO_CHANGE_KNOWN | SPREADING | RAPID_SPREAD | UNKNOWN
exposure_flags  → NEAR_SETTLEMENT | NEAR_ROAD | NEAR_INFRASTRUCTURE | ECOLOGICALLY_SENSITIVE | NONE_KNOWN
ground_status   → ACTIVE_FIRE | POSSIBLE_FIRE | CONTROLLED_ACTIVITY | FALSE_ALERT | UNCERTAIN

photo_hash / image_embedding / image_quality
note            (optional, ≤160 chars — never required to submit)
signature       (Ed25519, device key)
```

## 9.3 Officer Action

```text
VERIFIED_ACTIVE | REJECTED | CONTROLLED_ACTIVITY | DISPATCHED | MONITOR | CONTAINED | RESOLVED
```

Officer actions are never generated automatically. Officer actions are also the class of record subject to conflict detection (§16).

---

# 10. Language & Literacy Design

*(Hardening addition — governs how §11's UX is actually built.)*

The v1.0 mockups were English-text-first. That does not hold up against the actual field persona: a fire watcher deep in forest terrain, under time pressure, possibly low-literacy in English. An interface requiring reading of English sentences to submit a report undermines the "photo-to-report in under 10 seconds" target and the product's own credibility.

| ID | Requirement | Pri |
|---|---|---|
| L-1 | Primary observation flow uses icon-first buttons with large tap targets; text is a supporting label, never the primary signal | M |
| L-2 | App ships with at least Kannada, Hindi, and English string sets for the pilot state's language(s); selected at first run, stored per device | M |
| L-3 | No flow requires typed free text to complete a submission — the optional note stays optional | M |
| L-4 | Icons pilot-tested with 3–5 people unfamiliar with the app before the demo, not just designed internally | S |
| L-5 | Officer dashboard (used by more literate range staff) may remain English-only for MVP | C |

Icons must not imply false certainty — e.g. a flame icon at capture time should not visually read as a "confirmed fire" badge before officer verification. This is the same discipline as the corroboration-language rule in §17.2 ("4 distinct field devices," never "4 witnesses").

---

# 11. Observation UX

A guard should not have to write a paragraph, and — per §10 — should not have to read one either.

```text
OPEN ALERT
    ↓
TAKE PHOTO
    ↓
WHAT DO YOU SEE?     [ 🔥 SMOKE ]  [ 🔥 FLAMES ]  [ 🔥 BOTH ]  [ ✕ NOTHING ]  [ ? UNSURE ]
    ↓
IS IT SPREADING?     [ ⚡ RAPIDLY ]  [ ↗ YES ]  [ ? NOT SURE ]
    ↓
ANY IMMEDIATE EXPOSURE?   [ 🏘 SETTLEMENT ]  [ 🛣 ROAD ]  [ 🏗 INFRASTRUCTURE ]  [ — NONE KNOWN ]
    ↓
SUBMIT
```

Target: **photo-to-report in under 10 seconds. Typing is optional.**

---

# 12. On-Device Vision

The AI is **evidence assistance, not the decision-maker.**

## 12.1 Image quality gate

Detects severe blur, extreme darkness, overexposure. Bad image: *"Image may not be usable as evidence. Retake?"* — the user may override it.

## 12.2 Visual fingerprint (pHash)

Purpose: the same photograph forwarded twice must not count as two independent visual observations.

## 12.3 Visual embedding

Generated with a lightweight offline mobile encoder. Purpose: similarity search, support event association, distinguish unrelated scenes, detect reused imagery, compare multiple photographs. **Embedding similarity must never alone merge incidents.**

## 12.4 Optional visual fire-assist model

Outputs `SMOKE_LIKE | FLAME_LIKE | NO_CLEAR_FIRE_EVIDENCE | UNCERTAIN`, presented as **"Visual evidence assist,"** never as **"AI says this is a wildfire."** The field worker's structured observation remains the primary ground label.

## 12.5 Model fallback

If confidence is low, manual structured observation remains available. There is no failure state where the guard cannot submit because the model is confused.

---

# 13. The Core Technical Contribution — Fire Event Resolution

The system must answer: **How many actual fire incidents do these observations represent?**

## 13.1 Level 0 — Transport Duplicate

Same serialized observation arrives through multiple devices → one observation, `times_received++`. Never affects corroboration.

## 13.2 Level 1 — Duplicate Evidence

Different submissions may carry the same photograph or copied evidence (signals: pHash, embedding, timestamp, metadata).

```text
Phone A captures photo → Phone B receives & re-submits it → Phone C forwards B's submission
        ↓
3 packets, 2 submissions, 1 originating visual observation
```

It must **not** become three witnesses.

## 13.3 Level 2 — Physical Fire Association

Distinct observations may describe the same physical fire. No single rule is sufficient — FireGround computes an association score:

```text
Assoc(a,E) = ws·Spatial(a,E) + wt·Temporal(a,E) + wh·HotspotAgreement(a,E) + wv·VisualSimilarity(a,E)
```

Weights are **configuration values, not trained scientific parameters.** Hackathon thresholds are deliberately treated as demo defaults — no claim of operational scientific validation.

**Why pHash alone is not enough:** two guards can photograph the same fire from opposite hillsides and get visually unrelated images. pHash answers "is this approximately the same photograph?", not "is this the same physical fire?" Physical incident association requires spatial and temporal context, which is why `Temporal(a,E)` depends on trustworthy timestamps — see §17.4 for how that trust is actually established rather than assumed.

## 13.4 Level 3 — Incident

```text
8 transmitted packets → 6 unique observations → 4 distinct originating devices
        → 2 satellite detections → 1 physical fire incident
```

The dashboard must expose all five numbers. Never show only "8 reports" — that invites officers to mistake message volume for evidence volume.

---

# 14. Incident Data Structure

```text
incident_id
status
first_seen_at / last_seen_at
centroid / spatial_extent_proxy
n_packets / n_observations / n_distinct_devices / n_satellite_alerts
visual_states[] / spread_states[] / exposure_flags[]
linked_alert_ids[] / linked_observation_ids[]
corroboration_score / priority_score
verification_state
conflict_state           (NONE | CONFLICTED — see §16)
assigned_team             optional
created_at / updated_at
```

---

# 15. Incident State Machine

```text
satellite alert ──► UNVERIFIED
                        │ field evidence
                        ▼
                  FIELD_REPORTED
                        │ sufficient independent supporting evidence
                        ▼
                  CORROBORATED
                        │ officer decision
          ┌─────────────┼──────────────┐
          ▼              ▼              ▼
   VERIFIED FIRE   FALSE ALERT   CONTROLLED ACTIVITY
          │
          ▼
     DISPATCHED → CONTAINED → RESOLVED
```

**CORROBORATED is not equivalent to VERIFIED.** Only authorized personnel can produce a human verification state.

---

# 16. Multi-Device Conflict Resolution

*(Hardening addition — the state machine above describes valid transitions; this section governs what happens when two valid transitions arrive from different disconnected officers with no shared prior state.)*

## 16.1 The problem

Two officers on two disconnected devices can both act on the same incident before syncing — e.g. Officer A marks `DISPATCHED` while Officer B marks `FALSE_ALERT`. This is not a hypothetical edge case in an offline-first system; it will happen during any real multi-range deployment.

## 16.2 Resolution rule

FireGround does **not** attempt automatic conflict resolution on verification-grade actions. Officer actions are authority-scoped, not timestamp-scoped — **last-write-wins is explicitly rejected**, because a stale device syncing hours late must not silently overwrite a more recent decision.

```text
CONFLICT DETECTED (two divergent officer actions on same incident_id)
        ↓
BOTH ACTIONS PRESERVED IN AUDIT LOG
        ↓
INCIDENT ENTERS "CONFLICTED — NEEDS RECONCILIATION" STATE
        ↓
Highest-authority role present resolves (Division Control Room > Range Officer)
        ↓
Resolution logged with reason
```

Non-authoritative data (field observations, photos, GPS points) merge freely with no conflict concept — only the seven officer-action states trigger this handling. Each device carries a logical (Lamport) clock alongside wall-clock time to correctly detect divergence even under clock drift (§17.4), not to auto-resolve it.

## 16.3 Requirements

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| CR-1 | Divergent officer actions on one incident detected at sync, not silently overwritten | M | Golden test: two conflicting actions injected, both survive in audit log |
| CR-2 | Conflicted incidents surface distinctly in the queue | M | Visible "Needs reconciliation" badge |
| CR-3 | Resolution requires explicit officer action, logged with old/new state + reason | M | Audit entry present |

---

# 17. Cross-Source Corroboration & Distinct Observer Evidence

## 17.1 Cross-source corroboration

Evidence is more useful when independent sources agree:

```text
SATELLITE DETECTION + Guard A: visible smoke + Guard B: visible flames → stronger evidence
```

than: `Guard A submits same fire three times`.

## 17.2 Distinct observer evidence

For MVP, **originating device key is the observer-independence proxy.** Same device × 5 reports ≠ 5 different field devices. UI wording: **"4 distinct field devices,"** never an academically stronger claim like "4 statistically independent witnesses" unless independence is actually established.

## 17.3 Device identity lifecycle: loss, theft, revocation

*(Hardening addition.)* Corroboration counting and observation signing both depend on the Ed25519 device key being trustworthy. A lost or compromised phone either silently breaks corroboration math or, worse, lets a bad actor inject fake independent-looking observations.

| ID | Requirement | Pri |
|---|---|---|
| ID-1 | Division Control Room maintains a device registry: public key → role → assigned staff | M |
| ID-2 | A registered device can be marked `REVOKED`; revoked-key signatures remain valid for historical audit but are excluded from future `n_distinct_devices` and corroboration scoring | M |
| ID-3 | Revocation list propagates via the same store-and-forward sync as other status data — eventually consistent, same as everything else in this offline system, and stated as such | M |
| ID-4 | Re-provisioning (new phone, same staff role) issues a fresh keypair; old key history remains attributed, not deleted | S |
| ID-5 | Real staff authentication (beyond device key) is out of MVP scope but flagged explicitly as **required before any real pilot**, not merely a nice-to-have | Pre-pilot |

**Explicit non-goal:** real-time revocation requiring network connectivity — this is fundamentally an offline system, so revocation is eventually-consistent by design, and the pitch should say so plainly rather than let a judge discover the gap.

## 17.4 Clock drift / untrusted timestamps

*(Hardening addition — this is what makes `Temporal(a,E)` in §13.3 and `Recency (R)` in §22/§28 actually trustworthy rather than assumed.)*

Cheap Android handsets drift, and a guard can manually change device time. If temporal scoring silently trusts the device clock, a stale photo can be miscategorized as fresh evidence and inflate priority — or a genuinely fresh report can be wrongly scored as stale.

| ID | Requirement | Pri |
|---|---|---|
| T-1 | Prefer GPS-derived time over system clock when a GPS fix is available at capture | M |
| T-2 | Store both `device_clock_time` and `gps_time`; flag disagreement beyond a threshold (e.g. 5 min) | M |
| T-3 | Observations with unresolved clock disagreement get a visible `TIME_UNCERTAIN` flag and are weighted down in temporal association — never silently trusted | M |
| T-4 | On sync handshake, devices compare clocks and log drift; no automatic correction of already-signed local timestamps | S |

---

# 18. Fire Priority Engine

Answers: **if only one response team is free, which unresolved incident deserves attention first?** It does **not** dispatch automatically.

## 18.1 Priority model v1

```text
Priority = 100 × (0.25·S + 0.20·C + 0.20·E + 0.15·G + 0.10·X + 0.10·R)
```

| Term | Meaning |
|---|---|
| **S** | Ground severity |
| **C** | Corroboration |
| **E** | Exposure |
| **G** | Apparent growth |
| **X** | Cross-source agreement |
| **R** | Recency |

Weights are **interpretable initial priors**, not claimed to be learned from historical fire-response outcomes.

## 18.2 Severity — S

| Observation | Normalized contribution |
|---|---:|
| uncertain smoke | 0.20 |
| confirmed smoke | 0.35 |
| visible flames | 0.60 |
| flames + spreading | 0.75 |
| rapid spread | 1.00 |

Configurable; a Range Officer can override the structured assessment.

## 18.3 Corroboration — C

```text
C = 1 - exp(-n_eff / 3)
```

`n_eff` = evidence from distinct trusted originating devices (post-revocation-filtering, per §17.3). Saturating on purpose: 1→2 observers matters operationally more than 21→22. The system should not reward report volume linearly.

## 18.4 Exposure — E

Settlement proximity, road proximity, known infrastructure, manually marked ecological sensitivity. For the hackathon: **preloaded static GIS layers**, not a claim of live government GIS integration.

## 18.5 Apparent Growth — G

Inferred from changes in field observations over time (new observations farther out, multiple workers reporting spread, more active locations). Must be labelled **"apparent growth from received evidence,"** never **"predicted fire spread."** FireGround contains no physical fire-spread model.

## 18.6 Cross-Source Agreement — X

```text
satellite only < field only < satellite + one field observation
  < satellite + multiple field reports < officer verified (maximum)
```

## 18.7 Recency — R

```text
R = 0.5 ^ (minutes_since_last_evidence / 60)
```

Old reports lose operational weight gradually. Age is always shown explicitly — no event silently disappears because its score decays. This term's integrity depends directly on §17.4's clock-drift handling.

## 18.8 Hard overrides

```text
FALSE_ALERT           → removed from active queue
CONTROLLED_ACTIVITY   → removed from emergency queue
RESOLVED              → archived
OFFICER_MARKED_URGENT → pinned at top, visible manual-override badge
```

Manual overrides are logged.

## 18.9 Explainability

Every incident drill-down shows a full term-by-term breakdown:

```text
PRIORITY 82
  Severity        +21
  Corroboration   +16
  Exposure        +18
  Growth          +12
  Cross-source    + 8
  Recency         + 7
                 ----
                   82
```

No opaque "AI priority: 82." A judge or officer must be able to ask "why is Fire A above Fire B?" and get a complete answer.

---

# 19. False-Positive Taxonomy

*(Hardening addition — v1.0 only offered the `CONTROLLED_ACTIVITY`/`FALSE_ALERT` override without naming the actual causes, which weakens both the CV design and the pitch's credibility.)*

```text
SATELLITE SIDE
  - agricultural stubble/crop burning near forest boundary
  - industrial heat sources at forest edge
  - repeat detection of the same fire on successive passes

FIELD-PHOTO SIDE
  - fog / mist misread as smoke
  - dust from vehicles or logging
  - sun glare / lens flare
  - wildlife or foliage motion mistaken for flame in low-confidence CV output
  - legitimate controlled burns (departmental or agricultural)
```

| ID | Requirement | Pri |
|---|---|---|
| FP-1 | Officer verification UI includes a short reason-code picker for `FALSE_ALERT`/`CONTROLLED_ACTIVITY`, drawn from this taxonomy, not free text only | S |
| FP-2 | Reason codes aggregate into a post-pilot report — a credible "how do you improve over time" answer without claiming any auto-learning in the MVP | S |
| FP-3 | Pitch explicitly states these failure modes exist and are handled by humans, never hidden | M |

---

# 20. Functional Requirements

MoSCoW: **M** = Must, **S** = Should, **C** = Could. Every Must has an acceptance condition.

## FR-1 — Alert Cache

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 1.1 | Import seeded satellite alerts | M | 100 demo alerts import correctly |
| 1.2 | Store alerts locally | M | Alerts remain after network removal + app restart |
| 1.3 | Render alert on offline map | M | Marker visible with all radios disconnected |
| 1.4 | Display detection age | M | Every alert shows timestamp/age |
| 1.5 | Open alert → verification flow | M | ≤2 taps |
| 1.6 | Production feed adapter interface | S | Alternative source can be added without changing UI |
| 1.7 | Real FSI integration | C | Not required for SIH demo |

## FR-2 — Field Observation

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 2.1 | Report existing alert | M | Submitted fully offline |
| 2.2 | Create new field-first fire report | M | Does not require satellite alert |
| 2.3 | Camera capture | M | Photo stored locally |
| 2.4 | Structured visual state (icon-first, §10–11) | M | ≤1 tap |
| 2.5 | Spread state (icon-first) | M | ≤1 tap |
| 2.6 | Exposure flags (icon-first) | M | selectable offline |
| 2.7 | GPS + reported accuracy | M | accuracy displayed |
| 2.8 | Last-known position fallback | M | visibly marked stale |
| 2.9 | Optional text note | S | ≤160 chars, never required |
| 2.10 | Compass/photo bearing | C | stored with observation |
| 2.11 | Language selection at first run (§10) | M | Kannada/Hindi/English string sets present |

## FR-3 — On-Device Vision

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 3.1 | Image-quality check | M | detects intentionally dark/blurred test images |
| 3.2 | Perceptual hash | M | duplicate photo recognized |
| 3.3 | Image embedding | M | generated fully offline |
| 3.4 | Processing without network calls | M | airplane-mode audit passes |
| 3.5 | Optional smoke/fire evidence assist | S | uncertainty state exists |
| 3.6 | Raw model confidence hidden from operator | M | UI uses evidence labels |
| 3.7 | Low-confidence model never blocks submission | M | manual flow always succeeds |

## FR-4 — Identity and Integrity

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 4.1 | Ed25519 device key | M | persists across restart |
| 4.2 | Sign every observation | M | altered observation rejected |
| 4.3 | Device role stored | M | WATCHER/GUARD/OFFICER supported |
| 4.4 | Duplicate observation IDs suppressed | M | repeated relay does not increment observer count |
| 4.5 | Replay detection | S | replay logged and ignored |
| 4.6 | Device registry with revocation (§17.3) | M | revoked device excluded from corroboration count |
| 4.7 | Revocation list propagates via store-and-forward | M | reaches a disconnected device after 2-hop sync |
| 4.8 | Production staff authentication | C→Pre-pilot | outside hackathon scope, required before real pilot |

Because FireGround serves a provisioned workforce rather than anonymous civilians, the elaborate anti-Sybil logic from ResQNet is not a priority — a device registry is enough.

## FR-5 — Offline Storage

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 5.1 | SQLite alert store | M | survives app kill/reboot |
| 5.2 | Observation store | M | survives reboot |
| 5.3 | Incident cache | M | range queue works offline |
| 5.4 | Sync-state store | M | already-synced items not resent endlessly |
| 5.5 | Offline map | M | full demo area available with internet disabled |
| 5.6 | Configurable retention | S | archived events purge cleanly |

## FR-6 — Nearby Encounter Sync

Nearby Connections is used as an **opportunistic synchronization layer**, not the product.

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 6.1 | Two phones discover offline | M | ≤15 s |
| 6.2 | Exchange observation-ID inventory | M | no internet |
| 6.3 | Transfer missing observations | M | exact store reconciliation |
| 6.4 | Transfer officer-status updates (incl. conflict/revocation state) | M | status reaches second device |
| 6.5 | Store-and-forward A→B→C | S | A and C never need direct contact |
| 6.6 | Transfer compressed thumbnails | S | configurable |
| 6.7 | Duty-cycled discovery, not continuous advertising (§23) | S | measurable battery improvement over continuous mode |
| 6.8 | Automatic background multi-hop mesh | C | explicitly nonessential |

## FR-7 — Event Resolution Engine

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 7.1 | Transport dedup | M | same ID counted once |
| 7.2 | Duplicate-image detection | M | copied demo photo counted once |
| 7.3 | Spatiotemporal incident association | M | seeded golden cases resolve correctly |
| 7.4 | Distinct-origin count (post-revocation filter) | M | relays do not inflate observer count |
| 7.5 | Satellite ↔ field association | M | matching alert attaches to incident |
| 7.6 | Multiple satellite detections → one incident | M | golden case passes |
| 7.7 | Officer manual merge | S | two incidents merge with audit record |
| 7.8 | Officer manual split | S | incorrect cluster can be separated |
| 7.9 | `TIME_UNCERTAIN` flagging on clock disagreement (§17.4) | M | injected drift test passes |

Manual merge/split is important — no clustering algorithm will be perfect.

## FR-8 — Priority Engine

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 8.1 | Compute 0–100 priority | M | deterministic |
| 8.2 | Distinct observers affect corroboration | M | duplicate relay has zero effect |
| 8.3 | Exposure affects ranking | M | golden scenario passes |
| 8.4 | Recency decay | M | verified by clock-shift test |
| 8.5 | Cross-source agreement | M | satellite + field > satellite alone |
| 8.6 | Explain every score term | M | drill-down totals exactly |
| 8.7 | Configurable weights | M | no hard-coded weights |
| 8.8 | Live judge-facing weight controls | C | ranking reorders |

## FR-9 — Range Officer Interface

Main screen:

```text
┌─────────────────────────────────────────────┐
│ ACTIVE FIRE INCIDENTS                       │
│ 1  🔥 FIRE-07     PRIORITY 87                │
│    4 field devices · 2 satellite alerts      │
│    spreading · settlement exposure           │
│    last evidence 6 min ago                   │
│ 2  🔥 FIRE-03     PRIORITY 62                │
│    2 field devices · 1 satellite alert       │
│    visible flame · no exposure known         │
│ 3  ? ALERT-19     PRIORITY 31                │
│    satellite only · unverified · 42 min old  │
│ ⚠ FIRE-05        NEEDS RECONCILIATION        │
│    conflicting officer actions — see §16     │
└─────────────────────────────────────────────┘
```

Incident drill-down must show: map; first detected; last evidence; satellite detections; field observation count; distinct originating devices; photograph timeline; GPS accuracy; ground-status reports; priority breakdown; verification state; officer action history; conflict-resolution history if applicable.

## FR-10 — Verification

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 10.1 | Officer verify active fire | M | state persisted |
| 10.2 | Mark false alert (with reason code, §19) | M | removed from active queue |
| 10.3 | Mark controlled activity (with reason code) | M | no emergency priority |
| 10.4 | Mark dispatched | M | timestamp + officer recorded |
| 10.5 | Mark contained/resolved | M | incident archived |
| 10.6 | Status propagates through sync | M | field phone sees new status |
| 10.7 | Audit every state transition | M | history visible |
| 10.8 | Detect and surface conflicting actions (§16) | M | conflict badge + audit trail |

---

# 21. Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-1 | Cold start | ≤2.5 s |
| NFR-2 | Open alert → submit report | ≤10 s |
| NFR-3 | On-device visual preprocessing | ≤1.5 s |
| NFR-4 | Fully offline capture | 100% |
| NFR-5 | Nearby discovery | ≤15 s |
| NFR-6 | 100 structured reports reconciliation | ≤10 s after connection |
| NFR-7 | Offline map | no external calls |
| NFR-8 | Local incident recomputation | ≤500 ms for 500 observations |
| NFR-9 | Backend ingest → dashboard | ≤5 s |
| NFR-10 | Local store | ≥5,000 observations |
| NFR-11 | Event duplicate-photo precision | ≥95% on test corpus |
| NFR-12 | Incident-association F1 | ≥85% on injected-ground-truth scenarios |
| NFR-13 | Android | API 26+ |
| NFR-14 | APK including model + demo tiles | ≤150 MB |
| NFR-15 | E2E demo reliability | 5/5 consecutive dry runs |
| NFR-16 | Battery, idle | reported on reference device |
| NFR-17 | Battery, active Nearby sync | reported on reference device — must not be estimated (§23) |

The original ResQNet design correctly insisted that performance be measured on a named mid-range reference device rather than a flagship phone. FireGround retains that rule.

## 21.1 Power & Multi-Day Field Constraints

*(Hardening addition.)* NFR-16/17 exist because field staff patrol for days without reliable charging — a capture-heavy app with continuous GPS and on-device ML can drain a phone faster than it can be recharged.

| ID | Requirement | Pri |
|---|---|---|
| P-1 | GPS sampled only on-demand at capture time, never continuously polled in background | M |
| P-2 | Nearby discovery runs on a duty cycle (periodic scan windows), not continuous advertising — configurable | S |
| P-3 | App displays an estimated battery budget ("~X reports remaining at current charge") | C |

---

# 22. Reference Device

Before final assessment, select one actual mid-range Android handset. All reported measurements use it. No estimated numbers in the final presentation.

| Metric | Device | Result |
|---|---|---|
| App cold start | reference phone | ___ |
| Image embedding | reference phone | ___ |
| Observation submit | reference phone | ___ |
| Nearby discovery | two reference phones | ___ |
| 100-report sync | two reference phones | ___ |
| Battery / hour, idle | reference phone | ___ |
| Battery / hour, active sync | reference phone | ___ |

Test matrix additionally includes one lower-spec phone to catch performance-cliff failures before demo day (§25.2).

---

# 23. Local Map

```text
OFFLINE BASE MAP
+ satellite alerts
+ field observations
+ resolved fire incidents
+ settlement layer
+ road/trail layer
+ optional forest administrative boundary
```

For the hackathon: **bounded synthetic/demo area with locally packaged map data.** No claim of possessing confidential or official Forest Department geospatial layers.

Suggested symbols: `○` satellite detection, `△` field observation, `🔥` resolved active incident, `?` unverified incident, `✓` resolved. **Never use "green = safe."** Absence of a fire marker means only: *no active incident is currently represented in FireGround's local evidence store* — not that no fire exists.

---

# 24. Backend

```text
FastAPI · PostgreSQL · PostGIS · Redis (optional)
```

Responsibilities: alert ingest; signature validation (checks device revocation list); observation persistence; divisional event resolution; priority calculation; audit history; conflict-reconciliation queue; device registry; dashboard API.

---

# 25. Android Stack & Shared Core Logic

## 25.1 Recommended stack

```text
Kotlin · Jetpack Compose · Room/SQLite · CameraX · Android Keystore
Nearby Connections · TensorFlow Lite / ONNX Runtime Mobile
MapLibre · PMTiles-compatible offline map approach
```

## 25.2 Shared core logic & QA strategy

Critical algorithms are deterministic and testable outside the UI — avoid burying them inside Activities or Compose screens:

```text
EventResolver · PriorityEngine · EvidenceAggregator · SyncReconciler
```

*(Hardening addition — v1.0 named this requirement without a concrete test strategy.)*

| ID | Requirement | Pri |
|---|---|---|
| QA-1 | Unit test suite for `EventResolver` and `PriorityEngine` runs outside Android (pure Kotlin/JVM or shared module), executable in CI without a device | M |
| QA-2 | Golden scenario (§27) becomes a regression test, run on every change to event-resolution or priority logic | M |
| QA-3 | Minimum 3 additional adversarial golden cases: (a) two fires close in space but far in time, (b) two fires far in space but same satellite-pass timestamp, (c) heavy duplicate-image forwarding with 5+ relay hops | S |
| QA-4 | Device test matrix: reference mid-range phone + one lower-spec phone | S |

---

# 26. Simulator

One of the highest-value pieces inherited from ResQNet — necessary because a handful of real phones cannot adequately demonstrate corroboration behaviour at scale. Models **observations**, not hundreds of anonymous mesh nodes.

Configurable inputs: number of satellite detections; number of actual fires; number of observers; GPS noise; duplicate photos; repeat satellite detections; false satellite alerts; observation timing; connectivity windows; officer verification; injected clock drift (§17.4); injected conflicting officer actions (§16).

---

# 27. Golden Simulator Scenario

Ground truth:

```text
3 actual fires
Satellite detections:       8
Field observations:        22
Duplicate forwarded images: 7
Distinct devices:          11
False satellite alerts:     2
```

Expected:

```text
37 raw evidence objects → 30 unique observations → 11 field devices
        → 3 actual active incidents + 2 rejected alerts
```

The simulator knows the ground truth. The event-resolution engine does not.

---

# 28. Evaluation Metrics

**Perception:** image-quality accuracy; optional fire-assist precision/recall; visual duplicate detection precision/recall.

**Event resolution:** pairwise same-event precision/recall; incident clustering F1; number-of-events error; duplicate-photo false merge/split rate.

**System:** capture latency; inference latency; Nearby discovery latency; sync duration; local DB latency; battery use (idle and active-sync, per §21.1).

**Decision layer:** top-priority agreement against golden scenarios; ranking stability; raw-alerts-to-actionable-incidents reduction; time for operator to understand evidence; redundant-incident-card elimination count.

## 28.1 The most important evaluation

```text
RAW OBSERVATIONS → RESOLVED INCIDENTS
```

Example: **"17 incoming alerts and field reports → 4 physical incidents → one high-priority response."** More meaningful than a bare classifier accuracy number.

---

# 29. Prior Art Positioning

## 29.1 Existing capability: FSI

FSI already performs near-real-time satellite fire monitoring; distributes alerts; provides forest-fire geospatial products; maintains Van Agni; analyses fire-prone areas.

Therefore these claims are **forbidden**:

> "We detect forest fires using AI." / "India doesn't have a forest-fire alert system." / "We created a forest-fire monitoring platform."

All are misleading.

## 29.2 Existing capability: State systems

State Forest Departments may already have dashboards, apps, feedback mechanisms and response workflows. FireGround must never be positioned as a **replacement forest-fire management platform**. The pitch is:

> **An offline field-evidence resolution and response-triage layer that can feed an existing State Forest Department workflow.**

## 29.3 Novelty claim — be conservative

Do not claim: *"Nobody has ever deduplicated forest-fire reports."* That requires a much deeper literature review than currently exists. The defensible contribution:

> **We combine offline field reporting, opportunistic staff-to-staff synchronization, satellite/ground evidence resolution, distinct-observer corroboration and explainable crew-priority ranking in one deployment workflow designed for disconnected forest operations.**

The innovation is primarily **system integration around a documented operational bottleneck.** That is enough for SIH.

---

# 30. Governance, Legal Basis, Data Ownership

*(Hardening addition — v1.0's privacy section did not address legal authorization or data ownership for a real pilot, which a Parliamentary Committee-aware judge panel is likely to ask about directly given the report cited throughout this document.)*

| ID | Requirement | Pri |
|---|---|---|
| G-1 | Pilot data collection framed explicitly as occurring under the State Forest Department's operational authority over its own staff and land — not public/consumer data collection | M |
| G-2 | Data ownership stated explicitly: the State Forest Department owns incident/observation data; the FireGround team has no independent claim | M |
| G-3 | Retention policy stated: resolved/archived incidents retained per department policy (configurable, per FR-5.6), not indefinitely by default | S |
| G-4 | No claim of compliance with any specific law (e.g. DPDP Act) without legal review — state: "designed with data-minimization principles; formal compliance review required before production deployment" | M |

---

# 31. Safety Rules

FireGround is decision support. It must never say *"No fire exists here"* — it may say *"No active incident is represented by available evidence."* It must never say *"This fire is safe."* It must never automatically instruct *"Send crew through this road."* It must never classify a controlled burn solely from AI. It must never automatically downgrade a field worker's active-fire report because a model failed to see flame.

---

# 32. Privacy

FireGround serves trained or provisioned personnel, not anonymous civilians (contrast with ResQNet). Production deployment may legitimately require user/account identity. For the prototype: device-local key identifies origin; no public personal profile; precise locations are treated as operational data; photographs remain within the operational system; no facial recognition; no continuous camera capture — camera operates only after explicit user action.

---

# 33. Failure Handling

| Situation | Handling |
|---|---|
| No GPS | Save report as `POSITION_STALE` with last-known accuracy; never invent coordinates |
| Model uncertain | Structured manual input remains available |
| No internet | Everything continues locally |
| Nearby fails | Observation stored, uploads later |
| Incorrect clustering | Officer manually splits |
| Two incidents incorrectly separate | Officer manually merges |
| Conflicting officer actions | Enters reconciliation state (§16), never silently overwritten |
| Device lost/compromised | Marked `REVOKED` in registry (§17.3), excluded from future corroboration |
| Clock drift detected | `TIME_UNCERTAIN` flag, weighted down (§17.4) |
| Satellite alert incorrect | Officer marks `FALSE_ALERT` or `CONTROLLED_ACTIVITY` with reason code (§19) |

---

# 34. Field Staff Onboarding & Training

*(Hardening addition — the original demo/MVP assumed users already know how to operate the app; onboarding was omitted end to end.)*

| ID | Requirement | Pri |
|---|---|---|
| ON-1 | One-page laminated/icon-based quick-reference card accompanies each provisioned device | S |
| ON-2 | In-app first-run walkthrough (≤5 screens): open alert, take photo, select state, submit — nothing else | S |
| ON-3 | Provisioning checklist for System Administrator: assign device, set role, install offline map tiles, verify GPS, pair for first sync test | S |
| ON-4 | Training plan documented (even if not built for MVP): half-day session per range before fire season, tied to existing departmental training cycles | C |

---

# 35. Scale-Out Beyond One Division

*(Hardening addition — a credibility slide, not new MVP scope, so this stays deliberately unbuilt.)*

```text
- incident_id namespacing per division to avoid collision on eventual merge
- backend event resolution scoped per division by default; cross-division
  incidents (fires near division boundaries) documented as future work
- sync topology at scale likely needs designated "gateway" roles
  (patrol vehicles, range offices with intermittent internet) rather
  than pure device-to-device flooding — consistent with
  "P2P is transportation, not the project"
```

---

# 36. Team Allocation

**Member 1 — Android/Capture:** Compose UI; alert workflow; camera; GPS; report flow; offline UX; icon-first multilingual flow (§10–11).

**Member 2 — Offline Sync:** Nearby Connections; peer handshake; store reconciliation; store-and-forward; status/revocation propagation; connectivity tests; duty-cycled discovery (§21.1). *(Notably reduced scope vs ResQNet — no epidemic-routing research.)*

**Member 3 — CV/Evidence:** image-quality model; pHash; embedding model; optional fire/smoke assist; TFLite export; benchmarks; visual-similarity evaluation.

**Member 4 — Event Intelligence:** observation resolution; spatiotemporal association; distinct-device counting (post-revocation); incident state machine + conflict resolution (§16); clock-drift handling (§17.4); FirePriority engine; simulator. *(Probably the most technically important role.)*

**Member 5 — Backend/GIS:** FastAPI; PostgreSQL; PostGIS; alert import; incident API; persistence; audit log; device registry (§17.3); conflict-reconciliation queue.

**Member 6 — Dashboard/Integration/Pitch:** Range Officer dashboard; MapLibre UI; evidence drill-down; system integration; prior-art slide; governance slide (§30); metrics; pitch; demo script; backup recording.

---

# 37. Build Order

Build **inside-out from the decision layer**, not from BLE upward.

**Gate 1 — Prove the product:** seed 15 observations → event resolver → 3 incidents → priority queue. If this isn't compelling, stop.

**Gate 2 — Android capture:** alert → photo → structured observation → local DB, all offline.

**Gate 3 — Two-device sync:** Phone A (5 obs) + Phone B (3 obs) → Nearby → both phones have 8 observations.

**Gate 4 — Corroboration:** Phone A + Phone B both see Fire X → 1 incident, 2 distinct devices.

**Gate 5 — False alert:** satellite alert exists; guard reports `NO FIRE VISIBLE` or `CONTROLLED ACTIVITY`; officer rejects/downgrades.

**Gate 6 — Full ranked queue:** three incidents exist; new evidence visibly changes ranking.

**Gate 7 — Conflict handling:** two officers act divergently on one incident offline; sync surfaces reconciliation state (§16).

**Gate 8 — Polish:** thumbnails; animations; fancy map layers; weight sliders; extended simulation; live backend; onboarding walkthrough.

---

# 38. Recommended Feature Cut Order

If schedule slips, cut in this order:

```text
1. live FSI integration
2. background sync
3. thumbnails over Nearby
4. compass bearing
5. officer live weight sliders
6. fancy GIS layers
7. optional smoke/fire classifier
8. full web backend during offline demo
9. onboarding walkthrough screens (keep the quick-reference card concept for the pitch)
10. duty-cycled discovery (fall back to always-on if time-constrained, note as a known trade-off)
```

**Never cut:** structured field observation; offline storage; event resolution; distinct-device corroboration (with revocation filtering); priority ranking; explainability; 2-device offline sync; range-officer queue; simulator; conflict detection on officer actions (§16) — this is cheap to build and expensive to explain away if a judge asks about it and it doesn't exist.

---

# 39. The 6–8 Minute Demo

**Stage setup:** three Android phones — Phone A (Fire Watcher), Phone B (Beat Guard), Phone C (Range Officer) — all visibly in **airplane mode, no internet**. Laptop mirrors Phone C / local dashboard. Preloaded: 3 satellite alerts.

**0:00 — Problem.** Show official evidence slide: *"India already detects forest fires from space. That's not what we built."* Then: *"FSI itself notes that satellite detections are not one-to-one with ground incidents, and the Parliamentary Committee this month identified poor connectivity and weak ground verification as operational gaps."*

**0:40 — No network.** Hold phones up: *"Every field phone is offline."* Open cached map — three satellite hotspots visible.

**1:10 — First ground observation.** Phone A opens SAT-01, photographs a demo fire scene, selects FLAMES + SPREADING. App runs quality check, pHash, embedding, GPS capture, signature — locally. *"No server was involved."*

**2:00 — Independent observation.** Phone B independently reports the same physical fire from another location/view. Initially: Phone A has 1 observation, Phone B has 1 observation.

**2:30 — Offline encounter.** Phones sync via Nearby. Range view becomes: 2 observations, 2 originating devices, 1 physical incident. *"Two reports. One fire. Two independent field devices."*

**3:00 — False-alert moment.** Phone B investigates SAT-02, reports `NO ACTIVE FIRE VISIBLE`, or the Range Officer marks `CONTROLLED ACTIVITY` with a reason code. Alert leaves the emergency queue. *"Satellite detection is evidence. It isn't automatically a ground incident."*

**3:40 — Priority climax.** A third incident, FIRE C, is introduced: visible flames, rapid spread, near settlement, only one field observer. Queue becomes: #1 FIRE C — 88, #2 FIRE A — 67, #3 SAT-03 — 29. Although FIRE A has more reports, FIRE C rises above it because its structured threat evidence is stronger. *"Seven raw observations. Three satellite detections. Two active fires. One team available. This is the decision FireGround exists to support."* **This is the demo climax.**

**4:30 — Explainability moment.** Open FIRE C, show the full term-by-term breakdown. *"The system isn't saying 'AI says 87.' Every point is inspectable."*

**5:15 — Simulator moment.** Switch to simulation. Input: 60 observations, 17 devices, 10 satellite detections, 4 actual fires, 9 copied images, 3 false alerts. Output: 60 → 51 unique evidence items → 17 originating devices → 4 active physical incidents. Show event-association accuracy against injected ground truth.

**6:30 — Close.** *"FSI tells the Forest Department where a possible fire was seen from space. FireGround closes the disconnected last mile: what field teams actually saw, which observations are the same incident, how strongly each one is verified, and which fire deserves the first response team."*

---

# 40. The Three Slides That Matter Most

**Slide 1 — We are not detecting fires.**
```text
FSI SATELLITE ALERT → [GAP] → FIELD VERIFICATION → CREW DECISION
```
**We live in the gap.**

**Slide 2 — Reports are not incidents.**
```text
10 ALERTS + 13 FIELD REPORTS + 6 DUPLICATE IMAGES → 3 PHYSICAL FIRES
```

**Slide 3 — Why now?** Use the 7 August 2026 Parliamentary Committee finding on connectivity, frontline integration and the ground verification loop — one of the strongest pieces of evidence available to the project.

---

# 41. Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Judge says FSI already does this | High | Critical | Open by saying FSI already handles detection |
| Judge says State apps already have verification | High | High | Focus on offline evidence fusion + incident resolution + triage |
| Nearby unreliable | Medium | Medium | Direct encounter sync only; no mesh dependency |
| Event clustering makes bad merges | Medium | High | Conservative thresholds + manual merge/split |
| CV performs badly | Medium | Medium | Structured field input remains primary |
| Fire classifier becomes pitch hero | Medium | High | Downgrade to optional evidence assist |
| Fake "AI priority" criticism | Medium | High | Show full term-by-term scoring |
| No real operational validation | High | High | Seek Forest Department/fire-management expert feedback before internal round |
| Too many features | High | High | Strict MVP/cut list |
| Live demo networking fails | Medium | Critical | Deterministic SIM_MODE using same event data structures |
| "Why Nearby?" | High | Medium | Show direct field-worker handoff under documented connectivity constraints |
| Thresholds look arbitrary | High | Medium | Call them tunable priors and measure sensitivity |
| Controlled burn misclassified | Medium | Critical | Only human can establish controlled-activity status |
| Two officers conflict offline | Medium | High | Conflict detection + reconciliation state (§16), demoed if time allows |
| Judge asks about legal/data authority | Medium | Medium | Governance slide ready (§30) |
| Judge asks about non-English users | Medium | Medium | Icon-first flow + language selection ready to show (§10) |

---

# 42. Questions Judges Will Ask

**"Doesn't FSI already detect forest fires?"** — *"Yes. We depend on that. FSI is upstream of us. We are not building another detector."*

**"So what are you adding?"** — *"Ground verification under unreliable connectivity, observation-to-incident resolution and an explainable response-priority queue."*

**"Why offline?"** — *"Because poor network connectivity in forest and hill terrain is specifically identified as an operational problem in current ground-level fire-alert implementation."*

**"Why P2P?"** — *"It isn't required for the whole product. It shortens the delay when disconnected staff physically encounter another guard, patrol vehicle or officer. If no peer appears, the report simply remains stored until connectivity returns."* Do not pretend Bluetooth magically solves forest communications.

**"Why not WhatsApp?"** — *"WhatsApp can move a photo when connectivity exists. It doesn't know that one satellite alert, three photos and two field updates represent the same physical fire, nor does it convert those observations into an evidence-backed operational queue."*

**"How do you know two reports are the same fire?"** — *"We don't use one magic AI model. We combine spatial distance, time, satellite-alert association and visual similarity, then expose the result for human correction. The officer can manually merge or split incidents."*

**"Can this incorrectly merge two nearby fires?"** — *"Yes. That is one of our core measurable failure modes. We optimise thresholds against injected ground truth, favour conservative merging and provide manual split. We do not claim perfect automatic incident identity."*

**"Can you predict where the fire will go?"** — *"No. Apparent growth in FireGround means received observations indicate expansion. We are not implementing a physical fire-spread model."*

**"Why not just send the nearest team?"** — *"Distance alone isn't enough. A farther fire spreading toward a settlement may deserve attention before a closer low-severity alert. FireGround ranks incidents; the officer still makes the deployment decision."*

**"What happens if two officers disagree while both offline?"** — *"We don't silently pick one. Both actions are preserved, the incident is flagged for reconciliation, and the higher-authority role resolves it with a logged reason. Last-write-wins was a deliberate rejection — a stale device syncing hours later must never overwrite a fresher decision."*

**"What if a phone is lost or stolen?"** — *"The device is marked revoked in the division's device registry. Its historical signed reports stay in the audit trail, but it stops counting toward corroboration going forward. Because we're offline-first, that revocation is eventually-consistent, not instant — we say that plainly rather than overclaim."*

**"Who actually owns this data, legally?"** — *"The State Forest Department, operating over its own staff and land — this isn't public data collection. We haven't done a formal legal compliance review; that's explicitly required before any real deployment, not something we're claiming today."*

---

# 43. Success Criteria for SIH Internal Selection

**Operational credibility:** a judge can identify real user, real data source, real operational gap, real deployment owner within sixty seconds.

**Technical credibility:** the demo proves offline capture, offline synchronization, event fusion, independent observer counting, priority ranking — not mock screens.

**Prior-art credibility:** the team explicitly acknowledges FSI, Van Agni, existing State systems before judges raise them.

**Measurability:** at least one CV metric, one event-resolution metric, one sync metric, one latency metric, one decision-layer metric is measured.

**Operational honesty (new in v2.0):** the team can answer, without stalling, what happens under conflicting offline actions, device loss, clock drift, and who legally owns the data — because these are documented, not because they were solved perfectly.

---

# 44. Definition of Done

- [ ] Three Android phones complete the demonstration without internet
- [ ] Satellite alerts remain visible offline
- [ ] New ground observation works offline, icon-first, in at least 2 languages
- [ ] Photo processing works offline
- [ ] Two devices synchronize through Nearby
- [ ] Duplicate transport does not inflate evidence
- [ ] Duplicate image does not become a new witness
- [ ] Two independent reports can become one incident
- [ ] One satellite alert can be marked false/controlled, with reason code
- [ ] Multiple satellite alerts can resolve to one incident
- [ ] Distinct-device count is visible and excludes revoked devices
- [ ] FirePriority changes when meaningful evidence changes
- [ ] Score is fully explainable
- [ ] Range Officer can verify/reject/resolve
- [ ] Conflicting officer actions are detected and surfaced, not silently overwritten
- [ ] A device can be marked revoked and disappears from future corroboration counts
- [ ] At least one observation demonstrates `TIME_UNCERTAIN` flagging under injected clock drift
- [ ] Simulator has injected ground truth, including conflict and drift scenarios
- [ ] Event-resolution metric has been measured
- [ ] Reference-phone performance numbers are real, including active-sync battery
- [ ] EventResolver + PriorityEngine unit tests run in CI independent of Android device
- [ ] Related-work slide explicitly acknowledges existing Indian systems
- [ ] Governance/data-ownership slide present in pitch deck
- [ ] No slide calls FireGround an "AI forest-fire detection system"
- [ ] Five consecutive full demo rehearsals succeed

---

# 45. Final Product Identity

> **FireGround is an offline-first ground-verification and response-triage layer for forest fire operations. It fuses satellite detections with field observations, resolves repeated and overlapping evidence into physical fire incidents, measures corroboration across distinct and currently-trusted field devices even under clock drift and offline conflicts, and presents forest officers with an explainable priority queue for response — built for a real provisioned workforce, with an honest account of its own operational limits.**

Shortest version:

> **From fire alerts to verified incidents to response priority — even when the forest has no network, two officers disagree, or a phone goes missing.**

## 45.1 What actually makes this *our* project

Not: forest fire detector. Not: Bluetooth mesh. Not: GIS dashboard. Not: AI classifier.

```text
                   FIREGROUND

      MANY NOISY OBSERVATIONS
                 ↓
       EVIDENCE RESOLUTION
                 ↓
     PHYSICAL FIRE INCIDENTS
                 ↓
  INDEPENDENT + CROSS-SOURCE
           CORROBORATION
                 ↓
     EXPLAINABLE PRIORITY
                 ↓
      HUMAN RESPONSE DECISION
   (with an honest account of
    where the system can fail)
```

That is the piece to build the architecture, evaluation and demo around. The original ResQNet PRD eventually reached the same engineering lesson: the corroboration engine was the product and the transport around it was plumbing. FireGround embraces that from day one — and, in this version, embraces the operational edges around it too.
