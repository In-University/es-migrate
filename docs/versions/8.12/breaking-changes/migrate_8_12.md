## Migrating to 8.12

This section discusses the changes that you need to be aware of when migrating
your application to Elasticsearch 8.12.

See also [release-highlights](#release-highlights) and [es-release-notes](#es-release-notes).

### Breaking changes

There are no breaking changes in 8.12

### Notable changes

There are notable changes in 8.12 that you need to be aware of, items that we may consider as notable changes are

* Changes to features that are in Technical Preview.
* Changes to log formats.
* Changes to non public APIs.
* Behaviour changes that repair critical bugs.

#### Authorization changes

.Fixed JWT principal from claims
[%collapsible]
====
*Details* +
This changes the format of a JWT's principal before the JWT is actually validated by any JWT realm. The JWT's principal is a convenient way to refer to a JWT that has not yet been verified by a JWT realm. The JWT's principal is printed in the audit and regular logs (notably for auditing authn failures) as well as the smart realm chain reordering optimization. The JWT principal is NOT required to be identical to the JWT-authenticated user's principal, but in general, they should be similar. Previously, the JWT's principal was built by individual realms in the same way the realms built the authenticated user's principal. This had the advantage that, in simpler JWT realms configurations (e.g. a single JWT realm in the chain), the JWT principal and the authenticated user's principal are very similar. However the drawback is that, in general, the JWT principal and the user principal can be very different (i.e. in the case where one JWT realm builds the JWT principal and a different one builds the user principal). Another downside is that the (unauthenticated) JWT principal depended on realm ordering, which makes identifying the JWT from its principal dependent on the ES authn realm configuration. This PR implements a consistent fixed logic to build the JWT principal, which only depends on the JWT's claims and no ES configuration.

*Impact* +
Users will observe changed format and values for the `user.name` attribute of `authentication_failed` audit log events, in the JWT (failed) authn case.
====

#### Java API changes

.Plugin.createComponents method has been refactored to take a single PluginServices object
[%collapsible]
====
*Details* +
Plugin.createComponents currently takes several different service arguments. The signature of this method changes every time a new service is added. The method has now been modified to take a single interface object that new services are added to. This will reduce API incompatibility issues when a new service is introduced in the future.

*Impact* +
Plugins that override createComponents will need to be refactored to override the new method on ES 8.12+
====

#### REST API changes

.[ES|QL] pow function always returns double
[%collapsible]
====
*Details* +
This corrects an earlier mistake in the ES|QL language design. Initially we had thought to have pow return the same type as its inputs, but in practice even for integer inputs this quickly grows out of the representable range, and we returned null much of the time. This also created a lot of edge cases around casting to/from doubles (which the underlying java function uses). The version in this PR follows the java spec, by always casting its inputs to doubles, and returning a double. Doing it this way also allows for a rather significant reduction in lines of code.

*Impact* +
low. Most queries should continue to function with the change.
====