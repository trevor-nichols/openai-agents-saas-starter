# Problem Tracker

## 2025-11-08 – Pylance false positives (13 errors)

- **Status:** resolved
- **Symptoms:** VS Code/Pylance reported missing imports for `app.services.rate_limit_service`, unknown symbol `raise_rate_limit_http_error`, type mismatches in `app/cli/auth_cli.py`, and a bad signature for `app/utils/tools/web_search.py`.
- **Root cause:** The editor wasn’t loading the repo’s `extraPaths`, so anything under `anything-agents/` looked like an unresolved namespace; once imports failed, every re-exported symbol showed as unknown. The Tavily helper also lacked guards when the SDK returned `None`.
- **Fix:** Added a repo-level `pyrightconfig.json` that mirrors the settings in `pyproject.toml`, introduced `_require_settings()` so the CLI always passes a concrete `Settings` object into the Vault/key helpers, and hardened the Tavily response formatter to short-circuit on unexpected payloads.
- **Validation:** `hatch run lint` and `hatch run pyright` on 2025-11-08 both report 0 issues.
- **Follow-up:** Communicate to frontend/backend devs that VS Code will now pick up the right config automatically; no additional work required unless new diagnostics appear.


[{
	"resource": "/Volumes/AGENAI/Coding/Public Github/openai-agents-starter/anything-agents/app/api/dependencies/rate_limit.py",
	"owner": "Pylance3",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/microsoft/pylance-release/blob/main/docs/diagnostics/reportMissingImports.md",
			"scheme": "https",
			"authority": "github.com"
		}
	},
	"severity": 8,
	"message": "Import \"app.services.rate_limit_service\" could not be resolved",
	"source": "Pylance",
	"startLineNumber": 11,
	"startColumn": 6,
	"endLineNumber": 11,
	"endColumn": 37,
	"origin": "extHost1"
},{
	"resource": "/Volumes/AGENAI/Coding/Public Github/openai-agents-starter/anything-agents/app/api/v1/billing/router.py",
	"owner": "Pylance3",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/microsoft/pylance-release/blob/main/docs/diagnostics/reportAttributeAccessIssue.md",
			"scheme": "https",
			"authority": "github.com"
		}
	},
	"severity": 8,
	"message": "\"raise_rate_limit_http_error\" is unknown import symbol",
	"source": "Pylance",
	"startLineNumber": 11,
	"startColumn": 34,
	"endLineNumber": 11,
	"endColumn": 61,
	"origin": "extHost1"
},{
	"resource": "/Volumes/AGENAI/Coding/Public Github/openai-agents-starter/anything-agents/app/api/v1/billing/router.py",
	"owner": "Pylance3",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/microsoft/pylance-release/blob/main/docs/diagnostics/reportMissingImports.md",
			"scheme": "https",
			"authority": "github.com"
		}
	},
	"severity": 8,
	"message": "Import \"app.services.rate_limit_service\" could not be resolved",
	"source": "Pylance",
	"startLineNumber": 37,
	"startColumn": 6,
	"endLineNumber": 37,
	"endColumn": 37,
	"origin": "extHost1"
},{
	"resource": "/Volumes/AGENAI/Coding/Public Github/openai-agents-starter/anything-agents/app/api/v1/chat/router.py",
	"owner": "Pylance3",
	"code": {
		"value": "reportAttributeAccessIssue",
		"target": {
			"$mid": 1,
			"path": "/microsoft/pylance-release/blob/main/docs/diagnostics/reportAttributeAccessIssue.md",
			"scheme": "https",
			"authority": "github.com"
		}
	},
	"severity": 8,
	"message": "\"raise_rate_limit_http_error\" is unknown import symbol",
	"source": "Pylance",
	"startLineNumber": 10,
	"startColumn": 34,
	"endLineNumber": 10,
	"endColumn": 61,
	"origin": "extHost1"
},{
	"resource": "/Volumes/AGENAI/Coding/Public Github/openai-agents-starter/anything-agents/app/api/v1/chat/router.py",
	"owner": "Pylance3",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/microsoft/pylance-release/blob/main/docs/diagnostics/reportMissingImports.md",
			"scheme": "https",
			"authority": "github.com"
		}
	},
	"severity": 8,
	"message": "Import \"app.services.rate_limit_service\" could not be resolved",
	"source": "Pylance",
	"startLineNumber": 15,
	"startColumn": 6,
	"endLineNumber": 15,
	"endColumn": 37,
	"origin": "extHost1"
},{
	"resource": "/Volumes/AGENAI/Coding/Public Github/openai-agents-starter/anything-agents/app/infrastructure/stripe/client.py",
	"owner": "Pylance3",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/microsoft/pylance-release/blob/main/docs/diagnostics/reportMissingImports.md",
			"scheme": "https",
			"authority": "github.com"
		}
	},
	"severity": 8,
	"message": "Import \"app.infrastructure.stripe.types\" could not be resolved",
	"source": "Pylance",
	"startLineNumber": 16,
	"startColumn": 6,
	"endLineNumber": 16,
	"endColumn": 37,
	"origin": "extHost1"
},{
	"resource": "/Volumes/AGENAI/Coding/Public Github/openai-agents-starter/anything-agents/app/infrastructure/stripe/client.py",
	"owner": "Pylance3",
	"code": {
		"value": "reportMissingImports",
		"target": {
			"$mid": 1,
			"path": "/microsoft/pylance-release/blob/main/docs/diagnostics/reportMissingImports.md",
			"scheme": "https",
			"authority": "github.com"
		}
	},
	"severity": 8,
	"message": "Import \"app.infrastructure.stripe.types\" could not be resolved",
	"source": "Pylance",
	"startLineNumber": 19,
	"startColumn": 6,
	"endLineNumber": 19,
	"endColumn": 37,
	"origin": "extHost1"
}]