# Milestone: Service Wiring Decoupling

## Background

The backend previously relied on pragmatic coupling via module-level singletons (`get_*` helpers) that materialized repositories, Redis clients, and settings on import. We introduced the new `ApplicationContainer` to centralize wiring, but several services still bypass it. This tracker outlines the remaining work required to fully align the codebase with the container pattern and eliminate hidden globals.

## Goals

1. Every long-lived service or infrastructure handle is provided by the application container (or explicit dependency injection in tests).
2. Module-level accessors become thin proxies that simply pull configured instances from the container.
3. Tests can override services by swapping container entries rather than monkeypatching private module state.

## Task Board

| # | Task | Owner | Status | Notes |
|---|------|-------|--------|-------|
| 1 | **AuthService containerization** – refactor `app/services/auth_service.py` so construction happens via the container/lifespan wiring instead of `auth_service = AuthService()` at import. |  | ☑ Done | Proxy now resolves through `get_auth_service()` and `main.py` wires the instance with container-provided deps (2025-11-11). |
| 2 | **GeoIP service provider** – replace `_GEOIP_SINGLETON` with a container-provided instance (defaulting to `NullGeoIPService`). |  | ☑ Done | Container owns the GeoIP service; callers use `get_geoip_service()` which simply returns the configured instance (2025-11-11). |
| 3 | **UserService factory refactor** – remove `_DEFAULT_SERVICE` in `user_service.py`. Build the service in lifespan wiring with explicit repository + Redis throttle dependencies; expose container accessor. |  | ☑ Done | `build_user_service()` now feeds container wiring; tests rely on `reset_container()` (2025-11-11). |
| 4 | **Password recovery service** – convert `get_password_recovery_service` to container-backed wiring, replacing `_DEFAULT_SERVICE`. |  | ☑ Done | Container now owns `password_recovery_service`; builder accepts explicit deps for tests/CLI (2025-11-11). |
| 5 | **Email verification service** – same approach as above; ensure signup flows receive the container-managed service. |  | ☑ Done | Container now owns `email_verification_service`; startup wires it with shared user repo (2025-11-11). |
| 6 | **Session + service account helpers** – audit `app/services/auth/session_service.py` and `app/services/auth/service_account_service.py` for implicit globals (e.g., default registries, user service lookups) and route them through the container. |  | ☑ Done | Container now owns session + service-account services; AuthService consumes injected instances (2025-11-11). |
| 7 | **Documentation + fixtures** – update `docs/frontend/data-access.md` (if impacted) and backend architecture docs to describe the container pattern; ensure pytest fixtures rely on `reset_container()` rather than monkeypatching. |  | ☑ Done | Added container guidelines to `docs/architecture/authentication-ed25519.md` and moved auth/unit fixtures to `get_container()` overrides (2025-11-11). |

## Next Steps

Work through the tasks in order, updating this tracker as items move to “In Progress” or “Complete.” Each step should include:

- Code changes (service/module refactor).
- Adjusted startup wiring and tests.
- Notes/comments here summarizing what changed and linking to PRs or commits when applicable.

When every row is checked off, the milestone is complete and we can archive this tracker under `docs/trackers/complete/`.
