# Vector store files

Vector store files represent files inside a vector store.

**Related guide:** File Search

---

## Create vector store file
`POST` `https://api.openai.com/v1/vector_stores/{vector_store_id}/files`

Create a vector store file by attaching a File to a vector store.

### Path parameters

*   **vector_store_id** `string` (Required)
    The ID of the vector store for which to create a File.

### Request body

*   **file_id** `string` (Required)
    A File ID that the vector store should use. Useful for tools like `file_search` that can access files.

*   **attributes** `map` (Optional)
    Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard. Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters, booleans, or numbers.

*   **chunking_strategy** `object` (Optional)
    The chunking strategy used to chunk the file(s). If not set, will use the auto strategy.

    **Possible types:**
    *   **Auto Chunking Strategy** `object`
        The default strategy. This strategy currently uses a `max_chunk_size_tokens` of 800 and `chunk_overlap_tokens` of 400.
        *   **type** `string` (Required): Always `auto`.
    *   **Static Chunking Strategy** `object`
        Customize your own chunking strategy by setting chunk size and chunk overlap.
        *   **static** `object` (Required)
            *   **chunk_overlap_tokens** `integer` (Required): The number of tokens that overlap between chunks. The default value is 400. Note that the overlap must not exceed half of `max_chunk_size_tokens`.
            *   **max_chunk_size_tokens** `integer` (Required): The maximum number of tokens in each chunk. The default value is 800. The minimum value is 100 and the maximum value is 4096.
        *   **type** `string` (Required): Always `static`.

### Returns
A vector store file object.

### Example request
```bash
curl https://api.openai.com/v1/vector_stores/vs_abc123/files \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -H "OpenAI-Beta: assistants=v2" \
    -d '{
      "file_id": "file-abc123"
    }'
```

### Response
```json
{
  "id": "file-abc123",
  "object": "vector_store.file",
  "created_at": 1699061776,
  "usage_bytes": 1234,
  "vector_store_id": "vs_abcd",
  "status": "completed",
  "last_error": null
}
```

---

## List vector store files
`GET` `https://api.openai.com/v1/vector_stores/{vector_store_id}/files`

Returns a list of vector store files.

### Path parameters

*   **vector_store_id** `string` (Required)
    The ID of the vector store that the files belong to.

### Query parameters

*   **after** `string` (Optional)
    A cursor for use in pagination. `after` is an object ID that defines your place in the list. For instance, if you make a list request and receive 100 objects, ending with obj_foo, your subsequent call can include `after=obj_foo` in order to fetch the next page of the list.

*   **before** `string` (Optional)
    A cursor for use in pagination. `before` is an object ID that defines your place in the list. For instance, if you make a list request and receive 100 objects, starting with obj_foo, your subsequent call can include `before=obj_foo` in order to fetch the previous page of the list.

*   **filter** `string` (Optional)
    Filter by file status. One of `in_progress`, `completed`, `failed`, `cancelled`.

*   **limit** `integer` (Optional)
    Defaults to 20. A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 20.

*   **order** `string` (Optional)
    Defaults to `desc`. Sort order by the `created_at` timestamp of the objects. `asc` for ascending order and `desc` for descending order.

### Returns
A list of vector store file objects.

### Example request
```bash
curl https://api.openai.com/v1/vector_stores/vs_abc123/files \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2"
```

### Response
```json
{
  "object": "list",
  "data": [
    {
      "id": "file-abc123",
      "object": "vector_store.file",
      "created_at": 1699061776,
      "vector_store_id": "vs_abc123"
    },
    {
      "id": "file-abc456",
      "object": "vector_store.file",
      "created_at": 1699061776,
      "vector_store_id": "vs_abc123"
    }
  ],
  "first_id": "file-abc123",
  "last_id": "file-abc456",
  "has_more": false
}
```

---

## Retrieve vector store file
`GET` `https://api.openai.com/v1/vector_stores/{vector_store_id}/files/{file_id}`

Retrieves a vector store file.

### Path parameters

*   **file_id** `string` (Required)
    The ID of the file being retrieved.

*   **vector_store_id** `string` (Required)
    The ID of the vector store that the file belongs to.

### Returns
The vector store file object.

### Example request
```bash
curl https://api.openai.com/v1/vector_stores/vs_abc123/files/file-abc123 \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2"
```

### Response
```json
{
  "id": "file-abc123",
  "object": "vector_store.file",
  "created_at": 1699061776,
  "vector_store_id": "vs_abcd",
  "status": "completed",
  "last_error": null
}
```

---

## Retrieve vector store file content
`GET` `https://api.openai.com/v1/vector_stores/{vector_store_id}/files/{file_id}/content`

