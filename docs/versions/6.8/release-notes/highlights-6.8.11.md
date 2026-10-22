## 6.8.11 release highlights

See also [Elasticsearch 6.8.11 release notes](#release-notes-6.8.11).

[float]
#### Fixed out-of-memory error when using {ccr} with large documents

A bug caused {ccr} to use more memory than configured with large documents,
which could cause memory pressure or even out-of-memory errors in some cases.