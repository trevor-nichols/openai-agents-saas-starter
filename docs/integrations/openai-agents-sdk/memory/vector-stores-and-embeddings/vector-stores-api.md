# Vector Stores

Vector stores power semantic search for the Retrieval API and the `file_search` tool in the Responses and Assistants APIs.

**Related guide:** [File Search](https://platform.openai.com/docs/assistants/tools/file-search)

---

## Create vector store

`POST https://api.openai.com/v1/vector_stores`

Create a vector store.

### Request body

-   `chunking_strategy` (object) *Optional*
    The chunking strategy used to chunk the file(s). If not set, will use the `auto` strategy. Only applicable if `file_ids` is non-empty.

    <details>
    <summary>Possible types</summary>

    -   **Auto Chunking Strategy** (object)
        The default strategy. This strategy currently uses a `max_chunk_size_tokens` of 800 and `chunk_overlap_tokens` of 400.
        -   `type` (string) *Required*
            Always `auto`.

    -   **Static Chunking Strategy** (object)
        Customize your own chunking strategy by setting chunk size and chunk overlap.
        -   `static` (object) *Required*
            -   `chunk_overlap_tokens` (integer) *Required*
                The number of tokens that overlap between chunks. The default value is 400.
                Note that the overlap must not exceed half of `max_chunk_size_tokens`.
            -   `max_chunk_size_tokens` (integer) *Required*
                The maximum number of tokens in each chunk. The default value is 800. The minimum value is 100 and the maximum value is 4096.
        -   `type` (string) *Required*
            Always `static`.
    </details>

-   `description` (string) *Optional*
    A description for the vector store. Can be used to describe the vector store's purpose.

-   `expires_after` (object) *Optional*
    The expiration policy for a vector store.
    -   `anchor` (string) *Required*
        Anchor timestamp after which the expiration policy applies. Supported anchors: `last_active_at`.
    -   `days` (integer) *Required*
        The number of days after the anchor time that the vector store will expire.

-   `file_ids` (array) *Optional*
    A list of File IDs that the vector store should use. Useful for tools like `file_search` that can access files.

-   `metadata` (map) *Optional*
    Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard. Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters.

-   `name` (string) *Optional*
    The name of the vector store.

### Returns
A vector store object.

### Example request

```javascript
import OpenAI from "openai";
const openai = new OpenAI();

async function main() {
  const vectorStore = await openai.vectorStores.create({
    name: "Support FAQ"
  });
  console.log(vectorStore);
}

main();
```

### Response

```json
{
  "id": "vs_abc123",
  "object": "vector_store",
  "created_at": 1699061776,
  "name": "Support FAQ",
  "description": "Contains commonly asked questions and answers, organized by topic.",
  "bytes": 139920,
  "file_counts": {
    "in_progress": 0,
    "completed": 3,
    "failed": 0,
    "cancelled": 0,
    "total": 3
  }
}
```

---

## List vector stores

`GET https://api.openai.com/v1/vector_stores`

Returns a list of vector stores.

### Query parameters

-   `after` (string) *Optional*
    A cursor for use in pagination. `after` is an object ID that defines your place in the list. For instance, if you make a list request and receive 100 objects, ending with `obj_foo`, your subsequent call can include `after=obj_foo` in order to fetch the next page of the list.

-   `before` (string) *Optional*
    A cursor for use in pagination. `before` is an object ID that defines your place in the list. For instance, if you make a list request and receive 100 objects, starting with `obj_foo`, your subsequent call can include `before=obj_foo` in order to fetch the previous page of the list.

-   `limit` (integer) *Optional, defaults to 20*
    A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 20.

-   `order` (string) *Optional, defaults to desc*
    Sort order by the `created_at` timestamp of the objects. `asc` for ascending order and `desc` for descending order.

### Returns
A list of vector store objects.

### Example request

```javascript
import OpenAI from "openai";
const openai = new OpenAI();

async function main() {
  const vectorStores = await openai.vectorStores.list();
  console.log(vectorStores);
}

main();  
```

### Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "vs_abc123",
      "object": "vector_store",
      "created_at": 1699061776,
      "name": "Support FAQ",
      "description": "Contains commonly asked questions and answers, organized by topic.",
      "bytes": 139920,
      "file_counts": {
        "in_progress": 0,
        "completed": 3,
        "failed": 0,
        "cancelled": 0,
        "total": 3
      }
    },
    {
      "id": "vs_abc456",
      "object": "vector_store",
      "created_at": 1699061776,
      "name": "Support FAQ v2",
      "description": null,
      "bytes": 139920,
      "file_counts": {
        "in_progress": 0,
        "completed": 3,
        "failed": 0,
        "cancelled": 0,
        "total": 3
      }
    }
  ],
  "first_id": "vs_abc123",
  "last_id": "vs_abc456",
  "has_more": false
}
```

---

## Retrieve vector store

`GET https://api.openai.com/v1/vector_stores/{vector_store_id}`

