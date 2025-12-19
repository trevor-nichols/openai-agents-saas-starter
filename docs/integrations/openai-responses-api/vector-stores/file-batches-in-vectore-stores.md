# Vector store file batches
Vector store file batches represent operations to add multiple files to a vector store. Related guide: [File Search](https://platform.openai.com/docs/assistants/tools/file-search)

---

## Create vector store file batch
Creates a vector store file batch.

<pre>
<code class="language-bash">
POST https://api.openai.com/v1/vector_stores/{vector_store_id}/file_batches
</code>
</pre>

### Path parameters
-   `vector_store_id` `string` **Required**  
    The ID of the vector store for which to create a File Batch.

### Request body
-   `attributes` `map` *Optional*  
    Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard. Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters, booleans, or numbers.

-   `chunking_strategy` `object` *Optional*  
    The chunking strategy used to chunk the file(s). If not set, will use the `auto` strategy.

    -   **Auto Chunking Strategy** `object`
        The default strategy. This strategy currently uses a `max_chunk_size_tokens` of 800 and `chunk_overlap_tokens` of 400.
        -   **Properties**
            -   `type` `string` **Required**  
                Always `auto`.

    -   **Static Chunking Strategy** `object`
        Customize your own chunking strategy by setting chunk size and chunk overlap.
        -   **Properties**
            -   `static` `object` **Required**
                -   **Properties**
                    -   `chunk_overlap_tokens` `integer` **Required**  
                        The number of tokens that overlap between chunks. The default value is 400. Note that the overlap must not exceed half of `max_chunk_size_tokens`.
                    -   `max_chunk_size_tokens` `integer` **Required**  
                        The maximum number of tokens in each chunk. The default value is 800. The minimum value is 100 and the maximum value is 4096.
            -   `type` `string` **Required**  
                Always `static`.

-   `file_ids` `array` *Optional*  
    A list of File IDs that the vector store should use. Useful for tools like `file_search` that can access files. If `attributes` or `chunking_strategy` are provided, they will be applied to all files in the batch. Mutually exclusive with `files`.

-   `files` `array` *Optional*  
    A list of objects that each include a `file_id` plus optional `attributes` or `chunking_strategy`. Use this when you need to override metadata for specific files. The global `attributes` or `chunking_strategy` will be ignored and must be specified for each file. Mutually exclusive with `file_ids`.
    -   **Properties**
        -   `file_id` `string` **Required**  
            A File ID that the vector store should use. Useful for tools like `file_search` that can access files.
        -   `attributes` `map` *Optional*  
            Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard. Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters, booleans, or numbers.
        -   `chunking_strategy` `object` *Optional*  
            The chunking strategy used to chunk the file(s). If not set, will use the `auto` strategy.
            -   **Auto Chunking Strategy** `object`
                The default strategy. This strategy currently uses a `max_chunk_size_tokens` of 800 and `chunk_overlap_tokens` of 400.
                -   **Properties**
                    -   `type` `string` **Required**  
                        Always `auto`.
            -   **Static Chunking Strategy** `object`
                Customize your own chunking strategy by setting chunk size and chunk overlap.
                -   **Properties**
                    -   `static` `object` **Required**
                        -   **Properties**
                            -   `chunk_overlap_tokens` `integer` **Required**  
                                The number of tokens that overlap between chunks. The default value is 400. Note that the overlap must not exceed half of `max_chunk_size_tokens`.
                            -   `max_chunk_size_tokens` `integer` **Required**  
                                The maximum number of tokens in each chunk. The default value is 800. The minimum value is 100 and the maximum value is 4096.
                    -   `type` `string` **Required**  
                        Always `static`.

### Returns
A vector store file batch object.

### Example request
```bash
curl https://api.openai.com/v1/vector_stores/vs_abc123/file_batches \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -H "OpenAI-Beta: assistants=v2" \
    -d '{
      "files": [
        {
          "file_id": "file-abc123",
          "attributes": {"category": "finance"}
        },
        {
          "file_id": "file-abc456",
          "chunking_strategy": {
            "type": "static",
            "static": {
              "max_chunk_size_tokens": 1200,
              "chunk_overlap_tokens": 200
            }
          }
        }
      ]
    }'
```

### Response
```json
{
  "id": "vsfb_abc123",
  "object": "vector_store.file_batch",
  "created_at": 1699061776,
  "vector_store_id": "vs_abc123",
  "status": "in_progress",
  "file_counts": {
    "in_progress": 1,
    "completed": 1,
    "failed": 0,
    "cancelled": 0,
    "total": 2
  }
}
```

---

## Retrieve vector store file batch
Retrieves a vector store file batch.

<pre>
<code class="language-bash">
GET https://api.openai.com/v1/vector_stores/{vector_store_id}/file_batches/{batch_id}
</code>
</pre>

### Path parameters
-   `vector_store_id` `string` **Required**  
    The ID of the vector store that the file batch belongs to.
-   `batch_id` `string` **Required**  
    The ID of the file batch being retrieved.

### Returns
The vector store file batch object.

### Example request
```bash
curl https://api.openai.com/v1/vector_stores/vs_abc123/file_batches/vsfb_abc123 \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2"
```

### Response
```json
{
  "id": "vsfb_abc123",
  "object": "vector_store.file_batch",
  "created_at": 1699061776,
  "vector_store_id": "vs_abc123",
  "status": "in_progress",
  "file_counts": {
    "in_progress": 1,
    "completed": 1,
    "failed": 0,
    "cancelled": 0,
    "total": 2
  }
}
```

---

## Cancel vector store file batch
Cancel a vector store file batch. This attempts to cancel the processing of files in this batch as soon as possible.

<pre>
<code class="language-bash">
POST https://api.openai.com/v1/vector_stores/{vector_store_id}/file_batches/{batch_id}/cancel
</code>
</pre>

### Path parameters
-   `vector_store_id` `string` **Required**  
    The ID of the vector store that the file batch belongs to.
-   `batch_id` `string` **Required**  
    The ID of the file batch to cancel.

### Returns
The modified vector store file batch object.

### Example request
```bash
curl https://api.openai.com/v1/vector_stores/vs_abc123/file_batches/vsfb_abc123/cancel \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2" \
  -X POST
```

### Response
```json
{
  "id": "vsfb_abc123",
  "object": "vector_store.file_batch",
  "created_at": 1699061776,
  "vector_store_id": "vs_abc123",
  "status": "cancelling",
  "file_counts": {
    "in_progress": 12,
    "completed": 3,
    "failed": 0,
    "cancelled": 0,
    "total": 15
  }
}
```

---

## List vector store files in a batch
Returns a list of vector store files in a batch.

<pre>
<code class="language-bash">
GET https://api.openai.com/v1/vector_stores/{vector_store_id}/file_batches/{batch_id}/files
</code>
</pre>

### Path parameters
-   `vector_store_id` `string` **Required**  
    The ID of the vector store that the files belong to.
-   `batch_id` `string` **Required**  
    The ID of the file batch that the files belong to.

### Query parameters
-   `limit` `integer` *Optional*  
    Defaults to 20. A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 20.
-   `order` `string` *Optional*  
    Defaults to `desc`. Sort order by the `created_at` timestamp of the objects. `asc` for ascending order and `desc` for descending order.
-   `after` `string` *Optional*  
    A cursor for use in pagination. `after` is an object ID that defines your place in the list. For instance, if you make a list request and receive 100 objects, ending with `obj_foo`, your subsequent call can include `after=obj_foo` in order to fetch the next page of the list.
-   `before` `string` *Optional*  
    A cursor for use in pagination. `before` is an object ID that defines your place in the list. For instance, if you make a list request and receive 100 objects, starting with `obj_foo`, your subsequent call can include `before=obj_foo` in order to fetch the previous page of the list.
-   `filter` `string` *Optional*  
    Filter by file status. One of `in_progress`, `completed`, `failed`, `cancelled`.

### Returns
A list of vector store file objects.

### Example request
```bash
curl https://api.openai.com/v1/vector_stores/vs_abc123/file_batches/vsfb_abc123/files \
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
      "vector_store_id": "vs_abc123",
      "status": "completed",
      "last_error": null
    },
    {
      "id": "file-abc456",
      "object": "vector_store.file",
      "created_at": 1699061776,
      "vector_store_id": "vs_abc123",
      "status": "completed",
      "last_error": null
    }
  ],
  "first_id": "file-abc123",
  "last_id": "file-abc456",
  "has_more": false
}
```

---

## The vector store files batch object
A batch of files attached to a vector store.

-   `id` `string`  
    The identifier, which can be referenced in API endpoints.
-   `object` `string`  
    The object type, which is always `vector_store.file_batch`.
-   `created_at` `integer`  
    The Unix timestamp (in seconds) for when the vector store files batch was created.
-   `vector_store_id` `string`  
    The ID of the vector store that the File is attached to.
-   `status` `string`  
    The status of the vector store files batch, which can be either `in_progress`, `completed`, `cancelled` or `failed`.
-   `file_counts` `object`  
    -   **Properties**
        -   `in_progress` `integer`  
            The number of files that are currently being processed.
        -   `completed` `integer`  
            The number of files that have been processed.
        -   `failed` `integer`  
            The number of files that have failed to process.
        -   `cancelled` `integer`  
            The number of files that where cancelled.
        -   `total` `integer`  
            The total number of files.

### Example Object
```json
{
  "id": "vsfb_123",
  "object": "vector_store.files_batch",
  "created_at": 1698107661,
  "vector_store_id": "vs_abc123",
  "status": "completed",
  "file_counts": {
    "in_progress": 0,
    "completed": 100,
    "failed": 0,
    "cancelled": 0,
    "total": 100
  }
}
```