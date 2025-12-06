# Next.js 16

This release provides the latest improvements to Turbopack, caching, and the Next.js architecture. Since the previous beta release, we added several new features and improvements:

*   **Cache Components:** New model using Partial Pre-Rendering (PPR) and use cache for instant navigation.
*   **Next.js Devtools MCP:** Model Context Protocol integration for improved debugging and workflow.
*   **Proxy:** Middleware replaced by proxy.ts to clarify network boundary.
*   **DX:** Improved logging for builds and development requests.

For reminder, those features were available since the previous beta release:

*   **Turbopack (stable):** Default bundler for all apps with up to 5-10x faster Fast Refresh, and 2-5x faster builds
*   **Turbopack File System Caching (beta):** Even faster startup and compile times for the largest apps
*   **React Compiler Support (stable):** Built-in integration for automatic memoization
*   **Build Adapters API (alpha):** Create custom adapters to modify the build process
*   **Enhanced Routing:** Optimized navigations and prefetching with layout deduplication and incremental prefetching
*   **Improved Caching APIs:** New `updateTag()` and refined `revalidateTag()`
*   **React 19.2:** View Transitions, `useEffectEvent()`, `<Activity/>`
*   **Breaking Changes:** Async params, next/image defaults, and more

### Upgrade to Next.js 16:

```bash
# Use the automated upgrade CLI
npx @next/codemod@canary upgrade latest
 
# ...or upgrade manually
npm install next@latest react@latest react-dom@latest
 
# ...or start a new project
npx create-next-app@latest
```

For cases where the codemod can't fully migrate your code, please read the upgrade guide.

---

## New Features and Improvements

### Cache Components

Cache Components are a new set of features designed to make caching in Next.js both more explicit, and more flexible. They center around the new "use cache" directive, which can be used to cache pages, components, and functions, and which leverages the compiler to automatically generate cache keys wherever it’s used.

Unlike the implicit caching found in previous versions of the App Router, caching with Cache Components is entirely opt-in. All dynamic code in any page, layout, or API route is executed at request time by default, giving Next.js an out-of-the-box experience that’s better aligned with what developers expect from a full-stack application framework.

Cache Components also complete the story of Partial Prerendering (PPR), which was first introduced in 2023. Prior to PPR, Next.js had to choose whether to render each URL statically or dynamically; there was no middle ground. PPR eliminated this dichotomy, and let developers opt portions of their static pages into dynamic rendering (via Suspense) without sacrificing the fast initial load of fully static pages.

You can enable Cache Components in your `next.config.ts` file:

**next.config.ts**
```typescript
const nextConfig = {
  cacheComponents: true,
};
 
export default nextConfig;
```

We will be sharing more about Cache Components and how to use them at Next.js Conf 2025 on October 22nd, and we will be sharing more content in our blog and documentation in the coming weeks.

**Note:** as previously announced in the beta release, the previous experimental `experimental.ppr` flag and configuration options have been removed in favor of the Cache Components configuration.

Learn more in the documentation here.

### Next.js Devtools MCP

Next.js 16 introduces Next.js DevTools MCP, a Model Context Protocol integration for AI-assisted debugging with contextual insight into your application.

The Next.js DevTools MCP provides AI agents with:

*   **Next.js knowledge:** Routing, caching, and rendering behavior
*   **Unified logs:** Browser and server logs without switching contexts
*   **Automatic error access:** Detailed stack traces without manual copying
*   **Page awareness:** Contextual understanding of the active route

This enables AI agents to diagnose issues, explain behavior, and suggest fixes directly within your development workflow.

Learn more in the documentation here.

### proxy.ts (formerly middleware.ts)

`proxy.ts` replaces `middleware.ts` and makes the app’s network boundary explicit. `proxy.ts` runs on the Node.js runtime.

*   **What to do:** Rename `middleware.ts` → `proxy.ts` and rename the exported function to `proxy`. Logic stays the same.
*   **Why:** Clearer naming and a single, predictable runtime for request interception.

**proxy.ts**
```typescript
export default function proxy(request: NextRequest) {
  return NextResponse.redirect(new URL('/home', request.url));
}
```

**Note:** The `middleware.ts` file is still available for Edge runtime use cases, but it is deprecated and will be removed in a future version.

Learn more in the documentation here.

### Logging Improvements

In Next.js 16 the development request logs are extended showing where time is spent.

