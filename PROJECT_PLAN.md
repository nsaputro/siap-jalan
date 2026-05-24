# 🧳 SiapJalan — Project Plan

**Smart Travel Packing App + Home Assistant Addon**
_Siap = Ready | Jalan = Travel/Go_

---

## Vision

SiapJalan is an AI-powered travel packing assistant that helps you pack the right things based on your destination, trip duration, activities, and live weather forecast. Inspired by PackPoint's activity-based template system, SiapJalan lets you **combine multiple activity templates** (e.g. Hiking + Swimming + Flight) to generate a complete, deduplicated packing list — then further refines it with AI and real weather data. Available as a **Home Assistant addon** (sidebar panel, multi-user) or **standalone app** (Docker Compose).

---

## Key Design Principle — Activity-Driven Packing

Like PackPoint, the core UX is built around **activities, not generic lists**:

1. User creates a trip and selects one or more activities (e.g. ✈️ Flight + 🏕️ Camping + 🏊 Swimming)
2. The system merges the item lists from all selected activity templates into a single, **deduplicated** packing list
3. AI then enriches the list using destination + weather + duration context
4. User can add/remove items manually on top

This produces a highly relevant list without overwhelming the user, since each activity template is curated to contain only what matters for that activity.

5. When an activity template is **edited later**, all active trips that use it are **automatically updated** — items added/removed/changed in the template are propagated to every packing list that was built from it, preserving any manual changes the user has made.

---

## Tech Stack

### Backend
| Layer | Choice | Version |
|---|---|---|
| Framework | FastAPI | 0.135.x |
| Python | Python | 3.12+ |
| ORM | SQLAlchemy | 2.x (async) |
| Database | SQLite | built-in |
| Validation | Pydantic v2 | 2.x |
| Server | Uvicorn | latest |
| AI | Anthropic Claude API | claude-sonnet-4 |
| Weather | Open-Meteo API | free, no key needed |
| HTTP client | httpx | latest |

### Frontend (Standalone)
| Layer | Choice | Version |
|---|---|---|
| Framework | React | 19 |
| Language | TypeScript | 5.x |
| Styling | TailwindCSS | v4 |
| Components | shadcn/ui | latest |
| Charts | Recharts | latest |
| Build | Vite | 6.x |
| Icons | Lucide React | latest |
| State | Zustand | latest |
| Forms | React Hook Form + Zod | latest |

### HA Addon Frontend
- Vanilla JS SPA (single `index.html`, no build step)
- Matches HA color palette, Material card style, dark mode

### Android App (Future — v0.5.0+)

React Native is **not** used for the HA addon UI because it cannot run directly in a browser / HA ingress without a separate compilation target. The recommended strategy for Android is:

**Shared layer (`packages/shared/`)** — a TypeScript package extracted from the standalone frontend containing:
- API client (`client.ts` — base URL configurable at runtime)
- TypeScript types / Zod schemas for all API models
- Business logic (activity merging preview, packing progress calculations)

**Native app** — a React Native (Expo) project that imports from `shared/` and builds its own native UI screens. This gives the maximum native feel (navigation, gestures, offline storage) while reusing all network and domain logic.

