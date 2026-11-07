# Embedded Metadata delegation and structured data
## Delegate instead of rewriting a working extractor
Check the current `Embedded Metadata.js` and measure its output for the actual site. Capabilities change; do not preserve a historical statement that JSON-LD is always read or never read. A site translator should add only what the shared extractor cannot reliably supply.
```js
async function scrape(doc, url = doc.location.href) {
	let translator = Zotero.loadTranslator('web');
	translator.setTranslator('951c027d-74ac-47d4-a107-9c3069ab7b48');
	translator.setDocument(doc);
	translator.setHandler('itemDone', (_obj, item) => {
		item.url = doc.querySelector('link[rel="canonical"]')?.href || url;
		item.complete();
	});
	await translator.translate();
}
```
Keep metadata corrections in `itemDone` and complete each item exactly once. Await translation so failures propagate. Use `getTranslatorObject()` only when EM needs pre-translation customization, such as setting its supported `itemType` or adding field mappings; inspect a current maintained example for the object API.
Do not blindly copy the illustrative canonical-link assignment: accept it only if it identifies the current article, not a homepage, another edition or an unrelated object. Set the item type deliberately; do not classify every news-like institutional page as a newspaper.
## Inspect channel conflicts
Inventory Highwire/Dublin Core/meta tags, JSON-LD, rendered DOM and application state. Compare which source supplied the extracted value. A generic meta author may be the site owner, a Facebook numeric ID, or a collective desk; a DOM byline may contain personal names and roles. Prefer strong article-specific evidence, not whichever field is nonempty.
For JSON-LD:
1. Parse each `application/ld+json` script independently; a malformed script must not discard valid later scripts.
2. Handle top-level arrays and `@graph`; `@type` can be a string or array.
3. Select the node for the current article using type, URL/ID/headline and document context. Do not take an unrelated recommended article or WebSite node.
4. Resolve `@id` references to Person/Organization nodes when required. Normalize singleton versus array author forms.
5. Distinguish publication/modification dates, article/reviewed-work dates, and Article/WebPage/VideoObject/CriticReview semantics.
Use only the parsing complexity the site actually needs; a short article-scoped extractor is preferable to a speculative universal schema engine.
For application state, first identify the real schema and current-page record. Do not grep an entire minified bundle for the first `author` or `date`. Framework payloads can contain flattened references, nested serialization, or unrelated content. Parse the payload with an explicit, tested traversal and keep author/date provenance.
## Check shared versus site-specific fixes
A missing field common to many publishers may belong in a shared extractor. Conversely, a generic JSON-LD helper may fill empty fields but leave an existing incorrect author untouched. Test both missing and wrong-field cases before declaring a shared patch sufficient.
Local checkout tests and a patched helper do not prove deployment to Citoid. Keep production access/extraction rechecks separate and document the revision tested.
