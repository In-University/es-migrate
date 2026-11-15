# Confluence Storage Format — Tags & Macros Reference

Storage format = XHTML + `ac:` (Atlassian Confluence) + `ri:` (resource identifier) elements.
Valid for Data Center/Server and Cloud API v1 `body.storage`.

**Sources:** Atlassian "Confluence Storage Format", "Confluence Storage Format for Macros" (CONF54 doc space), individual macro pages on confluence.atlassian.com/doc (Code Block, Table of Contents, Status, Expand, Jira Issues, Page Properties). Parameter names below are the **storage names** (case-sensitive).

**Confidence:**
- **Core** — built-in, stable across DC 6.x–9.x.
- **Check** — name/params vary by version, edition, or installed app. Before using: `get` an existing page on the target instance that uses it and copy its XML, or ask the user.

**Golden rule:** when unsure, copy from the instance. In Confluence UI: page `…` menu → *View Storage Format* (DC) shows exact XML.

---

## 1. Basic XHTML

| Element | Storage format | Notes |
|---|---|---|
| Headings | `<h1>`…`<h6>` | `toc` builds from these |
| Paragraph | `<p>…</p>` | |
| Bold / italic / underline / strike | `<strong>`, `<em>`, `<u>`, `<span style="text-decoration: line-through;">` | |
| Inline code (monospace) | `<code>…</code>` | |
| Sub / superscript | `<sub>`, `<sup>` | |
| Text colour | `<span style="color: rgb(255,0,0);">…</span>` | |
| Quote | `<blockquote><p>…</p></blockquote>` | |
| Preformatted | `<pre>…</pre>` | prefer `code`/`noformat` macro |
| Lists | `<ul><li>…</li></ul>`, `<ol><li>…</li></ol>`, nested lists inside `<li>` | `<ol start="3">` continues numbering |
| Line break / rule | `<br />`, `<hr />` | |
| Table | `<table><tbody><tr><th>H</th></tr><tr><td>C</td></tr></tbody></table>` | `<th>` = heading cell |
| Merge cells | `<td rowspan="2">`, `<td colspan="2">` | |
| Highlighted cell (DC) | `<td class="highlight-green" data-highlight-colour="green">` | Check |
| Non-breaking space | `&nbsp;` | valid in storage, not in strict XML |
| Date lozenge | `<time datetime="2026-11-15" />` | Core |

Escape `&`, `<`, `>` as `&amp;`, `&lt;`, `&gt;` in normal text; CDATA content is raw.

## 2. Links

```xml
<!-- External URL -->
<a href="https://jenkins.corp/job/x/">Jenkins job</a>

<!-- Another page (same space: omit ri:space-key) -->
<ac:link><ri:page ri:space-key="OPS" ri:content-title="ES Migration Runbook" /></ac:link>

<!-- Page with custom text -->
<ac:link><ri:page ri:content-title="ES Migration Runbook" />
  <ac:plain-text-link-body><![CDATA[runbook]]></ac:plain-text-link-body></ac:link>

<!-- Page with rich link text -->
<ac:link><ri:page ri:content-title="Runbook" /><ac:link-body>the <strong>runbook</strong></ac:link-body></ac:link>

<!-- Anchor on same page / on another page -->
<ac:link ac:anchor="step-2"><ac:plain-text-link-body><![CDATA[Step 2]]></ac:plain-text-link-body></ac:link>
<ac:link ac:anchor="rollback"><ri:page ri:content-title="Runbook" /></ac:link>

<!-- Attachment (on this page / on another page) -->
<ac:link><ri:attachment ri:filename="plan.txt" /></ac:link>
<ac:link><ri:attachment ri:filename="plan.txt"><ri:page ri:content-title="Other page" /></ri:attachment></ac:link>

<!-- Blog post, space, user -->
<ac:link><ri:blog-post ri:content-title="Release notes" ri:posting-day="2026/11/15" /></ac:link>
<ac:link><ri:space ri:space-key="OPS" /></ac:link>
<ac:link><ri:user ri:userkey="2c9680f7405147ee0140514c26120003" /></ac:link>   <!-- DC/Server -->
<ac:link><ri:user ri:account-id="5b10ac8d82e05b22cc7d4ef5" /></ac:link>        <!-- Cloud -->
```

Resource identifiers (`ri:`): `ri:page` (`ri:space-key`, `ri:content-title`), `ri:blog-post` (`ri:posting-day`), `ri:attachment` (`ri:filename`), `ri:url` (`ri:value`), `ri:space` (`ri:space-key`), `ri:user` (`ri:userkey` DC / `ri:account-id` Cloud), `ri:shortcut` (`ac:key`, `ac:parameter`), `ri:content-entity` (`ri:content-id`).

User mention on DC needs the **userkey** (not username): find it via `GET /rest/api/user?username=<name>` → `userKey`.

