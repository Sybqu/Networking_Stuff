# FireGround — Product Requirements Document

**Working title:** FireGround  
**Product:** Offline Ground Verification & Response Triage for Forest Fire Alerts  
**Version:** 1.0  
**Context:** MAHE Internal Smart India Hackathon 2026  
**Team:** 6 students  
**Status:** Proposed pivot from ResQNet

---

# 0. Executive Summary

**FireGround is an offline-first field verification and response-triage system for forest fire operations.**

India already has a strong satellite-based forest fire detection infrastructure. Forest Survey of India receives MODIS and SNPP-VIIRS thermal detections, processes them, and disseminates near-real-time fire alerts to State Forest Departments and registered users. FSI itself notes an important limitation: satellite detections are thermal anomalies, the number of detections does not necessarily equal the number of real fire incidents on the ground, and the same physical fire can be detected repeatedly on successive satellite passes. citeturn832565search3

The missing operational layer is **what happens after an alert reaches the field**.

A Parliamentary Committee report published on **7 August 2026** identified poor network connectivity in forest and hill terrain, weak integration with frontline firefighting response, and the absence of a robust ground feedback/verification loop as problems affecting Uttarakhand's fire-alert application's ground-level utility. It recommended improved GIS monitoring, field-level verification and stronger integration with response teams. citeturn832565search2

FireGround targets that gap.

A satellite detection, a photograph from a beat guard, another observation from a fire watcher and a second satellite pass should not automatically appear as four separate fires.

FireGround resolves noisy observations into **physical fire incidents**, estimates how strongly each incident has been corroborated, and produces an explainable ranked queue showing:

> **Which fire needs the first available response team?**

The core product is:

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

---

# 1. Product Definition

## 1.1 One-line pitch

> **Satellite systems tell the Forest Department where a possible fire is. FireGround determines which observations describe the same real fire, collects ground verification even where networks fail, and tells officers which incident deserves the first response team.**

---

## 1.2 The problem

India's forest-fire monitoring infrastructure already performs large-scale satellite detection and alert dissemination. FSI uses remote sensing for near-real-time fire monitoring and maintains the Van Agni forest-fire information system. citeturn832565search0turn832565search4

The remaining field problem can be represented as:

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

FSI explicitly states that the number of satellite detections can differ from the number of actual ground fire incidents and that the same fire can produce detections on successive days because of satellite repeat coverage. citeturn832565search3

That makes **alert-to-incident resolution** an actual operational data problem.

---

# 2. Product Thesis

FireGround is **not an AI forest-fire detector**.

The product thesis is:

> **The scarce resource is not another fire-detection model. It is reliable, structured, ground-verified information that lets a forest officer turn noisy alerts into a response queue under poor connectivity.**

The system therefore optimises for five things:

1. **Offline evidence capture**
2. **Opportunistic synchronization**
3. **Observation-to-incident resolution**
4. **Independent and cross-source corroboration**
5. **Explainable response prioritization**

Everything else exists to serve those five functions.

This preserves the strongest technical concept from ResQNet: resolve transmissions and observations into real-world events before ranking them. The original ResQNet design explicitly separated packet duplication, observation-level equivalence and physical-event clustering rather than treating every report as a new incident. fileciteturn2file5L317-L333

---

# 3. Deployment Owner and Users

## 3.1 Primary deployment owner

**State Forest Department**

Pilot deployment should be scoped at:

```text
ONE FOREST DIVISION
        ↓
2–4 RANGES
        ↓
BEATS / PATROL TEAMS
```

FireGround is not intended initially as a nationwide consumer application.

FSI remains the upstream satellite-alert provider.

The State Forest Department owns:

- field verification;
- incident confirmation;
- response prioritization;
- crew deployment;
- incident closure.

---

## 3.2 Personas

| Persona | Situation | Need | FireGround role |
|---|---|---|---|
| **Fire Watcher / Patrol Staff** | Deep inside forest, weak/no signal | Record what is visible quickly | Capture observations |
| **Beat Guard** | Moving across beat, may encounter alerts or fires | Verify alerts and report conditions | Reporter + verifier |
| **Patrol Vehicle / Mobile Team** | Moves between disconnected field staff | Carry accumulated observations | Opportunistic gateway |
| **Range Officer** | Several possible incidents, limited teams | Decide where to respond first | Primary decision user |
| **Division Control Room** | Multiple ranges | Maintain operational picture | Dashboard user |
| **System Administrator** | Before fire season | Provision devices/maps/configuration | Configuration |

---

## 3.3 Core job to be done

> **When several possible forest fires are being reported and network coverage is unreliable, help me determine which observations describe real distinct fires, what evidence supports each one, and where I should send the next available team.**

---

# 4. Current Workflow vs FireGround

## Current simplified workflow

```text
FSI ALERT
   ↓
SMS / portal / departmental channel
   ↓
Officer/guard receives alert
   ↓
Someone travels toward location
   ↓
phone call / message / manual feedback
   ↓
control room manually reconciles information
   ↓
response decision
```

The 2026 Parliamentary Committee report specifically identified poor mobile connectivity, weak integration with frontline response and insufficient ground feedback/verification as problems in Uttarakhand's implementation. citeturn832565search2

---

## FireGround workflow

```text
FSI / SATELLITE ALERT
        ↓
cached onto relevant range devices
        ↓
GUARD ENTERS LOW-CONNECTIVITY AREA
        ↓
opens cached alert
        ↓
captures photograph + structured ground observation
        ↓
ON DEVICE
GPS
timestamp
image quality
visual fingerprint
image embedding
signature
        ↓
LOCAL STORE
        ↓
encounters another FireGround device
        ↓
OFFLINE SYNCHRONIZATION
        ↓
their observation stores reconcile
        ↓
EVENT RESOLUTION ENGINE
        ↓
6 observations → 2 physical fire incidents
        ↓
PRIORITY ENGINE
        ↓
#1 FIRE A — priority 87
#2 FIRE B — priority 54
        ↓
RANGE OFFICER REVIEWS
        ↓
VERIFY / REJECT / DISPATCH / RESOLVE
```

---

# 5. Scope

## 5.1 MVP

The hackathon MVP must support:

