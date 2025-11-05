Exceptions
RunErrorDetails dataclass
Data collected from an agent run when an exception occurs.

Source code in src/agents/exceptions.py
AgentsException
Bases: Exception

Base class for all exceptions in the Agents SDK.

Source code in src/agents/exceptions.py
MaxTurnsExceeded
Bases: AgentsException

Exception raised when the maximum number of turns is exceeded.

Source code in src/agents/exceptions.py
ModelBehaviorError
Bases: AgentsException

Exception raised when the model does something unexpected, e.g. calling a tool that doesn't exist, or providing malformed JSON.

Source code in src/agents/exceptions.py
UserError
Bases: AgentsException

Exception raised when the user makes an error using the SDK.

Source code in src/agents/exceptions.py
InputGuardrailTripwireTriggered
Bases: AgentsException

Exception raised when a guardrail tripwire is triggered.

Source code in src/agents/exceptions.py
guardrail_result instance-attribute

guardrail_result: InputGuardrailResult = guardrail_result
The result data of the guardrail that was triggered.

OutputGuardrailTripwireTriggered
Bases: AgentsException

Exception raised when a guardrail tripwire is triggered.

Source code in src/agents/exceptions.py
guardrail_result instance-attribute

guardrail_result: OutputGuardrailResult = guardrail_result
The result data of the guardrail that was triggered.

