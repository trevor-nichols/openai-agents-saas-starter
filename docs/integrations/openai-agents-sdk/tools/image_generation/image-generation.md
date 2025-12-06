Image generation
================

Allow models to generate or edit images.

The image generation tool allows you to generate images using a text prompt, and optionally image inputs. It leverages the [GPT Image model](/docs/models/gpt-image-1), and automatically optimizes text inputs for improved performance.

To learn more about image generation, refer to our dedicated [image generation guide](/docs/guides/image-generation?image-generation-model=gpt-image-1&api=responses).

Usage
-----

When you include the `image_generation` tool in your request, the model can decide when and how to generate images as part of the conversation, using your prompt and any provided image inputs.

The `image_generation_call` tool call result will include a base64-encoded image.

Generate an image

```python
from openai import OpenAI
import base64

client = OpenAI() 

response = client.responses.create(
    model="gpt-5",
    input="Generate an image of gray tabby cat hugging an otter with an orange scarf",
    tools=[{"type": "image_generation"}],
)

# Save the image to a file
image_data = [
    output.result
    for output in response.output
    if output.type == "image_generation_call"
]
    
if image_data:
    image_base64 = image_data[0]
    with open("otter.png", "wb") as f:
        f.write(base64.b64decode(image_base64))
```

You can [provide input images](/docs/guides/image-generation?image-generation-model=gpt-image-1#edit-images) using file IDs or base64 data.

To force the image generation tool call, you can set the parameter `tool_choice` to `{"type": "image_generation"}`.

### Tool options

You can configure the following output options as parameters for the [image generation tool](/docs/api-reference/responses/create#responses-create-tools):

*   Size: Image dimensions (e.g., 1024x1024, 1024x1536)
*   Quality: Rendering quality (e.g. low, medium, high)
*   Format: File output format
*   Compression: Compression level (0-100%) for JPEG and WebP formats
*   Background: Transparent or opaque

`size`, `quality`, and `background` support the `auto` option, where the model will automatically select the best option based on the prompt.

For more details on available options, refer to the [image generation guide](/docs/guides/image-generation#customize-image-output).

### Revised prompt

When using the image generation tool, the mainline model (e.g. `gpt-4.1`) will automatically revise your prompt for improved performance.

You can access the revised prompt in the `revised_prompt` field of the image generation call:

```json
{
  "id": "ig_123",
  "type": "image_generation_call",
  "status": "completed",
  "revised_prompt": "A gray tabby cat hugging an otter. The otter is wearing an orange scarf. Both animals are cute and friendly, depicted in a warm, heartwarming style.",
  "result": "..."
}
```

### Prompting tips

Image generation works best when you use terms like "draw" or "edit" in your prompt.

For example, if you want to combine images, instead of saying "combine" or "merge", you can say something like "edit the first image by adding this element from the second image".

Multi-turn editing
------------------

You can iteratively edit images by referencing previous response or image IDs. This allows you to refine images across multiple turns in a conversation.

Using previous response ID

Multi-turn image generation

```python
from openai import OpenAI
import base64

client = OpenAI()

response = client.responses.create(
    model="gpt-5",
    input="Generate an image of gray tabby cat hugging an otter with an orange scarf",
    tools=[{"type": "image_generation"}],
)

image_data = [
    output.result
    for output in response.output
    if output.type == "image_generation_call"
]

if image_data:
    image_base64 = image_data[0]

    with open("cat_and_otter.png", "wb") as f:
        f.write(base64.b64decode(image_base64))

# Follow up

response_fwup = client.responses.create(
    model="gpt-5",
    previous_response_id=response.id,
    input="Now make it look realistic",
    tools=[{"type": "image_generation"}],
)

image_data_fwup = [
    output.result
    for output in response_fwup.output
    if output.type == "image_generation_call"
]

if image_data_fwup:
    image_base64 = image_data_fwup[0]
    with open("cat_and_otter_realistic.png", "wb") as f:
        f.write(base64.b64decode(image_base64))
```

Using image ID

Multi-turn image generation

```python
import openai
import base64

response = openai.responses.create(
    model="gpt-5",
    input="Generate an image of gray tabby cat hugging an otter with an orange scarf",
    tools=[{"type": "image_generation"}],
)

image_generation_calls = [
    output
    for output in response.output
    if output.type == "image_generation_call"
]

image_data = [output.result for output in image_generation_calls]

if image_data:
    image_base64 = image_data[0]

    with open("cat_and_otter.png", "wb") as f:
        f.write(base64.b64decode(image_base64))

# Follow up

response_fwup = openai.responses.create(
    model="gpt-5",
    input=[
        {
            "role": "user",
            "content": [{"type": "input_text", "text": "Now make it look realistic"}],
        },
        {
            "type": "image_generation_call",
            "id": image_generation_calls[0].id,
        },
    ],
    tools=[{"type": "image_generation"}],
)

image_data_fwup = [
    output.result
    for output in response_fwup.output
    if output.type == "image_generation_call"
]

if image_data_fwup:
    image_base64 = image_data_fwup[0]
    with open("cat_and_otter_realistic.png", "wb") as f:
        f.write(base64.b64decode(image_base64))
```

Streaming
---------

The image generation tool supports streaming partial images as the final result is being generated. This provides faster visual feedback for users and improves perceived latency.

You can set the number of partial images (1-3) with the `partial_images` parameter.

Stream an image

```python
from openai import OpenAI
import base64

client = OpenAI()

stream = client.images.generate(
    prompt="Draw a gorgeous image of a river made of white owl feathers, snaking its way through a serene winter landscape",
    model="gpt-image-1",
    stream=True,
    partial_images=2,
)

for event in stream:
    if event.type == "image_generation.partial_image":
        idx = event.partial_image_index
        image_base64 = event.b64_json
        image_bytes = base64.b64decode(image_base64)
        with open(f"river{idx}.png", "wb") as f:
            f.write(image_bytes)
```

The model used for the image generation process is always `gpt-image-1`, but these models can be used as the mainline model in the Responses API as they can reliably call the image generation tool when needed.

Starter repo cookbook (OpenAI Agents SaaS Starter)
-------------------------------------------------

Enable the tool for an agent

```python
# app/agents/my_agent/spec.py
from app.agents._shared.specs import AgentSpec


def get_agent_spec() -> AgentSpec:
    return AgentSpec(
        key="designer",
        display_name="Image Designer",
        description="Creates and edits marketing visuals.",
        model_key="code",  # uses settings.agent_code_model or agent_default_model
        tool_keys=("image_generation",),
        tool_configs={
            "image_generation": {
                "size": "1024x1024",
                "quality": "high",
                "format": "png",
                "background": "auto",
                # optional: "compression": 80, "partial_images": 2
            }
        },
        prompt_path=...,  # your prompt file
    )
```

Config defaults (can override via env / settings)

- `IMAGE_DEFAULT_SIZE` (default `1024x1024`)
- `IMAGE_DEFAULT_QUALITY` (default `high`)
- `IMAGE_DEFAULT_FORMAT` (default `png`)
- `IMAGE_DEFAULT_BACKGROUND` (default `auto`)
- `IMAGE_DEFAULT_COMPRESSION` (optional 0–100)
- `IMAGE_OUTPUT_MAX_MB` (default 6 MB guard)
- `IMAGE_MAX_PARTIAL_IMAGES` (default 2)

Storage + attachments

- Generated images are decoded and stored via the built-in storage service (MinIO/GCS/memory) and linked to the conversation/user/agent.
- Conversation messages carry `attachments` with `object_id`, filename, mime, size, presigned URL, and `tool_call_id`. Streaming events include attachments as they are stored.
- Images are **not** stored as base64 in Postgres; only metadata and storage references are persisted.
- Fallbacks: if storage fails, chat still returns text; we log `image.ingest_failed` with tool_call_id/tenant for debugging.

DX checklist

- Ensure `OPENAI_API_KEY` and storage provider env vars are set (`STORAGE_PROVIDER`, `MINIO_*` or `GCS_*`).
- Run migrations to add the `attachments` column: `just migrate` (or `hatch run migrate` with `DATABASE_URL` set).
- Add `image_generation` to agent `tool_keys`; use `tool_configs.image_generation` for per-agent overrides.
