# Embeddings
Get a vector representation of a given input that can be easily consumed by machine learning models and algorithms. Related guide: [Embeddings](https://platform.openai.com/docs/guides/embeddings)

***

## Create embeddings
`POST` https://api.openai.com/v1/embeddings

Creates an embedding vector representing the input text.

### Request body

| Parameter | Type | Description |
| --- | --- | --- |
| `input` | string or array | **Required**<br>Input text to embed, encoded as a string or array of tokens. To embed multiple inputs in a single request, pass an array of strings or array of token arrays. The input must not exceed the max input tokens for the model (8192 tokens for all embedding models), cannot be an empty string, and any array must be 2048 dimensions or less. [Example Python code for counting tokens.](https://github.com/openai/openai-cookbook/blob/main/examples/how_to_count_tokens_with_tiktoken.ipynb) In addition to the per-input token limit, all embedding models enforce a maximum of 300,000 tokens summed across all inputs in a single request. |
| `model` | string | **Required**<br>ID of the model to use. You can use the [List models API](https://platform.openai.com/docs/api-reference/models/list) to see all of your available models, or see our [Model overview](https://platform.openai.com/docs/models/overview) for descriptions of them. |
| `dimensions` | integer | **Optional**<br>The number of dimensions the resulting output embeddings should have. Only supported in `text-embedding-3` and later models. |
| `encoding_format`| string | **Optional**<br>Defaults to `float`<br>The format to return the embeddings in. Can be either `float` or `base64`. |
| `user` | string | **Optional**<br>A unique identifier representing your end-user, which can help OpenAI to monitor and detect abuse. [Learn more.](https://platform.openai.com/docs/guides/safety-best-practices/end-user-ids) |

### Returns
A list of embedding objects.

### Example request
```bash
curl https://api.openai.com/v1/embeddings \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "The food was delicious and the waiter...",
    "model": "text-embedding-ada-002",
    "encoding_format": "float"
  }'
```

### Response
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [
        0.0023064255,
        -0.009327292,
        // ... (1536 floats total for ada-002)
        -0.0028842222,
      ],
      "index": 0
    }
  ],
  "model": "text-embedding-ada-002",
  "usage": {
    "prompt_tokens": 8,
    "total_tokens": 8
  }
}
```

***

### The embedding object
Represents an embedding vector returned by embedding endpoint.

| Parameter | Type | Description |
| --- | --- | --- |
| `embedding` | array | The embedding vector, which is a list of floats. The length of vector depends on the model as listed in the [embedding guide](https://platform.openai.com/docs/guides/embeddings). |
| `index` | integer | The index of the embedding in the list of embeddings. |
| `object` | string | The object type, which is always `"embedding"`. |

#### OBJECT The embedding object
```json
{
  "object": "embedding",
  "embedding": [
    0.0023064255,
    -0.009327292,
    // ... (1536 floats total for ada-002)
    -0.0028842222,
  ],
  "index": 0
}
```