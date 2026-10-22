# Breaking changes

[partintro]
--
This section discusses the changes that you need to be aware of when migrating
your application from one version of Elasticsearch to another.

As a general rule:

* Migration between minor versions -- e.g. `6.x` to `6.y` -- can be
  performed by [upgrading one node at a time](#rolling-upgrades).

* Migration between consecutive major versions -- e.g. `5.x` to `6.x` --
  requires a [full cluster restart](#restart-upgrade).

* Migration between non-consecutive major versions -- e.g. `2.x` to `6.x` --
  is not supported.

For more information, see [setup-upgrade](#setup-upgrade).

See also [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

--
include::migrate_6_0.asciidoc[]

include::migrate_6_1.asciidoc[]

include::migrate_6_2.asciidoc[]

include::migrate_6_3.asciidoc[]

include::migrate_6_4.asciidoc[]

include::migrate_6_5.asciidoc[]

include::migrate_6_6.asciidoc[]

include::migrate_6_7.asciidoc[]

include::migrate_6_8.asciidoc[]