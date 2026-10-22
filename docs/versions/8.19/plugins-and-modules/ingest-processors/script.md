### Script processor

Runs an inline or stored [script](#modules-scripting) on incoming documents. The
script runs in the {painless}/painless-ingest-processor-context.html[`ingest`]
context.

The script processor uses the [script cache](#scripts-and-search-speed) to avoid
recompiling the script for each incoming document. To improve performance,
ensure the script cache is properly sized before using a script processor in
production.

.Script options
[options="header"]
|======
| Name        | Required  | Default    | Description
| `lang`      | no        | "painless" | [Script language](#scripting-available-languages).
| `id`        | no        | -          | ID of a [stored script](#create-stored-script-api).
                                         If no `source` is specified, this parameter is required.
| `source`    | no        | -          | Inline script.
                                         If no `id` is specified, this parameter is required.
| `params`    | no        | -          | Object containing parameters for the script.
include::common-options.asciidoc[]
|======

#### Access source fields

The script processor parses each incoming document's JSON source fields into a
set of maps, lists, and primitives. To access these fields with a Painless
script, use the
{painless}/painless-operators-reference.html#map-access-operator[map access
operator]: `ctx['my-field']`. You can also use the shorthand `ctx.<my-field>`
syntax.

NOTE: The script processor does not support the `ctx['_source']['my-field']` or
`ctx._source.<my-field>` syntaxes.

The following processor uses a Painless script to extract the `tags` field from
the `env` source field.

[source,console]
```
POST _ingest/pipeline/_simulate
{
  "pipeline": {
    "processors": [
      {
        "script": {
          "description": "Extract 'tags' from 'env' field",
          "lang": "painless",
          "source": """
            String[] envSplit = ctx['env'].splitOnToken(params['delimiter']);
            ArrayList tags = new ArrayList();
            tags.add(envSplit[params['position']].trim());
            ctx['tags'] = tags;
          """,
          "params": {
            "delimiter": "-",
            "position": 1
          }
        }
      }
    ]
  },
  "docs": [
    {
      "_source": {
        "env": "es01-prod"
      }
    }
  ]
}
```

The processor produces:

[source,console-result]
```
{
  "docs": [
    {
      "doc": {
        ...
        "_source": {
          "env": "es01-prod",
          "tags": [
            "prod"
          ]
        }
      }
    }
  ]
}
```
// TESTRESPONSE[s/\.\.\./"_index":"_index","_id":"_id","_version":"-3","_ingest":{"timestamp":$body.docs.0.doc._ingest.timestamp},/]

#### Access metadata fields

You can also use a script processor to access metadata fields. The following
processor uses a Painless script to set an incoming document's `_index`.

[source,console]
```
POST _ingest/pipeline/_simulate
{
  "pipeline": {
    "processors": [
      {
        "script": {
          "description": "Set index based on `lang` field and `dataset` param",
          "lang": "painless",
          "source": """
            ctx['_index'] = ctx['lang'] + '-' + params['dataset'];
          """,
          "params": {
            "dataset": "catalog"
          }
        }
      }
    ]
  },
  "docs": [
    {
      "_index": "generic-index",
      "_source": {
        "lang": "fr"
      }
    }
  ]
}
```

The processor changes the document's `_index` to `fr-catalog` from
`generic-index`.

[source,console-result]
```
{
  "docs": [
    {
      "doc": {
        ...
        "_index": "fr-catalog",
        "_source": {
          "lang": "fr"
        }
      }
    }
  ]
}
```
// TESTRESPONSE[s/\.\.\./"_id":"_id","_version":"-3","_ingest":{"timestamp":$body.docs.0.doc._ingest.timestamp},/]