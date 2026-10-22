## Snapshot/restore repository plugins

Repository plugins extend the {ref}/snapshot-restore.html[Snapshot/Restore]
functionality in Elasticsearch by adding repositories backed by the cloud or
by distributed file systems:

#### Official repository plugins

NOTE: Support for S3, GCS and Azure repositories is now bundled in Elasticsearch by
default.

The official repository plugins are:

**[HDFS Repository](#repository-hdfs)**:

The Hadoop HDFS Repository plugin adds support for using HDFS as a repository.

### Community contributed repository plugins

The following plugin has been contributed by our community:

* [Openstack Swift](https://github.com/BigDataBoutique/elasticsearch-repository-swift) (by Wikimedia Foundation and BigData Boutique)

include::repository-hdfs.asciidoc[]