*   **Compile:** Routing and compilation
*   **Render:** Running your code and React rendering

The build is also extended to show where time is spent. Each step in the build process is now shown with the time it took to complete.

```text
   ▲ Next.js 16 (Turbopack)
 
 ✓ Compiled successfully in 615ms
 ✓ Finished TypeScript in 1114ms
 ✓ Collecting page data in 208ms
 ✓ Generating static pages in 239ms
 ✓ Finalizing page optimization in 5ms
```

The following features were previously announced in the beta release:

---

## Developer Experience

### Turbopack (stable)

Turbopack has reached stability for both development and production builds, and is now the default bundler for all new Next.js projects. Since its beta release earlier this summer, adoption has scaled rapidly: more than 50% of development sessions and 20% of production builds on Next.js 15.3+ are already running on Turbopack.

With Turbopack, you can expect:

*   2–5× faster production builds
*   Up to 10× faster Fast Refresh

We're making Turbopack the default to bring these performance gains to every Next.js developer, no configuration required. For apps with custom webpack setups, you can continue using webpack by running:

```bash
next dev --webpack
next build --webpack
```

### Turbopack File System Caching (beta)

Turbopack now supports filesystem caching in development, storing compiler artifacts on disk between runs for significantly faster compile times across restarts, especially in large projects.

Enable filesystem caching in your configuration:

**next.config.ts**
```typescript
const nextConfig = {
  experimental: {
    turbopackFileSystemCacheForDev: true,
  },
};
 
export default nextConfig;
```

All internal Vercel apps are already using this feature, and we’ve seen notable improvements in developer productivity across large repositories.

We’d love to hear your feedback as we iterate on filesystem caching. Please try it out and share your experience.

### Simplified create-next-app

`create-next-app` has been redesigned with a simplified setup flow, updated project structure, and improved defaults. The new template includes the App Router by default, TypeScript-first configuration, Tailwind CSS, and ESLint.

### Build Adapters API (alpha)

Following the Build Adapters RFC, we've worked with the community and deployment platforms to deliver the first alpha version of the Build Adapters API.

Build Adapters allow you to create custom adapters that hook into the build process, enabling deployment platforms and custom build integrations to modify Next.js configuration or process build output.

**next.config.js**
```javascript
const nextConfig = {
  experimental: {
    adapterPath: require.resolve('./my-adapter.js'),
  },
};
 
module.exports = nextConfig;
```

Share your feedback in the RFC discussion.

### React Compiler Support (stable)

Built-in support for the React Compiler is now stable in Next.js 16 following the React Compiler's 1.0 release. The React Compiler automatically memoizes components, reducing unnecessary re-renders with zero manual code changes.

The `reactCompiler` configuration option has been promoted from experimental to stable. It is not enabled by default as we continue gathering build performance data across different application types. Expect compile times in development and during builds to be higher when enabling this option as the React Compiler relies on Babel.

**next.config.ts**
```typescript
const nextConfig = {
  reactCompiler: true,
};
 
export default nextConfig;
```

Install the latest version of the React Compiler plugin:

```bash
npm install babel-plugin-react-compiler@latest
```

---

## Core Features & Architecture

### Enhanced Routing and Navigation

Next.js 16 includes a complete overhaul of the routing and navigation system, making page transitions leaner and faster.

*   **Layout deduplication:** When prefetching multiple URLs with a shared layout, the layout is downloaded once instead of separately for each Link. For example, a page with 50 product links now downloads the shared layout once instead of 50 times, dramatically reducing the network transfer size.
*   **Incremental prefetching:** Next.js only prefetches parts not already in cache, rather than entire pages. The prefetch cache now:
    *   Cancels requests when the link leaves the viewport
    *   Prioritizes link prefetching on hover or when re-entering the viewport
    *   Re-prefetches links when their data is invalidated
    *   Works seamlessly with upcoming features like Cache Components

**Trade-off:** You may see more individual prefetch requests, but with much lower total transfer sizes. We believe this is the right trade-off for nearly all applications. If the increased request count causes issues, please let us know. We're working on additional optimizations to inline data chunks more efficiently.

These changes require no code modifications and are designed to improve performance across all apps.

### Improved Caching APIs

Next.js 16 introduces refined caching APIs for more explicit control over cache behavior.

#### revalidateTag() (updated)