- Android field application
- cached satellite/fire-alert markers
- fully offline observation capture
- GPS + accuracy
- photographs
- structured fire-status reporting
- on-device visual preprocessing
- signed device identity
- SQLite local store
- offline map
- Nearby Connections synchronization between phones
- store-and-forward synchronization
- observation deduplication
- incident association
- independent-device counting
- satellite + field evidence fusion
- explainable priority score
- range-officer incident queue
- verification states
- local simulator
- completely internet-free live demo

---

## 5.2 Explicit non-goals

The MVP will **not** implement:

- automatic wildfire detection from continuous camera feeds;
- drone surveillance;
- live satellite imagery processing;
- its own satellite fire-detection algorithm;
- autonomous dispatch;
- autonomous evacuation advice;
- fire-spread simulation;
- weather forecasting;
- controlled-burn classification from photographs;
- exact fire-perimeter estimation;
- citizen social network;
- public chat;
- nationwide deployment;
- iOS;
- custom radio hardware;
- LoRa;
- full BLE epidemic flooding;
- complex routing across hundreds of phones;
- facial recognition;
- responder tracking;
- automated claims that an area is safe.

These exclusions are intentional.

---

# 6. The Key Pivot from ResQNet

ResQNet had an elaborate epidemic mesh because the assumed network consisted of arbitrary disaster victims and bystanders.

FireGround has a **known operational population**:

```text
fire watcher
     ↕
beat guard
     ↕
patrol team
     ↕
range officer
     ↕
division
```

Therefore the transport problem gets dramatically simpler.

## Keep

- offline-first Android architecture;
- SQLite;
- PMTiles/offline mapping;
- Nearby Connections abstraction;
- store-and-forward;
- cryptographic report identity;
- image fingerprints;
- event resolution;
- independent-device evidence;
- scoring engine;
- verification states;
- simulator;
- ranked operational dashboard.

The previous ResQNet architecture already separated capture, perception, signing, storage, offline transport, backend deduplication and ranked evidence presentation. fileciteturn2file4L266-L289

## Remove or downgrade

- random TTL;
- origin-location privacy tricks;
- dense-network flood suppression;
- fanout optimisation;
- Sybil defence designed for anonymous civilians;
- hundreds-of-node epidemic flooding;
- complex courier budgets;
- class-tiered radio scheduling;
- message-level mesh novelty.

## New philosophy

> **P2P is transportation, not the project.**

If Nearby behaves badly, the product should still be useful through:

```text
offline capture → later internet upload
```

Nearby simply improves the time at which evidence escapes disconnected areas.

---

# 7. High-Level Architecture

```text
┌────────────────────── FIELD ANDROID DEVICE ──────────────────────┐
│                                                                  │
│ ALERT CACHE                                                      │
│  cached FSI-like hotspots · beat/range map · offline tiles       │
│       ↓                                                          │
│ CAPTURE                                                          │
│  alert verification · new fire observation · photo · GPS        │
│       ↓                                                          │
│ STRUCTURE                                                        │
│  smoke/flame state · spread observation · exposure flags         │
│       ↓                                                          │
│ ON-DEVICE VISION                                                 │
│  image-quality check                                             │
│  pHash                                                           │
│  mobile visual embedding                                         │
│  optional smoke/fire evidence assist                             │
│       ↓                                                          │
│ SIGN                                                             │
│  Ed25519 device key → signed observation                         │
│       ↓                                                          │
│ STORE                                                            │
│  SQLite · alerts · observations · incidents · sync state         │
│       ↓                                                          │
│ LOCAL EVENT ENGINE                                               │
│  dedup · incident association · priority                         │
│       ↓                                                          │
│ OFFLINE MAP                                                      │
│  hotspots · field reports · resolved incidents                   │
│       ↓                                                          │
│ NEARBY SYNC                                                      │
│  direct device encounter                                         │
│  exchange IDs → missing records → optional thumbnails            │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          │ connectivity eventually exists
                          ↓
┌──────────────────────── BACKEND ─────────────────────────────────┐
│                                                                  │
│ ALERT INGEST                                                     │
│  public/departmental feed adapter                                │
│       ↓                                                          │
│ SIGNATURE VALIDATION                                             │
│       ↓                                                          │
│ DIVISION-WIDE EVENT RESOLUTION                                   │
│       ↓                                                          │
│ FIRE PRIORITY ENGINE                                             │
│       ↓                                                          │
│ PostgreSQL + PostGIS                                             │
│       ↓                                                          │
│ DASHBOARD                                                        │
│ map · ranked incidents · timeline · evidence · verification      │
└──────────────────────────────────────────────────────────────────┘
```

---

# 8. Architectural Invariant

**The cloud must not be necessary to capture or preserve a field observation.**

Additionally, for the SIH demo:

**event resolution and priority ranking must also be executable locally on the Range Officer device.**

Therefore:

```text
NO INTERNET
    ↓
capture works
map works
vision works
sync works
event fusion works
priority works
officer review works
```

The backend provides a larger divisional picture, persistence and integration.

It is not the brain required to make the demo work.

---

# 9. Input Model

FireGround consumes three primary observation classes.

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

The hackathon implementation uses a **seeded FSI-like alert dataset**, not a fake claim of official API integration.

Production integration would require authorization/data-feed agreements appropriate to the State Forest Department.

---

## 9.2 Field Observation

A structured ground observation contains:

```text
observation_id
origin_device_id
observer_role

observed_at

latitude
longitude
gps_accuracy

linked_alert_id[] optional

visual_state
  SMOKE_VISIBLE
  FLAME_VISIBLE
  BOTH
  NO_FIRE_VISIBLE
  UNCERTAIN

spread_state
  NO_CHANGE_KNOWN
  SPREADING
  RAPID_SPREAD
  UNKNOWN

exposure_flags
  NEAR_SETTLEMENT
  NEAR_ROAD
  NEAR_INFRASTRUCTURE
  ECOLOGICALLY_SENSITIVE
  NONE_KNOWN

ground_status
  ACTIVE_FIRE
  POSSIBLE_FIRE
  CONTROLLED_ACTIVITY
  FALSE_ALERT
  UNCERTAIN

photo_hash
image_embedding
image_quality

note

signature
```

