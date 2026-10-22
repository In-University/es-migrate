## Snapshot/Restore Repository Plugins

Repository plugins extend the {ref}/modules-snapshots.html[Snapshot/Restore]
functionality in Elasticsearch by adding repositories backed by the cloud or
by distributed file systems:

[float]
#### Core repository plugins

The core repository plugins are:

**[S3 Repository](#repository-s3)**:

The S3 repository plugin adds support for using S3 as a repository.

**[Azure Repository](#repository-azure)**:

The Azure repository plugin adds support for using Azure as a repository.

**[HDFS Repository](#repository-hdfs)**:

The Hadoop HDFS Repository plugin adds support for using HDFS as a repository.

**[Google Cloud Storage Repository](#repository-gcs)**:

The GCS repository plugin adds support for using Google Cloud Storage service as a repository.

[float]
### Community contributed repository plugins

The following plugin has been contributed by our community:

* [Openstack Swift](https://github.com/BigDataBoutique/elasticsearch-repository-swift) (by Wikimedia Foundation and BigData Boutique)

include::repository-azure.asciidoc[]

include::repository-s3.asciidoc[]

include::repository-hdfs.asciidoc[]

include::repository-gcs.asciidoc[]