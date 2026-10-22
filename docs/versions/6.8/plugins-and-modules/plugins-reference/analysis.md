## Analysis Plugins

Analysis plugins extend Elasticsearch by adding new analyzers, tokenizers,
token filters, or character filters to Elasticsearch.

[float]
#### Core analysis plugins

The core analysis plugins are:

**[ICU](#analysis-icu)**:

Adds extended Unicode support using the [ICU](http://site.icu-project.org/)
libraries, including better analysis of Asian languages, Unicode
normalization, Unicode-aware case folding, collation support, and
transliteration.

**[Kuromoji](#analysis-kuromoji)**:

Advanced analysis of Japanese using the [Kuromoji analyzer](http://www.atilika.org/).

**[Nori](#analysis-nori)**:

Morphological analysis of Korean using the Lucene Nori analyzer.

**[Phonetic](#analysis-phonetic)**:

Analyzes tokens into their phonetic equivalent using Soundex, Metaphone,
Caverphone, and other codecs.

**[SmartCN](#analysis-smartcn)**:

An analyzer for Chinese or mixed Chinese-English text. This analyzer uses
probabilistic knowledge to find the optimal word segmentation for Simplified
Chinese text. The text is first broken into sentences, then each sentence is
segmented into words.

**[Stempel](#analysis-stempel)**:

Provides high quality stemming for Polish.

**[Ukrainian](#analysis-ukrainian)**:

Provides stemming for Ukrainian.

[float]
#### Community contributed analysis plugins

A number of analysis plugins have been contributed by our community:

* [IK Analysis Plugin](https://github.com/medcl/elasticsearch-analysis-ik) (by Medcl)
* [Pinyin Analysis Plugin](https://github.com/medcl/elasticsearch-analysis-pinyin) (by Medcl)
* [Vietnamese Analysis Plugin](https://github.com/duydo/elasticsearch-analysis-vietnamese) (by Duy Do)
* [Network Addresses Analysis Plugin](https://github.com/ofir123/elasticsearch-network-analysis) (by Ofir123)
* [Dandelion Analysis Plugin](https://github.com/ZarHenry96/elasticsearch-dandelion-plugin) (by ZarHenry96)
* [STConvert Analysis Plugin](https://github.com/medcl/elasticsearch-analysis-stconvert) (by Medcl)

include::analysis-icu.asciidoc[]

include::analysis-kuromoji.asciidoc[]

include::analysis-nori.asciidoc[]

include::analysis-phonetic.asciidoc[]

include::analysis-smartcn.asciidoc[]

include::analysis-stempel.asciidoc[]

include::analysis-ukrainian.asciidoc[]