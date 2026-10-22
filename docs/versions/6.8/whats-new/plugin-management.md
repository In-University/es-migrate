**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs/reference/elasticsearch/plugins/plugin-management).

## Plugin Management

The `plugin` script is used to install, list, and remove plugins. It is
located in the `$ES_HOME/bin` directory by default but it may be in a
different location depending on which Elasticsearch package you installed:

* [Directory layout of `.zip` and `.tar.gz` archives](/guide/en/elasticsearch/reference/6.8/zip-targz.html#zip-targz-layout)

* [Directory layout of Debian package](/guide/en/elasticsearch/reference/6.8/deb.html#deb-layout)

* [Directory layout of RPM](/guide/en/elasticsearch/reference/6.8/rpm.html#rpm-layout)

Run the following command to get usage instructions:

```
sudo bin/elasticsearch-plugin -h
```

Running as root

If Elasticsearch was installed using the deb or rpm package then run
`/usr/share/elasticsearch/bin/elasticsearch-plugin` as `root` so it can write to the appropriate files on disk.
Otherwise run `bin/elasticsearch-plugin` as the user that owns all of the Elasticsearch
files.