`revalidateTag()` now requires a `cacheLife` profile as the second argument to enable stale-while-revalidate (SWR) behavior:

```typescript
import { revalidateTag } from 'next/cache';
 
// ✅ Use built-in cacheLife profile (we recommend 'max' for most cases)
revalidateTag('blog-posts', 'max');
 
// Or use other built-in profiles
revalidateTag('news-feed', 'hours');
revalidateTag('analytics', 'days');
 
// Or use an inline object with a custom revalidation time
revalidateTag('products', { expire: 3600 });
 
// ⚠️ Deprecated - single argument form
revalidateTag('blog-posts');
```

The profile argument accepts built-in `cacheLife` profile names (like `'max'`, `'hours'`, `'days'`) or custom profiles defined in your `next.config`. You can also pass an inline `{ expire: number }` object. We recommend using `'max'` for most cases, as it enables background revalidation for long-lived content. When users request tagged content, they receive cached data immediately while Next.js revalidates in the background.

Use `revalidateTag()` when you want to invalidate only properly tagged cached entries with stale-while-revalidate behavior. This is ideal for static content that can tolerate eventual consistency.

**Migration guidance:** Add the second argument with a `cacheLife` profile (we recommend `'max'`) for SWR behavior, or use `updateTag()` in Server Actions if you need read-your-writes semantics.

#### updateTag() (new)

`updateTag()` is a new Server Actions-only API that provides read-your-writes semantics, expiring and immediately reading fresh data within the same request:

```typescript
'use server';
 
import { updateTag } from 'next/cache';
 
export async function updateUserProfile(userId: string, profile: Profile) {
  await db.users.update(userId, profile);
 
  // Expire cache and refresh immediately - user sees their changes right away
  updateTag(`user-${userId}`);
}
```

This ensures interactive features reflect changes immediately. Perfect for forms, user settings, and any workflow where users expect to see their updates instantly.

#### refresh() (new)

`refresh()` is a new Server Actions-only API for refreshing uncached data only. It doesn't touch the cache at all:

```typescript
'use server';
 
import { refresh } from 'next/cache';
 
export async function markNotificationAsRead(notificationId: string) {
  // Update the notification in the database
  await db.notifications.markAsRead(notificationId);
 
  // Refresh the notification count displayed in the header
  // (which is fetched separately and not cached)
  refresh();
}
```

This API is complementary to the client-side `router.refresh()`. Use it when you need to refresh uncached data displayed elsewhere on the page after performing an action. Your cached page shells and static content remain fast while dynamic data like notification counts, live metrics, or status indicators refresh.

### React 19.2 and Canary Features

The App Router in Next.js 16 uses the latest React Canary release, which includes the newly released React 19.2 features and other features being incrementally stabilized. Highlights include:

*   **View Transitions:** Animate elements that update inside a Transition or navigation
*   **useEffectEvent:** Extract non-reactive logic from Effects into reusable Effect Event functions
*   **Activity:** Render "background activity" by hiding UI with `display: none` while maintaining state and cleaning up Effects

Learn more in the React 19.2 announcement.

---

## Breaking Changes and Other Updates

### Version Requirements

| Change | Details |
| :--- | :--- |
| **Node.js 20.9+** | Minimum version now 20.9.0 (LTS); Node.js 18 no longer supported |
| **TypeScript 5+** | Minimum version now 5.1.0 |
| **Browsers** | Chrome 111+, Edge 111+, Firefox 111+, Safari 16.4+ |

### Removals

These features were previously deprecated and are now removed:

| Removed | Replacement |
| :--- | :--- |
| **AMP support** | All AMP APIs and configs removed (`useAmp`, `export const config = { amp: true }`) |
| **next lint command** | Use Biome or ESLint directly; `next build` no longer runs linting. A codemod is available: `npx @next/codemod@canary next-lint-to-eslint-cli .` |
| **devIndicators options** | `appIsrStatus`, `buildActivity`, `buildActivityPosition` removed from config. The indicator remains. |
| **serverRuntimeConfig, publicRuntimeConfig** | Use environment variables (`.env` files) |
| **experimental.turbopack location** | Config moved to top-level `turbopack` (no longer in `experimental`) |
| **experimental.dynamicIO flag** | Renamed to `cacheComponents` |
| **experimental.ppr flag** | PPR flag removed; evolving into Cache Components programming model |
| **export const experimental_ppr** | Route-level PPR export removed; evolving into Cache Components programming model |
| **Automatic scroll-behavior: smooth** | Add `data-scroll-behavior="smooth"` to HTML document to opt back in |
| **unstable_rootParams()** | We are working on an alternative API that we will ship in an upcoming minor |
| **Sync params, searchParams props access** | Must use async: `await params`, `await searchParams` |
| **Sync cookies(), headers(), draftMode() access** | Must use async: `await cookies()`, `await headers()`, `await draftMode()` |
| **Metadata image route params argument** | Changed to async `params`; `id` from `generateImageMetadata` now `Promise<string>` |
| **next/image local src with query strings** | Now requires `images.localPatterns` config to prevent enumeration attacks |