---

## 9.3 Officer Action

```text
VERIFIED_ACTIVE
REJECTED
CONTROLLED_ACTIVITY
DISPATCHED
MONITOR
CONTAINED
RESOLVED
```

Officer actions are never generated automatically.

---

# 10. Observation UX

A guard should not have to write a paragraph.

Primary flow:

```text
OPEN ALERT
    ↓
TAKE PHOTO
    ↓
WHAT DO YOU SEE?

[ SMOKE ]
[ FLAMES ]
[ BOTH ]
[ NOTHING ]
[ UNSURE ]

    ↓

IS IT SPREADING?

[ RAPIDLY ]
[ YES ]
[ NOT SURE ]

    ↓

ANY IMMEDIATE EXPOSURE?

[ SETTLEMENT ]
[ ROAD ]
[ INFRASTRUCTURE ]
[ NONE KNOWN ]

    ↓
SUBMIT
```

Target:

**photo-to-report in under 10 seconds.**

Typing is optional.

---

# 11. On-Device Vision

The AI is **evidence assistance**, not the decision-maker.

## 11.1 Required components

### Image quality gate

Detect:

- severe blur;
- extremely dark image;
- overexposure.

Bad image:

> **"Image may not be usable as evidence. Retake?"**

The user may override it.

---

### Visual fingerprint

Compute a small perceptual hash.

Purpose:

```text
same photograph forwarded twice
        ↓
do not count as two independent visual observations
```

---

### Visual embedding

Generate an offline image embedding using a lightweight mobile encoder.

Purpose:

- similarity search;
- support event association;
- distinguish obvious unrelated scenes;
- detect reused imagery;
- compare multiple field photographs.

Embedding similarity must **never alone merge incidents**.

---

## 11.2 Optional visual fire-assist model

A small quantized mobile model may output:

```text
SMOKE_LIKE
FLAME_LIKE
NO_CLEAR_FIRE_EVIDENCE
UNCERTAIN
```

This is explicitly presented as:

> **Visual evidence assist**

not:

> **AI says this is a wildfire.**

The field worker's structured observation remains the primary ground label.

---

## 11.3 Model fallback

If confidence is low:

```text
AI uncertain
     ↓
manual structured observation remains available
```

There is no failure state where the guard cannot submit because the model is confused.

---

# 12. The Core Technical Contribution — Fire Event Resolution

This is the heart of FireGround.

The system must answer:

> **How many actual fire incidents do these observations represent?**

---

# 13. The Resolution Ladder

## Level 0 — Transport Duplicate

Same serialized observation arrives through multiple devices.

```text
same observation_id
        ↓
one observation
times_received++
```

Never affects corroboration.

---

## Level 1 — Duplicate Evidence

Different submissions may contain the same photograph or copied evidence.

Signals:

- perceptual hash;
- visual embedding;
- timestamp;
- metadata.

Example:

```text
Phone A captures photo
Phone B receives photo and submits it again
Phone C forwards B's submission
```

Result:

```text
3 packets
2 submissions
1 originating visual observation
```

It must **not** become three witnesses.

---

# 14. Level 2 — Physical Fire Association

Distinct observations may describe the **same physical fire**.

No single rule is sufficient.

FireGround computes an association score using:

```text
SPATIAL COMPATIBILITY
+
TEMPORAL COMPATIBILITY
+
SATELLITE-HOTSPOT COMPATIBILITY
+
VISUAL COMPATIBILITY
+
EXISTING INCIDENT CONTINUITY
```

For observations `a` and incident `E`:

```text
Assoc(a,E) =
    ws × Spatial(a,E)
  + wt × Temporal(a,E)
  + wh × HotspotAgreement(a,E)
  + wv × VisualSimilarity(a,E)
```

These weights are **configuration values, not trained scientific parameters**.

The initial hackathon thresholds are deliberately treated as demo defaults.

No pitch should claim they have been scientifically validated for operational forestry.

---

# 15. Why a Simple pHash Is Not Enough

Two guards can photograph the same fire from opposite hillsides.

The images may look completely different.

Therefore:

```text
pHash
```

answers:

> "Is this approximately the same photograph?"

It does **not** reliably answer:

> "Is this the same physical fire?"

Physical incident association therefore requires spatial and temporal context.

This corrects an important weakness in naïve visual deduplication.

---

# 16. Level 3 — Incident

Once observations are associated:

```text
8 transmitted packets
        ↓
6 unique observations
        ↓
4 distinct originating devices
        ↓
2 satellite detections
        ↓
1 physical fire incident
```

The dashboard must expose all five numbers.

Never show only:

> 8 reports

because that invites officers to mistake message volume for evidence volume.

---

# 17. Incident Data Structure

```text
incident_id

status

first_seen_at
last_seen_at

centroid
spatial_extent_proxy

n_packets
n_observations
n_distinct_devices
n_satellite_alerts

visual_states[]
spread_states[]
exposure_flags[]

linked_alert_ids[]
linked_observation_ids[]

corroboration_score
priority_score

verification_state

assigned_team optional

created_at
updated_at
```

---

# 18. Incident State Machine

```text
                    ┌───────────────────┐
satellite alert ───►│   UNVERIFIED       │
                    └─────────┬─────────┘
                              │
                       field evidence
                              ↓
                    ┌───────────────────┐
                    │   FIELD_REPORTED   │
                    └─────────┬─────────┘
                              │
                    sufficient independent
                       supporting evidence
                              ↓
                    ┌───────────────────┐
                    │  CORROBORATED      │
                    └─────────┬─────────┘
                              │
                       officer decision
                ┌─────────────┼──────────────┐
                ↓             ↓              ↓
        ┌──────────────┐ ┌────────────┐ ┌──────────────────┐
        │ VERIFIED FIRE│ │ FALSE ALERT │ │ CONTROLLED       │
        └──────┬───────┘ └────────────┘ │ ACTIVITY         │
               │                         └──────────────────┘
               ↓
        ┌──────────────┐
        │  DISPATCHED   │
        └──────┬───────┘
               ↓
        ┌──────────────┐
        │  CONTAINED    │
        └──────┬───────┘
               ↓
        ┌──────────────┐
        │   RESOLVED    │
        └──────────────┘
```

