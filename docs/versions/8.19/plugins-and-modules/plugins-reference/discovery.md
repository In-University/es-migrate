## Discovery plugins

Discovery plugins extend Elasticsearch by adding new seed hosts providers that
can be used to extend the {ref}/modules-discovery.html[cluster formation
module].

#### Core discovery plugins

The core discovery plugins are:

**[EC2 discovery](#discovery-ec2)**:

The EC2 discovery plugin uses the [AWS API](https://github.com/aws/aws-sdk-java)
to identify the addresses of seed hosts.

**[Azure Classic discovery](#discovery-azure-classic)**:

The Azure Classic discovery plugin uses the Azure Classic API to identify the
addresses of seed hosts.

**[GCE discovery](#discovery-gce)**:

The Google Compute Engine discovery plugin uses the GCE API to identify the
addresses of seed hosts.

include::discovery-ec2.asciidoc[]

include::discovery-azure-classic.asciidoc[]

include::discovery-gce.asciidoc[]