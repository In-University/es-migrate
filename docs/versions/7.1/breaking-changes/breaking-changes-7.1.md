**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## Breaking changes in 7.1

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 7.1.

See also [*What’s new in 7.17*](release-highlights.html) and [Release notes](es-release-notes.html).

### HTTP changes

#### Deprecation of old HTTP settings

The `http.tcp_no_delay` setting is deprecated in 7.1. It is replaced by
`http.tcp.no_delay`.

### Network changes

#### Deprecation of old network settings

The `network.tcp.connect_timeout` setting is deprecated in 7.1. This setting
was a fallback setting for `transport.connect_timeout`. To change the default
connection timeout for client connections, modify `transport.connect_timeout`.

### Transport changes

#### Deprecation of old transport settings

The following settings are deprecated in 7.1. Each setting has a replacement
setting that was introduced in 6.7.

* `transport.tcp.port` is replaced by `transport.port`

* `transport.tcp.compress` is replaced by `transport.compress`

* `transport.tcp.connect_timeout` is replaced by `transport.connect_timeout`

* `transport.tcp_no_delay` is replaced by `transport.tcp.no_delay`

* `transport.profiles.profile_name.tcp_no_delay` is replaced by
`transport.profiles.profile_name.tcp.no_delay`

* `transport.profiles.profile_name.tcp_keep_alive` is replaced by
`transport.profiles.profile_name.tcp.keep_alive`

* `transport.profiles.profile_name.reuse_address` is replaced by
`transport.profiles.profile_name.tcp.reuse_address`

* `transport.profiles.profile_name.send_buffer_size` is replaced by `transport.profiles.profile_name.tcp.send_buffer_size`

* `transport.profiles.profile_name.receive_buffer_size` is replaced by `transport.profiles.profile_name.tcp.receive_buffer_size`