Retrieves a vector store.

### Path parameters

-   `vector_store_id` (string) *Required*
    The ID of the vector store to retrieve.

### Returns
The vector store object matching the specified ID.

### Example request

```javascript
import OpenAI from "openai";
const openai = new OpenAI();

async function main() {
  const vectorStore = await openai.vectorStores.retrieve(
    "vs_abc123"
  );
  console.log(vectorStore);
}

main();
```

### Response

```json
{
  "id": "vs_abc123",
  "object": "vector_store",
  "created_at": 1699061776
}
```

---

## Modify vector store

`POST https://api.openai.com/v1/vector_stores/{vector_store_id}`

Modifies a vector store.

### Path parameters

-   `vector_store_id` (string) *Required*
    The ID of the vector store to modify.

### Request body

-   `expires_after` (object or null) *Optional*
    The expiration policy for a vector store.
    -   `anchor` (string) *Required*
        Anchor timestamp after which the expiration policy applies. Supported anchors: `last_active_at`.
    -   `days` (integer) *Required*
        The number of days after the anchor time that the vector store will expire.

-   `metadata` (map) *Optional*
    Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard. Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters.

-   `name` (string or null) *Optional*
    The name of the vector store.

### Returns
The modified vector store object.

### Example request

```javascript
import OpenAI from "openai";
const openai = new OpenAI();

async function main() {
  const vectorStore = await openai.vectorStores.update(
    "vs_abc123",
    {
      name: "Support FAQ"
    }
  );
  console.log(vectorStore);
}

main();
```

### Response

```json
{
  "id": "vs_abc123",
  "object": "vector_store",
  "created_at": 1699061776,
  "name": "Support FAQ",
  "description": "Contains commonly asked questions and answers, organized by topic.",
  "bytes": 139920,
  "file_counts": {
    "in_progress": 0,
    "completed": 3,
    "failed": 0,
    "cancelled": 0,
    "total": 3
  }
}
```

---

## Delete vector store

`DELETE https://api.openai.com/v1/vector_stores/{vector_store_id}`

Delete a vector store.

### Path parameters

-   `vector_store_id` (string) *Required*
    The ID of the vector store to delete.

### Returns
Deletion status.

### Example request

```javascript
import OpenAI from "openai";
const openai = new OpenAI();

async function main() {
  const deletedVectorStore = await openai.vectorStores.delete(
    "vs_abc123"
  );
  console.log(deletedVectorStore);
}

main();
```

### Response

```json
{
  "id": "vs_abc123",
  "object": "vector_store.deleted",
  "deleted": true
}
```

---

## Search vector store

`POST https://api.openai.com/v1/vector_stores/{vector_store_id}/search`

Search a vector store for relevant chunks based on a query and file attributes filter.

### Path parameters

-   `vector_store_id` (string) *Required*
    The ID of the vector store to search.

### Request body

-   `query` (string or array) *Required*
    A query string for a search.

-   `filters` (object) *Optional*
    A filter to apply based on file attributes.
    <details>
    <summary>Possible types</summary>

    -   **Comparison Filter** (object)
        A filter used to compare a specified attribute key to a given value using a defined comparison operation.
        -   `key` (string) *Required*
            The key to compare against the value.
        -   `type` (string) *Required*
            Specifies the comparison operator: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `nin`.
            - `eq`: equals
            - `ne`: not equal
            - `gt`: greater than
            - `gte`: greater than or equal
            - `lt`: less than
            - `lte`: less than or equal
            - `in`: in
            - `nin`: not in
        -   `value` (string / number / boolean / array) *Required*
            The value to compare against the attribute key; supports string, number, or boolean types.

    -   **Compound Filter** (object)
        Combine multiple filters using `and` or `or`.
        -   `filters` (array) *Required*
            Array of filters to combine. Items can be `ComparisonFilter` or `CompoundFilter`.
            <details>
            <summary>Possible types</summary>

            - **Comparison Filter** (object)
              A filter used to compare a specified attribute key to a given value using a defined comparison operation.
              -   `key` (string) *Required*
                  The key to compare against the value.
              -   `type` (string) *Required*
                  Specifies the comparison operator: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `nin`.
                  - `eq`: equals
                  - `ne`: not equal
                  - `gt`: greater than
                  - `gte`: greater than or equal
                  - `lt`: less than
                  - `lte`: less than or equal
                  - `in`: in
                  - `nin`: not in
              -   `value` (string / number / boolean / array) *Required*
                  The value to compare against the attribute key; supports string, number, or boolean types.
            </details>
        -   `type` (string) *Required*
            Type of operation: `and` or `or`.
    </details>