**CORROBORATED is not equivalent to VERIFIED.**

Only authorized personnel can produce a human verification state.

---

# 19. Cross-Source Corroboration

Evidence is more useful when independent sources agree.

Possible sources:

```text
SATELLITE DETECTION
FIELD PHOTO
FIELD STRUCTURED OBSERVATION
OFFICER VERIFICATION
```

Example:

```text
Satellite hotspot
+
Guard A: visible smoke
+
Guard B: visible flames
        ↓
stronger evidence
```

than:

```text
Guard A submits same fire three times
```

---

# 20. Distinct Observer Evidence

For MVP:

**originating device key is used as the observer-independence proxy.**

Therefore:

```text
same device × 5 reports
```

does not equal:

```text
5 different field devices
```

The UI wording should be:

> **4 distinct field devices**

rather than making an academically stronger claim such as:

> **4 statistically independent witnesses**

unless that independence has actually been established.

---

# 21. Fire Priority Engine

The priority engine answers:

> **If only one response team is free, which unresolved incident deserves attention first?**

It does **not** dispatch automatically.

---

# 22. Priority Model v1

```text
Priority =
100 × (
    0.25 × S
  + 0.20 × C
  + 0.20 × E
  + 0.15 × G
  + 0.10 × X
  + 0.10 × R
)
```

Where:

| Term | Meaning |
|---|---|
| **S** | Ground severity |
| **C** | Corroboration |
| **E** | Exposure |
| **G** | Apparent growth |
| **X** | Cross-source agreement |
| **R** | Recency |

These weights are **interpretable initial priors**.

They are not claimed to be learned from historical fire-response outcomes.

---

# 23. Severity — S

Structured field evidence contributes to severity.

Example configuration:

| Observation | Normalized contribution |
|---|---:|
| uncertain smoke | 0.20 |
| confirmed smoke | 0.35 |
| visible flames | 0.60 |
| flames + spreading | 0.75 |
| rapid spread | 1.00 |

This is configurable.

A Range Officer can override the structured assessment.

---

# 24. Corroboration — C

Use a saturating function:

```text
C = 1 - exp(-n_eff / 3)
```

where `n_eff` is evidence from distinct trusted originating devices.

Why saturating?

The difference between:

```text
1 → 2 observers
```

is operationally more useful than:

```text
21 → 22 observers
```

The system should not reward social-report volume linearly.

---

# 25. Exposure — E

Exposure measures whether something important may be threatened.

Inputs may include:

- settlement proximity;
- road proximity;
- known infrastructure;
- manually marked ecological sensitivity.

For the hackathon:

**use preloaded static GIS layers.**

Do not pretend to have live government GIS integration.

---

# 26. Apparent Growth — G

Growth is inferred from changes in field observations over time.

Possible evidence:

- new observations appearing farther from previous observations;
- multiple field workers explicitly reporting spread;
- increasing number of active locations.

Growth must be labelled:

> **Apparent growth from received evidence**

not:

> **predicted fire spread**

FireGround does not contain a physical fire-spread model.

---

# 27. Cross-Source Agreement — X

Example:

```text
satellite only                       low
field only                           moderate
satellite + one field observation   stronger
satellite + multiple field reports  stronger still
officer verified                     maximum
```

The exact mapping remains configuration-driven.

---

# 28. Recency — R

Example decay:

```text
R = 0.5 ^ (minutes_since_last_evidence / 60)
```

Old reports should gradually lose operational weight.

Age is always shown explicitly.

No event silently disappears simply because its score decays.

---

# 29. Hard Overrides

Some states bypass normal scoring.

```text
FALSE_ALERT
        → removed from active queue

CONTROLLED_ACTIVITY
        → removed from emergency queue

RESOLVED
        → archived

OFFICER_MARKED_URGENT
        → pinned at top with visible manual-override badge
```

Manual overrides are logged.

---

# 30. Explainability

Every incident drill-down must show:

```text
PRIORITY 82

Severity             +21
Corroboration         +16
Exposure              +18
Growth                +12
Cross-source          + 8
Recency               + 7
                     ----
                      82
```

There must be **no opaque "AI priority: 82"**.

A judge or officer should be able to ask:

> "Why is Fire A above Fire B?"

and receive a complete answer.

---

# 31. Functional Requirements

MoSCoW:

- **M** = Must
- **S** = Should
- **C** = Could

Every Must requirement has an acceptance condition.

---

# 32. FR-1 — Alert Cache

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 1.1 | Import seeded satellite alerts | M | 100 demo alerts import correctly |
| 1.2 | Store alerts locally | M | Alerts remain after network removal + app restart |
| 1.3 | Render alert on offline map | M | Marker visible with all radios disconnected |
| 1.4 | Display detection age | M | Every alert shows timestamp/age |
| 1.5 | Open alert → verification flow | M | ≤2 taps |
| 1.6 | Production feed adapter interface | S | Alternative source can be added without changing UI |
| 1.7 | Real FSI integration | C | Not required for SIH demo |

---

# 33. FR-2 — Field Observation

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 2.1 | Report existing alert | M | Submitted fully offline |
| 2.2 | Create new field-first fire report | M | Does not require satellite alert |
| 2.3 | Camera capture | M | Photo stored locally |
| 2.4 | Structured visual state | M | ≤1 tap |
| 2.5 | Spread state | M | ≤1 tap |
| 2.6 | Exposure flags | M | selectable offline |
| 2.7 | GPS + reported accuracy | M | accuracy displayed |
| 2.8 | Last-known position fallback | M | visibly marked stale |
| 2.9 | Optional text note | S | ≤160 chars |
| 2.10 | Compass/photo bearing | C | stored with observation |

---

# 34. FR-3 — On-Device Vision

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 3.1 | Image-quality check | M | detects intentionally dark/blurred test images |
| 3.2 | Perceptual hash | M | duplicate photo recognized |
| 3.3 | Image embedding | M | generated fully offline |
| 3.4 | Processing without network calls | M | airplane-mode audit passes |
| 3.5 | Optional smoke/fire evidence assist | S | uncertainty state exists |
| 3.6 | Raw model confidence hidden from operator | M | UI uses evidence labels |
| 3.7 | Low-confidence model never blocks submission | M | manual flow always succeeds |