### Behavior Changes

These features have new default behaviors in Next.js 16:

| Changed Behavior | Details |
| :--- | :--- |
| **Default bundler** | Turbopack is now the default bundler for all apps; opt out with `next build --webpack` |
| **images.minimumCacheTTL default** | Changed from 60s to 4 hours (14400s); reduces revalidation cost for images without cache-control headers |
| **images.imageSizes default** | Removed 16 from default sizes (used by only 4.2% of projects); reduces srcset size and API variations |
| **images.qualities default** | Changed from `[1..100]` to `[75]`; quality prop is now coerced to closest value in `images.qualities` |
| **images.dangerouslyAllowLocalIP** | New security restriction blocks local IP optimization by default; set to `true` for private networks only |
| **images.maximumRedirects default** | Changed from unlimited to 3 redirects maximum; set to 0 to disable or increase for rare edge cases |
| **@next/eslint-plugin-next default** | Now defaults to ESLint Flat Config format, aligning with ESLint v10 which will drop legacy config support |
| **Prefetch cache behavior** | Complete rewrite with layout deduplication and incremental prefetching |
| **revalidateTag() signature** | Now requires `cacheLife` profile as second argument for stale-while-revalidate behavior |
| **Babel configuration in Turbopack** | Automatically enables Babel if a babel config is found (previously exited with hard error) |
| **Terminal output** | Redesigned with clearer formatting, better error messages, and improved performance metrics |
| **Dev and build output directories** | `next dev` and `next build` now use separate output directories, enabling concurrent execution |
| **Lockfile behavior** | Added lockfile mechanism to prevent multiple `next dev` or `next build` instances on the same project |
| **Parallel routes default.js** | All parallel route slots now require explicit `default.js` files; builds fail without them. Create `default.js` that calls `notFound()` or returns `null` for previous behavior |
| **Modern Sass API** | Bumped `sass-loader` to v16, which supports modern Sass syntax and new features |

### Deprecations

These features are deprecated in Next.js 16 and will be removed in a future version:

| Deprecated | Details |
| :--- | :--- |
| **middleware.ts filename** | Rename to `proxy.ts` to clarify network boundary and routing focus |
| **next/legacy/image component** | Use `next/image` instead for improved performance and features |
| **images.domains config** | Use `images.remotePatterns` config instead for improved security restriction |
| **revalidateTag() single argument** | Use `revalidateTag(tag, profile)` for SWR, or `updateTag(tag)` in Actions for read-your-writes |

### Additional Improvements

*   **Performance improvements:** Significant performance optimizations for `next dev` and `next start` commands
*   **Node.js native TypeScript for next.config.ts:** Run `next dev`, `next build`, and `next start` commands with `--experimental-next-config-strip-types` flag to enable native TypeScript for `next.config.ts`.


## 1. Hard breaking & removals (must be addressed to upgrade)

### 1.1 Version / toolchain requirements

* **Node.js 20.9+ required**

  * **Was:** Node 18 supported.
  * **Now:** Minimum Node is `20.9.0` (LTS). Node 18 is no longer supported; running under 18 is out of spec. ([Next.js][1])
  * **Action:** Bump your runtime (local + CI + hosting) to Node 20.9+ and update `engines` in `package.json`.

* **TypeScript 5.1+ required**

  * **Was:** TS 4.x/early 5.x often worked.
  * **Now:** Official minimum is TS `5.1`. ([Next.js][1])
  * **Action:** Upgrade TypeScript and @types packages.

* **Browser baselines raised**

  * **Now:** Chrome/Edge/Firefox 111+, Safari 16.4+ as baseline. ([Next.js][2])
  * Usually not a code break, but relevant for support matrix.

