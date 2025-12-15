# Vector stores
Vector stores power semantic search for the Retrieval API and the `file_search` tool in the Responses and Assistants APIs.

**Related guide:** File Search

***

### Create vector store
`POST` `https://api.openai.com/v1/vector_stores`

Create a vector store.

#### Request body
*   `chunking_strategy` `object` (Optional)
    The chunking strategy used to chunk the file(s). If not set, will use the `auto` strategy. Only applicable if `file_ids` is non-empty.
    > **Possible types**
    >
    > **Auto Chunking Strategy** `object`
    > The default strategy. This strategy currently uses a `max_chunk_size_tokens` of 800 and `chunk_overlap_tokens` of 400.
    > > **Properties**
    > >
    > > *   `type` `string` (Required)
    > >     Always `auto`.
    >
    > **Static Chunking Strategy** `object`
    > Customize your own chunking strategy by setting chunk size and chunk overlap.
    > > **Properties**
    > >
    > > *   `static` `object` (Required)
    > >     > **Properties**
    > >     >
    > >     > *   `chunk_overlap_tokens` `integer` (Required)
    > >     >     The number of tokens that overlap between chunks. The default value is 400. Note that the overlap must not exceed half of `max_chunk_size_tokens`.
    > >     > *   `max_chunk_size_tokens` `integer` (Required)
    > >     >     The maximum number of tokens in each chunk. The default value is 800. The minimum value is 100 and the maximum value is 4096.
    > > *   `type` `string` (Required)
    > >     Always `static`.
*   `description` `string` (Optional)
    A description for the vector store. Can be used to describe the vector store's purpose.
*   `expires_after` `object` (Optional)
    The expiration policy for a vector store.
    > **Properties**
    >
    > *   `anchor` `string` (Required)
    >     Anchor timestamp after which the expiration policy applies. Supported anchors: `last_active_at`.
    > *   `days` `integer` (Required)
    >     The number of days after the anchor time that the vector store will expire.
*   `file_ids` `array` (Optional)
    A list of File IDs that the vector store should use. Useful for tools like `file_search` that can access files.
*   `metadata` `map` (Optional)
    Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard. Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters.
*   `name` `string` (Optional)
    The name of the vector store.

#### Returns
A vector store object.

#### Example request
```sh
curl https://api.openai.com/v1/vector_stores \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2" \
  -d '{
    "name": "Support FAQ"
  }'
```
#### Response
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
***

### List vector stores
`GET` `https://api.openai.com/v1/vector_stores`

Returns a list of vector stores.

#### Query parameters
*   `after` `string` (Optional)
    A cursor for use in pagination. `after` is an object ID that defines your place in the list. For instance, if you make a list request and receive 100 objects, ending with `obj_foo`, your subsequent call can include `after=obj_foo` in order to fetch the next page of the list.
*   `before` `string` (Optional)
    A cursor for use in pagination. `before` is an object ID that defines your place in the list. For instance, if you make a list request and receive 100 objects, starting with `obj_foo`, your subsequent call can include `before=obj_foo` in order to fetch the previous page of the list.
*   `limit` `integer` (Optional, defaults to 20)
    A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 20.
*   `order` `string` (Optional, defaults to `desc`)
    Sort order by the `created_at` timestamp of the objects. `asc` for ascending order and `desc` for descending order.

#### Returns
A list of vector store objects.

#### Example request
```sh
curl https://api.openai.com/v1/vector_stores \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2"
```
#### Response
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
***

### Retrieve vector store
`GET` `https://api.openai.com/v1/vector_stores/{vector_store_id}`

Retrieves a vector store.

#### Path parameters
*   `vector_store_id` `string` (Required)
    The ID of the vector store to retrieve.

#### Returns
The vector store object matching the specified ID.

#### Example request
```sh
curl https://api.openai.com/v1/vector_stores/vs_abc123 \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2"
```
#### Response
```json
{
  "id": "vs_abc123",
  "object": "vector_store",
  "created_at": 1699061776
}
```
***

### Modify vector store
`POST` `https://api.openai.com/v1/vector_stores/{vector_store_id}`

Modifies a vector store.

#### Path parameters
*   `vector_store_id` `string` (Required)
    The ID of the vector store to modify.

#### Request body
*   `expires_after` `object` or `null` (Optional)
    The expiration policy for a vector store.
    > **Properties**
    >
    > *   `anchor` `string` (Required)
    >     Anchor timestamp after which the expiration policy applies. Supported anchors: `last_active_at`.
    > *   `days` `integer` (Required)
    >     The number of days after the anchor time that the vector store will expire.
*   `metadata` `map` (Optional)
    Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard. Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters.
*   `name` `string` or `null` (Optional)
    The name of the vector store.

#### Returns
The modified vector store object.

#### Example request
```sh
curl https://api.openai.com/v1/vector_stores/vs_abc123 \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2" \
  -d '{
    "name": "Support FAQ"
  }'
```
#### Response
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
***

