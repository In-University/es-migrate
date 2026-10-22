**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs/manage-data/data-store/mapping/removal-of-mapping-types).

## Removal of mapping types

Indices created in Elasticsearch 6.0.0 or later may only contain a
single [mapping type](mapping.html#mapping-type).  Indices created in 5.x with multiple
mapping types will continue to function as before in Elasticsearch 6.x.
Types will be deprecated in APIs in Elasticsearch 7.0.0, and completely
removed in 8.0.0.

### What are mapping types?

Since the first release of Elasticsearch, each document has been stored in a
single index and assigned a single mapping type.  A mapping type was used to
represent the type of document or entity being indexed, for instance a
`twitter` index might have a `user` type and a `tweet` type.

Each mapping type could have its own fields, so the `user` type might have a
`full_name` field, a `user_name` field, and an `email` field, while the
`tweet` type could have a `content` field, a `tweeted_at` field and, like the
`user` type, a `user_name` field.

Each document had a `_type` meta-field containing the type name, and searches
could be limited to one or more types by specifying the type name(s) in the
URL:

```
GET twitter/user,tweet/_search
{
  "query": {
    "match": {
      "user_name": "kimchy"
    }
  }
}
```

The `_type` field was combined with the document’s `_id` to generate a `_uid`
field, so documents of different types with the same `_id` could exist in a
single index.

Mapping types were also used to establish a
[parent-child relationship](mapping-parent-field.html)
between documents, so documents of type `question` could be parents to
documents of type `answer`.

### Why are mapping types being removed?

Initially, we spoke about an “index” being similar to a “database” in an
SQL database, and a “type” being equivalent to a
“table”.

This was a bad analogy that led to incorrect assumptions. In an SQL database,
tables are independent of each other.  The columns in one table have no
bearing on columns with the same name in another table.  This is not the case
for fields in a mapping type.

In an Elasticsearch index, fields that have the same name in different mapping
types are backed by the same Lucene field internally.  In other words, using
the example above, the `user_name` field in the `user` type is stored in
exactly the same field as the `user_name` field in the `tweet` type, and both
`user_name` fields must have the same mapping (definition) in both types.

This can lead to frustration when, for example, you want `deleted` to be a
`date` field in one type and a `boolean` field in another type in the same
index.

On top of that, storing different entities that have few or no fields in
common in the same index leads to sparse data and interferes with Lucene’s
ability to compress documents efficiently.

For these reasons, we have decided to remove the concept of mapping types from
Elasticsearch.

### Alternatives to mapping types

#### Index per document type

The first alternative is to have an index per document type.  Instead of
storing tweets and users in a single `twitter` index, you could store tweets
in the `tweets` index and users in the `user` index. Indices are completely
independent of each other and so there will be no conflict of field types
between indices.

This approach has two benefits:

* Data is more likely to be dense and so benefit from compression techniques
used in Lucene.

* The term statistics used for scoring in full text search are more likely to
be accurate because all documents in the same index represent a single
entity.

Each index can be sized appropriately for the number of documents it will
contain: you can use a smaller number of primary shards for `users` and a
larger number of primary shards for `tweets`.

#### Custom type field

Of course, there is a limit to how many primary shards can exist in a cluster
so you may not want to waste an entire shard for a collection of only a few
thousand documents.  In this case, you can implement your own custom `type`
field which will work in a similar way to the old `_type`.

Let’s take the `user`/`tweet` example above.  Originally, the workflow would
have looked something like this:

```
PUT twitter
{
  "mappings": {
    "user": {
      "properties": {
        "name": { "type": "text" },
        "user_name": { "type": "keyword" },
        "email": { "type": "keyword" }
      }
    },
    "tweet": {
      "properties": {
        "content": { "type": "text" },
        "user_name": { "type": "keyword" },
        "tweeted_at": { "type": "date" }
      }
    }
  }
}

PUT twitter/user/kimchy
{
  "name": "Shay Banon",
  "user_name": "kimchy",
  "email": "shay@kimchy.com"
}

PUT twitter/tweet/1
{
  "user_name": "kimchy",
  "tweeted_at": "2017-10-24T09:00:00Z",
  "content": "Types are going away"
}

GET twitter/tweet/_search
{
  "query": {
    "match": {
      "user_name": "kimchy"
    }
  }
}
```

You could achieve the same thing by adding a custom `type` field as follows:

```
PUT twitter
{
  "mappings": {
    "_doc": {
      "properties": {
        "type": { "type": "keyword" }, 
        "name": { "type": "text" },
        "user_name": { "type": "keyword" },
        "email": { "type": "keyword" },
        "content": { "type": "text" },
        "tweeted_at": { "type": "date" }
      }
    }
  }
}

PUT twitter/_doc/user-kimchy
{
  "type": "user", 
  "name": "Shay Banon",
  "user_name": "kimchy",
  "email": "shay@kimchy.com"
}

PUT twitter/_doc/tweet-1
{
  "type": "tweet", 
  "user_name": "kimchy",
  "tweeted_at": "2017-10-24T09:00:00Z",
  "content": "Types are going away"
}

GET twitter/_search
{
  "query": {
    "bool": {
      "must": {
        "match": {
          "user_name": "kimchy"
        }
      },
      "filter": {
        "match": {
          "type": "tweet" 
        }
      }
    }
  }
}
```

|  | The explicit type field takes the place of the implicit _type field. |
| --- | --- |

#### Parent/Child without mapping types

Previously, a parent-child relationship was represented by making one mapping
type the parent, and one or more other mapping types the children.  Without
types, we can no longer use this syntax.  The parent-child feature will
continue to function as before, except that the way of expressing the
relationship between documents has been changed to use the new
[`join` field](parent-join.html).

### Schedule for removal of mapping types

This is a big change for our users, so we have tried to make it as painless as
possible.  The change will roll out as follows:

Elasticsearch 5.6.0

* Setting `index.mapping.single_type: true` on an index will enable the
single-type-per-index behaviour which will be enforced in 6.0.

* The [`join` field](parent-join.html) replacement for parent-child is available
on indices created in 5.6.

Elasticsearch 6.x

* Indices created in 5.x will continue to function in 6.x as they did in 5.x.

* Indices created in 6.x only allow a single-type per index.  Any name
can be used for the type, but there can be only one. The preferred type name
is `_doc`, so that index APIs have the same path as they will have in 7.0:
`PUT {index}/_doc/{id}` and `POST {index}/_doc`

* The `_type` name can no longer be combined with the `_id` to form the `_uid`
field. The `_uid` field has become an alias for the `_id` field.

* New indices no longer support the old-style of parent/child and should
use the [`join` field](parent-join.html) instead.

* The `_default_` mapping type is deprecated.

* In 6.7, the index creation, index template, and mapping APIs support a query
string parameter (`include_type_name`) which indicates whether requests and
responses should include a type name. It defaults to `true`, and should be set
to an explicit value to prepare to upgrade to 7.0. Not setting `include_type_name`
will result in a deprecation warning. Indices which don’t have an explicit type will
use the dummy type name `_doc`.

Elasticsearch 7.x

* Specifying types in requests is deprecated. For instance, indexing a
document no longer requires a document `type`.  The new index APIs
are `PUT {index}/_doc/{id}` in case of explicit ids and `POST {index}/_doc`
for auto-generated ids.

* The `include_type_name` parameter in the index creation, index template,
and mapping APIs will default to `false`. Setting the parameter at all will
result in a deprecation warning.

* The `_default_` mapping type is removed.

Elasticsearch 8.x

* Specifying types in requests is no longer supported.

* The `include_type_name` parameter is removed.

### Migrating multi-type indices to single-type

The [Reindex API](docs-reindex.html) can be used to convert multi-type indices to
single-type indices. The following examples can be used in Elasticsearch 5.6
or Elasticsearch 6.x.  In 6.x, there is no need to specify
`index.mapping.single_type` as that is the default.

#### Index per document type

This first example splits our `twitter` index into a `tweets` index and a
`users` index:

```
PUT users
{
  "settings": {
    "index.mapping.single_type": true
  },
  "mappings": {
    "_doc": {
      "properties": {
        "name": {
          "type": "text"
        },
        "user_name": {
          "type": "keyword"
        },
        "email": {
          "type": "keyword"
        }
      }
    }
  }
}

PUT tweets
{
  "settings": {
    "index.mapping.single_type": true
  },
  "mappings": {
    "_doc": {
      "properties": {
        "content": {
          "type": "text"
        },
        "user_name": {
          "type": "keyword"
        },
        "tweeted_at": {
          "type": "date"
        }
      }
    }
  }
}

POST _reindex
{
  "source": {
    "index": "twitter",
    "type": "user"
  },
  "dest": {
    "index": "users",
    "type": "_doc"
  }
}

POST _reindex
{
  "source": {
    "index": "twitter",
    "type": "tweet"
  },
  "dest": {
    "index": "tweets",
    "type": "_doc"
  }
}
```

#### Custom type field

This next example adds a custom `type` field and sets it to the value of the
original `_type`.  It also adds the type to the `_id` in case there are any
documents of different types which have conflicting IDs:

```
PUT new_twitter
{
  "mappings": {
    "_doc": {
      "properties": {
        "type": {
          "type": "keyword"
        },
        "name": {
          "type": "text"
        },
        "user_name": {
          "type": "keyword"
        },
        "email": {
          "type": "keyword"
        },
        "content": {
          "type": "text"
        },
        "tweeted_at": {
          "type": "date"
        }
      }
    }
  }
}

POST _reindex
{
  "source": {
    "index": "twitter"
  },
  "dest": {
    "index": "new_twitter"
  },
  "script": {
    "source": """
      ctx._source.type = ctx._type;
      ctx._id = ctx._type + '-' + ctx._id;
      ctx._type = '_doc';
    """
  }
}
```

### Typeless APIs in 7.0

In Elasticsearch 7.0, each API will support typeless requests,
and specifying a type will produce a deprecation warning. Certain
typeless APIs are also available in 6.7, to enable a smooth upgrade
path to 7.0.

#### Indices APIs

Index creation, index template, and mapping APIs support a new `include_type_name`
URL parameter that specifies whether mapping definitions in requests and responses
should contain the type name. The parameter defaults to `true` in version 6.7 to
match the pre-7.0 behavior of using type names in mappings. It defaults to `false`
in version 7.0 and will be removed in version 8.0.

It should be set explicitly in 6.7 to prepare to upgrade to 7.0. To avoid deprecation
warnings in 6.7, the parameter can be set to either `true` or `false`. In 7.0, setting
`include_type_name` at all will result in a deprecation warning.

See some examples of interactions with Elasticsearch with this option set to `false`:

```
PUT index?include_type_name=false
{
  "mappings": {
    "properties": { 
      "foo": {
        "type": "keyword"
      }
    }
  }
}
```

|  | Mappings are included directly under the mappings key, without a type name. |
| --- | --- |

```
PUT index/_mappings?include_type_name=false
{
  "properties": { 
    "bar": {
      "type": "text"
    }
  }
}
```

|  | Mappings are included directly under the mappings key, without a type name. |
| --- | --- |

```
GET index/_mappings?include_type_name=false
```

The above call returns

```
{
  "index": {
    "mappings": {
      "properties": { 
        "foo": {
          "type": "keyword"
        },
        "bar": {
          "type": "text"
        }
      }
    }
  }
}
```

|  | Mappings are included directly under the mappings key, without a type name. |
| --- | --- |

#### Index templates

It is recommended to make index templates typeless by re-adding them with
`include_type_name` set to `false`. Under the hood, typeless templates will use
the dummy type `_doc` when creating indices.

In case typeless templates are used with typed index creation calls or typed
templates are used with typeless index creation calls, the template will still
be applied but the index creation call decides whether there should be a type
or not. For instance in the below example, `index-1-01` will have a type in
spite of the fact that it matches a template that is typeless, and `index-2-01`
will be typeless in spite of the fact that it matches a template that defines
a type. Both `index-1-01` and `index-2-01` will inherit the `foo` field from
the template that they match.

```
PUT _template/template1?include_type_name=false
{
  "index_patterns":[ "index-1-*" ],
  "mappings": {
    "properties": {
      "foo": {
        "type": "keyword"
      }
    }
  }
}

PUT _template/template2?include_type_name=true
{
  "index_patterns":[ "index-2-*" ],
  "mappings": {
    "type": {
      "properties": {
        "foo": {
          "type": "keyword"
        }
      }
    }
  }
}

PUT index-1-01?include_type_name=true
{
  "mappings": {
    "type": {
      "properties": {
        "bar": {
          "type": "long"
        }
      }
    }
  }
}

PUT index-2-01?include_type_name=false
{
  "mappings": {
    "properties": {
      "bar": {
        "type": "long"
      }
    }
  }
}
```

In case of implicit index creation, because of documents that get indexed in
an index that doesn’t exist yet, the template is always honored. This is
usually not a problem due to the fact that typeless index calls work on typed
indices.

#### Mixed-version clusters

In a cluster composed of both 6.7 and 7.0 nodes, the parameter
`include_type_name` should be specified in indices APIs like index
creation. This is because the parameter has a different default between
6.7 and 7.0, so the same mapping definition will not be valid for both
node versions.

Typeless document APIs such as `bulk` and `update` are only available as of
7.0, and will not work with 6.7 nodes. This also holds true for the typeless
versions of queries that perform document lookups, such as `terms`.