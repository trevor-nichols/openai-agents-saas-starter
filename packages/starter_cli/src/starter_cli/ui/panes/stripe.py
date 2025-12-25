from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    Collapsible,
    DataTable,
    Input,
    OptionList,
    RadioButton,
    RadioSet,
    Static,
    Switch,
)

from starter_cli.core import CLIContext
from starter_cli.services.infra.ops_models import mask_value
from starter_cli.services.stripe.stripe_status import REQUIRED_ENV_KEYS, StripeStatus
from starter_cli.ui.prompt_controller import PromptController
from starter_cli.ui.workflow_runner import WorkflowResult, WorkflowRunner
from starter_cli.workflows.home.hub import HubService
from starter_cli.workflows.stripe import (
    DEFAULT_WEBHOOK_FORWARD_URL,
    DISPATCH_STATUS_CHOICES,
    DispatchListConfig,
    DispatchReplayConfig,
    StripeSetupConfig,
    WebhookSecretConfig,
    run_dispatch_list,
    run_dispatch_replay,
    run_dispatch_validate_fixtures,
    run_stripe_setup,
    run_webhook_secret,
)


class StripePane(Vertical):
    def __init__(self, ctx: CLIContext, hub: HubService) -> None:
        super().__init__(id="stripe", classes="section-pane")
        self.ctx = ctx
        self.hub = hub
        self._env_values: dict[str, str | None] = {}
        self._prompt_controller = PromptController(self, prefix="stripe")
        self._runner = WorkflowRunner(
            ctx=self.ctx,
            prompt_controller=self._prompt_controller,
            on_status=self._set_status,
            on_output=self._set_output,
            on_complete=self._handle_runner_complete,
            on_state_change=self._set_action_state,
        )
        self._refresh_task: asyncio.Task[None] | None = None

    def compose(self) -> ComposeResult:
        yield Static("Stripe", classes="section-title")
        yield Static("Stripe billing configuration overview.", classes="section-description")
        with Horizontal(classes="ops-actions"):
            yield Button("Refresh", id="stripe-refresh", variant="primary")
            yield Button("Run Stripe Setup", id="stripe-run-setup", variant="primary")
            yield Button("Capture Webhook Secret", id="stripe-run-webhook")
        with Horizontal(classes="stripe-options-actions"):
            yield Static("Setup options", classes="section-summary")
            yield Button("Reset defaults", id="stripe-reset-defaults", classes="stripe-reset")
        with Collapsible(
            title="Stripe setup options",
            id="stripe-options-collapsible",
            collapsed=True,
        ):
            with Horizontal(classes="stripe-options"):
                yield Static("Currency", classes="wizard-control-label")
                yield Input(id="stripe-currency")
                yield Static("Trial days", classes="wizard-control-label")
                yield Input(id="stripe-trial-days")
            with Horizontal(classes="stripe-options"):
                yield Static("Secret key", classes="wizard-control-label")
                yield Input(id="stripe-secret-key")
                yield Static("Webhook secret", classes="wizard-control-label")
                yield Input(id="stripe-webhook-secret")
            with Horizontal(classes="stripe-options"):
                yield Static("Webhook forward URL", classes="wizard-control-label")
                yield Input(id="stripe-forward-url")
            with Horizontal(classes="stripe-options"):
                yield Static(
                    "Plan overrides (code=cents, comma-separated)",
                    classes="wizard-control-label",
                )
                yield Input(id="stripe-plan-overrides")
            with Horizontal(classes="stripe-options"):
                yield Static("Non-interactive", classes="wizard-control-label")
                yield Switch(value=False, id="stripe-non-interactive")
                yield Static("Auto webhook", classes="wizard-control-label")
                yield RadioSet(
                    RadioButton("Yes", id="stripe-auto-webhook-yes"),
                    RadioButton("No", id="stripe-auto-webhook-no"),
                    id="stripe-auto-webhook",
                )
                yield Static("Skip Postgres", classes="wizard-control-label")
                yield RadioSet(
                    RadioButton("Yes", id="stripe-skip-postgres-yes"),
                    RadioButton("No", id="stripe-skip-postgres-no"),
                    id="stripe-skip-postgres",
                )
            with Horizontal(classes="stripe-options"):
                yield Static("Skip Stripe CLI", classes="wizard-control-label")
                yield RadioSet(
                    RadioButton("Yes", id="stripe-skip-cli-yes"),
                    RadioButton("No", id="stripe-skip-cli-no"),
                    id="stripe-skip-cli",
                )
                yield Static("Webhook print-only", classes="wizard-control-label")
                yield RadioSet(
                    RadioButton("Yes", id="stripe-webhook-print-yes"),
                    RadioButton("No", id="stripe-webhook-print-no"),
                    id="stripe-webhook-print",
                )
        with Collapsible(
            title="Dispatch tools",
            id="stripe-dispatch-collapsible",
            collapsed=True,
        ):
            with Horizontal(classes="stripe-options"):
                yield Static("List status", classes="wizard-control-label")
                yield Input(id="stripe-dispatch-status")
                yield Static("Handler", classes="wizard-control-label")
                yield Input(id="stripe-dispatch-handler")
                yield Static("Limit", classes="wizard-control-label")
                yield Input(id="stripe-dispatch-limit")
                yield Static("Page", classes="wizard-control-label")
                yield Input(id="stripe-dispatch-page")
            with Horizontal(classes="stripe-options"):
                yield Static("Replay dispatch IDs", classes="wizard-control-label")
                yield Input(id="stripe-replay-dispatch-ids")
                yield Static("Replay event IDs", classes="wizard-control-label")
                yield Input(id="stripe-replay-event-ids")
            with Horizontal(classes="stripe-options"):
                yield Static("Replay status", classes="wizard-control-label")
                yield Input(id="stripe-replay-status")
                yield Static("Replay handler", classes="wizard-control-label")
                yield Input(id="stripe-replay-handler")
                yield Static("Replay limit", classes="wizard-control-label")
                yield Input(id="stripe-replay-limit")
                yield Static("Assume yes", classes="wizard-control-label")
                yield Switch(value=False, id="stripe-replay-yes")
            with Horizontal(classes="stripe-options"):
                yield Static("Fixtures path", classes="wizard-control-label")
                yield Input(id="stripe-fixtures-path")
            with Horizontal(classes="stripe-options"):
                yield Button("List Dispatches", id="stripe-dispatch-list")
                yield Button("Replay Dispatches", id="stripe-dispatch-replay")
                yield Button("Validate Fixtures", id="stripe-dispatch-validate")
        yield DataTable(id="stripe-table", zebra_stripes=True)
        yield Static("", id="stripe-output", classes="ops-output")
        with Vertical(id="stripe-prompt"):
            yield Static("", id="stripe-prompt-label")
            yield Static("", id="stripe-prompt-detail")
            yield Input(id="stripe-input")
            yield OptionList(id="stripe-options")
            with Horizontal(id="stripe-prompt-actions"):
                yield Button("Submit", id="stripe-submit", variant="primary")
                yield Button("Clear", id="stripe-clear")
            yield Static("", id="stripe-prompt-status", classes="section-footnote")
        yield Static("", id="stripe-status", classes="section-footnote")

    async def on_mount(self) -> None:
        self._configure_defaults()
        self._configure_dispatch_defaults()
        self._prompt_controller.set_visibility(False)
        self.set_interval(0.2, self._runner.poll_prompt)
        self.set_interval(0.4, self._runner.refresh_output)
        await self.refresh_data()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "stripe-refresh":
            await self.refresh_data()
        elif event.button.id == "stripe-run-setup":
            self._start_setup()
        elif event.button.id == "stripe-run-webhook":
            self._start_webhook()
        elif event.button.id == "stripe-reset-defaults":
            self._configure_defaults()
            self.query_one("#stripe-status", Static).update("Stripe defaults restored.")
        elif event.button.id == "stripe-dispatch-list":
            self._start_dispatch_list()
        elif event.button.id == "stripe-dispatch-replay":
            self._start_dispatch_replay()
        elif event.button.id == "stripe-dispatch-validate":
            self._start_dispatch_validate()
        elif event.button.id == "stripe-submit":
            self._prompt_controller.submit_current()
        elif event.button.id == "stripe-clear":
            self._prompt_controller.clear_input()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "stripe-input":
            self._prompt_controller.submit_current()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "stripe-options":
            return
        self._prompt_controller.submit_choice(event.option_index)

    async def refresh_data(self) -> None:
        snapshot = await asyncio.to_thread(self._load)
        self._env_values = snapshot.values
        table = self.query_one("#stripe-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Key", "Status", "Value")
        for key in REQUIRED_ENV_KEYS:
            value = self._env_values.get(key)
            status = "set" if value else "missing"
            display = mask_value(value)
            if key == "STRIPE_PRODUCT_PRICE_MAP" and value:
                display = "configured"
            table.add_row(key, status, display)
        enable_billing = snapshot.enable_billing
        if enable_billing:
            table.add_row("ENABLE_BILLING", "set", enable_billing)
        self.query_one("#stripe-status", Static).update("Stripe status loaded.")

    def _start_setup(self) -> None:
        config = self._build_setup_config()
        self._start_session("Stripe setup", lambda ctx: run_stripe_setup(ctx, config))

    def _start_webhook(self) -> None:
        config = self._build_webhook_config()
        self._start_session("Webhook secret", lambda ctx: run_webhook_secret(ctx, config))

    def _start_dispatch_list(self) -> None:
        config = self._build_dispatch_list_config()
        self._start_session("Dispatch list", lambda ctx: run_dispatch_list(ctx, config))

    def _start_dispatch_replay(self) -> None:
        config = self._build_dispatch_replay_config()
        self._start_session("Dispatch replay", lambda ctx: run_dispatch_replay(ctx, config))

    def _start_dispatch_validate(self) -> None:
        path = self._string_value(
            "stripe-fixtures-path",
            default="apps/api-service/tests/fixtures/stripe",
        )
        self._start_session(
            "Dispatch fixture validation",
            lambda ctx: run_dispatch_validate_fixtures(ctx, path),
        )

    def _start_session(self, label: str, runner) -> None:
        if not self._runner.start(label, runner):
            self._set_status("Stripe task already running.")
            return

    def _handle_runner_complete(self, result: WorkflowResult[object]) -> None:
        if result.label == "Stripe setup" and not result.error:
            self._refresh_task = asyncio.create_task(self.refresh_data())

    def _set_action_state(self, running: bool) -> None:
        self.query_one("#stripe-run-setup", Button).disabled = running
        self.query_one("#stripe-run-webhook", Button).disabled = running
        self.query_one("#stripe-dispatch-list", Button).disabled = running
        self.query_one("#stripe-dispatch-replay", Button).disabled = running
        self.query_one("#stripe-dispatch-validate", Button).disabled = running

    def _set_status(self, message: str) -> None:
        self.query_one("#stripe-status", Static).update(message)

    def _set_output(self, message: str) -> None:
        self.query_one("#stripe-output", Static).update(message)

    def _build_setup_config(self) -> StripeSetupConfig:
        currency = self._string_value("stripe-currency", default="usd")
        trial_days = self._int_value("stripe-trial-days", default=7)
        forward_url = self._string_value("stripe-forward-url", default=DEFAULT_WEBHOOK_FORWARD_URL)
        secret_key = self._string_value("stripe-secret-key", default="")
        webhook_secret = self._string_value("stripe-webhook-secret", default="")
        overrides = self._plan_overrides()
        non_interactive = self.query_one("#stripe-non-interactive", Switch).value
        auto_webhook = self._radio_bool("stripe-auto-webhook", default=True)
        skip_postgres = self._radio_bool("stripe-skip-postgres", default=False)
        skip_cli = self._radio_bool("stripe-skip-cli", default=False)
        return StripeSetupConfig(
            currency=currency,
            trial_days=trial_days,
            non_interactive=non_interactive,
            secret_key=secret_key or None,
            webhook_secret=webhook_secret or None,
            auto_webhook_secret=auto_webhook,
            webhook_forward_url=forward_url,
            plan_overrides=overrides,
            skip_postgres=skip_postgres,
            skip_stripe_cli=skip_cli,
        )

    def _build_webhook_config(self) -> WebhookSecretConfig:
        forward_url = self._string_value("stripe-forward-url", default=DEFAULT_WEBHOOK_FORWARD_URL)
        print_only = self._radio_bool("stripe-webhook-print", default=False)
        skip_cli = self._radio_bool("stripe-skip-cli", default=False)
        return WebhookSecretConfig(
            forward_url=forward_url,
            print_only=print_only,
            skip_stripe_cli=skip_cli,
        )

    def _string_value(self, input_id: str, *, default: str) -> str:
        field = self.query_one(f"#{input_id}", Input)
        value = field.value.strip()
        return value or default

    def _int_value(self, input_id: str, *, default: int) -> int:
        raw = self._string_value(input_id, default=str(default))
        try:
            return int(raw)
        except ValueError:
            self.query_one("#stripe-status", Static).update(
                f"Invalid numeric value for {input_id}; using default {default}."
            )
            return default

    def _radio_bool(self, radio_id: str, *, default: bool) -> bool:
        radio = self.query_one(f"#{radio_id}", RadioSet)
        selected = radio.pressed_button
        if selected is None or selected.id is None:
            return default
        return selected.id.endswith("yes")

    def _plan_overrides(self) -> list[str]:
        raw = self._string_value("stripe-plan-overrides", default="")
        if not raw:
            return []
        return [
            entry
            for entry in (part.strip() for part in raw.replace(",", " ").split())
            if entry
        ]

    def _build_dispatch_list_config(self) -> DispatchListConfig:
        status = self._string_value("stripe-dispatch-status", default="failed").strip()
        if status not in DISPATCH_STATUS_CHOICES and status != "all":
            status = "failed"
        handler = self._string_value("stripe-dispatch-handler", default="billing_sync")
        limit = self._int_value("stripe-dispatch-limit", default=20)
        page = self._int_value("stripe-dispatch-page", default=1)
        return DispatchListConfig(handler=handler, status=status, limit=limit, page=page)

    def _build_dispatch_replay_config(self) -> DispatchReplayConfig:
        dispatch_ids = self._split_list("stripe-replay-dispatch-ids")
        event_ids = self._split_list("stripe-replay-event-ids")
        status_raw = self._string_value("stripe-replay-status", default="")
        status = status_raw if status_raw in DISPATCH_STATUS_CHOICES else None
        handler = self._string_value("stripe-replay-handler", default="billing_sync")
        limit = self._int_value("stripe-replay-limit", default=5)
        assume_yes = self.query_one("#stripe-replay-yes", Switch).value
        return DispatchReplayConfig(
            dispatch_ids=dispatch_ids or None,
            event_ids=event_ids or None,
            status=status,
            limit=limit,
            handler=handler,
            assume_yes=assume_yes,
        )

    def _split_list(self, input_id: str) -> list[str]:
        raw = self._string_value(input_id, default="")
        if not raw:
            return []
        parts = [part.strip() for part in raw.replace(";", ",").split(",")]
        return [part for part in parts if part]

    def _configure_defaults(self) -> None:
        self.query_one("#stripe-currency", Input).value = "usd"
        self.query_one("#stripe-trial-days", Input).value = "7"
        self.query_one("#stripe-forward-url", Input).value = DEFAULT_WEBHOOK_FORWARD_URL
        self.query_one("#stripe-plan-overrides", Input).value = ""
        self.query_one("#stripe-secret-key", Input).password = True
        self.query_one("#stripe-webhook-secret", Input).password = True
        self.query_one("#stripe-secret-key", Input).value = ""
        self.query_one("#stripe-webhook-secret", Input).value = ""
        self.query_one("#stripe-non-interactive", Switch).value = False
        self._set_radio_default("stripe-auto-webhook", yes_default=True)
        self._set_radio_default("stripe-skip-postgres", yes_default=False)
        self._set_radio_default("stripe-skip-cli", yes_default=False)
        self._set_radio_default("stripe-webhook-print", yes_default=False)

    def _configure_dispatch_defaults(self) -> None:
        self.query_one("#stripe-dispatch-status", Input).value = "failed"
        self.query_one("#stripe-dispatch-handler", Input).value = "billing_sync"
        self.query_one("#stripe-dispatch-limit", Input).value = "20"
        self.query_one("#stripe-dispatch-page", Input).value = "1"
        self.query_one("#stripe-replay-status", Input).value = ""
        self.query_one("#stripe-replay-handler", Input).value = "billing_sync"
        self.query_one("#stripe-replay-limit", Input).value = "5"
        self.query_one("#stripe-replay-yes", Switch).value = False
        self.query_one("#stripe-fixtures-path", Input).value = (
            "apps/api-service/tests/fixtures/stripe"
        )

    def _set_radio_default(self, radio_id: str, *, yes_default: bool) -> None:
        yes_id = f"#{radio_id}-yes"
        no_id = f"#{radio_id}-no"
        button_id = yes_id if yes_default else no_id
        button = self.query_one(button_id, RadioButton)
        button.value = True

    def _load(self) -> StripeStatus:
        return self.hub.load_stripe()


__all__ = ["StripePane"]