-   `max_num_results` (integer) *Optional, defaults to 10*
    The maximum number of results to return. This number should be between 1 and 50 inclusive.

-   `ranking_options` (object) *Optional*
    Ranking options for search.
    -   `ranker` (string) *Optional, defaults to auto*
        Enable re-ranking; set to `none` to disable, which can help reduce latency.
    -   `score_threshold` (number) *Optional, defaults to 0*
    -   `rewrite_query` (boolean) *Optional, defaults to false*
        Whether to rewrite the natural language query for vector search.

### Returns
A page of search results from the vector store.

### Example request

```bash
curl -X POST \
https://api.openai.com/v1/vector_stores/vs_abc123/search \
-H "Authorization: Bearer $OPENAI_API_KEY" \
-H "Content-Type: application/json" \
-d '{"query": "What is the return policy?", "filters": {...}}'
```

### Response

```json
{
  "object": "vector_store.search_results.page",
  "search_query": "What is the return policy?",
  "data": [
    {
      "file_id": "file_123",
      "filename": "document.pdf",
      "score": 0.95,
      "attributes": {
        "author": "John Doe",
        "date": "2023-01-01"
      },
      "content": [
        {
          "type": "text",
          "text": "Relevant chunk"
        }
      ]
    },
    {
      "file_id": "file_456",
      "filename": "notes.txt",
      "score": 0.89,
      "attributes": {
        "author": "Jane Smith",
        "date": "2023-01-02"
      },
      "content": [
        {
          "type": "text",
          "text": "Sample text content from the vector store."
        }
      ]
    }
  ],
  "has_more": false,
  "next_page": null
}
```

---

## The vector store object

A vector store is a collection of processed files can be used by the `file_search` tool.

-   `id` (string)
    The identifier, which can be referenced in API endpoints.
-   `object` (string)
    The object type, which is always `vector_store`.
-   `created_at` (integer)
    The Unix timestamp (in seconds) for when the vector store was created.
-   `name` (string)
    The name of the vector store.
-   `usage_bytes` (integer)
    The total number of bytes used by the files in the vector store.
-   `file_counts` (object)
    -   `in_progress` (integer)
        The number of files that are currently being processed.
    -   `completed` (integer)
        The number of files that have been successfully processed.
    -   `failed` (integer)
        The number of files that have failed to process.
    -   `cancelled` (integer)
        The number of files that were cancelled.
    -   `total` (integer)
        The total number of files.
-   `status` (string)
    The status of the vector store, which can be either `expired`, `in_progress`, or `completed`. A status of `completed` indicates that the vector store is ready for use.
-   `expires_after` (object)
    The expiration policy for a vector store.
    -   `anchor` (string)
        Anchor timestamp after which the expiration policy applies. Supported anchors: `last_active_at`.
    -   `days` (integer)
        The number of days after the anchor time that the vector store will expire.
-   `expires_at` (integer)
    The Unix timestamp (in seconds) for when the vector store will expire.
-   `last_active_at` (integer)
    The Unix timestamp (in seconds) for when the vector store was last active.
-   `metadata` (map)
    Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard. Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters.

### Example Object

```json
{
  "id": "vs_123",
  "object": "vector_store",
  "created_at": 1698107661,
  "usage_bytes": 123456,
  "last_active_at": 1698107661,
  "name": "my_vector_store",
  "status": "completed",
  "file_counts": {
    "in_progress": 0,
    "completed": 100,
    "cancelled": 0,
    "failed": 0,
    "total": 100
  },
  "last_used_at": 1698107661
}
```

---
---

# Vector store files

Vector store files represent files inside a vector store.

