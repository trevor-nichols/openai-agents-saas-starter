# **Primitive Storybook Components Tracker**

_Last updated: November 22, 2025_

## **Context Snapshot**
- Storybook 10.0.8 with `@storybook/nextjs`; stories glob from `features/**` and `components/**`; addon: Docs; preview centers layout and imports `app/globals.css`; alias shim for `next/config`.
- Existing stories only in feature folders (`features/marketing/access-request`, `features/settings/signup-guardrails`); no coverage for `components/ui/**` primitives yet.
- UI primitives live under `web-app/components/ui` (see checklist below) following shadcn-style patterns on Next.js 16 / React 19 / Tailwind 3.

## **Objective**
Deliver complete, documented Storybook coverage for every UI primitive so design/dev can iterate quickly, spot regressions early, and showcase the component library to stakeholders.

## **Scope & Deliverables**
- Harden Storybook runtime (global providers, theming, controls/viewport presets, MDX Docs styling).
- Author interactive + docs stories for every primitive in `components/ui/**`, including AI kit, foundations, and media.
- Reusable story helpers (layout wrappers, default args, theme toggles) to keep stories DRY and consistent.
- CI-friendly Storybook build + lint/type-check guardrails; static build reference for handoff.

## **Success Criteria**
- `pnpm storybook` and `pnpm storybook:build` pass without missing providers or styling regressions.
- Each primitive exposes at least one Controls-ready story covering default + key variants, plus dark/light modes.
- Docs tab documents props/usage and links to feature examples where relevant.
- Existing feature stories remain functional after shared decorator changes.

