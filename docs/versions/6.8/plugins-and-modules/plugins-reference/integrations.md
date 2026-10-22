## Integrations

Integrations are not plugins, but are external tools or modules that make it easier to work with Elasticsearch.

[float]
### CMS integrations

[float]
#### Supported by the community:

* [Drupal](http://drupal.org/project/search_api_elasticsearch):
  Drupal Elasticsearch integration via Search API.

* [Drupal](https://drupal.org/project/elasticsearch_connector):
  Drupal Elasticsearch integration.

* [ElasticPress](https://wordpress.org/plugins/elasticpress/):
  Elasticsearch WordPress Plugin

* [WPSOLR](https://wordpress.org/plugins/wpsolr-search-engine/):
  Elasticsearch (and Apache Solr) WordPress Plugin

* [Tiki Wiki CMS Groupware](https://doc.tiki.org/Elasticsearch):
  Tiki has native support for Elasticsearch. This provides faster & better
  search (facets, etc), along with some Natural Language Processing features
  (ex.: More like this)

* [XWiki Next Generation Wiki](http://extensions.xwiki.org/xwiki/bin/view/Extension/Elastic+Search+Macro/):
  XWiki has an Elasticsearch and Kibana macro allowing to run Elasticsearch queries and display the results in XWiki pages using XWiki's scripting language as well as include Kibana Widgets in XWiki pages

[float]
### Data import/export and validation

NOTE: Rivers were used to import data from external systems into Elasticsearch prior to the 2.0 release. Elasticsearch
releases 2.0 and later do not support rivers.

[float]
#### Supported by Elasticsearch:

* {logstash-ref}/plugins-outputs-elasticsearch.html[Logstash output to Elasticsearch]:
  The Logstash `elasticsearch` output plugin.
* {logstash-ref}/plugins-inputs-elasticsearch.html[Elasticsearch input to Logstash]
  The Logstash `elasticsearch` input plugin.
* {logstash-ref}/plugins-filters-elasticsearch.html[Elasticsearch event filtering in Logstash]
  The Logstash `elasticsearch` filter plugin.
* {logstash-ref}/plugins-codecs-es_bulk.html[Elasticsearch bulk codec]
  The Logstash `es_bulk` plugin decodes the Elasticsearch bulk format into individual events.

[float]
#### Supported by the community:

* [JDBC importer](https://github.com/jprante/elasticsearch-jdbc):
  The Java Database Connection (JDBC) importer allows to fetch data from JDBC sources for indexing into Elasticsearch (by Jörg Prante)

* https://github.com/BigDataDevs/kafka-elasticsearch-consumer [Kafka Standalone Consumer(Indexer)]:
  Kafka Standalone Consumer [Indexer] will read messages from Kafka in batches, processes(as implemented) and bulk-indexes them into Elasticsearch. Flexible and scalable. More documentation in above GitHub repo's Wiki.

* [Mongolastic](https://github.com/ozlerhakan/mongolastic):
  A tool that clones data from Elasticsearch to MongoDB and vice versa

* [Scrutineer](https://github.com/Aconex/scrutineer):
  A high performance consistency checker to compare what you've indexed
  with your source of truth content (e.g. DB)

* [IMAP/POP3/Mail importer](https://github.com/salyh/elasticsearch-imap):
  The Mail importer allows to fetch data from IMAP and POP3 servers for indexing into Elasticsearch (by Hendrik Saly)

* [FS Crawler](https://github.com/dadoonet/fscrawler):
  The File System (FS) crawler allows to index documents (PDF, Open Office...) from your local file system and over SSH. (by David Pilato)

[float]
### Deployment

[float]
#### Supported by Elasticsearch:

* [Ansible playbook for Elasticsearch](https://github.com/elastic/ansible-elasticsearch):
  An officially supported ansible playbook for Elasticsearch. Tested with the latest version of 5.x and 6.x on Ubuntu 14.04/16.04, Debian 8, Centos 7.

* [Puppet](https://github.com/elastic/puppet-elasticsearch):
  Elasticsearch puppet module.

[float]
#### Supported by the community:

* [Chef](https://github.com/elastic/cookbook-elasticsearch):
  Chef cookbook for Elasticsearch

[float]
### Framework integrations

[float]
#### Supported by the community:

* [Aspire for Elasticsearch](http://www.searchtechnologies.com/aspire-for-elasticsearch):
  Aspire, from Search Technologies, is a powerful connector and processing
  framework designed for unstructured data. It has connectors to internal and
  external repositories including SharePoint, Documentum, Jive, RDB, file
  systems, websites and more, and can transform and normalize this data before
  indexing in Elasticsearch.

* [Apache Camel Integration](https://camel.apache.org/elasticsearch.html):
  An Apache camel component to integrate Elasticsearch

* [Catmanadu](https://metacpan.org/release/Catmandu-Store-ElasticSearch):
  An Elasticsearch backend for the Catmandu framework.

* [elasticsearch-test](https://github.com/tlrx/elasticsearch-test):
  Elasticsearch Java annotations for unit testing with
  [JUnit](http://www.junit.org/)

* [FOSElasticaBundle](https://github.com/FriendsOfSymfony/FOSElasticaBundle):
  Symfony2 Bundle wrapping Elastica.

* [Grails](http://grails.org/plugin/elasticsearch):
  Elasticsearch Grails plugin.

* [Haystack](http://haystacksearch.org/):
  Modular search for Django

* [Hibernate Search](http://hibernate.org/search/)
  Integration with Hibernate ORM, from the Hibernate team. Automatic synchronization of write operations, yet exposes full Elasticsearch capabilities for queries. Can return either Elasticsearch native or re-map queries back into managed entities loaded within transaction from the reference database.

* [play2-elasticsearch](https://github.com/cleverage/play2-elasticsearch):
  Elasticsearch module for Play Framework 2.x

* [Spring Data Elasticsearch](https://github.com/spring-projects/spring-data-elasticsearch):
  Spring Data implementation for Elasticsearch

* [Spring Elasticsearch](https://github.com/dadoonet/spring-elasticsearch):
  Spring Factory for Elasticsearch

* [Twitter Storehaus](https://github.com/twitter/storehaus):
  Thin asynchronous Scala client for Storehaus.

[float]
### Hadoop integrations

[float]
#### Supported by Elasticsearch:

* link:/guide/en/elasticsearch/hadoop/current/[es-hadoop]: Elasticsearch real-time
  search and analytics natively integrated with Hadoop. Supports Map/Reduce,
  Cascading, Apache Hive, Apache Pig, Apache Spark and Apache Storm.

[float]
### Health and Performance Monitoring

[float]
#### Supported by the community:

* [check_elasticsearch](https://github.com/anchor/nagios-plugin-elasticsearch):
  An Elasticsearch availability and performance monitoring plugin for
  Nagios.

* [check-es](https://github.com/radu-gheorghe/check-es):
  Nagios/Shinken plugins for checking on Elasticsearch

* [es2graphite](https://github.com/mattweber/es2graphite):
  Send cluster and indices stats and status to Graphite for monitoring and graphing.

* [ElasticOcean](https://itunes.apple.com/us/app/elasticocean/id955278030?ls=1&mt=8):
  Elasticsearch & DigitalOcean iOS Real-Time Monitoring tool to keep an eye on DigitalOcean Droplets or Elasticsearch instances or both of them on-a-go.

* [opsview-elasticsearch](https://github.com/rbramley/Opsview-elasticsearch):
  Opsview plugin written in Perl for monitoring Elasticsearch

* [Scout](https://scoutapp.com): Provides plugins for monitoring Elasticsearch [nodes](https://scoutapp.com/plugin_urls/1331-elasticsearch-node-status), [clusters](https://scoutapp.com/plugin_urls/1321-elasticsearch-cluster-status), and [indices](https://scoutapp.com/plugin_urls/1341-elasticsearch-index-status).

* [SPM for Elasticsearch](http://sematext.com/spm/index.html):
  Performance monitoring with live charts showing cluster and node stats, integrated
  alerts, email reports, etc.

[float]
### Other integrations

[float]
#### Supported by the community:

* [Pes](https://github.com/kodcu/pes):
  A pluggable elastic JavaScript query DSL builder for Elasticsearch

* [Wireshark](https://www.wireshark.org/):
  Protocol dissection for Zen discovery, HTTP and the binary protocol

* [ItemsAPI](https://www.itemsapi.com/):
  Search backend for mobile and web

These projects appear to have been abandoned:

* [daikon](http://www.github.com/neogenix/daikon):
  Daikon Elasticsearch CLI

* [dangle](https://github.com/fullscale/dangle):
  A set of AngularJS directives that provide common visualizations for Elasticsearch based on
  D3.
* [eslogd](https://github.com/OlegKunitsyn/eslogd):
  Linux daemon that replicates events to a central Elasticsearch server in realtime