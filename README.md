<div align="center">

# Adib Sunasra

**Full-Stack Developer & Systems Builder**

</div>

<br>

I build software systems that operate under real constraints — safety protocols, multi-tenant isolation, human-in-the-loop verification, and local-first autonomy.

<div align="center">

[Selected Work](#selected-work) · [Systems Map](#systems-map) · [Engineering Principles](#engineering-principles) · [Stack](#stack)

</div>

<br>

---

## Systems Map

<div align="center">

![Systems Map](assets/systems-map.svg)

</div>

<br>

---

## Selected Work

### [Civic-eye](https://github.com/Adib-07/Civic-eye) · Civic Operations

Multi-tenant civic issue platform with SLA tracking and evidence-based resolution.

| What it does | How it's enforced |
|---|---|
| Citizen reporting with photo evidence, GPS, category classification | Guided wizard flow |
| Staff dashboards with assignment, SLA compliance, before/after comparison | Role-based views |
| Multi-tenant data isolation | Supabase RLS — no custom backend server |
| 4 roles: citizen, ward_officer, admin, super_admin | Granular permissions at database level |

`React 19` · `TanStack Start` · `Supabase` · `Leaflet` · `TypeScript`

<div align="center">

[**Live Demo**](https://civic-eye-alpha.vercel.app) · [**Source**](https://github.com/Adib-07/Civic-eye)

</div>

<br>

---

### [IMNCI-Safe](https://github.com/Adib-07/IMNCI-Safe) · Responsible AI

AI-assisted child-health classification combining LLM extraction with deterministic safety rules.

| What it does | How it's enforced |
|---|---|
| Three-layer architecture: Gemini extracts, human verifies, rules decide | Separation of concerns |
| `UNKNOWN` is never converted to `false` | Core invariant — missing data blocks classification |
| Regex-based extraction when Gemini API is unavailable | Deterministic fallback |
| 245 automated tests | Rules engine boundaries, unknown propagation, determinism |

`Next.js 16` · `Gemini API` · `Vitest` · `TypeScript` · `Tailwind CSS`

<div align="center">

[**Live Demo**](https://imnci-safe.vercel.app) · [**Source**](https://github.com/Adib-07/IMNCI-Safe)

</div>

<br>

---

### [CIRCUVA](https://github.com/Adib-07/CIRCUVA) · Campus Operations

Campus environmental issue reporting with a closed-loop verification workflow.

| What it does | How it's enforced |
|---|---|
| Report → dispatch → resolve → verify pipeline | Role-based dashboards |
| Custom SVG rendering — campus map and analytics charts | No external charting libraries |
| JWT/RBAC with PBKDF2 | Four roles with enforced status transition graph |
| 66 automated tests | Security, API, and workflow coverage |

`FastAPI` · `SQLAlchemy` · `JWT/RBAC` · `Python` · `SQLite`

<div align="center">

[**Source**](https://github.com/Adib-07/CIRCUVA)

</div>

<br>

---

### [Jervis](https://github.com/Adib-07/Jervis) · Local AI

Modular personal AI assistant with voice interaction and local LLM support.

| What it does | How it's enforced |
|---|---|
| Text, voice, or web input routed through command handler | System tools or LLM providers |
| On-device by default — SQLite memory, macOS integration | No cloud dependency for core tasks |
| Dual LLM backend — OpenAI when configured, Ollama as fallback | Graceful degradation |
| Local web UI with conversation log, quick actions, microphone input | Waveform feedback |

`Python` · `OpenAI/Ollama` · `SQLite` · `pyttsx3`

<div align="center">

[**Source**](https://github.com/Adib-07/Jervis)

</div>

<br>

---

## Engineering Principles

<div align="center">

![Engineering Principles](assets/engineering-principles.svg)

</div>

<br>

---

## Evidence

| Metric | Detail |
|---|---|
| **311 tests** | 245 IMNCI-Safe + 66 CIRCUVA |
| **RLS policies** | Supabase Row Level Security in Civic-eye |
| **JWT/RBAC** | python-jose + PBKDF2-SHA256 in CIRCUVA |
| **Deterministic rules** | Same input → same output, always |
| **UNKNOWN invariant** | Missing critical data blocks classification |
| **Custom SVG rendering** | Campus map and charts, zero external libraries |
| **Local-first AI** | On-device processing, optional cloud delegation |

<br>

---

## Stack

| Layer | Technologies |
|---|---|
| **Languages** | TypeScript, Python, JavaScript |
| **Frontend** | React, Next.js, TanStack Router, Tailwind CSS, Leaflet |
| **Backend** | FastAPI, Supabase, TanStack Start |
| **Data** | PostgreSQL (Supabase), SQLite, SQLAlchemy |
| **AI** | Google Gemini, OpenAI API, Ollama |
| **Testing** | Vitest, pytest, Testing Library |
| **Security** | Supabase RLS, JWT, RBAC, PBKDF2, CSP |
| **Tools** | Git, Vercel, Bun, Vite |

<br>

---

<div align="center">

[![GitHub](https://img.shields.io/badge/-Adib--07-181717?style=flat&logo=github)](https://github.com/Adib-07)

</div>
