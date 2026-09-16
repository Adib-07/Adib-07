<div align="center">

### Adib Sunasra

**Full-Stack Developer & Systems Builder**

I build software systems that operate under real constraints — safety protocols, multi-tenant isolation, human-in-the-loop verification, and local-first autonomy.

</div>

<small align="center">

[Work](#selected-work) · [Engineering](#engineering-stack) · [How I Build](#how-i-build) · [GitHub](https://github.com/Adib-07)

</small>

<br>

| Domain | What I build | Key constraint |
|--------|-------------|----------------|
| **Civic operations** | Issue tracking platforms with SLA enforcement | Multi-tenant data isolation |
| **Clinical decision support** | AI-assisted classification with deterministic safety rules | Incomplete data is refused, never guessed |
| **Campus operations** | Closed-loop reporting and verification workflows | Role-based access at every layer |
| **Local AI** | On-device assistants with optional LLM delegation | Zero cloud dependency for core tasks |

<br>

### Selected Work

<table>
<tr>
<td width="100%" valign="top">

#### [Civic-eye](https://github.com/Adib-07/Civic-eye)

Multi-tenant civic issue platform with SLA tracking and evidence-based resolution.

- **Citizen reporting flow** — guided wizard with photo evidence, GPS, and category classification
- **Staff dashboards** — assignment, SLA compliance, before/after evidence comparison
- **Database-enforced isolation** — Supabase RLS policies handle all access control; no custom backend server
- **4 roles** — citizen, ward_officer, admin, super_admin with granular permissions

`React 19` · `TanStack Start` · `Supabase` · `Leaflet` · `TypeScript`

</td>
</tr>
<tr>
<td width="100%" valign="top">

#### [IMNCI-Safe](https://github.com/Adib-07/IMNCI-Safe)

AI-assisted child-health classification combining LLM extraction with deterministic safety rules.

- **Three-layer architecture** — Gemini extracts clinical observations, a human verifies, pure TypeScript rules decide
- **Core invariant** — `UNKNOWN` is never converted to `false`; missing critical data blocks classification
- **Deterministic fallback** — regex-based extraction when Gemini API is unavailable
- **245 automated tests** — rules engine boundaries, unknown value propagation, determinism verification

`Next.js 16` · `Gemini API` · `Vitest` · `TypeScript` · `Tailwind CSS`

</td>
</tr>
<tr>
<td width="100%" valign="top">

#### [CIRCUVA](https://github.com/Adib-07/CIRCUVA)

Campus environmental issue reporting with a closed-loop verification workflow.

- **Report → dispatch → resolve → verify pipeline** with role-based dashboards
- **Custom SVG rendering** — campus map and analytics charts, no external charting libraries
- **JWT/RBAC with PBKDF2** — four roles with enforced status transition graph
- **66 automated tests** — security, API, and workflow coverage

`FastAPI` · `SQLAlchemy` · `JWT/RBAC` · `Python` · `SQLite`

</td>
</tr>
<tr>
<td width="100%" valign="top">

#### [Jervis](https://github.com/Adib-07/Jervis)

Modular personal AI assistant with voice interaction and local LLM support.

- **Text, voice, or web input** routed through a command handler to system tools or LLM providers
- **On-device by default** — SQLite memory, macOS system integration, no cloud dependency for core tasks
- **Dual LLM backend** — OpenAI when configured, local Ollama as fallback
- **Local web UI** — conversation log, quick actions, microphone input with waveform feedback

`Python` · `OpenAI/Ollama` · `SQLite` · `pyttsx3`

</td>
</tr>
</table>

<br>

### Engineering Stack

<table>
<tr>
<td><strong>Languages</strong></td>
<td>TypeScript, Python, JavaScript</td>
</tr>
<tr>
<td><strong>Frontend</strong></td>
<td>React, Next.js, TanStack Router, Tailwind CSS, Leaflet</td>
</tr>
<tr>
<td><strong>Backend</strong></td>
<td>FastAPI, Supabase, TanStack Start</td>
</tr>
<tr>
<td><strong>Data</strong></td>
<td>PostgreSQL (Supabase), SQLite, SQLAlchemy</td>
</tr>
<tr>
<td><strong>AI</strong></td>
<td>Google Gemini, OpenAI API, Ollama</td>
</tr>
<tr>
<td><strong>Testing</strong></td>
<td>Vitest, pytest, Testing Library</td>
</tr>
<tr>
<td><strong>Security</strong></td>
<td>Supabase RLS, JWT, RBAC, PBKDF2, CSP, input sanitization</td>
</tr>
<tr>
<td><strong>Tools</strong></td>
<td>Git, Vercel, Bun, Vite</td>
</tr>
</table>

<br>

### How I Build

| Principle | Evidence |
|-----------|----------|
| **Security-first architecture** | RLS policies across Civic-eye, JWT/RBAC in CIRCUVA, CSP headers and input sanitization in IMNCI-Safe |
| **Deterministic safety rules** | IMNCI-Safe's rules engine: same input always yields same output; UNKNOWN blocks classification rather than guessing |
| **Automated testing** | 311 tests across IMNCI-Safe (245) and CIRCUVA (66) covering boundaries, edge cases, and security |
| **Evidence-based workflows** | Photo evidence and before/after comparison in Civic-eye and CIRCUVA; verification loops with auto-reopen |
| **Multi-tenant isolation** | Organization-scoped data in Civic-eye enforced at the database level via Supabase RLS |
| **Structured documentation** | Architecture docs, API specs, protocol rules, and build checklists in IMNCI-Safe and CIRCUVA |

<br>

### Currently Exploring

- **Responsible AI patterns** — safety-first architectures where human judgment remains in the loop
- **Edge / local-first computing** — applications that work without cloud dependencies
- **Type-safe APIs** — end-to-end type safety from database to frontend

<br>

<div align="center">

[![GitHub](https://img.shields.io/badge/-Adib--07-181717?style=flat&logo=github)](https://github.com/Adib-07)

</div>
