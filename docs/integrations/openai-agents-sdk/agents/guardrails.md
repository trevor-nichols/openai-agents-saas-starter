Guardrails
GuardrailFunctionOutput dataclass
The output of a guardrail function.

Source code in src/agents/guardrail.py
output_info instance-attribute

output_info: Any
Optional information about the guardrail's output. For example, the guardrail could include information about the checks it performed and granular results.

tripwire_triggered instance-attribute

tripwire_triggered: bool
Whether the tripwire was triggered. If triggered, the agent's execution will be halted.

InputGuardrailResult dataclass
The result of a guardrail run.

Source code in src/agents/guardrail.py
guardrail instance-attribute

guardrail: InputGuardrail[Any]
The guardrail that was run.

output instance-attribute

output: GuardrailFunctionOutput
The output of the guardrail function.

OutputGuardrailResult dataclass
The result of a guardrail run.

Source code in src/agents/guardrail.py
guardrail instance-attribute

guardrail: OutputGuardrail[Any]
The guardrail that was run.

agent_output instance-attribute

agent_output: Any
The output of the agent that was checked by the guardrail.

agent instance-attribute

agent: Agent[Any]
The agent that was checked by the guardrail.

output instance-attribute

output: GuardrailFunctionOutput
The output of the guardrail function.

InputGuardrail dataclass
Bases: Generic[TContext]

Input guardrails are checks that run in parallel to the agent's execution. They can be used to do things like: - Check if input messages are off-topic - Take over control of the agent's execution if an unexpected input is detected

You can use the @input_guardrail() decorator to turn a function into an InputGuardrail, or create an InputGuardrail manually.

Guardrails return a GuardrailResult. If result.tripwire_triggered is True, the agent's execution will immediately stop, and an InputGuardrailTripwireTriggered exception will be raised

Source code in src/agents/guardrail.py
guardrail_function instance-attribute

guardrail_function: Callable[
    [
        RunContextWrapper[TContext],
        Agent[Any],
        str | list[TResponseInputItem],
    ],
    MaybeAwaitable[GuardrailFunctionOutput],
]
A function that receives the agent input and the context, and returns a GuardrailResult. The result marks whether the tripwire was triggered, and can optionally include information about the guardrail's output.

name class-attribute instance-attribute

name: str | None = None
The name of the guardrail, used for tracing. If not provided, we'll use the guardrail function's name.

OutputGuardrail dataclass
Bases: Generic[TContext]

Output guardrails are checks that run on the final output of an agent. They can be used to do check if the output passes certain validation criteria

You can use the @output_guardrail() decorator to turn a function into an OutputGuardrail, or create an OutputGuardrail manually.

Guardrails return a GuardrailResult. If result.tripwire_triggered is True, an OutputGuardrailTripwireTriggered exception will be raised.

Source code in src/agents/guardrail.py
guardrail_function instance-attribute

guardrail_function: Callable[
    [RunContextWrapper[TContext], Agent[Any], Any],
    MaybeAwaitable[GuardrailFunctionOutput],
]
A function that receives the final agent, its output, and the context, and returns a GuardrailResult. The result marks whether the tripwire was triggered, and can optionally include information about the guardrail's output.

name class-attribute instance-attribute

name: str | None = None
The name of the guardrail, used for tracing. If not provided, we'll use the guardrail function's name.

input_guardrail

input_guardrail(
    func: _InputGuardrailFuncSync[TContext_co],
) -> InputGuardrail[TContext_co]

input_guardrail(
    func: _InputGuardrailFuncAsync[TContext_co],
) -> InputGuardrail[TContext_co]

input_guardrail(
    *, name: str | None = None
) -> Callable[
    [
        _InputGuardrailFuncSync[TContext_co]
        | _InputGuardrailFuncAsync[TContext_co]
    ],
    InputGuardrail[TContext_co],
]

input_guardrail(
    func: _InputGuardrailFuncSync[TContext_co]
    | _InputGuardrailFuncAsync[TContext_co]
    | None = None,
    *,
    name: str | None = None,
) -> (
    InputGuardrail[TContext_co]
    | Callable[
        [
            _InputGuardrailFuncSync[TContext_co]
            | _InputGuardrailFuncAsync[TContext_co]
        ],
        InputGuardrail[TContext_co],
    ]
)
Decorator that transforms a sync or async function into an InputGuardrail. It can be used directly (no parentheses) or with keyword args, e.g.:


@input_guardrail
def my_sync_guardrail(...): ...

@input_guardrail(name="guardrail_name")
async def my_async_guardrail(...): ...
Source code in src/agents/guardrail.py
output_guardrail

output_guardrail(
    func: _OutputGuardrailFuncSync[TContext_co],
) -> OutputGuardrail[TContext_co]

output_guardrail(
    func: _OutputGuardrailFuncAsync[TContext_co],
) -> OutputGuardrail[TContext_co]

output_guardrail(
    *, name: str | None = None
) -> Callable[
    [
        _OutputGuardrailFuncSync[TContext_co]
        | _OutputGuardrailFuncAsync[TContext_co]
    ],
    OutputGuardrail[TContext_co],
]

output_guardrail(
    func: _OutputGuardrailFuncSync[TContext_co]
    | _OutputGuardrailFuncAsync[TContext_co]
    | None = None,
    *,
    name: str | None = None,
) -> (
    OutputGuardrail[TContext_co]
    | Callable[
        [
            _OutputGuardrailFuncSync[TContext_co]
            | _OutputGuardrailFuncAsync[TContext_co]
        ],
        OutputGuardrail[TContext_co],
    ]
)
Decorator that transforms a sync or async function into an OutputGuardrail. It can be used directly (no parentheses) or with keyword args, e.g.:


@output_guardrail
def my_sync_guardrail(...): ...

@output_guardrail(name="guardrail_name")
async def my_async_guardrail(...): ...
Source code in src/agents/guardrail.py