---

# 35. FR-4 — Identity and Integrity

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 4.1 | Ed25519 device key | M | persists across restart |
| 4.2 | Sign every observation | M | altered observation rejected |
| 4.3 | Device role stored | M | WATCHER/GUARD/OFFICER supported |
| 4.4 | Duplicate observation IDs suppressed | M | repeated relay does not increment observer count |
| 4.5 | Replay detection | S | replay logged and ignored |
| 4.6 | Production staff authentication | C | outside hackathon scope |

Because FireGround serves a provisioned workforce rather than anonymous civilians, the very elaborate anti-Sybil logic from ResQNet is not a priority.

---

# 36. FR-5 — Offline Storage

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 5.1 | SQLite alert store | M | survives app kill/reboot |
| 5.2 | Observation store | M | survives reboot |
| 5.3 | Incident cache | M | range queue works offline |
| 5.4 | Sync-state store | M | already-synced items not resent endlessly |
| 5.5 | Offline map | M | full demo area available with internet disabled |
| 5.6 | Configurable retention | S | archived events purge cleanly |

---

# 37. FR-6 — Nearby Encounter Sync

Nearby Connections is used as an **opportunistic synchronization layer**.

Not as the product.

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 6.1 | Two phones discover offline | M | ≤15 s |
| 6.2 | Exchange observation-ID inventory | M | no internet |
| 6.3 | Transfer missing observations | M | exact store reconciliation |
| 6.4 | Transfer officer-status updates | M | status reaches second device |
| 6.5 | Store-and-forward A→B→C | S | A and C never need direct contact |
| 6.6 | Transfer compressed thumbnails | S | configurable |
| 6.7 | Automatic background multi-hop mesh | C | explicitly nonessential |

---

# 38. Sync Protocol

When devices meet:

```text
1. handshake
2. exchange device identity + role
3. exchange compact observation-ID digest
4. compute missing IDs
5. exchange missing critical records
6. exchange incident/status updates
7. optionally exchange thumbnails
8. persist sync receipt
9. disconnect
```

Priority:

```text
OFFICER STATUS
    ↓
ACTIVE FIRE OBSERVATION
    ↓
SATELLITE ALERT
    ↓
THUMBNAIL
```

---

# 39. FR-7 — Event Resolution Engine

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 7.1 | Transport dedup | M | same ID counted once |
| 7.2 | Duplicate-image detection | M | copied demo photo counted once |
| 7.3 | Spatiotemporal incident association | M | seeded golden cases resolve correctly |
| 7.4 | Distinct-origin count | M | relays do not inflate observer count |
| 7.5 | Satellite ↔ field association | M | matching alert attaches to incident |
| 7.6 | Multiple satellite detections → one incident | M | golden case passes |
| 7.7 | Officer manual merge | S | two incidents merge with audit record |
| 7.8 | Officer manual split | S | incorrect cluster can be separated |

Manual merge/split is important.

No clustering algorithm will be perfect.

---

# 40. FR-8 — Priority Engine

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

---

# 41. FR-9 — Range Officer Interface

Main screen:

```text
┌─────────────────────────────────────────────┐
│ ACTIVE FIRE INCIDENTS                       │
│                                             │
│ 1  🔥 FIRE-07               PRIORITY 87     │
│    4 field devices · 2 satellite alerts     │
│    spreading · settlement exposure          │
│    last evidence 6 min ago                  │
│                                             │
│ 2  🔥 FIRE-03               PRIORITY 62     │
│    2 field devices · 1 satellite alert      │
│    visible flame · no exposure known        │
│                                             │
│ 3  ? ALERT-19               PRIORITY 31     │
│    satellite only                           │
│    unverified · 42 min old                  │
└─────────────────────────────────────────────┘
```

---

# 42. Incident Drill-Down

Must show:

- map;
- first detected;
- last evidence;
- satellite detections;
- number of field observations;
- number of distinct originating devices;
- photograph timeline;
- GPS accuracy;
- ground-status reports;
- priority breakdown;
- verification state;
- officer action history.

---

# 43. FR-10 — Verification

| ID | Requirement | Pri | Acceptance |
|---|---|---|---|
| 10.1 | Officer verify active fire | M | state persisted |
| 10.2 | Mark false alert | M | removed from active queue |
| 10.3 | Mark controlled activity | M | no emergency priority |
| 10.4 | Mark dispatched | M | timestamp + officer recorded |
| 10.5 | Mark contained/resolved | M | incident archived |
| 10.6 | Status propagates through sync | M | field phone sees new status |
| 10.7 | Audit every state transition | M | history visible |

---

# 44. Non-Functional Requirements

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

The original ResQNet design correctly insisted that performance be measured on a named mid-range reference device rather than a flagship phone. fileciteturn2file3L198-L220

FireGround retains that rule.

---

# 45. Reference Device

Before final assessment, select one actual mid-range Android handset.

All reported measurements must use it.

Example benchmark table:

| Metric | Device | Result |
|---|---|---|
| App cold start | reference phone | ___ |
| Image embedding | reference phone | ___ |
| Observation submit | reference phone | ___ |
| Nearby discovery | two reference phones | ___ |
| 100-report sync | two reference phones | ___ |
| Battery / hour | reference phone | ___ |

No estimated numbers in the final presentation.

---

# 46. Local Map

Map layers:

```text
OFFLINE BASE MAP

+ satellite alerts
+ field observations
+ resolved fire incidents
+ settlement layer
+ road/trail layer
+ optional forest administrative boundary
```

For the hackathon:

**use a bounded synthetic/demo area with locally packaged map data.**

Do not claim to possess confidential or official Forest Department geospatial layers.

---

# 47. Map Semantics

Suggested symbols:

```text
○ satellite detection
△ field observation
🔥 resolved active incident
? unverified incident
✓ resolved
```

Do not use:

> green = safe

Absence of a fire marker means only:

> **No active incident is currently represented in FireGround's local evidence store.**

It does not prove that no fire exists.

---

# 48. Backend

Recommended stack:

```text
FastAPI
PostgreSQL
PostGIS
Redis optional
```

Responsibilities:

