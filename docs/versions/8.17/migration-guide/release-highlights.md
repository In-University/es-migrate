**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs).

## What’s new in 8.17

Here are the highlights of what’s new and improved in Elasticsearch 8.17!
For detailed information about this release, see the [Release notes](es-release-notes.html) and
[Migration guide](breaking-changes.html).

Other versions:

[8.16](/guide/en/elasticsearch/reference/8.16/release-highlights.html)
| [8.15](/guide/en/elasticsearch/reference/8.15/release-highlights.html)
| [8.14](/guide/en/elasticsearch/reference/8.14/release-highlights.html)
| [8.13](/guide/en/elasticsearch/reference/8.13/release-highlights.html)
| [8.12](/guide/en/elasticsearch/reference/8.12/release-highlights.html)
| [8.11](/guide/en/elasticsearch/reference/8.11/release-highlights.html)
| [8.10](/guide/en/elasticsearch/reference/8.10/release-highlights.html)
| [8.9](/guide/en/elasticsearch/reference/8.9/release-highlights.html)
| [8.8](/guide/en/elasticsearch/reference/8.8/release-highlights.html)
| [8.7](/guide/en/elasticsearch/reference/8.7/release-highlights.html)
| [8.6](/guide/en/elasticsearch/reference/8.6/release-highlights.html)
| [8.5](/guide/en/elasticsearch/reference/8.5/release-highlights.html)
| [8.4](/guide/en/elasticsearch/reference/8.4/release-highlights.html)
| [8.3](/guide/en/elasticsearch/reference/8.3/release-highlights.html)
| [8.2](/guide/en/elasticsearch/reference/8.2/release-highlights.html)
| [8.1](/guide/en/elasticsearch/reference/8.1/release-highlights.html)
| [8.0](/guide/en/elasticsearch/reference/8.0/release-highlights.html)

### `logsdb` index mode is now generally available

The `logsdb` index mode has been GA-ed. This feature allows Elasticsearch to store logs more efficiently.

`logsdb` index mode allows to reduce storage usage up to ~3 times compared to storing logs in Elasticsearch using the default index mode.
Refer to the [documentation](logs-data-stream.html) for further information.

### Elastic Rerank

In 8.17, we are introducing [Elastic Rerank](/guide/en/machine-learning/8.17/ml-nlp-rerank.html), Elastic’s new model for semantic reranking. Reranking can be used as the second stage on top of your existing search approach, whether this is lexical search, ELSER, or dense embeddings, resulting in significant semantic relevance gains mainly via recall improvements. This is very important for RAG applications, where you want to send the most relevant information to an LLM in order to generate the possible responses.

Elastic Rerank is a cross-encoder architecture and it is in technical preview in 8.17.

To understand reranking and how you can use it to improve your search, read [What is semantic reranking and how to use it](/search-labs/blog/elastic-semantic-reranker-part-1), a blog by the creators of Elastic Rerank.

For more information on the Elastic Rerank model architecture and how it compares for relevance and cost against other reranking models, see [Introducing Elastic Rerank](/search-labs/blog/elastic-semantic-reranker-part-2) by the same authors.

### Pre-configured default ELSER endpoint

With this release, we are introducing a pre-configured default ELSER endpoint. This removes the need for any inference configuration in order to use ELSER. There is no more need for an inference endpoint setup or for downloading the model and configuring threads and allocations through the trained models UI. Simply create a [semantic text](semantic-text.html) mapping with your indices and start using it. The default inference endpoint will download, deploy and start using ELSER for inference with  [adaptive allocations](/guide/en/machine-learning/8.17/ml-nlp-auto-scale.html#nlp-model-adaptive-allocations) out of the box.

### Full-text search for ES|QL

The technical preview of the new `MATCH` and `QSTR` (query string) functions in ES|QL makes log searches easier and more intuitive. `MATCH` delivers full-text search functionality in ES|QL using a Lucene match query, while `QTSR` aids in more advanced filtering of log data by enabling Lucene query string queries.

Full-text search for ES|QL enables easier and more performant searching in Discover, especially when dealing with multiple terms or conditional logic. Learn more in the [ES|QL full-text search documentation](esql-functions-operators.html#esql-search-functions).