## **Phased Work Plan**
| # | Phase | Status | Owner | Target |
| - | ----- | ------ | ----- | ------ |
| 1 | Baseline audit of Storybook config, dependencies, and theming inputs; document gaps and required providers. | ✅ Completed | Frontend Platform | Nov 22, 2025 |
| 2 | Infrastructure hardening: add global decorators (theme/fonts/query), viewport/background presets, DocsPage theming, lint/type-check hooks for stories. | ✅ Completed | Frontend Platform | Nov 22, 2025 |
| 3 | Foundation & layout primitives (foundation/*, separator/status/skeleton/spinner/switch/theme-toggle, card/banner/badge) with shared layout wrappers. | ✅ Completed | Frontend Platform | Nov 22, 2025 |
| 4 | Form controls & inputs (input/textarea/select/radio/checkbox/toggle/dropzone/form patterns) with validation + accessibility scenarios. | ✅ Completed | Frontend Platform | Nov 22, 2025 |
| 5 | Navigation & overlays (nav-bar/navigation-menu/breadcrumb/pagination/tabs, dialog/alert-dialog/sheet/popover/tooltip/dropdown/context-menu/collapsible/accordion). | ✅ Completed | Frontend Platform | Nov 22, 2025 |
| 6 | Data display & feedback (table/data-table/progress/pagination variants/resizable/scroll-area/carousel/marquee/beam/hero/motion/code-blocks). | ✅ Completed | Frontend Platform | Nov 22, 2025 |
| 7 | AI kit + media (components/ui/ai/*, video-player, sonner/use-toast/banner/copy-button/alert) using realistic mocks/streaming fixtures. | ✅ Completed | Frontend Platform | Nov 22, 2025 |
| 8 | Quality gates & publishing: add Storybook build to CI, optional visual regression baseline, doc updates in `web-app/README.md`, static build pointer. | ⏳ Pending | Frontend Platform | Dec 13, 2025 |

## **Phase 1 Findings (Baseline Audit — Nov 22, 2025)**
- Config: `.storybook/main.ts` uses Next builder with only `@storybook/addon-docs`; story globs cover `features/**` and `components/**`. Alias shim exists only for `next/config`; no path alias for `@/*` declared (Next builder may infer from `tsconfig` but we should lock it explicitly to avoid resolver drift).
- Preview: imports `app/globals.css` and centers layout; no global decorators/providers. Missing theme provider (`next-themes`), query client (`@tanstack/react-query`), toaster host (`sonner`), and font class injection (Geist) used by app layout—stories currently render without app-level context.
- Existing stories: only three feature stories (`features/marketing/access-request` and `features/settings/signup-guardrails`). No `components/ui/**` coverage.
- Add-ons/parameters: defaults only; no viewport/background grid presets, no actions/controls configuration tuning, no MDX Docs theming.
- Risks observed: components relying on hooks like `useTheme`, `useQuery`, or toast host will fail/crash in Storybook without providers; design tokens (CSS vars) load via globals.css, but font CSS variables are absent, so typography falls back to system fonts.
- Inputs for Phase 2: add shared decorators for Theme + QueryClient + Toaster, register `@` alias, configure backgrounds/viewports, ensure controls exclude non-serializable props, and decide on DocsPage theming + MDX support.

## **Phase 2 Notes (Infrastructure Hardening — Nov 22, 2025)**
- Added `@storybook/addon-essentials` and Storybook alias for `@` in `.storybook/main.ts`; retained `addon-docs` and `next/config` shim.
- Preview now wraps all stories with `ThemeProvider` (next-themes), `QueryClientProvider`, Geist font variables, and `Toaster`; default layout switched to padded.
- Introduced global theme toolbar (light/dark/system), background presets (Dark/Light/Accent), common viewports (mobile/tablet/desktop), action/controls defaults, and story sorting.
- Providers mirror app-level defaults (dark-first, 60s staleTime, retry=1, no refetch on focus) to keep stories aligned with runtime UX.

## **Phase 3 Notes (Foundation & Layout — Nov 22, 2025)**
- Added stories for foundation primitives: `GlassPanel`, `InlineTag`, `KeyValueList`, `PasswordPolicyList`, `SectionHeader`, `StatCard`.
- Added layout/feedback primitives: `Card`, `Badge`, `Banner`, `Separator`, `Status`, `Skeleton`, `Spinner`, `Switch`, `ThemeToggle`.
- Stories include variant galleries, compositional examples, and padded layouts matching app chrome.

## **Phase 4 Notes (Form Controls — Nov 22, 2025)**
- Authored `Form Controls` showcase covering `Input`, `Textarea`, `Select`, `RadioGroup`, `Checkbox`, `Toggle`, `Switch`, and `Dropzone`.
- Added hook-form example using shared `Form` helpers for validation + accessibility wiring.
- Ensured interactive controls rely on Storybook providers (theme/query/toaster) and remain keyboard-accessible.

## **Phase 5 Notes (Navigation & Overlays — Nov 22, 2025)**
- Added navigation stories: `NavBar`, `NavigationMenu`, `Breadcrumb`, `Pagination`, `Tabs`.
- Added overlay/interactions: `Accordion`, `Collapsible`, `Dialog` + `AlertDialog`, `Sheet`, `Popover`, `Tooltip`, `DropdownMenu`, `ContextMenu`.
- Stories focus on realistic app flows (workspace chrome, pagination with ellipsis, invite dialogs) and exercise portal-based components to ensure decorator coverage is solid.

## **Phase 6 Notes (Data Display & Feedback — Nov 22, 2025)**
- Added data-display stories: `Table`, `DataTable` (sorted/paginated + loading/empty states), `Progress`.
- Layout/viewport stories: `Resizable`, `ScrollArea`.
- Media/motion stories: `Carousel`, `Marquee`, `Beam`, `HeroGeometric`, `Magnetic`.
- Code presentation: `CodeBlock` story with file switcher, copy button, and themed syntax view.

## **Phase 7 Notes (AI Kit + Media — Nov 22, 2025)**
- Added stories for all AI primitives: actions, branch selector, conversation + messages, prompt input, reasoning, response (markdown), suggestions, tasks, loader, inline citations, sources, tool execution, AI code block, AI images, web preview.
- Media/feedback additions: `video-player`, `alert`, `copy-button`, `use-toast` (sonner), plus existing banner coverage.
- Stories use realistic agent/billing examples and exercise streaming, portal, and clipboard contexts under Storybook providers.

## **Validation Plan**
- Local: `pnpm lint`, `pnpm type-check`, `pnpm storybook`, `pnpm storybook:build`.
- Optional: add Playwright-based Storybook snapshot suite in Phase 8 if value outweighs maintenance.

## **Risks & Mitigations**
| Risk | Impact | Mitigation |
| --- | --- | --- |
| Missing providers (theme/query) break controls | Medium | Introduce shared decorators and enforce templates. |
| Noisy controls or story sprawl | Low | Centralize default args; disable non-serializable controls. |
| Drift between UI tokens and stories | Medium | Co-locate fixtures with components; add lint to fail when primitive lacks a story. |

Got it. Here’s the tracker with **only the components that have a `*.stories.tsx` file checked**.

---

## **Subdirectories**

### **ai/**

* [x] actions.tsx
* [x] branch.tsx
* [x] code-block.tsx
* [x] conversation.tsx
* [x] image.tsx
* [x] inline-citation.tsx
* [x] loader.tsx
* [x] message.tsx
* [x] prompt-input.tsx
* [x] reasoning.tsx
* [x] response.tsx
* [x] source.tsx
* [x] suggestion.tsx
* [x] task.tsx
* [x] tool.tsx
* [x] web-preview.tsx

---

### **avatar/**

* [x] AnimatedTooltip.tsx
* [x] Avatar.tsx
* [x] AvatarGroup.tsx
* [x] index.ts

---

### **code-block/**

* [x] index.tsx
* [ ] server.tsx

---

### **foundation/**

* [x] GlassPanel.tsx
* [x] InlineTag.tsx
* [x] KeyValueList.tsx
* [x] PasswordPolicyList.tsx
* [x] SectionHeader.tsx
* [x] StatCard.tsx
* [x] index.ts

---

### **hero/**

* [x] Geometric.tsx
* [x] index.ts

---

### **motion/**

* [x] Magnetic.tsx
* [x] index.ts

---

### **states/**

* [x] EmptyState.tsx
* [x] ErrorState.tsx
* [x] SkeletonPanel.tsx
* [x] index.ts

---

## **Core**

* [x] accordion.tsx
* [x] alert-dialog.tsx
* [x] alert.tsx
* [x] aspect-ratio.tsx
* [x] badge.tsx
* [x] banner.tsx
* [x] beam.tsx
* [x] breadcrumb.tsx
* [x] button.tsx
* [x] card.tsx
* [x] carousel.tsx
* [x] checkbox.tsx
* [x] collapsible.tsx
* [x] command.tsx
* [x] context-menu.tsx
* [x] copy-button.tsx
* [x] data-table.tsx
* [x] dialog.tsx
* [x] dropdown-menu.tsx
* [x] dropzone.tsx
* [x] form.tsx
* [x] hover-card.tsx
* [x] input.tsx
* [x] label.tsx
* [x] marquee.tsx
* [x] nav-bar.tsx
* [x] navigation-menu.tsx
* [x] pagination.tsx
* [x] popover.tsx
* [x] progress.tsx
* [x] radio-group.tsx
* [x] resizable.tsx
* [x] scroll-area.tsx
* [x] select.tsx
* [x] separator.tsx
* [x] sheet.tsx
* [x] skeleton.tsx
* [x] sonner.tsx
* [x] spinner.tsx
* [x] status.tsx
* [x] switch.tsx
* [x] table.tsx
* [x] tabs.tsx
* [x] testimonials.tsx
* [x] textarea.tsx
* [x] theme-toggle.tsx
* [x] toggle.tsx
* [x] tooltip.tsx
* [x] video-player.tsx
