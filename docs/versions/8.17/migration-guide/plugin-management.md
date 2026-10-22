**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs/reference/elasticsearch/plugins/plugin-management).

## Plugin management

### Managing plugins on Elasticsearch Service

Refer to the [Elasticsearch Service documentation](/guide/en/cloud/current/ec-adding-plugins.html) for information
about managing plugins on Elastic Cloud.

### Managing plugins for self-managed deployments

Use the `elasticsearch-plugin` command line tool to install, list, and remove plugins. It is
located in the `$ES_HOME/bin` directory by default but it may be in a
different location depending on which Elasticsearch package you installed:

* [Directory layout of `.tar.gz` archives](/guide/en/elasticsearch/reference/8.17/targz.html#targz-layout)

* [Directory layout of Windows `.zip` archives](/guide/en/elasticsearch/reference/8.17/zip-windows.html#windows-layout)

* [Directory layout of Debian package](/guide/en/elasticsearch/reference/8.17/deb.html#deb-layout)

* [Directory layout of RPM](/guide/en/elasticsearch/reference/8.17/rpm.html#rpm-layout)

Run the following command to get usage instructions:

```
sudo bin/elasticsearch-plugin -h
```

Running as root

If Elasticsearch was installed using the deb or rpm package then run
`/usr/share/elasticsearch/bin/elasticsearch-plugin` as `root` so it can write to the appropriate files on disk.
Otherwise run `bin/elasticsearch-plugin` as the user that owns all of the Elasticsearch
files.

### Docker

If you run Elasticsearch using Docker, you can manage plugins using a
[configuration file](manage-plugins-using-configuration-file.html).