### Delete vector store
`DELETE` `https://api.openai.com/v1/vector_stores/{vector_store_id}`

Delete a vector store.

#### Path parameters
*   `vector_store_id` `string` (Required)
    The ID of the vector store to delete.

#### Returns
Deletion status.

#### Example request
```sh
curl https://api.openai.com/v1/vector_stores/vs_abc123 \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "OpenAI-Beta: assistants=v2" \
  -X DELETE
```
#### Response
```json
{
  "id": "vs_abc123",
  "object": "vector_store.deleted",
  "deleted": true
}
```
***

### Search vector store
`POST` `https://api.openai.com/v1/vector_stores/{vector_store_id}/search`

Search a vector store for relevant chunks based on a query and file attributes filter.

#### Path parameters
*   `vector_store_id` `string` (Required)
    The ID of the vector store to search.

#### Request body
*   `query` `string` or `array` (Required)
    A query string for a search.
*   `filters` `object` (Optional)
    A filter to apply based on file attributes.
    > **Possible types**
    >
    > **Comparison Filter** `object`
    > A filter used to compare a specified attribute key to a given value using a defined comparison operation.
    > > **Properties**
    > >
    > > *   `key` `string` (Required)
    > >     The key to compare against the value.
    > > *   `type` `string` (Required)
    > >     Specifies the comparison operator: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `nin`.
    > >     - `eq`: equals
    > >     - `ne`: not equal
    > >     - `gt`: greater than
    > >     - `gte`: greater than or equal
    > >     - `lt`: less than
    > >     - `lte`: less than or equal
    > >     - `in`: in
    > >     - `nin`: not in
    > > *   `value` `string` / `number` / `boolean` / `array` (Required)
    > >     The value to compare against the attribute key; supports string, number, or boolean types.
    >
    > **Compound Filter** `object`
    > Combine multiple filters using `and` or `or`.
    > > **Properties**
    > >
    > > *   `filters` `array` (Required)
    > >     Array of filters to combine. Items can be `ComparisonFilter` or `CompoundFilter`.
    > > *   `type` `string` (Required)
    > >     Type of operation: `and` or `or`.
*   `max_num_results` `integer` (Optional, defaults to 10)
    The maximum number of results to return. This number should be between 1 and 50 inclusive.
*   `ranking_options` `object` (Optional)
    Ranking options for search.
    > **Properties**
    >
    > *   `ranker` `string` (Optional, defaults to `auto`)
    >     Enable re-ranking; set to `none` to disable, which can help reduce latency.
    > *   `score_threshold` `number` (Optional, defaults to 0)
    > *   `rewrite_query` `boolean` (Optional, defaults to `false`)
    >     Whether to rewrite the natural language query for vector search.

#### Returns
A page of search results from the vector store.

#### Example request
```sh
curl -X POST \
https://api.openai.com/v1/vector_stores/vs_abc123/search \
-H "Authorization: Bearer $OPENAI_API_KEY" \
-H "Content-Type: application/json" \
-d '{"query": "What is the return policy?", "filters": {...}}'
```
#### Response
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
***

### The vector store object
A vector store is a collection of processed files can be used by the `file_search` tool.

*   `created_at` `integer`
    The Unix timestamp (in seconds) for when the vector store was created.
*   `expires_after` `object`
    The expiration policy for a vector store.
    > **Properties**
    >
    > *   `anchor` `string`
    >     Anchor timestamp after which the expiration policy applies. Supported anchors: `last_active_at`.
    > *   `days` `integer`
    >     The number of days after the anchor time that the vector store will expire.
*   `expires_at` `integer`
    The Unix timestamp (in seconds) for when the vector store will expire.
*   `file_counts` `object`
    > **Properties**
    >
    > *   `cancelled` `integer`
    >     The number of files that were cancelled.
    > *   `completed` `integer`
    >     The number of files that have been successfully processed.
    > *   `failed` `integer`
    >     The number of files that have failed to process.
    > *   `in_progress` `integer`
    >     The number of files that are currently being processed.
    > *   `total` `integer`
    >     The total number of files.
*   `id` `string`
    The identifier, which can be referenced in API endpoints.
*   `last_active_at` `integer`
    The Unix timestamp (in seconds) for when the vector store was last active.
*   `metadata` `map`
    Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format, and querying for objects via API or the dashboard. Keys are strings with a maximum length of 64 characters. Values are strings with a maximum length of 512 characters.
*   `name` `string`
    The name of the vector store.
*   `object` `string`
    The object type, which is always `vector_store`.
*   `status` `string`
    The status of the vector store, which can be either `expired`, `in_progress`, or `completed`. A status of `completed` indicates that the vector store is ready for use.
*   `usage_bytes` `integer`
    The total number of bytes used by the files in the vector store.

#### The vector store object
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