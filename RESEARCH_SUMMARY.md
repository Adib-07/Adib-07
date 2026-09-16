# CivicEye — Verified Repository Facts

## 1. Technologies Used (from `package.json` and README)

| Category | Technologies |
|----------|--------------|
| **Framework** | React 19, TanStack Start, TanStack Router |
| **State/Data** | TanStack React Query, Supabase JS Client |
| **Styling** | Tailwind CSS 4, shadcn/ui (New York style), Framer Motion |
| **UI Components** | shadcn/ui primitives, Radix UI, Lucide React icons |
| **Maps** | Leaflet, React Leaflet, OpenStreetMap tiles |
| **Charts** | Chart.js, Recharts |
| **Forms** | React Hook Form, Zod, @hookform/resolvers |
| **Database** | Supabase PostgreSQL with Row Level Security |
| **Auth** | Supabase Auth (email/password with confirmation) |
| **Storage** | Supabase Storage (private bucket, signed URLs) |
| **Build** | Vite, Nitro, TypeScript |
| **Linting** | ESLint with Prettier, React Hooks + React Refresh plugins |
| **Package Manager** | Bun |
| **Deployment** | Vercel |

**Verified in**: `package.json` dependencies and devDependencies.

---

## 2. What the Project Actually Does

CivicEye is a **multi-tenant civic issue management platform** designed for municipalities, campus facilities, and property management teams. It includes:

- **Citizen Reporting Flow** (`/report`): 4-step guided wizard for submitting civic issues with photo evidence, GPS location, and category.
- **Staff Dashboard** (`/dashboard`): Operations dashboard with stat cards, charts, issue queue, SLA tracking, and resolution verification.
- **Reports Queue** (`/reports`): Full-text search, filters, sorting, and responsive layouts (table on desktop, cards on mobile).
- **Interactive Map** (`/map`): Full-viewport OpenStreetMap with color-coded markers by status.
- **Issue Lifecycle**: Status workflow (Pending → In Progress → Resolved → Verified/Closed/Reopened) with staff assignment, evidence upload, and audit trail.
- **Multi-Tenant Organization Management**: Organization-scoped data with departments, wards, and subscription tiers.

**Intended for**: Facility managers, campus administrators, municipal operations teams, and ward-level government staff.

**Verified in**: `README.md` and `src/routes/` structure.

---

## 3. Live Demo Exists

- **URL**: https://civic-eye-alpha.vercel.app
- **Deployment**: Vercel (verified via `vercel.json` and README).
- **Note**: Staff features require a Supabase backend with seeded data. The citizen reporting flow (`/report`) works without authentication.

**Verified in**: `README.md` and `vercel.json`.

---

## 4. Security Features

### Row Level Security (RLS)
- **10 migration phases** implement RLS policies for organization isolation.
- Staff can only access their organization's data; citizens are routed to their configured organization.
- **Verified in**: `supabase/migrations/003_rls_hardening.sql` and `docs/RLS_VERIFICATION.md`.

### Role-Based Access Control (RBAC)
- **Four roles**: `citizen`, `ward_officer`, `admin`, `super_admin`.
- Granular permissions enforced at the database level (e.g., only admins can delete reports, manage SLA policies).
- **Verified in**: `003_rls_hardening.sql` (function `is_org_admin`, `is_org_staff`).

### Authentication
- **Supabase Auth** with email/password, session persistence, auto-refresh tokens, and email confirmation flow.
- **Verified in**: `src/lib/auth.ts` and README.

### Client-Side Security
- **No service role keys** exposed to the browser.
- **CSRF protection** via server-side middleware.
- **Storage security**: Private bucket with signed URLs (24h TTL). File path validation extracts organization ID.
- **Environment variables**: Secrets excluded via `.gitignore`, validated in `env.ts`.
- **Verified in**: `docs/SECURITY_PHASE3.md` and README.

### Still Required (Noted Limitations)
- Rate limiting on report submission.
- CAPTCHA/abuse prevention on anonymous insert.
- MFA for admin accounts.
- Disable open staff self-registration.
- CSP, dependency scanning, penetration test.
- **Verified in**: `docs/SECURITY_PHASE3.md`.

---

## 5. Architecture Details

### Multi-Tenant Design
- **Organization-scoped data** via Supabase Row Level Security.
- **Tenant root**: `organizations` table; every other table is scoped to an org.
- **Subscription tiers**: Free Pilot (30 days), Community, Growth, Enterprise with plan limits.
- **Note**: Multi-tenancy is at the application level (organization scoping), not infrastructure level (single Supabase project per deployment).
- **Verified in**: `README.md` and `003_rls_hardening.sql`.

### Frontend Architecture
- **No custom backend API server**. Frontend reads/writes directly to Supabase via client SDK.
- **File-based routing** with TanStack Router.
- **State management**: TanStack React Query for server state.
- **Verified in**: `README.md` and project structure.

### Database Design
- **Key entities**: `organizations`, `profiles`, `reports`, `issue_evidence`, `issue_status_history`, `sla_policies`, `departments`/`wards`, `resolution_verifications`.
- **Migrations**: Numbered sequentially (`001` through `010`).
- **Verified in**: `README.md` and `supabase/migrations/`.

---

## 6. Test Counts and Test Setup

### Automated Tests
- **No automated test suite** is currently configured.
- **No test runner, test files, or test configuration** exists.
- **Verified in**: `README.md` ("Known Limitations" section) and absence of test dependencies in `package.json`.

### Quality Checks (CI)
- **Lint**: `bun run lint` (ESLint) — Passes.
- **Type checking**: `bun run typecheck` (TypeScript) — Passes.
- **Build**: `bun run build` (Vite) — Builds successfully.
- **CI pipeline**: `.github/workflows/ci.yml` runs lint, typecheck, and build on push/PR to `main`.
- **Verified in**: `.github/workflows/ci.yml` and `package.json` scripts.

---

## 7. Verified Claims Summary

| Claim | Status | Source |
|-------|--------|--------|
| Multi-tenant with RLS | **Verified** | `003_rls_hardening.sql`, `RLS_VERIFICATION.md` |
| Four user roles | **Verified** | `003_rls_hardening.sql`, `README.md` |
| Live demo on Vercel | **Verified** | `README.md`, `vercel.json` |
| No automated tests | **Verified** | `README.md`, `package.json` |
| SLA tracking | **Verified** | `README.md`, `supabase/migrations/` |
| Evidence-based resolution | **Verified** | `README.md`, `issue_evidence` table |
| Public citizen reporting | **Verified** | `003_rls_hardening.sql` (anon insert policies) |
| Private storage with signed URLs | **Verified** | `docs/SECURITY_PHASE3.md`, `003_rls_hardening.sql` |

**Note**: All claims are derived from repository files. No external assumptions or guesses were made.