## 3. Images, emoticons, tasks, layouts

```xml
<ac:image ac:width="600" ac:align="center"><ri:attachment ri:filename="diagram.png" /></ac:image>
<ac:image><ri:url ri:value="https://img.corp/x.png" /></ac:image>
<!-- image attrs: ac:align, ac:border, ac:class, ac:title, ac:style, ac:thumbnail, ac:alt, ac:height, ac:width, ac:vspace, ac:hspace -->

<ac:emoticon ac:name="tick" />
<!-- smile, sad, cheeky, laugh, wink, thumbs-up, thumbs-down, information, tick, cross, warning, plus, minus, question, light-on, light-off, yellow-star, red-star, green-star, blue-star -->

<ac:task-list>
  <ac:task><ac:task-status>incomplete</ac:task-status><ac:task-body>Announce maintenance</ac:task-body></ac:task>
  <ac:task><ac:task-status>complete</ac:task-status><ac:task-body>Snapshot taken</ac:task-body></ac:task>
</ac:task-list>

<ac:layout>
  <ac:layout-section ac:type="two_equal">
    <ac:layout-cell><p>left</p></ac:layout-cell>
    <ac:layout-cell><p>right</p></ac:layout-cell>
  </ac:layout-section>
</ac:layout>
<!-- ac:type: single | two_equal | two_left_sidebar | two_right_sidebar | three_equal | three_with_sidebars -->
```

If a page uses `ac:layout`, **all** body content must sit inside layout sections. Task assignee/due date inside `ac:task-body`: `<ac:link><ri:user …/></ac:link>` and `<time datetime="…"/>`.

## 4. Macro anatomy

```xml
<ac:structured-macro ac:name="NAME">
  <ac:parameter ac:name="PARAM">value</ac:parameter>
  <ac:parameter ac:name="">default/unnamed param value</ac:parameter>
  <ac:rich-text-body> …XHTML… </ac:rich-text-body>                 <!-- rich body -->
  <ac:plain-text-body><![CDATA[ raw text ]]></ac:plain-text-body>  <!-- plain body -->
</ac:structured-macro>
```

- Parameter values can hold resources: `<ac:parameter ac:name="name"><ri:attachment ri:filename="a.pdf" /></ac:parameter>`, `<ri:page …/>`, `<ri:user …/>`, `<ri:space …/>`, `<ri:url …/>`.
- Server adds `ac:schema-version="1"` and `ac:macro-id="…"` on save — keep them when editing existing macros; omit on new ones.
- `]]>` inside CDATA must be split: `]]]]><![CDATA[>`.
- Legacy pages may contain `<ac:macro ac:name="…">` (pre-5.x form). Leave it as is.

## 5. Macros used in runbooks (most important)

### Callouts — `info`, `tip`, `note`, `warning` (Core)
Rich body. Params: `title`, `icon` (true). Meaning: info = context, tip = good practice, note = caution, warning = danger/irreversible.

```xml
<ac:structured-macro ac:name="warning">
  <ac:parameter ac:name="title">PRD change</ac:parameter>
  <ac:rich-text-body><p>Requires approved change ticket.</p></ac:rich-text-body>
</ac:structured-macro>
```

### `panel` (Core; colour params Check)
Rich body. Params: `title`, `borderStyle` (solid, dashed, …), `borderColor`, `borderWidth`, `bgColor`, `titleBGColor`, `titleColor` (CSS colours, e.g. `#deebff`).

### `expand` (Core)
Rich body. Param: `title` (link text; default "Click here to expand…"). Preferred container for per-environment details.

```xml
<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">STG – 2 steps</ac:parameter>
  <ac:rich-text-body><ol><li><p>…</p></li></ol></ac:rich-text-body>
</ac:structured-macro>
```

### `code` (Core)
Plain body (CDATA). Params: `language`, `title`, `linenumbers` (false), `firstline` (1), `collapse` (false), `theme` (Default, DJango, Emacs, FadeToGrey, Midnight, RDark, Eclipse, Confluence — Check).

`language` (current DC list, lower-case in storage): `bash`/`shell`, `powershell`, `python`, `java`, `javascript`, `typescript`, `go`, `sql`, `json`, `yaml`, `xml`, `html`, `css`, `hcl`, `dockerfile`, `groovy`, `nginx`, `diff`, `ruby`, `php`, `kotlin`, `rust`, `scala`, `csharp`, `cpp`, `text`/`none` … (81 total on recent DC). **Older DC lacks `hcl`, `dockerfile`, `go`, `yaml`** — Check; fall back to `text`/`none`.

```xml
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">bash</ac:parameter>
  <ac:parameter ac:name="title">Check rollout</ac:parameter>
  <ac:parameter ac:name="linenumbers">true</ac:parameter>
  <ac:plain-text-body><![CDATA[kubectl -n app rollout status deploy/api --timeout=5m]]></ac:plain-text-body>
</ac:structured-macro>
```

