## Creating an Elasticsearch plugin

Elasticsearch plugins are modular bits of code that add functionality to
Elasticsearch. Plugins are written in Java and implement Java interfaces that
are defined in the source code. Plugins are composed of JAR files and metadata
files, compressed in a single zip file.

There are two ways to create a plugin:

**[creating-stable-plugins](#creating-stable-plugins)**:
Text analysis plugins can be developed against the stable plugin API to provide
Elasticsearch with custom Lucene analyzers, token filters, character filters, and
tokenizers.

**[creating-classic-plugins](#creating-classic-plugins)**:
Other plugins can be developed against the classic plugin API to provide custom
authentication, authorization, or scoring mechanisms, and more.

:plugin-type: stable
include::development/creating-stable-plugins.asciidoc[]
include::development/example-text-analysis-plugin.asciidoc[]
:!plugin-type:

:plugin-type: classic
include::development/creating-classic-plugins.asciidoc[]
:!plugin-type: