[role="xpack"]
[testenv="basic"]
### Migration upgrade API

IMPORTANT: To prepare a cluster for an upgrade to Elasticsearch version 7, use
the {kibana-ref}/upgrade-assistant.html[Kibana Upgrade Assistant] or
[reindex manually](#reindex-upgrade) before upgrading.

ifdef::asciidoctor[]
deprecated::[6.7, "Use the {kibana-ref}/upgrade-assistant.html[Kibana Upgrade Assistant] or [reindex manually](#reindex-upgrade) before upgrading."]
endif::[]
ifndef::asciidoctor[]
deprecated[6.7, Use the {kibana-ref}/upgrade-assistant.html[Kibana Upgrade
Assistant] or [reindex manually](#reindex-upgrade) before upgrading.]
endif::[]
The migration upgrade API performs the upgrade of internal indices to make them
compatible with version 6 of Elasticsearch.

[float]
#### Request

`POST /_xpack/migration/upgrade/<index_name>`

[float]
#### Description

Indices must be upgraded one at a time.

[float]
#### Path Parameters

**`index_name`**:
  (string) Identifier for the index.

**`wait_for_completion`**:
  (boolean) Defines whether the upgrade call blocks until the upgrade process is
  finished. The default value is `true`. If set to `false`, the upgrade can be
  performed asynchronously.

//==== Query Parameters

//==== Authorization

[float]
#### Examples

The following example submits a POST request to the
`/_xpack/migration/upgrade/<index_name>` endpoint:

[source,js]
--------------------------------------------------
POST /_xpack/migration/upgrade/.watches
--------------------------------------------------
// CONSOLE
// TEST[skip:cannot create an old index in docs test]

A successful call returns the statistics about the upgrade process:

[source,js]
--------------------------------------------------
{
  "took" : 127,
  "timed_out" : false,
  "total" : 4,
  "updated" : 0,
  "created" : 4,
  "deleted" : 0,
  "batches" : 1,
  "version_conflicts" : 0,
  "noops" : 0,
  "retries" : {
    "bulk" : 0,
    "search" : 0
  },
  "throttled_millis" : 0,
  "failures" : [ ]
}
--------------------------------------------------
// NOTCONSOLE

The following example upgrades a large index asynchronously by specifying the
`wait_for_completion` parameter:

[source,js]
--------------------------------------------------
POST /_xpack/migration/upgrade/.watches?wait_for_completion=false
--------------------------------------------------
// CONSOLE
// TEST[skip:cannot create an old index in docs test]

This call should return the id of the upgrade process task:

[source,js]
--------------------------------------------------
{
  "task" : "PFvgv7T6TGumRyFF3vqTFg:1137"
}
--------------------------------------------------
// NOTCONSOLE

The status of the running or finished upgrade requests can be obtained by using
the [Task API](#tasks):

[source,js]
--------------------------------------------------
GET _tasks/PFvgv7T6TGumRyFF3vqTFg:1137?detailed=true
--------------------------------------------------
// CONSOLE
// TEST[skip:cannot create an old index in docs test]

[source,js]
--------------------------------------------------
{
  "completed" : true, <1>
  "task" : {
    "node" : "PFvgv7T6TGumRyFF3vqTFg",
    "id" : 1137,
    "type" : "transport",
    "action" : "cluster:admin/xpack/upgrade",
    "description" : "",
    "start_time_in_millis" : 1500650625413,
    "running_time_in_nanos" : 947456819,
    "cancellable" : true
  },
  "response" : { <2>
    "took" : 212,
    "timed_out" : false,
    "total" : 4,
    "updated" : 0,
    "created" : 4,
    "deleted" : 0,
    "batches" : 1,
    "version_conflicts" : 0,
    "noops" : 0,
    "retries" : {
      "bulk" : 0,
      "search" : 0
    },
    "throttled_millis" : 0,
    "failures" : [ ]
  }
}
--------------------------------------------------
// NOTCONSOLE

<1> If the `completed` field value is `true`, the upgrade request has finished.
If it is `false`, the request is still running.

<2> The `response` field contains the status of the upgrade request.