- alert ingest;
- signature validation;
- observation persistence;
- divisional event resolution;
- priority calculation;
- audit history;
- dashboard API.

---

# 49. Android Stack

Recommended:

```text
Kotlin
Jetpack Compose
Room / SQLite
CameraX
Android Keystore
Nearby Connections
TensorFlow Lite / ONNX Runtime Mobile
MapLibre
PMTiles-compatible offline map approach
```

---

# 50. Shared Core Logic

Critical algorithms should be deterministic and testable outside the UI:

```text
EventResolver
PriorityEngine
EvidenceAggregator
SyncReconciler
```

Avoid burying these inside Android Activities or Compose screens.

---

# 51. Simulator

The simulator remains one of the highest-value pieces inherited from ResQNet.

The previous project already treated a simulator as necessary because a handful of real phones cannot adequately demonstrate corroboration behaviour. fileciteturn2file1L79-L110

FireGround's simulator should model **observations**, not hundreds of anonymous mesh nodes.

---

# 52. Simulator Inputs

Configurable:

```text
number of satellite detections
number of actual fires
number of observers
GPS noise
duplicate photos
repeat satellite detections
false satellite alerts
observation timing
connectivity windows
officer verification
```

---

# 53. Golden Simulator Scenario

Ground truth:

```text
3 actual fires

Satellite detections:       8
Field observations:        22
Duplicate forwarded images: 7
Distinct devices:          11
False satellite alerts:     2
```

Expected:

```text
37 raw evidence objects
        ↓
30 unique observations
        ↓
11 field devices
        ↓
3 actual active incidents
+ 2 rejected alerts
```

The simulator knows the ground truth.

The event-resolution engine does not.

---

# 54. Evaluation Metrics

## Perception

- image-quality accuracy;
- optional fire-assist precision/recall;
- visual duplicate detection precision/recall.

## Event resolution

- pairwise same-event precision;
- pairwise same-event recall;
- incident clustering F1;
- number-of-events error;
- duplicate-photo false merge rate;
- duplicate-photo false split rate.

## System

- capture latency;
- inference latency;
- Nearby discovery latency;
- sync duration;
- local DB latency;
- battery use.

## Decision layer

- top-priority agreement against manually authored golden scenarios;
- ranking stability;
- number of raw alerts reduced to actionable incidents;
- time required for operator to understand evidence;
- number of redundant incident cards eliminated.

---

# 55. Most Important Evaluation

The strongest single demo metric is:

```text
RAW OBSERVATIONS
        ↓
RESOLVED INCIDENTS
```

Example:

> **17 incoming alerts and field reports → 4 physical incidents → one high-priority response.**

That is more meaningful than:

> "Our classifier achieved 94.2% accuracy."

---

# 56. Prior Art Positioning

This section must appear in the actual SIH presentation.

## Existing capability: FSI

FSI already:

- performs near-real-time satellite fire monitoring;
- distributes alerts;
- provides forest-fire geospatial products;
- maintains Van Agni;
- analyses fire-prone areas. citeturn832565search3turn832565search4

Therefore these claims are forbidden:

> "We detect forest fires using AI."

> "India doesn't have a forest-fire alert system."

> "We created a forest-fire monitoring platform."

All are misleading.

---

# 57. Existing Capability: State Systems

State Forest Departments may already have dashboards, apps, feedback mechanisms and response workflows.

Therefore FireGround must never be positioned as:

> **replacement forest-fire management platform**

The pitch is:

> **an offline field-evidence resolution and response-triage layer that can feed an existing State Forest Department workflow.**

---

# 58. Why This Project Still Exists

The current official evidence supports the problem.

FSI says satellite detections and physical ground incidents are not one-to-one. citeturn832565search3

The August 2026 Parliamentary Committee report identifies:

- poor network connectivity in fire-prone forest/hill areas;
- weak ground-level use of the existing application;
- lack of integration with frontline response;
- inadequate feedback/verification;
- need for GIS-enabled monitoring and measurable reductions in response time. citeturn832565search2

FireGround is designed specifically around that operational gap.

---

# 59. Novelty Claim — Be Conservative

Do **not** claim:

> "Nobody has ever deduplicated forest-fire reports."

That would require a much deeper literature review than we currently have.

The defensible contribution is:

> **We combine offline field reporting, opportunistic staff-to-staff synchronization, satellite/ground evidence resolution, distinct-observer corroboration and explainable crew-priority ranking in one deployment workflow designed for disconnected forest operations.**

The innovation is primarily **system integration around a documented operational bottleneck**.

That is enough for SIH.

---

# 60. Safety Rules

FireGround is decision support.

It must never say:

> "No fire exists here."

It may say:

> "No active incident is represented by available evidence."

It must never say:

> "This fire is safe."

It must never automatically instruct:

> "Send crew through this road."

It must never classify a controlled burn solely from AI.

It must never automatically downgrade a field worker's active-fire report because a model failed to see flame.

---

# 61. Privacy

Unlike ResQNet, FireGround serves trained or provisioned personnel.

Production deployment may legitimately require user/account identity.

For the prototype:

- device-local key identifies origin;
- public personal profile is unnecessary;
- precise locations are operational data;
- photographs remain within the operational system;
- no facial recognition;
- no continuous camera capture;
- camera operates only after explicit user action.

---

# 62. Failure Handling

## No GPS

Save report with:

```text
POSITION_STALE
```

and last-known accuracy.

Never invent coordinates.

---

## Model uncertain

Use structured manual input.

---

## No internet

Everything continues locally.

---

## Nearby fails

Observation remains stored and uploads later.

---

## Incorrect clustering

Officer can manually split.

---

## Two incidents incorrectly separate

Officer can manually merge.

---

## Satellite alert incorrect

Officer marks:

```text
FALSE_ALERT
```

or:

```text
CONTROLLED_ACTIVITY
```

with reason.

---

# 63. Team Allocation

## Member 1 — Android / Capture

Owns:

- Compose UI;
- alert workflow;
- camera;
- GPS;
- report flow;
- offline UX.

---

## Member 2 — Offline Sync

Owns:

- Nearby Connections;
- peer handshake;
- store reconciliation;
- store-and-forward;
- status propagation;
- connectivity tests.