---

### 1.2 Request & routing APIs that are now *only async* (real code breaks)

* **Async Request APIs – sync access removed (Breaking)**

  * **Was (15):** Next 15 introduced async Dynamic APIs but kept a temporary sync compatibility path.
  * **Now (16):** Sync access is gone. You *must* use them asynchronously:

    * `cookies()`, `headers()`, `draftMode()`
    * `params` in `layout.js`, `page.js`, `route.js`, `default.js`, `opengraph-image`, `twitter-image`, `icon`, `apple-icon`
    * `searchParams` in `page.js` ([Next.js][1])
  * **Action:**

    * Make components `async` where needed and `await props.params` / `await props.searchParams`.
    * Use `npx next typegen` and the generated `PageProps`, `LayoutProps`, `RouteContext` types to get proper async typing. ([Next.js][1])

* **Async params for metadata image routes (Breaking)**

  * Affects: `opengraph-image`, `twitter-image`, `icon`, `apple-icon`.
  * **Was:** `params` and `id` were plain values.
  * **Now:** These props are Promises; `generateImageMetadata` stays sync, but the image function receives `params`/`id` as async. ([Next.js][1])
  * **Action:** Mark image functions `async` and `await params` / `await id`.

* **Async `id` for `sitemap` (Breaking)**

  * **Was:** `id` from `generateSitemaps` passed into `sitemap` as a number.
  * **Now:** `id` is a `Promise<number>`. ([Next.js][1])
  * **Action:** `await id` inside `sitemap`.

---

### 1.3 Bundler & build behavior that can break builds

* **Turbopack is the default bundler for dev *and* build (Breaking for webpack-heavy setups)**

  * **Was:** Webpack default; Turbopack opt-in (`--turbopack` / `--turbo`).
  * **Now:** Turbopack is default for `next dev` and `next build`. `experimental.turbopack` config is gone; there’s a top-level `turbopack` option instead. ([Next.js][1])
  * If a **custom `webpack` config** is detected, `next build` with default settings **fails** to avoid misconfigurations. ([Next.js][1])
  * **Action:**

    * Remove `--turbopack` from scripts and use:

      ```json
      { "scripts": { "dev": "next dev", "build": "next build" } }
      ```
    * Either:

      * Fully migrate to Turbopack via `nextConfig.turbopack = { ... }`, or
      * Stick with Webpack by using `next build --webpack` and/or keeping Turbopack only for dev. ([Next.js][1])

* **Parallel routes now *require* `default.js` (Breaking when using `@slot`)**

  * **Was:** Parallel route slots could omit `default.js`.
  * **Now:** Every parallel route slot must have an explicit `default` file or the build fails. ([Next.js][1])
  * **Action:** For each `app/@slot`, add:

    ```tsx
    // app/@slot/default.tsx
    import { notFound } from 'next/navigation'

    export default function Default() {
      notFound()        // or `return null`
    }
    ```

---

### 1.4 Image / caching defaults that are marked “Breaking”

All of these are behavior changes that can break specific setups:

* **Local images with query strings require config (Breaking)**

  * **Was:** `/assets/photo?v=1` just worked.
  * **Now:** You must whitelist patterns with `images.localPatterns.search` to avoid enumeration attacks. ([Next.js][1])
  * **Action:** In `next.config`:

    ```ts
    images: {
      localPatterns: [{ pathname: '/assets/**', search: '?v=1' }],
    }
    ```

* **`images.minimumCacheTTL` default changed (Breaking)**

  * **Was:** 60 seconds.
  * **Now:** 4 hours (14400s). ([Next.js][1])
  * **Action:** If you relied on very frequent image revalidation, explicitly set `minimumCacheTTL: 60`.

* **`images.imageSizes` default changed (Breaking)**

  * **Was:** Included `16`px.
  * **Now:** `16` removed from the default sizes; cuts down `srcset` noise. ([Next.js][1])
  * **Action:** If you really use 16px images, define your own `imageSizes`.

* **`images.qualities` default changed (Breaking)**

  * **Was:** Conceptually all qualities allowed.
  * **Now:** Default is `[75]` only; other requested qualities get coerced to the nearest configured value. ([Next.js][1])

* **Local IP optimization blocked by default (Breaking)**

  * **Was:** You could optimize images from local IPs without extra config.
  * **Now:** New security restriction blocks this; must enable `images.dangerouslyAllowLocalIP` explicitly (for private networks only). ([Next.js][1])