### `noformat` (Core)
Plain body. Param: `nopanel` (false). For raw logs/output without highlighting.

### `status` (Core)
No body. Params: `colour` (**British spelling**; Grey default, Red, Yellow, Green, Blue), `title` (default = colour name), `subtle` (false).

```xml
<ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">Green</ac:parameter><ac:parameter ac:name="title">DONE</ac:parameter></ac:structured-macro>
```

### `toc` (Core) / `toc-zone` (Core)
No body (`toc-zone`: rich body + `location` = both|top|bottom). Params: `type` (list|flat), `outline` (false), `style` (CSS list style), `indent`, `separator` (brackets|braces|parens|pipe|text; flat only), `minLevel` (1), `maxLevel` (7), `include` / `exclude` (regex), `printable` (true), `class`, `absoluteUrl` (false).

### `anchor` (Core)
No body. Unnamed param = anchor name: `<ac:structured-macro ac:name="anchor"><ac:parameter ac:name="">rollback</ac:parameter></ac:structured-macro>`.

### `section` + `column` (Core)
Older multi-column layout (prefer `ac:layout`). `section`: rich body containing `column` macros; param `border` (false). `column`: rich body; param `width` (px or %).

```xml
<ac:structured-macro ac:name="section"><ac:rich-text-body>
  <ac:structured-macro ac:name="column"><ac:parameter ac:name="width">50%</ac:parameter><ac:rich-text-body><p>STG</p></ac:rich-text-body></ac:structured-macro>
  <ac:structured-macro ac:name="column"><ac:parameter ac:name="width">50%</ac:parameter><ac:rich-text-body><p>PRD</p></ac:rich-text-body></ac:structured-macro>
</ac:rich-text-body></ac:structured-macro>
```

### Reuse — `excerpt`, `excerpt-include`, `include` (Core)
- `excerpt`: rich body; params `hidden` (false), `atlassian-macro-output-type` (BLOCK|INLINE). Newer DC also `name` for multiple excerpts — Check.
- `excerpt-include`: no body; unnamed param holds the page link; `nopanel` (false).
- `include`: no body; unnamed param holds the page link.

```xml
<ac:structured-macro ac:name="include"><ac:parameter ac:name="">
  <ac:link><ri:page ri:space-key="OPS" ri:content-title="Common pre-checks" /></ac:link>
</ac:parameter></ac:structured-macro>
```

### Page metadata — `details` (Page Properties) / `detailssummary` (Report)
- `details`: rich body = 2-column table, left column as `<th>` (keys), right `<td>` (values); no macros in the key column. Params: `id`, `hidden` (false), `label` — Check.
- `detailssummary`: no body. Params: `label` (older) or `cql` (newer), `headings`, `firstcolumn`, `sortBy`, `pageSize`, `showCommentsCount`, `showLikesCount` — Check. Only one label and one id per report.

```xml
<ac:structured-macro ac:name="details"><ac:rich-text-body><table><tbody>
  <tr><th>Owner</th><td><ac:link><ri:user ri:userkey="…" /></ac:link></td></tr>
  <tr><th>Status</th><td><ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">Yellow</ac:parameter><ac:parameter ac:name="title">DRAFT</ac:parameter></ac:structured-macro></td></tr>
</tbody></table></ac:rich-text-body></ac:structured-macro>
```

### Jira — `jira` (current) / `jiraissues` (legacy) — Check
- `jira` (DC 5.x+): params `server` (app-link name), `serverId` (**instance-specific UUID**), `key` (single issue) **or** `jqlQuery`, `columns` (comma list), `maximumIssues` (20), `count` (true = count only). Copy `server`/`serverId` from an existing page — never guess.
- `jiraissues` (legacy): `url` (required, XML filter URL), `columns` (semicolon list), `count`, `cache` (on|off), `renderMode` (static|dynamic), `height`, `width`, `title`, `anonymous`, `baseurl`.
- `jirachart`: `chartType` (pie), `jql`, `statType` (statuses|assignees|priorities|components|issuetype|allFixfor), `showinfor`, `width`, `border` — Check.

```xml
<ac:structured-macro ac:name="jira">
  <ac:parameter ac:name="server">Corp JIRA</ac:parameter>
  <ac:parameter ac:name="serverId">COPY-FROM-EXISTING-PAGE</ac:parameter>
  <ac:parameter ac:name="key">OPS-1234</ac:parameter>
</ac:structured-macro>
```