Notice the scope reduction from ResQNet: Member 2 no longer spends the project implementing sophisticated epidemic-routing research.

---

## Member 3 — CV / Evidence

Owns:

- image-quality model;
- pHash;
- embedding model;
- optional fire/smoke assist;
- TFLite export;
- benchmarks;
- visual-similarity evaluation.

---

## Member 4 — Event Intelligence

Owns:

- observation resolution;
- spatiotemporal association;
- distinct-device counting;
- incident state;
- FirePriority engine;
- simulator.

This is probably the most technically important role.

---

## Member 5 — Backend / GIS

Owns:

- FastAPI;
- PostgreSQL;
- PostGIS;
- alert import;
- incident API;
- persistence;
- audit log.

---

## Member 6 — Dashboard / Integration / Pitch

Owns:

- Range Officer dashboard;
- MapLibre UI;
- evidence drill-down;
- system integration;
- prior-art slide;
- metrics;
- pitch;
- demo script;
- backup recording.

The previous ResQNet plan correctly made story/integration a dedicated responsibility rather than giving it to whoever happened to be free. fileciteturn2file9L492-L505

---

# 64. Build Order

The project should be built **inside-out from the decision layer**, not from BLE upward.

## Gate 1 — Prove the product

Before worrying about Nearby:

```text
seed 15 observations
        ↓
event resolver
        ↓
3 incidents
        ↓
priority queue
```

If this isn't compelling, stop.

---

## Gate 2 — Android capture

Phone:

```text
alert → photo → structured observation → local DB
```

all offline.

---

## Gate 3 — Two-device sync

```text
Phone A
5 observations

Phone B
3 different observations

        ↓ Nearby

both phones
8 observations
```

---

## Gate 4 — Corroboration

```text
Phone A sees Fire X
Phone B sees Fire X

        ↓

1 incident
2 distinct devices
```

---

## Gate 5 — False alert

Satellite alert exists.

Guard reports:

```text
NO FIRE VISIBLE
or
CONTROLLED ACTIVITY
```

Officer rejects/downgrades it.

---

## Gate 6 — Full ranked queue

Three incidents exist.

Adding new evidence visibly changes the ranking.

---

## Gate 7 — Polish

Only after the above work:

- thumbnails;
- animations;
- fancy map layers;
- weight sliders;
- extended simulation;
- live backend.

---

# 65. Recommended Feature Cut Order

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
```

Never cut:

```text
structured field observation
offline storage
event resolution
distinct-device corroboration
priority ranking
explainability
2-device offline sync
range-officer queue
simulator
```

---

# 66. The 6–8 Minute Demo

## Stage setup

Three Android phones:

```text
Phone A — Fire Watcher
Phone B — Beat Guard
Phone C — Range Officer
```

All visibly:

```text
AIRPLANE MODE
NO INTERNET
```

Laptop mirrors Phone C / local dashboard.

Preloaded:

```text
3 satellite alerts
```

---

# 67. Demo Script

## 0:00 — Problem

Show official evidence slide.

> "India already detects forest fires from space. That's not what we built."

Then:

> "FSI itself notes that satellite detections are not one-to-one with ground incidents, and the Parliamentary Committee this month identified poor connectivity and weak ground verification as operational gaps." citeturn832565search3turn832565search2

---

## 0:40 — No network

Hold phones up.

> "Every field phone is offline."

Open cached map.

Three satellite hotspots visible.

---

## 1:10 — First ground observation

Phone A opens:

```text
SAT-01
```

Photographs printed/demo fire scene.

Selects:

```text
FLAMES
SPREADING
```

The app runs:

```text
quality check
pHash
embedding
GPS capture
signature
```

locally.

> "No server was involved."

---

## 2:00 — Independent observation

Phone B independently reports the same physical fire from another location/view.

Initially:

```text
Phone A: 1 observation
Phone B: 1 observation
```

---

## 2:30 — Offline encounter

Phones synchronize through Nearby.

Range view becomes:

```text
2 observations
2 originating devices
1 physical incident
```

The line:

> **"Two reports. One fire. Two independent field devices."**

---

# 68. False-Alert Moment

Phone B investigates:

```text
SAT-02
```

and reports:

```text
NO ACTIVE FIRE VISIBLE
```

or the Range Officer manually marks:

```text
CONTROLLED ACTIVITY
```

The alert leaves the emergency queue.

> "Satellite detection is evidence. It isn't automatically a ground incident."

---

# 69. Priority Climax

A third incident is introduced:

```text
FIRE C
visible flames
rapid spread
near settlement
only one field observer
```

The queue becomes:

```text
#1 FIRE C — 88
#2 FIRE A — 67
#3 SAT-03 — 29
```

Although FIRE A has more reports, FIRE C rises above it because its structured threat evidence is stronger.

Then say:

> **"Seven raw observations. Three satellite detections. Two active fires. One team available. This is the decision FireGround exists to support."**

That is the demo climax.

---

# 70. Explainability Moment

Open FIRE C.

Show:

```text
Severity        24
Corroboration    8
Exposure        20
Growth          15
Cross-source    10
Recency         10
                --
Priority        87
```

> "The system isn't saying 'AI says 87'. Every point is inspectable."

---

# 71. Simulator Moment

Switch to simulation.

Input:

```text
60 observations
17 devices
10 satellite detections
4 actual fires
9 copied images
3 false alerts
```

Output:

```text
60 observations
        ↓
51 unique evidence items
        ↓
17 originating devices
        ↓
4 active physical incidents
```

Show event-association accuracy against injected ground truth.

---

# 72. Close

> **"FSI tells the Forest Department where a possible fire was seen from space. FireGround closes the disconnected last mile: what field teams actually saw, which observations are the same incident, how strongly each one is verified, and which fire deserves the first response team."**

---

# 73. The Three Slides That Matter Most

## Slide 1

### We are not detecting fires.

```text
FSI SATELLITE ALERT
        ↓
      [GAP]
        ↓
FIELD VERIFICATION
        ↓
CREW DECISION
```

**We live in the gap.**

---

## Slide 2

### Reports are not incidents.

```text
10 ALERTS
+
13 FIELD REPORTS
+
6 DUPLICATE IMAGES
        ↓
