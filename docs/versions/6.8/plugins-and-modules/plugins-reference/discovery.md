## Discovery Plugins

Discovery plugins extend Elasticsearch by adding new discovery mechanisms that
can be used instead of {ref}/modules-discovery-zen.html[Zen Discovery].

[float]
#### Core discovery plugins

The core discovery plugins are:

**[EC2 discovery](#discovery-ec2)**:

The EC2 discovery plugin uses the [AWS API](https://github.com/aws/aws-sdk-java) for unicast discovery.

**[Azure Classic discovery](#discovery-azure-classic)**:

The Azure Classic discovery plugin uses the Azure Classic API for unicast discovery.

**[GCE discovery](#discovery-gce)**:

The Google Compute Engine discovery plugin uses the GCE API for unicast discovery.

**[File-based discovery](#discovery-file)**:

The File-based discovery plugin allows providing the unicast hosts list through a dynamically updatable file.

[float]
#### Community contributed discovery plugins

A number of discovery plugins have been contributed by our community:

* [eskka Discovery Plugin](https://github.com/shikhar/eskka) (by Shikhar Bhushan)
* [Kubernetes Discovery Plugin](https://github.com/fabric8io/elasticsearch-cloud-kubernetes) (by Jimmi Dyson, [fabric8](http://fabric8.io))

include::discovery-ec2.asciidoc[]

include::discovery-azure-classic.asciidoc[]

include::discovery-gce.asciidoc[]

include::discovery-file.asciidoc[]