Retrieve the parsed contents of a vector store file.

### Path parameters

*   **file_id** `string` (Required)
    The ID of the file within the vector store.

*   **vector_store_id** `string` (Required)
    The ID of the vector store.

### Returns
The parsed contents of the specified vector store file.

### Example request
```bash
curl \
https://api.openai.com/v1/vector_stores/vs_abc123/files/file-abc123/content \
-H "Authorization: Bearer $OPENAI_API_KEY"
```

### Response
```json
{
  "file_id": "file-abc123",
  "filename": "example.txt",
  "attributes": {"key": "value"},
  "content": [
    {"type": "text", "text": "..."},
    ...
  ]
}
```

---

## Update vector store file attributes
`POST` `https://api.openai.com/v1/vector_stores/{vector_store_id}/files/{file_id}`

Update attributes on a vector store file.

### Path parameters

*   **file_id** `string` (Required)
    The ID of the file to update attributes.

*   **vector_store_id** `string` (Required)
    The ID of the vector store the file belongs to.

### Request body

*   **attributes** `map` (Required)
    Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard. Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters, booleans, or numbers.

### Returns
The updated vector store file object.

### Example request
```bash
curl https://api.openai.com/v1/vector_stores/{vector_store_id}/files/{file_id} \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"attributes": {"key1": "value1", "key2": 2}}'
```

### Response
```json
{
  "id": "file-abc123",
  "object": "vector_store.file",
  "usage_bytes": 1234,
  "created_at": 1699061776,
  "vector_store_id": "vs_abcd",
  "status": "completed",
  "last_error": null,
  "chunking_strategy": {...},
  "attributes": {"key1": "value1", "key2": 2}
}
```

---

## Delete vector store file
`DELETE` `https://api.openai.com/v1/vector_stores/{vector_store_id}/files/{file_id}`

Delete a vector store file. This will remove the file from the vector store but the file itself will not be deleted. To delete the file, use the delete file endpoint.

### Path parameters

*   **file_id** `string` (Required)
    The ID of the file to delete.

*   **vector_store_id** `string` (Required)
    The ID of the vector store that the file belongs to.

### Returns
Deletion status

### Example request
```bash
curl https://api.openai.com/v1/vector_stores/vs_abc123/files/file-abc123 \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2" \
  -X DELETE
```

### Response
```json
{
  "id": "file-abc123",
  "object": "vector_store.file.deleted",
  "deleted": true
}
```

---

## The vector store file object
`Beta`

A list of files attached to a vector store.

*   **attributes** `map`
    Set of 16 key-value pairs that can be attached to an object. Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters, booleans, or numbers.

*   **chunking_strategy** `object`
    The strategy used to chunk the file.
    *   **Static Chunking Strategy** `object`
        *   **static** `object`
            *   **chunk_overlap_tokens** `integer`: The number of tokens that overlap between chunks. Default is 400. Overlap must not exceed half of `max_chunk_size_tokens`.
            *   **max_chunk_size_tokens** `integer`: The maximum number of tokens in each chunk. Default is 800. Range: 100 to 4096.
        *   **type** `string`: Always `static`.
    *   **Other Chunking Strategy** `object`
        This is returned when the chunking strategy is unknown. Typically, this is because the file was indexed before the `chunking_strategy` concept was introduced in the API.
        *   **type** `string`: Always `other`.

*   **created_at** `integer`
    The Unix timestamp (in seconds) for when the vector store file was created.

*   **id** `string`
    The identifier, which can be referenced in API endpoints.

*   **last_error** `object`
    The last error associated with this vector store file. Will be null if there are no errors.
    *   **code** `string`: One of `server_error`, `unsupported_file`, or `invalid_file`.
    *   **message** `string`: A human-readable description of the error.

*   **object** `string`
    The object type, which is always `vector_store.file`.

*   **status** `string`
    The status of the vector store file: `in_progress`, `completed`, `cancelled`, or `failed`. `completed` indicates readiness for use.

*   **usage_bytes** `integer`
    The total vector store usage in bytes. Note that this may be different from the original file size.

*   **vector_store_id** `string`
    The ID of the vector store that the File is attached to.

### Example Object
```json
{
  "id": "file-abc123",
  "object": "vector_store.file",
  "usage_bytes": 1234,
  "created_at": 1698107661,
  "vector_store_id": "vs_abc123",
  "status": "completed",
  "last_error": null,
  "chunking_strategy": {
    "type": "static",
    "static": {
      "max_chunk_size_tokens": 800,
      "chunk_overlap_tokens": 400
    }
  }
}
```