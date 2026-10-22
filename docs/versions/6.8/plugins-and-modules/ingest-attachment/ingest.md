## Ingest Plugins

The ingest plugins extend Elasticsearch by providing additional ingest node capabilities.

[float]
### Core Ingest Plugins

The core ingest plugins are:

**[ingest-attachment](#ingest-attachment)**:

The ingest attachment plugin lets Elasticsearch extract file attachments in common formats (such as PPT, XLS, and PDF) by
using the Apache text extraction library [Tika](http://lucene.apache.org/tika/).

**[ingest-geoip](#ingest-geoip)**:

The `geoip` processor adds information about the geographical location of IP
addresses, based on data from the Maxmind databases. This processor adds this
information by default under the `geoip` field. The `geoip` processor is no
longer distributed as a plugin, but is now a module distributed by default with
Elasticsearch. See {ref}/geoip-processor.html[GeoIP processor] for more
details.

**[ingest-user-agent](#ingest-user-agent)**:

A processor that extracts details from the User-Agent header value. The
`user_agent` processor is no longer distributed as a plugin, but is now a module
distributed by default with Elasticsearch. See
{ref}/user-agent-processor.html[User Agent processor] for more details.

[float]
### Community contributed ingest plugins

The following plugin has been contributed by our community:

* [Ingest CSV Processor Plugin](https://github.com/johtani/elasticsearch-ingest-csv) (by Jun Ohtani)

include::ingest-attachment.asciidoc[]

include::ingest-geoip.asciidoc[]

include::ingest-user-agent.asciidoc[]