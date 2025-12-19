# Image Streaming

Stream image generation and editing in real time with server-sent events. Learn more about image streaming.

## image_generation.partial_image

Emitted when a partial image is available during image generation streaming.

**b64_json**
*string*

Base64-encoded partial image data, suitable for rendering as an image.

**background**
*string*

The background setting for the requested image.

**created_at**
*integer*

The Unix timestamp when the event was created.

**output_format**
*string*

The output format for the requested image.

**partial_image_index**
*integer*

0-based index for the partial image (streaming).

**quality**
*string*

The quality setting for the requested image.

**size**
*string*

The size of the requested image.

**type**
*string*

The type of the event. Always image_generation.partial_image.

**OBJECT image_generation.partial_image**

```json
{
  "type": "image_generation.partial_image",
  "b64_json": "...",
  "created_at": 1620000000,
  "size": "1024x1024",
  "quality": "high",
  "background": "transparent",
  "output_format": "png",
  "partial_image_index": 0
}
```

## image_generation.completed

Emitted when image generation has completed and the final image is available.

**b64_json**
*string*

Base64-encoded image data, suitable for rendering as an image.

**background**
*string*

The background setting for the generated image.

**created_at**
*integer*

The Unix timestamp when the event was created.

**output_format**
*string*

The output format for the generated image.

**quality**
*string*

The quality setting for the generated image.

**size**
*string*

The size of the generated image.

**type**
*string*

The type of the event. Always image_generation.completed.

**usage**
*object*

For gpt-image-1 only, the token usage information for the image generation.

*   **input_tokens**
    *integer*

    The number of tokens (images and text) in the input prompt.

*   **input_tokens_details**
    *object*

    The input tokens detailed information for the image generation.

    *   **image_tokens**
        *integer*

        The number of image tokens in the input prompt.

    *   **text_tokens**
        *integer*

        The number of text tokens in the input prompt.

*   **output_tokens**
    *integer*

    The number of image tokens in the output image.

*   **total_tokens**
    *integer*

    The total number of tokens (images and text) used for the image generation.

**OBJECT image_generation.completed**

```json
{
  "type": "image_generation.completed",
  "b64_json": "...",
  "created_at": 1620000000,
  "size": "1024x1024",
  "quality": "high",
  "background": "transparent",
  "output_format": "png",
  "usage": {
    "total_tokens": 100,
    "input_tokens": 50,
    "output_tokens": 50,
    "input_tokens_details": {
      "text_tokens": 10,
      "image_tokens": 40
    }
  }
}
```

## image_edit.partial_image

Emitted when a partial image is available during image editing streaming.

**b64_json**
*string*

Base64-encoded partial image data, suitable for rendering as an image.

**background**
*string*

The background setting for the requested edited image.

**created_at**
*integer*

The Unix timestamp when the event was created.

**output_format**
*string*

The output format for the requested edited image.

**partial_image_index**
*integer*

0-based index for the partial image (streaming).

**quality**
*string*

The quality setting for the requested edited image.

**size**
*string*

The size of the requested edited image.

**type**
*string*

The type of the event. Always image_edit.partial_image.

**OBJECT image_edit.partial_image**

```json
{
  "type": "image_edit.partial_image",
  "b64_json": "...",
  "created_at": 1620000000,
  "size": "1024x1024",
  "quality": "high",
  "background": "transparent",
  "output_format": "png",
  "partial_image_index": 0
}
```

## image_edit.completed

Emitted when image editing has completed and the final image is available.

**b64_json**
*string*

Base64-encoded final edited image data, suitable for rendering as an image.

**background**
*string*

The background setting for the edited image.

**created_at**
*integer*

The Unix timestamp when the event was created.

**output_format**
*string*

The output format for the edited image.

**quality**
*string*

The quality setting for the edited image.

**size**
*string*

The size of the edited image.

**type**
*string*

The type of the event. Always image_edit.completed.

**usage**
*object*

For gpt-image-1 only, the token usage information for the image generation.

*   **input_tokens**
    *integer*

    The number of tokens (images and text) in the input prompt.

*   **input_tokens_details**
    *object*

    The input tokens detailed information for the image generation.

    *   **image_tokens**
        *integer*

        The number of image tokens in the input prompt.

    *   **text_tokens**
        *integer*

        The number of text tokens in the input prompt.

*   **output_tokens**
    *integer*

    The number of image tokens in the output image.

*   **total_tokens**
    *integer*

    The total number of tokens (images and text) used for the image generation.

**OBJECT image_edit.completed**

```json
{
  "type": "image_edit.completed",
  "b64_json": "...",
  "created_at": 1620000000,
  "size": "1024x1024",
  "quality": "high",
  "background": "transparent",
  "output_format": "png",
  "usage": {
    "total_tokens": 100,
    "input_tokens": 50,
    "output_tokens": 50,
    "input_tokens_details": {
      "text_tokens": 10,
      "image_tokens": 40
    }
  }
}
```