### Navigation / listing (Core)
| Macro | Body | Key params |
|---|---|---|
| `children` | none | `all` (false), `depth`, `first`, `sort` (creation\|title\|modified), `reverse`, `style` (h1–h6), `excerpt` (false), `page` (`ri:page`) |
| `pagetree` | none | `root` (@home\|@self\|@parent\|page title), `startDepth` (1), `sort` (position\|natural\|creation\|modified\|bitwise), `reverse`, `searchBox`, `expandCollapseAll`, `excerpt` |
| `pagetreesearch` | none | `root` |
| `contentbylabel` | none | `labels` (required), `spaces` (@all\|@self\|keys), `type` (page\|blogpost\|attachment), `operator` (OR\|AND), `max` (15), `sort` (modified\|title\|creation), `reverse`, `showLabels`, `showSpace`, `excerpt`, `title`, `author` — newer DC uses `cql` instead — Check |
| `content-report-table` | none | `spaces`, `labels`, `maxResults` |
| `recently-updated` | none | `spaces`, `labels`, `types`, `max` (15, ≤200), `theme` (concise\|social\|sidebar), `author`, `hideHeading`, `showProfilePic`, `width` |
| `blog-posts` | none | `content` (entire\|excerpts\|titles), `spaces`, `label`, `author`, `time` (e.g. `7d`), `sort`, `reverse`, `max` (15) |
| `search` | none | `query` (required), `spacekey`, `type`, `lastModified`, `contributor`, `maxLimit` (10) |
| `livesearch` | none | `spaceKey`, `labels`, `type`, `placeholder`, `size` (medium\|large), `additional` |
| `index` | none | — (page index of space) |
| `change-history` | none | — |
| `listlabels`, `popular-labels`, `related-labels`, `recently-used-labels` | none | label browsing; see Atlassian docs |

### Files & media
| Macro | Body | Key params |
|---|---|---|
| `attachments` | none | `patterns` (regex), `sortBy` (date\|size\|name), `sortOrder`, `labels`, `old` (false), `upload` (false), `page` |
| `viewpdf` | none | `name` = `<ri:attachment ri:filename="x.pdf"/>`, `page` |
| `viewdoc` / `viewxls` / `viewppt` | none | `name` (attachment), `page`; xls: `sheet`, `row`, `col`, `grid`; ppt: `slide`, `width`, `height` |
| `view-file` | none | `name` (attachment), `height` — Check (DC 5.7+ file preview) |
| `multimedia` | none | `name` (attachment), `page`, `space`, `width`, `height`, `autostart` |
| `gallery` | none | `columns` (4), `include`, `exclude`, `includeLabel`, `excludeLabel`, `sort`, `reverse`, `title`, `page` |
| `space-attachments` | none | `space`, `showFilter` (true) |
| `widget` | none | `url` = `<ri:url ri:value="…"/>`, `width`, `height` |

### Charts & reports
| Macro | Body | Key params |
|---|---|---|
| `chart` | rich (data tables) | `type` (pie\|bar\|line\|area\|xyLine\|timeSeries\|gantt…), `title`, `subTitle`, `xLabel`, `yLabel`, `width`/`height` (300), `legend`, `stacked`, `3D`, `dataOrientation`, `dataDisplay`, `colors` |
| `tasks-report-macro` | none | `spaces`, `pages`, `labels`, `assignees`, `status` (incomplete\|complete), `duedateFrom/To`, `pageSize` — Check |
| `contributors` / `contributors-summary` | none | `scope`, `include`, `order`, `limit`, `showCount`, `columns`, `groupby` |

### People
| Macro | Body | Key params |
|---|---|---|
| `profile` | none | `user` = `<ri:user ri:userkey="…"/>` |
| `profile-picture` | none | `User` = `<ri:user …/>` |
| `userlister` | none | `groups` (required, or `*`), `online` |

### Other built-ins
`html` (plain body, raw HTML — **usually disabled by admins**, Check), `html-include` (`url`), `rss` (`url` via `ri:url`, `max`, `showTitlesOnly`, `titleBar`), `create-from-template` (`templateName`, `buttonLabel`, `spaceKey`, `templateId`), `create-space-button`, `spaces` (unnamed param all|category|favourite|new), `space-details`, `spacejump`, `navmap`, `global-reports`, `favpages`, `loremipsum`, `cheese`, `im`, `network`, `gadget`, `roadmap` (Check), `team-calendar` (app, Check), `ui-tabs`/`ui-tab`/`ui-expand` (Marketplace apps — Check, often not installed).

## 6. Gotchas

- Body is a fragment with many top-level elements and undeclared `ac:`/`ri:` namespaces — strict XML parsers need a wrapper root that declares them (the helper's `check` does this).
- Macro and parameter names are case-sensitive (`maxLevel`, `colour`, `linenumbers`).
- A macro name the instance doesn't know renders as an "Unknown macro" box — the API still accepts it. Re-`get` and open the page to confirm rendering.
- Cloud converts storage on save and may show a page as "legacy editor" content; DC stores what you send.
