<div align="center">

### Adib Sunasra

**Full-Stack Developer & Systems Builder**

Building tools that solve real problems — from civic infrastructure to clinical decision support.

</div>

---

### What I Do

I design and build full-stack applications that address practical challenges: tracking civic issues across municipalities, supporting frontline health workers with AI-assisted diagnostics, and managing campus operations. My work emphasizes **security-first architecture**, **deterministic logic**, and **evidence-based workflows**.

---

### Current Focus

My recent work sits at the intersection of **responsible AI** and **operational systems** — building tools where AI assists but doesn't replace human judgment, and where every decision is traceable and verifiable.

---

### Selected Work

<table>
<tr>
<td width="100%" valign="top">

#### Civic-eye

Multi-tenant civic issue management platform with SLA tracking, evidence-based resolution, and role-based access control.

**Problem:** Municipalities need structured workflows to track and resolve civic issues (potholes, water leaks, broken infrastructure) across distributed teams.

**What I built:** A full-stack platform with a citizen-facing reporting flow, staff dashboards, interactive maps, and photographic evidence trails. Row Level Security enforces organization isolation at the database level.

**Key technical detail:** The frontend reads and writes directly to Supabase with no custom backend server — RLS policies handle all access control.

`React 19` · `TanStack Start` · `Supabase` · `Leaflet` · `TypeScript`

[View Repository →](https://github.com/Adib-07/Civic-eye)

</td>
</tr>
<tr>
<td width="100%" valign="top">

#### IMNCI-Safe

AI-assisted child-health classification combining LLM extraction with deterministic safety rules.

**Problem:** Frontline health workers screening sick children need to evaluate multiple danger signs against age-specific thresholds under time pressure with paper-based protocols.

**What I built:** A three-layer safety architecture — AI extracts clinical observations, a human verifies them, then pure TypeScript rules make the classification. The core invariant: `UNKNOWN` is never converted to `false`.

**Key technical detail:** 245 automated tests covering rules engine boundaries, unknown value propagation, and determinism verification.

`Next.js 16` · `Gemini API` · `Vitest` · `TypeScript` · `Tailwind CSS`

[View Repository →](https://github.com/Adib-07/IMNCI-Safe)

</td>
</tr>
<tr>
<td width="100%" valign="top">

#### CIRCUVA

Campus environmental issue reporting and operations platform with a closed-loop verification workflow.

**Problem:** Campus waste management relies on fragmented processes — email, paper forms, informal requests — leading to overflowing bins, illegal dumping, and missed collections.

**What I built:** A report → dispatch → resolve → verify pipeline with role-based dashboards, custom SVG campus maps, analytics, and before/after evidence comparison.

**Key technical detail:** Custom SVG rendering engine for campus visualization and charts — no external charting libraries.

`FastAPI` · `SQLAlchemy` · `JWT/RBAC` · `Python` · `SQLite`

[View Repository →](https://github.com/Adib-07/CIRCUVA)

</td>
</tr>
<tr>
<td width="100%" valign="top">

#### Jervis

Modular personal AI assistant with voice interaction, local LLM support, and system automation.

**Problem:** Running AI tasks locally without cloud dependencies for privacy-sensitive operations.

**What I built:** A lightweight assistant that accepts text, voice, or web input, routes through a command handler, and performs system tasks, manages notes/reminders, or delegates to OpenAI or local Ollama.

**Key technical detail:** Runs entirely on-device with no cloud dependency for core functionality. Voice input/output via macOS-native tools.

`Python` · `OpenAI/Ollama` · `SQLite` · `pyttsx3`

[View Repository →](https://github.com/Adib-07/Jervis)

</td>
</tr>
</table>

---

### Engineering Stack

| Domain | Technologies |
|--------|-------------|
| **Languages** | TypeScript, Python, JavaScript |
| **Frontend** | React, Next.js, TanStack Router, Tailwind CSS, Leaflet |
| **Backend** | FastAPI, Supabase, TanStack Start |
| **Data** | PostgreSQL (Supabase), SQLite, SQLAlchemy |
| **AI/ML** | Google Gemini, OpenAI API, Ollama |
| **Testing** | Vitest, pytest, Testing Library |
| **Auth & Security** | JWT, Supabase RLS, PBKDF2, RBAC, CSP |
| **Tools** | Git, Vercel, Bun, Vite |

---

### How I Build

- **Security-first architecture** — RLS policies, RBAC, input sanitization, CSP headers across projects
- **Evidence-based workflows** — Photo evidence, before/after comparison, verification loops
- **Deterministic safety rules** — AI assists but rules decide; incomplete data is refused, not guessed
- **Automated testing** — 300+ tests across IMNCI-Safe and CIRCUVA covering boundaries and edge cases
- **Structured documentation** — Architecture docs, API specs, and technical decision records
- **Multi-tenant isolation** — Organization-scoped data with database-enforced access control

---

### Currently Exploring

- **Responsible AI patterns** — Safety-first architectures where human judgment remains in the loop
- **Edge computing** — Local-first applications that work without cloud dependencies
- **Real-time systems** — WebSocket integration and live data synchronization
- **Type-safe APIs** — End-to-end type safety from database to frontend

---

<div align="center">

[![GitHub](https://img.shields.io/badge/-Adib--07-181717?style=flat&logo=github)](https://github.com/Adib-07)

</div>
