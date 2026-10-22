## 6.8.13 release highlights

See also [Elasticsearch 6.8.13 release notes](#release-notes-6.8.13).

[float]
#### Fixed retries for {ccr}

{ccr-cap} now retries operations that failed due to a circuit breaker or a lost
remote cluster connection.