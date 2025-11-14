# Marketing Surface Guide

_Last updated: November 14, 2025_

Platform Foundations owns every marketing route (`/`, `/features`, `/pricing`, `/docs`, `/status`). This guide keeps copy, CTA wiring, and analytics consistent so future changes stay aligned with the code we just shipped.

## 1. Voice & Positioning
- **Tone:** confident, operator-friendly, and action-oriented. Emphasize production readiness (GPT-5 agents, Ed25519 auth, billing automation) without hype.
- **Audience:** product engineers, platform teams, and GTM partners evaluating the starter. Avoid consumer phrasing.
- **Structure:** every hero uses the pattern _eyebrow → title (≤12 words) → two-sentence description → primary/secondary CTAs_. Reference the constants under `agent-next-15-frontend/features/marketing/*/constants.ts`.
- **Proof points:** highlight cross-stack alignment (FastAPI + Next.js), enterprise guardrails, billing automation, and ops tooling. Keep bullets as outcome statements, not feature lists.

## 2. CTA & Analytics Rules
- **CTA intents:** `primary` for the main action (register, start, launch). `secondary` for exploration (docs, agents, contact). Update `features/marketing/types.ts` if new intents appear.
- **Event payload:** all marketing CTAs call `useMarketingAnalytics().trackCtaClick` with `{ location, cta }`. `location` must describe the surface + element (e.g., `landing-hero-primary`, `docs-resource-openapi`).
- **Lead capture:** the shared `StatusAlertsCard` fires `trackLeadSubmit` after a successful mutation with `{ location, channel: 'email', severity, emailDomain }`. Reuse this card anywhere lead capture is required instead of duplicating forms.
- **New CTAs:** when adding buttons/links on marketing pages, bubble the handler through the component props (following patterns in `LandingExperience`, `FeaturesExperience`, `PricingExperience`, `DocsExperience`, and `StatusExperience`). Never call `trackEvent` directly in nested components.

## 3. Component & Layout Guidance
- **Feature orchestrators:** keep the `max-w-6xl`, `px-6 py-16` container and compose panels from `components/ui/foundation` (GlassPanel, InlineTag, SectionHeader, StatCard). Avoid bespoke layout wrappers.
- **Shared components:**
  - `StatusAlertsCard` handles email subscriptions, validation copy, and success/error states. Pass `source` to distinguish analytics locations.
  - `CtaBand` renders the closing CTA block. Feed it a `CtaConfig` (title, description, CTAs) and pass `trackCtaClick` down.
  - `FaqSection` is the default for FAQs. Supply an eyebrow/title only when diverging from the defaults.
- **Marketing constants:** treat `features/marketing/*/constants.ts` as the single source of truth for hero copy, FAQs, proof points, and CTA labels. Update those files before touching JSX.

## 4. Status Alert Contract (Marketing View)
- Visitors submit email + severity via `StatusAlertsCard` → `POST /api/status-subscriptions` (public email channel). Response triggers a verification email; CTA copy must remind users to check inbox.
- `/status` handles `token` + `unsubscribe_token` query params. The verification banners already surface success/error states—keep messaging aligned with the backend contract in `docs/architecture/status-alert-subscriptions.md`.
- When referencing the alert flow in copy, describe it as “double opt-in email alerts for major/maintenance incidents” and mention RSS + CLI as complementary channels.

## 5. Adding New Marketing Surfaces
1. Create a feature module under `features/marketing/<surface>/` following the orchestrator/components/hooks pattern.
2. Define copy/CTA constants first, then build components composed of shared primitives.
3. Pass `trackCtaClick`/`trackLeadSubmit` into every actionable element.
4. Update this guide if the surface introduces new voice, CTA types, or analytics events.

Maintaining this document is part of Milestone FR-UI. Update the “Last updated” line whenever we land material changes.
