# Pywikibot ↔ MediaWiki API Mapping

Complete cross-reference between MediaWiki API actions (`api.php`) and Pywikibot methods.

## Core Actions

| `action=` | Pywikibot Method(s) | Module |
|---|---|---|
| `block` | `User.block()` | `pywikibot.page.User` |
| `clientlogin` | `Site.login()` | `pywikibot.site` |
| `compare` | `Site.compare()` | `pywikibot.site` |
| `delete` | `Page.delete()` | `pywikibot.page.BasePage` |
| `deletedrevisions` | `Page.delete()` | `pywikibot.page.BasePage` |
| `echomarkread` | `Site.notifications_mark_read()`, `echo.Notification.mark_as_read()` | `pywikibot.site`, `pywikibot.echo` |
| `edit` | `BasePage.save()`, `BasePage.put()`, `BasePage.touch()`, `Page.set_redirect_target()`, `BasePage.change_category()`, `ProofreadPage.save()`, `IndexPage.save()`, `BaseBot.userPut()`, `CurrentPageBot.put_current()` | various |
| `emailuser` | `User.send_email()` | `pywikibot.page.User` |
| `expandtemplates` | `BasePage.expand_text()`, `Site.expand_text()`, `textlib.getCategoryLinks()` | `pywikibot.page`, `pywikibot.site`, `pywikibot.textlib` |
| `login` | `Site.login()` | `pywikibot.site` |
| `logout` | `Site.logout()` | `pywikibot.site` |
| `mergehistory` | `Site.merge_history()`, `BasePage.merge_history()` | `pywikibot.site`, `pywikibot.page` |
| `move` | `Site.movepage()`, `BasePage.move()` | `pywikibot.site`, `pywikibot.page` |
| `parse` | `BasePage.get_parsed_page()`, `Site.get_parsed_page()` | `pywikibot.page`, `pywikibot.site` |
| `patrol` | `Site.patrol()` | `pywikibot.site` |
| `protect` | `Site.protect()`, `BasePage.protect()` | `pywikibot.site`, `pywikibot.page` |
| `purge` | `Site.purgepages()`, `BasePage.purge()`, `ProofreadPage.purge()` | `pywikibot.site`, `pywikibot.page` |
| `revisiondelete` | `Site.deleterevs()` | `pywikibot.site` |
| `rollback` | `Site.rollbackpage()`, `BasePage.rollback()` | `pywikibot.site`, `pywikibot.page` |
| `shortenurl` | `Site.create_short_link()`, `BasePage.create_short_link()` | `pywikibot.site`, `pywikibot.page` |
| `sitematrix` | `Site.fromDBName()` | `pywikibot.site` |
| `thank` | `Site.thank_revision()` | `pywikibot.site` |
| `unblock` | `Site.unblockuser()`, `User.unblock()` | `pywikibot.site`, `pywikibot.page` |
| `undelete` | `Site.undelete()`, `BasePage.undelete()` | `pywikibot.site`, `pywikibot.page` |
| `upload` | `Site.upload()`, `Site.Uploader.upload()`, `FilePage.upload()`, `UploadRobot.upload_file()` | `pywikibot.site`, `pywikibot.page` |
| `watch` | `Site.watch()`, `BasePage.watch()` | `pywikibot.site`, `pywikibot.page` |

## Query Submodules

The `action=query` submodules map to Pywikibot **page generators** (all accessible via `pagegenerators` module and CLI flags):

| `list=` / `prop=` | Pywikibot Generator / Method | CLI Flag |
|---|---|---|
| `allcategories` | `Site.allcategories()` | `-cat` (implicit) |
| `allimages` | `Site.allimages()` | newimages |
| `alllinks` | `Site.alllinks()` | — |
| `allpages` | `Site.allpages()` | `-start:` |
| `allusers` | `Site.allusers()` | — |
| `backlinks` | `Site.pagebacklinks()` | `-links:` |
| `blocks` | `Site.blocks()` | — |
| `categorymembers` | `Site.categorizedpages()`, `Category.articles()`, `Category.subcategories()` | `-cat:`, `-catr:`, `-subcats:` |
| `contributions` | `User.contributions()` | — |
| `embeddedin` | `Site.page_embeddedin()` | `-transcludes:` |
| `exturlusage` | `Site.exturlusage()` | — |
| `filearchive` | `Site.filearchive()` | — |
| `imageusage` | `Site.imageusage()` | `-filelinks:` |
| `iwbacklinks` | `Site.iwbacklinks()` | — |
| `langbacklinks` | `Site.langbacklinks()` | — |
| `logevents` | `Site.logevents()` | `-logevents:` |
| `newimages` | `Site.newimages()` | `-newimages:` |
| `newpages` | `Site.newpages()` | `-newpages:` |
| `oldreviewedpages` | `Site.oldreviewedpages()` | — |
| `pageswithprop` | `Site.pageswithprop()` | — |
| `prefixsearch` | `Site.prefixsearch()` | — |
| `protectedtitles` | `Site.protectedtitles()` | — |
| `querypage` | `Site.querypage()` | `-unusedfiles`, `-uncatfiles`, etc. |
| `random` | `Site.randompages()` | `-random:` |
| `recentchanges` | `Site.recentchanges()` | `-recentchanges:` |
| `search` | `Site.search()` | `-search:` |
| `tags` | `Site.tags()` | — |
| `usercontribs` | `User.contributions()` | — |
| `users` | `Site.users()` | — |
| `watchlist` | `Site.watchlist_reverse()` | `-watchlist:` |

## Wikibase (Wikidata) API

| Wikibase Action | Pywikibot Method |
|---|---|
| `wbgetentities` | `ItemPage.get()` |
| `wbgetclaims` | `ItemPage.get()` (claims sub-dict) |
| `wbeditentity` | `ItemPage.editEntity()` |
| `wbsetlabel` | `ItemPage.editLabels()` |
| `wbsetdescription` | `ItemPage.editDescriptions()` |
| `wbsetaliases` | `ItemPage.editAliases()` |
| `wbsetsitelink` | `ItemPage.setSitelink()` |
| `wbcreateclaim` | `ItemPage.addClaim()` |
| `wbsetclaim` | `Claim.changeTarget()` |
| `wbremoveclaims` | `Claim.remove()` |
| `wbsetclaimvalue` | `Claim.changeTarget()` |
| `wbsearchentities` | `Site.search_entities()` |
| `wbmergeitems` | `ItemPage.mergeInto()` |
| `wbsetqualifier` | `Claim.addQualifier()` |
| `wbremovequalifiers` | `Claim.removeQualifier()` |
| `wbsetsource` | `Claim.addSource()` |
| `wbremovesources` | `Claim.removeSource()` |
| `wblinktitles` | `Site.linkTitles()` |
| `wbsetlabeldescriptionaliases` | `ItemPage.editLabels()` + `editDescriptions()` |

## ProofreadPage (Wikisource) API

| ProofreadPage Action | Pywikibot Method |
|---|---|
| `setprpflag` | `ProofreadPage.set_flags()`, `IndexPage.set_flags()` |

Full source: https://doc.wikimedia.org/pywikibot/stable/mwapi.html