**Related guide:** [File Search](https://platform.openai.com/docs/assistants/tools/file-search)

---

## Create vector store file

`POST https://api.openai.com/v1/vector_stores/{vector_store_id}/files`

Create a vector store file by attaching a File to a vector store.

### Path parameters

-   `vector_store_id` (string) *Required*
    The ID of the vector store for which to create a File.

### Request body

-   `file_id` (string) *Required*
    A File ID that the vector store should use. Useful for tools like `file_search` that can access files.

-   `attributes` (map) *Optional*
    Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard. Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters, booleans, or numbers.

-   `chunking_strategy` (object) *Optional*
    The chunking strategy used to chunk the file(s). If not set, will use the `auto` strategy.
    <details>
    <summary>Possible types</summary>

    -   **Auto Chunking Strategy** (object)
        The default strategy. This strategy currently uses a `max_chunk_size_tokens` of 800 and `chunk_overlap_tokens` of 400.
        -   `type` (string) *Required*
            Always `auto`.

    -   **Static Chunking Strategy** (object)
        Customize your own chunking strategy by setting chunk size and chunk overlap.
        -   `static` (object) *Required*
            -   `chunk_overlap_tokens` (integer) *Required*
                The number of tokens that overlap between chunks. The default value is 400. Note that the overlap must not exceed half of `max_chunk_size_tokens`.
            -   `max_chunk_size_tokens` (integer) *Required*
                The maximum number of tokens in each chunk. The default value is 800. The minimum value is 100 and the maximum value is 4096.
        -   `type` (string) *Required*
            Always `static`.
    </details>

### Returns
A vector store file object.

### Example request

```javascript
import OpenAI from "openai";
const openai = new OpenAI();

async function main() {
  const myVectorStoreFile = await openai.vectorStores.files.create(
    "vs_abc123",
    {
      file_id: "file-abc123"
    }
  );
  console.log(myVectorStoreFile);
}

main();
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

`GET https://api.openai.com/v1/vector_stores/{vector_store_id}/files`

Returns a list of vector store files.

### Path parameters

-   `vector_store_id` (string) *Required*
    The ID of the vector store that the files belong to.

### Query parameters

-   `after` (string) *Optional*
    A cursor for use in pagination. `after` is an object ID that defines your place in the list. For instance, if you make a list request and receive 100 objects, ending with `obj_foo`, your subsequent call can include `after=obj_foo` in order to fetch the next page of the list.

-   `before` (string) *Optional*
    A cursor for use in pagination. `before` is an object ID that defines your place in the list. For instance, if you make a list request and receive 100 objects, starting with `obj_foo`, your subsequent call can include `before=obj_foo` in order to fetch the previous page of the list.

-   `filter` (string) *Optional*
    Filter by file status. One of `in_progress`, `completed`, `failed`, `cancelled`.

-   `limit` (integer) *Optional, defaults to 20*
    A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 20.

-   `order` (string) *Optional, defaults to desc*
    Sort order by the `created_at` timestamp of the objects. `asc` for ascending order and `desc` for descending order.

### Returns
A list of vector store file objects.

### Example request

```javascript
import OpenAI from "openai";
const openai = new OpenAI();

async function main() {
  const vectorStoreFiles = await openai.vectorStores.files.list(
    "vs_abc123"
  );
  console.log(vectorStoreFiles);
}

main();
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

`GET https://api.openai.com/v1/vector_stores/{vector_store_id}/files/{file_id}`

Retrieves a vector store file.

### Path parameters

-   `vector_store_id` (string) *Required*
    The ID of the vector store that the file belongs to.
-   `file_id` (string) *Required*
    The ID of the file being retrieved.

### Returns
The vector store file object.

### Example request

```javascript
import OpenAI from "openai";
const openai = new OpenAI();

async function main() {
  const vectorStoreFile = await openai.vectorStores.files.retrieve(
    "file-abc123",
    { vector_store_id: "vs_abc123" }
  );
  console.log(vectorStoreFile);
}

main();
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

`GET https://api.openai.com/v1/vector_stores/{vector_store_id}/files/{file_id}/content`

Retrieve the parsed contents of a vector store file.

### Path parameters

-   `vector_store_id` (string) *Required*
    The ID of the vector store.
-   `file_id` (string) *Required*
    The ID of the file within the vector store.

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

`POST https://api.openai.com/v1/vector_stores/{vector_store_id}/files/{file_id}`

Update attributes on a vector store file.

### Path parameters

-   `vector_store_id` (string) *Required*
    The ID of the vector store the file belongs to.
-   `file_id` (string) *Required*
    The ID of the file to update attributes.

### Request body

-   `attributes` (map) *Required*
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

`DELETE https://api.openai.com/v1/vector_stores/{vector_store_id}/files/{file_id}`

Delete a vector store file. This will remove the file from the vector store but the file itself will not be deleted. To delete the file, use the delete file endpoint.

### Path parameters

-   `vector_store_id` (string) *Required*
    The ID of the vector store that the file belongs to.
-   `file_id` (string) *Required*
    The ID of the file to delete.

### Returns
Deletion status.

### Example request

```javascript
import OpenAI from "openai";
const openai = new OpenAI();

async function main() {
  const deletedVectorStoreFile = await openai.vectorStores.files.delete(
    "file-abc123",
    { vector_store_id: "vs_abc123" }
  );
  console.log(deletedVectorStoreFile);
}

main();
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

A list of files attached to a vector store.

-   `id` (string)
    The identifier, which can be referenced in API endpoints.
-   `object` (string)
    The object type, which is always `vector_store.file`.
-   `usage_bytes` (integer)
    The total vector store usage in bytes. Note that this may be different from the original file size.
-   `created_at` (integer)
    The Unix timestamp (in seconds) for when the vector store file was created.
-   `vector_store_id` (string)
    The ID of the vector store that the File is attached to.
-   `status` (string)
    The status of the vector store file, which can be either `in_progress`, `completed`, `cancelled`, or `failed`. The status `completed` indicates that the vector store file is ready for use.
-   `last_error` (object)
    The last error associated with this vector store file. Will be `null` if there are no errors.
    -   `code` (string)
        One of `server_error`, `unsupported_file`, or `invalid_file`.
    -   `message` (string)
        A human-readable description of the error.
-   `chunking_strategy` (object)
    The strategy used to chunk the file.
    <details>
    <summary>Possible types</summary>

    -   **Static Chunking Strategy** (object)
        -   `static` (object)
            -   `max_chunk_size_tokens` (integer)
                The maximum number of tokens in each chunk. The default value is 800. The minimum value is 100 and the maximum value is 4096.
            -   `chunk_overlap_tokens` (integer)
                The number of tokens that overlap between chunks. The default value is 400. Note that the overlap must not exceed half of `max_chunk_size_tokens`.
        -   `type` (string)
            Always `static`.

    -   **Other Chunking Strategy** (object)
        This is returned when the chunking strategy is unknown. Typically, this is because the file was indexed before the `chunking_strategy` concept was introduced in the API.
        -   `type` (string)
            Always `other`.
    </details>
-   `attributes` (map)
    Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard. Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters, booleans, or numbers.

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

---
---

# Vector store file batches

Vector store file batches represent operations to add multiple files to a vector store.

**Related guide:** [File Search](https://platform.openai.com/docs/assistants/tools/file-search)

---

## Create vector store file batch

`POST https://api.openai.com/v1/vector_stores/{vector_store_id}/file_batches`

Create a vector store file batch.

### Path parameters

-   `vector_store_id` (string) *Required*
    The ID of the vector store for which to create a File Batch.

### Request body

-   `file_ids` (array) *Optional*
    A list of File IDs that the vector store should use. Useful for tools like `file_search` that can access files. If `attributes` or `chunking_strategy` are provided, they will be applied to all files in the batch. Mutually exclusive with `files`.

-   `files` (array) *Optional*
    A list of objects that each include a `file_id` plus optional `attributes` or `chunking_strategy`. Use this when you need to override metadata for specific files. The global `attributes` or `chunking_strategy` will be ignored and must be specified for each file. Mutually exclusive with `file_ids`.
    -   `file_id` (string) *Required*
        A File ID that the vector store should use.
    -   `attributes` (map) *Optional*
        Set of 16 key-value pairs.
    -   `chunking_strategy` (object) *Optional*
        The chunking strategy for the file.
        <details>
        <summary>Possible types</summary>
        <!-- ... (details omitted for brevity, but would be included) ... -->
        </details>

-   `attributes` (map) *Optional*
    Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format. Keys are strings with a maximum length of 64 characters. Values are strings, booleans, or numbers.

-   `chunking_strategy` (object) *Optional*
    The chunking strategy used to chunk the file(s). If not set, will use the `auto` strategy.
    <details>
    <summary>Possible types</summary>

    -   **Auto Chunking Strategy** (object)
        The default strategy. `max_chunk_size_tokens`: 800, `chunk_overlap_tokens`: 400.
        -   `type` (string) *Required* - Always `auto`.

    -   **Static Chunking Strategy** (object)
        Customize chunking strategy.
        -   `static` (object) *Required*
            -   `chunk_overlap_tokens` (integer) *Required*
            -   `max_chunk_size_tokens` (integer) *Required*
        -   `type` (string) *Required* - Always `static`.
    </details>

### Returns
A vector store file batch object.

### Example request

```javascript
import OpenAI from "openai";
const openai = new OpenAI();

async function main() {
  const myVectorStoreFileBatch = await openai.vectorStores.fileBatches.create(
    "vs_abc123",
    {
      files: [
        {
          file_id: "file-abc123",
          attributes: { category: "finance" },
        },
        {
          file_id: "file-abc456",
          chunking_strategy: {
            type: "static",
            static: {
              max_chunk_size_tokens: 1200,
              chunk_overlap_tokens: 200,
            }
          },
        },
      ]
    }
  );
  console.log(myVectorStoreFileBatch);
}

main();
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

`GET https://api.openai.com/v1/vector_stores/{vector_store_id}/file_batches/{batch_id}`

Retrieves a vector store file batch.

### Path parameters

-   `vector_store_id` (string) *Required*
    The ID of the vector store that the file batch belongs to.
-   `batch_id` (string) *Required*
    The ID of the file batch being retrieved.

### Returns
The vector store file batch object.

### Example request

```javascript
import OpenAI from "openai";
const openai = new OpenAI();

async function main() {
  const vectorStoreFileBatch = await openai.vectorStores.fileBatches.retrieve(
    "vsfb_abc123",
    { vector_store_id: "vs_abc123" }
  );
  console.log(vectorStoreFileBatch);
}

main();
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

`POST https://api.openai.com/v1/vector_stores/{vector_store_id}/file_batches/{batch_id}/cancel`

Cancel a vector store file batch. This attempts to cancel the processing of files in this batch as soon as possible.

### Path parameters

-   `vector_store_id` (string) *Required*
    The ID of the vector store that the file batch belongs to.
-   `batch_id` (string) *Required*
    The ID of the file batch to cancel.

### Returns
The modified vector store file batch object.

### Example request

```javascript
import OpenAI from "openai";
const openai = new OpenAI();

async function main() {
  const deletedVectorStoreFileBatch = await openai.vectorStores.fileBatches.cancel(
    "vsfb_abc123",
    { vector_store_id: "vs_abc123" }
  );
  console.log(deletedVectorStoreFileBatch);
}

main();
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

`GET https://api.openai.com/v1/vector_stores/{vector_store_id}/file_batches/{batch_id}/files`

Returns a list of vector store files in a batch.

### Path parameters

-   `vector_store_id` (string) *Required*
    The ID of the vector store that the files belong to.
-   `batch_id` (string) *Required*
    The ID of the file batch that the files belong to.

### Query parameters

-   `after` (string) *Optional*
    A cursor for use in pagination.
-   `before` (string) *Optional*
    A cursor for use in pagination.
-   `filter` (string) *Optional*
    Filter by file status. One of `in_progress`, `completed`, `failed`, `cancelled`.
-   `limit` (integer) *Optional, defaults to 20*
    A limit on the number of objects to be returned (1-100).
-   `order` (string) *Optional, defaults to desc*
    Sort order by `created_at` timestamp (`asc` or `desc`).

### Returns
A list of vector store file objects.

### Example request

```javascript
import OpenAI from "openai";
const openai = new OpenAI();

async function main() {
  const vectorStoreFiles = await openai.vectorStores.fileBatches.listFiles(
    "vsfb_abc123",
    { vector_store_id: "vs_abc123" }
  );
  console.log(vectorStoreFiles);
}

main();
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

## The vector store files batch object

A batch of files attached to a vector store.

-   `id` (string)
    The identifier, which can be referenced in API endpoints.
-   `object` (string)
    The object type, which is always `vector_store.file_batch`.
-   `created_at` (integer)
    The Unix timestamp (in seconds) for when the vector store files batch was created.
-   `vector_store_id` (string)
    The ID of the vector store that the File is attached to.
-   `status` (string)
    The status of the vector store files batch, which can be `in_progress`, `completed`, `cancelled` or `failed`.
-   `file_counts` (object)
    -   `in_progress` (integer)
        The number of files that are currently being processed.
    -   `completed` (integer)
        The number of files that have been processed.
    -   `failed` (integer)
        The number of files that have failed to process.
    -   `cancelled` (integer)
        The number of files that where cancelled.
    -   `total` (integer)
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