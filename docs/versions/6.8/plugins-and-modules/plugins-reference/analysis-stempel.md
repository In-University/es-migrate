### Stempel Polish Analysis Plugin

The Stempel Analysis plugin integrates Lucene's Stempel analysis
module for Polish into elasticsearch.

It provides high quality stemming for Polish, based on the
[Egothor project](http://www.egothor.org/).

:plugin_name: analysis-stempel
include::install_remove.asciidoc[]

[float]
#### `stempel` tokenizer and token filter

The plugin provides the `polish` analyzer and `polish_stem` token filter,
which are not configurable.