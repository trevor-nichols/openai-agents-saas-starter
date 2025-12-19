# Containers
Create and manage containers for use with the Code Interpreter tool.

***

## Create container
`POST` `https://api.openai.com/v1/containers`

Creates a container.

### Request body
**`name`** *string* `Required`
<br>
Name of the container to create.

**`expires_after`** *object* `Optional`
<br>
Container expiration time in seconds relative to the 'anchor' time.
- **`anchor`** *string* `Required`
  <br>
  Time anchor for the expiration time. Currently only 'last_active_at' is supported.
- **`minutes`** *integer* `Required`

**`file_ids`** *array* `Optional`
<br>
IDs of files to copy to the container.

**`memory_limit`** *string* `Optional`
<br>
Optional memory limit for the container. Defaults to "1g".

### Returns
The created container object.

### Example request
```shell
curl https://api.openai.com/v1/containers \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "name": "My Container",
        "memory_limit": "4g"
      }'
```
### Response
```json
{
    "id": "cntr_682e30645a488191b6363a0cbefc0f0a025ec61b66250591",
    "object": "container",
    "created_at": 1747857508,
    "status": "running",
    "expires_after": {
        "anchor": "last_active_at",
        "minutes": 20
    },
    "last_active_at": 1747857508,
    "memory_limit": "4g",
    "name": "My Container"
}
```

***

## List containers
`GET` `https://api.openai.com/v1/containers`

Lists containers.

### Query parameters
**`after`** *string* `Optional`
<br>
A cursor for use in pagination. `after` is an object ID that defines your place in the list. For instance, if you make a list request and receive 100 objects, ending with `obj_foo`, your subsequent call can include `after=obj_foo` in order to fetch the next page of the list.

**`limit`** *integer* `Optional` `Defaults to 20`
<br>
A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 20.

**`order`** *string* `Optional` `Defaults to desc`
<br>
Sort order by the `created_at` timestamp of the objects. `asc` for ascending order and `desc` for descending order.

### Returns
A list of container objects.

### Example request
```shell
curl https://api.openai.com/v1/containers \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```
### Response
```json
{
  "object": "list",
  "data": [
    {
        "id": "cntr_682dfebaacac8198bbfe9c2474fb6f4a085685cbe3cb5863",
        "object": "container",
        "created_at": 1747844794,
        "status": "running",
        "expires_after": {
            "anchor": "last_active_at",
            "minutes": 20
        },
        "last_active_at": 1747844794,
        "memory_limit": "4g",
        "name": "My Container"
    }
  ],
  "first_id": "container_123",
  "last_id": "container_123",
  "has_more": false
}
```

***

## Retrieve container
`GET` `https://api.openai.com/v1/containers/{container_id}`

Retrieves a container.

### Path parameters
**`container_id`** *string* `Required`

### Returns
The container object.

### Example request
```shell
curl https://api.openai.com/v1/containers/cntr_682dfebaacac8198bbfe9c2474fb6f4a085685cbe3cb5863 \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```
### Response
```json
{
    "id": "cntr_682dfebaacac8198bbfe9c2474fb6f4a085685cbe3cb5863",
    "object": "container",
    "created_at": 1747844794,
    "status": "running",
    "expires_after": {
        "anchor": "last_active_at",
        "minutes": 20
    },
    "last_active_at": 1747844794,
    "memory_limit": "4g",
    "name": "My Container"
}
```

***

## Delete a container
`DELETE` `https://api.openai.com/v1/containers/{container_id}`

Delete a container.

### Path parameters
**`container_id`** *string* `Required`
<br>
The ID of the container to delete.

### Returns
Deletion Status

### Example request
```shell
curl -X DELETE https://api.openai.com/v1/containers/cntr_682dfebaacac8198bbfe9c2474fb6f4a085685cbe3cb5863 \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```
### Response
```json
{
    "id": "cntr_682dfebaacac8198bbfe9c2474fb6f4a085685cbe3cb5863",
    "object": "container.deleted",
    "deleted": true
}
```

***

## The container object

**`created_at`** *integer*
<br>
Unix timestamp (in seconds) when the container was created.

**`expires_after`** *object*
<br>
The container will expire after this time period. The anchor is the reference point for the expiration. The minutes is the number of minutes after the anchor before the container expires.
- **`anchor`** *string*
  <br>
  The reference point for the expiration.
- **`minutes`** *integer*
  <br>
  The number of minutes after the anchor before the container expires.

**`id`** *string*
<br>
Unique identifier for the container.

**`last_active_at`** *integer*
<br>
Unix timestamp (in seconds) when the container was last active.

**`memory_limit`** *string*
<br>
The memory limit configured for the container.

**`name`** *string*
<br>
Name of the container.

**`object`** *string*
<br>
The type of this object.

**`status`** *string*
<br>
Status of the container (e.g., active, deleted).

### Example container object
```json
{
   "id": "cntr_682dfebaacac8198bbfe9c2474fb6f4a085685cbe3cb5863",
   "object": "container",
   "created_at": 1747844794,
   "status": "running",
   "expires_after": {
     "anchor": "last_active_at",
     "minutes": 20
   },
   "last_active_at": 1747844794,
   "memory_limit": "1g",
   "name": "My Container"
}
```