3 PHYSICAL FIRES
```

---

## Slide 3

### Why now?

Use the **7 August 2026 Parliamentary Committee finding** on connectivity, frontline integration and the ground verification loop. citeturn832565search2

This is one of the strongest pieces of evidence available to the project.

---

# 74. Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Judge says FSI already does this | High | Critical | Open by saying FSI already handles detection |
| Judge says State apps already have verification | High | High | Focus on offline evidence fusion + incident resolution + triage |
| Nearby unreliable | Medium | Medium | Direct encounter sync only; no mesh dependency |
| Event clustering makes bad merges | Medium | High | conservative thresholds + manual merge/split |
| CV performs badly | Medium | Medium | structured field input remains primary |
| Fire classifier becomes pitch hero | Medium | High | downgrade to optional evidence assist |
| Fake "AI priority" criticism | Medium | High | show full term-by-term scoring |
| No real operational validation | High | High | seek Forest Department/fire-management expert feedback before internal round |
| Too many features | High | High | strict MVP/cut list |
| Live demo networking fails | Medium | Critical | deterministic SIM_MODE using same event data structures |
| "Why Nearby?" | High | Medium | show direct field-worker handoff under documented connectivity constraints |
| Thresholds look arbitrary | High | Medium | call them tunable priors and measure sensitivity |
| Controlled burn misclassified | Medium | Critical | only human can establish controlled-activity status |

---

# 75. Questions Judges Will Ask

## "Doesn't FSI already detect forest fires?"

Correct answer:

> **"Yes. We depend on that. FSI is upstream of us. We are not building another detector."**

FSI already runs nationwide satellite-based forest-fire monitoring and alert dissemination. citeturn832565search0turn832565search3

---

## "So what are you adding?"

> **"Ground verification under unreliable connectivity, observation-to-incident resolution and an explainable response-priority queue."**

---

## "Why offline?"

> **"Because poor network connectivity in forest and hill terrain is specifically identified as an operational problem in current ground-level fire-alert implementation."** citeturn832565search2

---

## "Why P2P?"

> **"It isn't required for the whole product. It shortens the delay when disconnected staff physically encounter another guard, patrol vehicle or officer. If no peer appears, the report simply remains stored until connectivity returns."**

This answer is important.

Do not pretend Bluetooth magically solves forest communications.

---

# 76. "Why not WhatsApp?"

> "WhatsApp can move a photo when connectivity exists. It doesn't know that one satellite alert, three photos and two field updates represent the same physical fire, nor does it convert those observations into an evidence-backed operational queue."

---

# 77. "How do you know two reports are the same fire?"

> "We don't use one magic AI model. We combine spatial distance, time, satellite-alert association and visual similarity, then expose the result for human correction. The officer can manually merge or split incidents."

---

# 78. "Can this incorrectly merge two nearby fires?"

> "Yes. That is one of our core measurable failure modes. We optimise thresholds against injected ground truth, favour conservative merging and provide manual split. We do not claim perfect automatic incident identity."

That is a much stronger answer than pretending it cannot fail.

---

# 79. "Can you predict where the fire will go?"

> **"No. Apparent growth in FireGround means received observations indicate expansion. We are not implementing a physical fire-spread model."**

---

# 80. "Why not just send the nearest team?"

> "Distance alone isn't enough. A farther fire spreading toward a settlement may deserve attention before a closer low-severity alert. FireGround ranks incidents; the officer still makes the deployment decision."

---

# 81. Success Criteria for SIH Internal Selection

The project succeeds if the team can demonstrate all of the following:

### Operational credibility

A judge can identify:

```text
real user
real data source
real operational gap
real deployment owner
```

within sixty seconds.

### Technical credibility

The demo proves:

```text
offline capture
offline synchronization
event fusion
independent observer counting
priority ranking
```

rather than merely displaying mock screens.

### Prior-art credibility

The team explicitly acknowledges:

```text
FSI
Van Agni
existing State systems
```

before judges raise them.

### Measurability

At least:

```text
one CV metric
one event-resolution metric
one sync metric
one latency metric
one decision-layer metric
```

is measured.

---

# 82. Definition of Done

FireGround is ready for internal assessment only when all of these are true:

- [ ] Three Android phones complete the demonstration without internet
- [ ] Satellite alerts remain visible offline
- [ ] New ground observation works offline
- [ ] Photo processing works offline
- [ ] Two devices synchronize through Nearby
- [ ] Duplicate transport does not inflate evidence
- [ ] Duplicate image does not become a new witness
- [ ] Two independent reports can become one incident
- [ ] One satellite alert can be marked false/controlled
- [ ] Multiple satellite alerts can resolve to one incident
- [ ] Distinct-device count is visible
- [ ] FirePriority changes when meaningful evidence changes
- [ ] Score is fully explainable
- [ ] Range Officer can verify/reject/resolve
- [ ] Simulator has injected ground truth
- [ ] Event-resolution metric has been measured
- [ ] Reference-phone performance numbers are real
- [ ] Related-work slide explicitly acknowledges existing Indian systems
- [ ] No slide calls FireGround an "AI forest-fire detection system"
- [ ] Five consecutive full demo rehearsals succeed

---

# 83. Final Product Identity

The cleanest description of FireGround is:

> **FireGround is an offline-first ground-verification and response-triage layer for forest fire operations. It fuses satellite detections with field observations, resolves repeated and overlapping evidence into physical fire incidents, measures corroboration across distinct field devices, and presents forest officers with an explainable priority queue for response.**

And the shortest version is:

> **From fire alerts to verified incidents to response priority — even when the forest has no network.**

---

# 84. What Actually Makes This *Our* Project

Not:

```text
forest fire detector
```

Not:

```text
Bluetooth mesh
```

Not:

```text
GIS dashboard
```

Not:

```text
AI classifier
```

The identity is:

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
```

That is the piece you should build the architecture, evaluation and demo around.

The original ResQNet PRD eventually reached the same engineering lesson: the corroboration engine was the product and the transport around it was plumbing. fileciteturn2file7L397-L418

**FireGround should embrace that from day one.**

techstack frameowrk feasbility implementation problems and solution and novelty breakdown
