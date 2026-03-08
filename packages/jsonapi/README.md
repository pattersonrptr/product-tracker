# fastapi-jsonapi

A lightweight [JSON:API](https://jsonapi.org/format/) implementation for
[FastAPI](https://fastapi.tiangolo.com/) using [Pydantic](https://docs.pydantic.dev/).

## Installation

```bash
pip install fastapi-jsonapi
```

## Features

- Pydantic v2 models for JSON:API **resource objects** and **error responses**
- Generic **middleware factory** that sets `Content-Type: application/vnd.api+json`
- Follows the [JSON:API 1.0 specification](https://jsonapi.org/format/)

## Quick Start

### Resource models

```python
from fastapi_jsonapi import (
    ResourceObject,
    ResourceObjectForCreation,
    SingleResourceRequest,
    SingleResourceResponse,
    CollectionResponse,
    ResourceIdentifier,
)

# Build a resource object from a Pydantic model or plain object
resource = ResourceObject.from_model(my_entity, type_name="users")

# Single-resource response
response = SingleResourceResponse(data=resource)

# Collection response with metadata
collection = CollectionResponse(
    data=[resource],
    meta={"total": 1},
    links={"self": "https://example.com/users"},
)
```

### Error models

```python
from fastapi_jsonapi import JsonApiError, JsonApiErrorResponse

error = JsonApiError(
    status="422",
    code="invalid_email",
    title="Invalid email",
    detail="The provided email address is not valid.",
    source={"pointer": "/data/attributes/email"},
)

error_response = JsonApiErrorResponse(errors=[error])
```

### Content-Type middleware

```python
from fastapi import FastAPI
from fastapi_jsonapi.middleware import make_jsonapi_middleware

app = FastAPI()

# Apply only to specific path prefixes
app.middleware("http")(make_jsonapi_middleware(path_prefixes=["/users", "/auth"]))

# Or apply to all routes
app.middleware("http")(make_jsonapi_middleware())
```

## License

MIT