> **Why not React Native Web for the HA addon?**
> React Native Web _can_ compile to a browser bundle, but it requires a build step (breaking the addon's no-build-step simplicity), uses RN's `StyleSheet` API instead of CSS/Tailwind, and produces a heavier bundle. The HA ingress relative-URL constraint also needs extra handling. The standalone `frontend/` React app is already a better web-first codebase to build on.

> **Simplest Android path with no new code**: add a `manifest.json` and service worker to `frontend/` to make it a **Progressive Web App (PWA)**. Android users can "Add to Home Screen" and get an app-like experience with zero native code. This is a viable v0.3.0 stepping stone before a full React Native app.

### Infrastructure
| Tool | Purpose |
|---|---|
| Docker + Docker Compose | Local dev & standalone deployment |
| GitHub Actions | CI + Release pipeline |
| GHCR | Container registry |
| Home Assistant Ingress | HA addon serving |

---

## Project Structure

```
siap-jalan/
├── packages/
│   └── shared/                  # (future) Shared TS package
│       ├── src/
│       │   ├── api/client.ts    # Fetch client, base URL injected at init
│       │   ├── types/           # Shared TypeScript types + Zod schemas
│       │   └── utils/           # Packing progress, activity merge preview
│       └── package.json         # name: @siapjalan/shared
│
├── mobile/                      # (future) React Native / Expo Android app
│   ├── app/                     # Expo Router screens
│   ├── components/              # Native UI components
│   └── package.json             # imports @siapjalan/shared
│
├── ha-addon/                    # Home Assistant addon (primary)
│   ├── config.yaml              # HA addon manifest
│   ├── build.yaml               # Multi-arch build config
│   ├── Dockerfile
│   ├── run.sh                   # Addon entrypoint
│   ├── app/
│   │   ├── main.py              # FastAPI app, serves static/
│   │   ├── database.py          # SQLAlchemy async engine
│   │   ├── dependencies.py      # HAUser + get_ha_user() dependency
│   │   ├── models/
│   │   │   └── packing.py       # ORM models
│   │   ├── schemas/
│   │   │   └── packing.py       # Pydantic v2 schemas + categories
│   │   ├── routers/
│   │   │   ├── trips.py         # CRUD for trips
│   │   │   ├── packing.py       # CRUD for packing lists & items
│   │   │   ├── activities.py    # Activity templates (built-in + custom)
│   │   │   ├── templates.py     # User-saved trip templates
│   │   │   └── ai.py            # AI suggestion endpoint
│   │   └── services/
│   │       ├── ai_suggestions.py      # Claude API integration
│   │       ├── activity_merger.py     # Merge + deduplicate activity lists
│   │       ├── template_propagation.py # Propagate template edits to active trips
│   │       └── weather.py             # Open-Meteo weather fetch
│   └── ui/
│       └── index.html           # Vanilla-JS SPA (HA addon UI)
│
├── backend/                     # Standalone FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── config.py            # Pydantic BaseSettings from .env
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   └── services/
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/                    # Standalone React frontend
│   ├── src/
│   │   ├── api/client.ts        # Axios/fetch client (baseURL: /api)
│   │   ├── components/
│   │   │   ├── ActivityPicker.tsx   # Multi-select activity grid
│   │   │   ├── PackingList.tsx      # Grouped, filterable item list
│   │   │   └── ...                  # Other reusable components
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx    # Trips overview
│   │   │   ├── TripDetail.tsx   # Trip + packing list
│   │   │   ├── NewTrip.tsx      # Trip creation wizard (w/ activity picker)
│   │   │   └── Templates.tsx    # Saved trip templates
│   │   ├── store/               # Zustand state
│   │   └── types/               # Shared TypeScript types
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── data/
│   └── activity_templates.json  # Seed data for built-in activity templates
│
├── .github/
│   └── workflows/
│       ├── ci.yml               # Lint + build checks
│       └── release.yml          # Docker build + push + GH release
│
├── docker-compose.yml
├── repository.yaml              # HA addon repository descriptor
├── CLAUDE.md
├── PROJECT_PLAN.md
├── CHANGELOG.md
├── .gitignore
├── .hadolint.yaml
├── .yamllint.yml
└── README.md
```

---

## Built-in Activity Templates

Each activity ships with a curated item list. Activities can be **freely combined** — the merger service deduplicates overlapping items (e.g. sunscreen appears in both Beach and Hiking but is only added once).

| Slug | Icon | Display Name | Key items added |
|---|---|---|---|
| `flight` | ✈️ | Flight | neck pillow, compression socks, ear plugs, eye mask, travel adaptor, documents pouch |
| `beach` | 🏖️ | Beach | swimwear, sunscreen, flip flops, beach towel, snorkel set, rash guard |
| `swimming` | 🏊 | Swimming | goggles, swim cap, swimwear, ear drops, chlorine-removing shampoo |
| `hiking` | 🥾 | Hiking | trekking poles, trail shoes, moisture-wicking socks, gaiters, blister kit, headlamp, map/compass |
| `camping` | 🏕️ | Camping | tent, sleeping bag, sleeping pad, camp stove, fire starter, bear canister, lantern |
| `skiing` | ⛷️ | Skiing / Snowboarding | ski jacket, thermal base layer, ski gloves, goggles, helmet, hand warmers, boot bag |
| `business` | 💼 | Business Trip | dress shirt/blouse, blazer, formal shoes, business cards, laptop, portable charger |
| `city_break` | 🏙️ | City Break | comfortable walking shoes, day bag, city map/guidebook, reusable bag, umbrella |
| `road_trip` | 🚗 | Road Trip | car phone mount, cooler bag, road snacks, blanket, emergency car kit, reusable cups |
| `cycling` | 🚴 | Cycling | helmet, padded shorts, gloves, repair kit, pump, reflective vest |
| `running` | 🏃 | Running | running shoes, moisture-wicking clothes, GPS watch, energy gels, foam roller |
| `diving` | 🤿 | Scuba / Snorkelling | dive mask, fins, wetsuit, dive computer, underwater torch, log book |
| `surfing` | 🏄 | Surfing | surfboard (or note to rent), leash, wax, rash guard, reef shoes |
| `photography` | 📷 | Photography | camera body, lenses, extra batteries, memory cards, tripod, cleaning kit |
| `backpacking` | 🎒 | Backpacking / Budget | packing cubes, money belt, padlock, microfibre towel, quick-dry clothes |
| `family_kids` | 👨‍👩‍👧 | Family with Kids | baby carrier, diapers, formula/snacks, changing mat, small toys, first-aid kit |

> **Extensibility**: users can create their own custom activity templates via the UI. Built-in templates are seeded from `data/activity_templates.json` and are read-only.

---

## Activity Merging Rules

When a user selects multiple activities, `activity_merger.py` applies the following logic:

1. **Collect** all items from every selected activity template.
2. **Deduplicate** by normalised item name (case-insensitive, ignoring plurals via simple stemming). Keep the item with the highest `priority` score if duplicated across activities.
3. **Mark source**: each merged item carries `source_activities: ["beach", "hiking"]` so the UI can show which activities brought in a given item.
4. **Quantity resolution**: take the maximum quantity suggested across all activities (e.g. sunscreen ×1 from Beach, ×1 from Hiking → ×1 in merged list).
5. **Essential flag**: item is `is_essential = true` if ANY activity marks it essential.
6. **AI enrichment**: after merging, the AI suggestion endpoint adds or adjusts items based on weather, destination culture, and trip duration.

---

## Template Propagation — Live Sync to Active Trips

When a custom activity template is saved (PUT `/activities/{id}`), `template_propagation.py` automatically updates every **active trip** that includes that activity.

**"Active trip"** = any trip where `end_date >= today` (trip hasn't ended yet).

### Per-item propagation rules

| Change in template | Item state in trip | Action |
|---|---|---|
| New item added | Not present | **Add** item to packing list |
| New item added | Already present (same name) | Skip — user likely added it manually |
| Item removed | `is_customised = false` | **Delete** item from packing list |
| Item removed | `is_customised = true` | **Skip** — user modified it, keep it |
| Item updated (name / qty / category / essential) | `is_customised = false` | **Update** matching fields |
| Item updated | `is_customised = true` | **Skip** — preserve user's version |
| Any change | `is_packed = true` | **Never** reset packed status |

### How "customised" is tracked

Each `packing_items` row stores:
- `template_item_id` — FK back to the `activity_template_items` row it originated from (NULL for AI-added or manually-added items)
- `is_customised` — set to `true` the first time a user edits any field (name, quantity, category, essential flag) on a template-sourced item

This lets the propagation service distinguish between *"user chose to change this"* and *"this is still exactly as the template said"*.

### Propagation is synchronous and atomic

The `PUT /activities/{id}` handler runs propagation in the same database transaction as the template update, so either all active trips are updated or none are (on error, the whole operation rolls back).

The response body includes a `propagation_summary` field:

```json
{
  "template": { ... },
  "propagation_summary": {
    "trips_updated": 3,
    "items_added": 2,
    "items_updated": 1,
    "items_removed": 0,
    "items_skipped_customised": 1
  }
}
```

---

## Two Ways to Add Items to a Packing List

Items can reach a packing list through two distinct paths:

### Path A — Edit the Activity Template (persistent)

User opens **Templates → Hiking → Edit** and adds "blister kit" to the template.

- The item is saved to `activity_template_items`
- `template_propagation.py` immediately adds "blister kit" to every **active trip** that includes Hiking (unless an item with that name already exists)
- All **future trips** that pick Hiking will also include "blister kit" automatically

Use this when the item belongs to the activity in general — it should be there every time someone goes hiking.

### Path B — Add Ad-hoc to an Active Trip (one-off)

User opens **Trip Detail → Hiking section → "+ Add item"** and types "blister kit" inline.

- A new `packing_items` row is created with `template_item_id = NULL`, `added_by = 'user'`, and `source_activities = ['hiking']` (so it groups correctly under the Hiking section)
- The Hiking template is **not touched** — this item exists only for this trip
- Template propagation will never overwrite or remove it (since `template_item_id` is NULL)

Use this for one-off needs specific to this trip that don't warrant changing the template.

### Optional: Promote Ad-hoc Item to Template

After adding an ad-hoc item the UI offers **"Also add to Hiking template?"**. Accepting calls `POST /activities/{slug}/items` with the item data, then sets `template_item_id` on the existing `packing_items` row so it becomes template-linked going forward.

### Comparison

| | Edit Template (Path A) | Ad-hoc to Trip (Path B) |
|---|---|---|
| Affects other active trips | ✅ Yes (propagated) | ❌ No |
| Affects future trips | ✅ Yes | ❌ No |
| Appears in template list | ✅ Yes | ❌ No |
| Can be promoted later | — | ✅ Optional |
| UI entry point | Templates screen | Trip detail screen |

---

## Core Features

### Phase 1 — MVP + Activity Templates (v0.1.0)
- [x] Trip management: create, edit, delete trips with destination, dates, activities
- [x] Packing list CRUD: add/edit/delete items, check off when packed
- [x] Item categories: Pakaian, Toilet & Kebersihan, Dokumen, Elektronik, Obat-obatan, etc.
- [x] Packing progress indicator (% packed)
- [x] HA addon: sidebar panel, multi-user via HA ingress
- [x] Standalone: Docker Compose, single-user
- [x] **Activity picker UI**: icon grid, multi-select, live preview of item count (`frontend/src/components/ActivityPicker.tsx`)
- [x] **Built-in activity templates**: 16 activities seeded from `data/activity_templates.json` on startup
- [x] **Activity merger service**: deduplication + source tagging (`backend/app/services/activity_merger.py`)
- [x] **Pre-fill packing list** from selected activities on trip creation (trips router calls `merge_activities`)
- [x] **Template propagation**: editing an activity template auto-updates all active trips that use it (`template_propagation.py`)
- [x] **Ad-hoc item entry**: add items directly to a trip under any activity section via `source_activity` field → `added_by="adhoc"`, `template_item_id=NULL`
- [x] **Promote ad-hoc to template**: `POST /items/{id}/promote` links item to template by name-match
- [x] **Test suite**: 60 backend tests (pytest + pytest-asyncio, integration + unit) + 20 frontend tests (Vitest + @testing-library/react); run on every PR via CI

### Phase 2 — AI & Weather Enrichment (v0.2.0)
- [ ] AI packing suggestions via Claude API (destination + duration + activities + weather)
- [ ] Weather integration via Open-Meteo (free, no API key needed)
- [ ] Smart deduplication: merge AI suggestions with existing items
- [ ] Essential items flagging
- [ ] **Per-activity AI context**: prompt includes which activities were chosen so AI doesn't re-suggest already-templated items

### Phase 3 — Personalisation & UX (v0.3.0)
- [ ] **Gender / traveller profile** filter (like PackPoint): hide gender-irrelevant items (e.g. women's clothing items, baby items)
- [ ] **Traveller count**: scale quantities for group/family trips (e.g. sunscreen ×3 for 3 people)
- [ ] **Custom activity templates**: create, edit, clone built-in activities
- [ ] Save a completed trip as a **user template** for future reuse
- [ ] Copy items between trips
- [ ] Packing weight estimator (grams per item)
- [ ] Export packing list (PDF / share link)
- [ ] Multi-bag assignment: carry-on vs checked vs personal item
- [ ] **PWA support**: add `manifest.json` + service worker to `frontend/` so standalone app is installable on Android as a home-screen app (zero native code — good stepping stone before v0.5.0)

### Phase 4 — Advanced (v0.4.0)
- [ ] Flight/itinerary integration (parse booking confirmation)
- [ ] Shopping list mode (items not owned yet → buy before trip)
- [ ] HA automation triggers (reminder notification 2 days before trip)
- [ ] Collaborative packing (family trips: assign items to travellers)

### Phase 5 — Android App (v0.5.0)
- [ ] Extract `packages/shared/` — API client + types + utils as a standalone TypeScript package
- [ ] Bootstrap `mobile/` as an Expo (React Native) project importing `@siapjalan/shared`
- [ ] Core screens: Trip list, Trip detail + packing list, Activity picker, Templates
- [ ] Native offline support (SQLite via `expo-sqlite`, sync when online)
- [ ] Push notifications for trip reminders (replaces HA automation trigger for standalone users)
- [ ] Publish to Google Play Store

---

## API Endpoints

### Trips
| Method | Endpoint | Description |
|---|---|---|
| GET | `/trips` | List all trips |
| POST | `/trips` | Create a trip |
| GET | `/trips/{id}` | Get trip detail |
| PUT | `/trips/{id}` | Update trip |
| DELETE | `/trips/{id}` | Delete trip |

### Packing Lists & Items
| Method | Endpoint | Description |
|---|---|---|
| GET | `/trips/{id}/lists` | Get packing lists for a trip |
| POST | `/trips/{id}/lists` | Create packing list |
| GET | `/lists/{id}/items` | Get items in a list |
| POST | `/lists/{id}/items` | Add item to list; optional `source_activity` body field groups it under that activity section (ad-hoc Path B) |
| PUT | `/items/{id}` | Update item (name, qty, packed status); sets `is_customised=true` if item is template-sourced |
| DELETE | `/items/{id}` | Delete item |
| POST | `/items/{id}/toggle` | Toggle packed status |
| POST | `/items/{id}/promote` | Promote ad-hoc item to its activity template (Path A); sets `template_item_id` on the item |
| POST | `/items/bulk` | Bulk create items (used when applying activity templates) |

### Activity Templates
| Method | Endpoint | Description |
|---|---|---|
| GET | `/activities` | List all activity templates (built-in + custom) |
| GET | `/activities/{slug}` | Get activity template with its items |
| POST | `/activities` | Create custom activity template |
| PUT | `/activities/{id}` | Update custom activity template metadata; propagates changes to all active trips |
| DELETE | `/activities/{id}` | Delete custom activity template |
| POST | `/activities/{id}/items` | Add an item to an activity template (Path A); propagates to active trips |
| PUT | `/activities/{id}/items/{item_id}` | Edit a template item; propagates change to active trips |
| DELETE | `/activities/{id}/items/{item_id}` | Remove item from template; propagates removal to active trips |
| POST | `/activities/merge` | Merge selected activities → deduplicated item list (preview) |

### AI & Weather
| Method | Endpoint | Description |
|---|---|---|
| POST | `/trips/{id}/suggest` | Generate AI packing suggestions |
| GET | `/trips/{id}/weather` | Get weather forecast for trip destination/dates |

### User Trip Templates
| Method | Endpoint | Description |
|---|---|---|
| GET | `/templates` | List user-saved trip templates |
| POST | `/templates` | Save a trip as a template |
| GET | `/templates/{id}` | Get template with items |
| DELETE | `/templates/{id}` | Delete template |
| POST | `/templates/{id}/apply/{trip_id}` | Apply template to a trip |

### Misc
| Method | Endpoint | Description |
|---|---|---|
| GET | `/categories` | List all packing categories |
| GET | `/auth/me` | Current HA user (addon only) |

---

## Data Models

### `trips`
```
id, ha_user_id, destination, country, start_date, end_date,
duration_days (computed), trip_type (leisure/business/adventure/family),
activities (JSON array of activity slugs), climate_type, notes,
traveller_count, created_at, updated_at
```

### `packing_lists`
```
id, trip_id (FK), name, description, is_default, created_at
```

### `packing_items`
```
id, list_id (FK), category, name, quantity, unit,
is_packed, is_essential,
added_by (activity|adhoc|ai|user),
  -- activity : seeded from an activity template on trip creation / propagation
  -- adhoc    : user added directly to this trip under an activity section (Path B)
  -- ai       : suggested by Claude API
  -- user     : added manually with no activity context
source_activities (JSON array),   -- activity slugs this item is grouped under
                                  -- set for both 'activity' and 'adhoc' items
template_item_id (FK → activity_template_items.id, nullable),
                                  -- non-null only for added_by='activity' items;
                                  -- NULL for adhoc/ai/user items
is_customised (bool, default false),
                                  -- true once user edits any field on an 'activity' item;
                                  -- prevents template propagation from overwriting user changes
weight_grams, bag_type (carry_on|checked|personal),
created_at, updated_at
```

### `activity_templates`
```
id, slug (unique), name, icon_emoji, description,
is_builtin (bool),    -- built-in templates are read-only
ha_user_id (nullable, custom templates only),
climate_types (JSON array),   -- hot|cold|tropical|temperate|any
created_at, updated_at
```

### `activity_template_items`
```
id, activity_template_id (FK), category, name,
quantity, unit, is_essential, priority (int),
notes,    -- e.g. "check airline carry-on liquid rules"
gender_filter (all|male|female),
created_at
```

### `user_trip_templates`
```
id, ha_user_id, name, description,
activities (JSON array of activity slugs),
trip_type, climate_type, duration_min_days, duration_max_days,
created_at
```

### `user_trip_template_items`
```
id, template_id (FK), category, name, quantity, is_essential
```

---

## Activity Picker UX

Trip creation wizard — **Step 2: Select Activities**

```
┌─────────────────────────────────────────────────────────────┐
│  What will you be doing on this trip? (select all that apply)│
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  ✈️     │  │  🏖️     │  │  🥾     │  │  🏕️     │       │
│  │ Flight  │  │  Beach  │  │ Hiking  │  │ Camping │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  💼     │  │  🏊     │  │  ⛷️     │  │  🚗     │       │
│  │Business │  │Swimming │  │Skiing   │  │Road Trip│       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│                         [+ More activities]                  │
│                                                             │
│  Selected: Flight + Hiking + Camping                        │
│  → 47 items across 8 categories (preview)                   │
│                                       [Back]  [Next →]      │
└─────────────────────────────────────────────────────────────┘
```

- Clicking an activity toggles selection (highlighted border + checkmark)
- Footer shows live item count as activities are toggled
- "Next" applies the merged list and opens the trip detail view

### Trip Detail — Packing List (per-activity sections)

```
┌──────────────────────────────────────────────────────────────┐
│  🏕️ Bali Camping Trip  · 5 days  · Jun 1–5                  │
│  Activities: ✈️ Flight  🥾 Hiking  🏕️ Camping               │
│  ████████░░░░  64% packed (28/44 items)                      │
│                                                              │
│  ✈️ Flight  ──────────────────────────────────  [+ Add item] │
│  ✅ Neck pillow                                              │
│  ✅ Compression socks                                        │
│  ☐  Travel adaptor                         [from template]  │
│                                                              │
│  🥾 Hiking  ──────────────────────────────── [+ Add item]   │
│  ✅ Trail shoes                                              │
│  ☐  Headlamp                               [from template]  │
│  ☐  Blister kit          ★ [→ Add to Hiking template?]      │
│        ↑ ad-hoc item added directly to this trip            │
│                                                              │
│  🏕️ Camping  ─────────────────────────────── [+ Add item]   │
│  ☐  Tent                                   [from template]  │
│  ☐  Sleeping bag                           [from template]  │
│                                                              │
│  ＋ General  ─────────────────────────────── [+ Add item]   │
│        (items with no activity grouping)                     │
└──────────────────────────────────────────────────────────────┘
```

**[+ Add item]** next to each activity section creates an ad-hoc item with `source_activities = [that_activity_slug]` (Path B).
**[→ Add to Hiking template?]** appears on ad-hoc items; accepting calls `POST /items/{id}/promote` (Path A).
Items sourced from a template show a small **[from template]** badge; clicking it opens the template for editing.

---

## Home Assistant Addon Config (`ha-addon/config.yaml`)

```yaml
name: SiapJalan
version: "0.1.0"
slug: siap_jalan
description: Smart travel packing assistant with AI suggestions and activity templates
url: https://github.com/nsaputro/siap-jalan
ingress: true
ingress_port: 8099
panel_icon: mdi:bag-suitcase
panel_title: SiapJalan
options:
  anthropic_api_key: ""
  log_level: info
schema:
  anthropic_api_key: str
  log_level: list(debug|info|warning|error)
```

---

## Development Milestones

| Milestone | Description |
|---|---|
| v0.1.0 | MVP: trip CRUD + packing list + activity templates + HA addon |
| v0.2.0 | AI suggestions + weather integration + per-activity AI context |
| v0.3.0 | Personalisation: gender filter, traveller count, custom activities, weight estimator, PWA |
| v0.4.0 | Advanced: shopping list, HA automations, collaborative packing |
| v0.5.0 | Android app: React Native (Expo) + shared TS package |

---

## Getting Started (Development)

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
# API: http://localhost:8000 | Docs: http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# App: http://localhost:5173
```

### Docker (full stack)
```bash
docker compose up --build
```

### HA Addon Installation
1. Settings → Add-ons → Add-on Store → ⋮ → Repositories
2. Add: `https://github.com/nsaputro/siap-jalan`
3. Find **SiapJalan** → Install → Start
4. The **SiapJalan** panel appears in the HA sidebar

---

_SiapJalan — Siapkan perjalananmu dengan cerdas 🧳✈️_
