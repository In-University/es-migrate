**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/dynamic).

## `dynamic`

When you index a document containing a new field, Elasticsearch [adds the field dynamically](dynamic-mapping.html) to a document or to inner objects within a document. The
following document adds the string field `username`, the object field
`name`, and two string fields under the `name` object:

```
PUT my-index-000001/_doc/1
{
  "username": "johnsmith",
  "name": { 
    "first": "John",
    "last": "Smith"
  }
}

GET my-index-000001/_mapping
```

|  | Refer to fields under the name object as name.first and name.last . |
| --- | --- |
|  | Check the mapping to view changes. |

The following document adds two string fields: `email` and `name.middle`:

```
PUT my-index-000001/_doc/2
{
  "username": "marywhite",
  "email": "mary@white.com",
  "name": {
    "first": "Mary",
    "middle": "Alice",
    "last": "White"
  }
}

GET my-index-000001/_mapping
```

### Setting `dynamic` on inner objects

[Inner objects](object.html) inherit the `dynamic` setting from their parent
object or from the mapping type. In the following example, dynamic mapping is
disabled at the type level, so no new top-level fields will be added
dynamically.

However, the `user.social_networks` object enables dynamic mapping, so you can
add fields to this inner object.

```
PUT my-index-000001
{
  "mappings": {
    "dynamic": false, 
    "properties": {
      "user": { 
        "properties": {
          "name": {
            "type": "text"
          },
          "social_networks": {
            "dynamic": true, 
            "properties": {}
          }
        }
      }
    }
  }
}
```

|  | Disables dynamic mapping at the type level. |
| --- | --- |
|  | The user object inherits the type-level setting. |
|  | Enables dynamic mapping for this inner object. |

### Parameters for `dynamic`

The `dynamic` parameter controls whether new fields are added dynamically, and
accepts the following parameters:

| true | New fields are added to the mapping (default). |
| --- | --- |
| runtime | New fields are added to the mapping as runtime fields . These fields are not indexed, and are loaded from _source at query time. |
| false | New fields are ignored. These fields will not be indexed or searchable, but will still appear in the _source field of returned hits. These fields will not be added to the mapping, and new fields must be added explicitly. |
| strict | If new fields are detected, an exception is thrown and the document is rejected. New fields must be explicitly added to the mapping. |