* **`images.maximumRedirects` default changed (Breaking)**

  * **Was:** Unlimited redirects.
  * **Now:** Default is **3**. You can set to `0` (disable) or increase for edge cases. ([Next.js][1])

---

### 1.5 Removed APIs and config (from “Removals” table)

If you use any of these, upgrading will break you until you migrate:

* **AMP support completely removed**

  * No `next/amp`, no `useAmp`, no `config = { amp: true }`, no `amp` section in `next.config`. ([Next.js][1])
  * **Action:** Drop AMP and rely on normal Next.js performance optimizations.

* **`next lint` command removed**

  * `next build` also no longer lints.
  * **Action:** Run ESLint or Biome directly and/or use the codemod:

    ````bash
    npx @next/codemod@canary next-lint-to-eslint-cli .
    ``` :contentReference[oaicite:18]{index=18}  

    ````

* **`serverRuntimeConfig` / `publicRuntimeConfig` removed**

  * Must switch to env vars (`process.env`, `NEXT_PUBLIC_*`) and optionally `connection()` to ensure runtime reads. ([Next.js][1])

* **`experimental.turbopack`, `experimental.dynamicIO`, `experimental.ppr`, `experimental_ppr` exports removed**

  * `dynamicIO` → `cacheComponents` flag.
  * PPR flags/exports removed in favor of Cache Components. ([Next.js][1])

* **`unstable_rootParams` removed** – replacement API TBD. ([Next.js][1])

---

## 2. High-impact behavior & config changes (can break assumptions / tooling)

These are mostly from the official “Behavior changes” table. ([Next.js][2])

* **Bundler default: Turbopack**

  * Already covered above, but from a behavior POV: all new apps and most commands assume Turbopack. Webpack is an opt-out via `--webpack`.

* **`revalidateTag()` signature changed**

  * **Was:** `revalidateTag(tag)`
  * **Now:** `revalidateTag(tag, cacheLifeProfile)` where the second arg is a `cacheLife` profile (`'max'`, `'hours'`, `'days'`, or a custom profile / inline object). Single-arg form is deprecated. ([Next.js][1])

* **Prefetch behavior rewritten**

  * Layout dedup + incremental prefetching; more, smaller prefetch requests, but lower total transfer size and much better nav behavior. ([Next.js][1])
  * **Action:** Mostly none, but reconsider any monitoring that assumes particular prefetch patterns.

* **Dev/build output directories & lockfile**

  * `next dev` outputs to `.next/dev`; `next build` keeps regular `.next`. A lockfile prevents multiple dev/build instances. ([Next.js][1])
  * **Action:** Update tooling that inspects `.next` (e.g., custom tracing commands, scripts that delete build artifacts).

* **`@next/eslint-plugin-next` defaults to Flat Config**

  * Aligns with ESLint v10 dropping legacy config. ([Next.js][1])
  * **Action:** If you’re still on `.eslintrc`, plan to migrate to `eslint.config.mjs`.

* **Scroll behavior no longer overridden by default**

  * **Was:** Next.js temporarily set `scroll-behavior: auto` on navigation even if you’ve set `smooth`, then restored it.
  * **Now:** Next.js does *not* override your `scroll-behavior`. To get old behavior, you explicitly add `data-scroll-behavior="smooth"` to `<html>`. ([Next.js][1])

* **Babel in Turbopack**

  * Turbopack now automatically enables Babel if it finds a config instead of erroring. ([Next.js][2])

* **Modern Sass loader**

  * `sass-loader` bumped to v16, supporting modern Sass syntax; Turbopack doesn’t support `~` imports, so you may have to update `@import '~pkg/...'` to `@import 'pkg/...'` or use `turbopack.resolveAlias`. ([Next.js][1])

* **Terminal/build output revamped**

  * Dev and build logs now show where time is spent per phase; some metrics like `First Load JS`/`size` were removed in favor of Lighthouse / Vercel Analytics. ([Next.js][1])

---

## 3. Deprecations (will become breaking later)

From the official “Deprecations” table. ([Next.js][2])

* **`middleware.ts` filename deprecated in favor of `proxy.ts`**

  * `proxy.ts` runs on the Node runtime and makes the network boundary explicit.
  * `middleware.ts` still works *only* for Edge runtime cases and will be removed in a future major. ([Next.js][1])
  * **Action now:**

    * Rename `middleware.ts` → `proxy.ts`.
    * Rename exported function to `proxy`.
    * Update config flags like `skipMiddlewareUrlNormalize` → `skipProxyUrlNormalize`.

* **`next/legacy/image` deprecated**

  * Use `next/image` instead. ([Next.js][1])

* **`images.domains` config deprecated**

  * Use `images.remotePatterns` for more fine-grained, secure remote host whitelisting. ([Next.js][1])

---

## 4. New features & architecture (optional but high-value)

These are “severity-low” but architecturally important.

### 4.1 New caching model: Cache Components + improved APIs

* **Cache Components & `use cache`**

  * New programming model built on Partial Pre-Rendering (PPR) + React’s `use cache` directive.
  * Lets you mix static, cached, and dynamic content per route with explicit control, instead of global “this page is static/dynamic” toggles. ([Next.js][3])
  * **Config:** `cacheComponents: true` in `next.config` to opt in. ([Next.js][1])

* **Refined caching APIs**

  * `revalidateTag(tag, cacheLifeProfile)` – updated signature.
  * New `updateTag()` and `refresh()` for server-side cache invalidation and router refresh semantics. ([Next.js][1])

### 4.2 AI-assisted dev: DevTools MCP & MCP server

* **Next.js DevTools MCP**

  * Next.js 16 introduces a **Model Context Protocol (MCP)** integration so AI agents (like coding assistants) can introspect your Next app: routing, caching, logs, stack traces, active route context. ([Next.js][2])

* **Next.js MCP server for coding agents**

  * There’s a dedicated MCP server (`next-devtools-mcp`) that agents can run against your repo to automate upgrade/migration tasks and debugging. ([Next.js][1])

### 4.3 React & compiler

* **React 19.2 on the App Router**

  * Brings View Transitions, `useEffectEvent`, `Activity`, plus canary features being incrementally stabilized. ([Next.js][1])

* **React Compiler (stable integration)**

  * `reactCompiler: true` in `next.config` + `babel-plugin-react-compiler` gives automatic memoization without manual `useMemo`/`useCallback`. There’s a compile-time overhead trade-off. ([Next.js][1])

### 4.4 DX / build & tooling

* **Turbopack (stable)**

  * Now *the* default for dev & build; significant speedups vs Webpack (2–5× faster builds, up to 10× faster Fast Refresh, per Vercel’s numbers). ([Next.js][2])

* **Turbopack File System Caching (beta)**

  * Opt-in via `experimental.turbopackFileSystemCacheForDev: true` for much faster cold starts in large repos. ([Next.js][1])

* **Build Adapters API (alpha)**

  * New experimental API to plug custom adapters into the build pipeline (for platforms / custom deployments). ([Next.js][1])

* **Simplified `create-next-app` template**

  * New project template: App Router, TS, Tailwind, ESLint, better defaults baked in. ([Next.js][2])

* **Logging & performance telemetry improvements**

  * Dev/build logs now break down compile/render phases, plus nicer formatting and metrics. ([Next.js][2])

---

### 5. Quick “what do I actually need to do?” checklist

If you’re upgrading a reasonably modern Next 15 app:

1. **Upgrade stack** → Node 20.9+, TS 5.1+.
2. **Run the codemod** → `npx @next/codemod@canary upgrade latest` (handles Turbopack config, `next lint` removal, middleware→proxy, PPR flags, etc.). ([Next.js][1])
3. **Fix async APIs** → search for `cookies(`, `headers(`, `draftMode(`, `params`, `searchParams` and make them async.
4. **Check routing edge cases** → parallel routes (add `default.js`), any custom prefetch assumptions.
5. **Audit images config** → query-string local images, TTL, sizes, qualities, remote domains vs `remotePatterns`, local IP usage.
6. **Migrate runtime config** → runtimeConfig → env vars.
7. **Optionally opt into new toys** → `cacheComponents`, React Compiler, Turbopack FS cache, MCP DevTools.

[1]: https://nextjs.org/docs/app/guides/upgrading/version-16 "Upgrading: Version 16 | Next.js"
[2]: https://nextjs.org/blog/next-16 "Next.js 16 | Next.js"
[3]: https://nextjs.org/docs/app/getting-started/cache-components?utm_source=chatgpt.com "Getting Started: Cache Components"
