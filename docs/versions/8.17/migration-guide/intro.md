**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs/reference/elasticsearch/plugins).

## Introduction to plugins

Plugins are a way to enhance the core Elasticsearch functionality in a custom
manner. They range from adding custom mapping types, custom analyzers, native
scripts, custom discovery and more.

Plugins contain JAR files, but may also contain scripts and config files, and
must be installed on every node in the cluster. After installation, each
node must be restarted before the plugin becomes visible.

A full cluster restart is required for installing plugins that have
custom cluster state metadata. It is still possible to upgrade
such plugins with a rolling restart.

This documentation distinguishes two categories of plugins:

Core Plugins

This category identifies plugins that are part of Elasticsearch
project. Delivered at the same time as Elasticsearch, their version number always
matches the version number of Elasticsearch itself. These plugins are maintained
by the Elastic team with the appreciated help of amazing community members (for
open source plugins). Issues and bug reports can be reported on the
[Github project page](https://github.com/elastic/elasticsearch).

Community contributed

This category identifies plugins that are external to
the Elasticsearch project. They are provided by individual developers or private
companies and have their own licenses as well as their own versioning system.
Issues and bug reports can usually be reported on the community plugin’s web site.

For advice on writing your own plugin, refer to [*Creating an Elasticsearch plugin*](plugin-authors.html).