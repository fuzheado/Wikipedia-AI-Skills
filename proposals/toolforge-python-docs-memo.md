== Python documentation is spread across 7 pages with no clear "start here" ==

I've been working on [https://github.com/fuzheado/Wikipedia-AI-Skills a project] that
needed a clear understanding of how to deploy Python on Toolforge, and I found the
documentation landscape confusing. Here's what I found and some suggestions for
improvement.

=== The current landscape ===

There are 7 pages about Python on Toolforge, spanning two completely different
deployment architectures:

'''Traditional (prebuilt images):'''
* [[Help:Toolforge/Web/Python]] — uWSGI conventions, fixed file layout, `uwsgi.ini`
* [[Help:Toolforge/My first Flask OAuth tool]] — oldest tutorial, predates Build Service

'''Build Service (containers):'''
* [[Help:Toolforge/Building container images/My first Buildpack Python tool]] — Flask
* [[Help:Toolforge/My first Python ASGI tool]] — FastAPI
* [[Help:Toolforge/Building container images/My first Buildpack Django tool]] — Django

And the landing page:
* [[Help:Toolforge/Python]] — links to everything with no guidance

=== What's confusing ===

1. '''No "start here" signal.''' A new user lands on [[Help:Toolforge/Python]] and sees
   links to both the Flask OAuth tutorial (traditional, predates Build Service) and the
   Buildpack tutorials (modern, container-based). These are completely different
   deployment architectures but are presented as peers. The user has no way to know
   which path is recommended for new tools.

2. '''The traditional and Build Service paths are incompatible.''' The traditional path
   requires a specific file layout (`$HOME/www/python/src/app.py`, venv at
   `$HOME/www/python/venv`). The Build Service path uses git-based deployment with a
   `Procfile` and `runtime.txt`. If a user follows one tutorial but tries to apply it
   to the other path, things break silently.

3. '''Overlapping content across pages.''' Both [[Help:Toolforge/Python]] and
   [[Help:Toolforge/Web/Python]] cover virtual environment creation, but at different
   levels of detail. The Flask OAuth tutorial and the Buildpack Flask tutorial both
   teach Flask deployment, but one uses `webservice python3.13 start` and the other
   uses `toolforge build start`.

4. '''Django knowledge is siloed.''' Production Django concerns (ToolsDB, WhiteNoise,
   `CSRF_TRUSTED_ORIGINS`, database migrations, `django-configurations`) only appear
   in the Django tutorial. A user deploying Django via the traditional path (which
   is documented in [[Help:Toolforge/Web/Python]]) would never find them.

=== Proposed fixes ===

Here's what I think would help, from smallest to largest change:

'''1. Add a recommendation to the landing page.''' At the top of
[[Help:Toolforge/Python]], add something like:

<blockquote>
  '''For new tools:''' Use the Build Service path.
  Start with [[Help:Toolforge/Building container images/My first Buildpack Python tool|the Buildpack Flask tutorial]]
  or [[Help:Toolforge/My first Python ASGI tool|the FastAPI tutorial]].
  '''For existing tools on the traditional backend:''' See
  [[Help:Toolforge/Web/Python|the uWSGI reference]].
</blockquote>

'''2. Add "For new users" links to each tutorial.''' Each tutorial page should say at
the top which path it teaches and link to the recommended starting point for the
other path. The Flask OAuth tutorial could add a banner: "This tutorial uses the
traditional backend. For new tools, see the [[Help:Toolforge/Building container images/My first Buildpack Python tool|Buildpack Python tutorial]] instead."

'''3. Merge the overlapping pages.''' [[Help:Toolforge/Python]] and
[[Help:Toolforge/Web/Python]] both cover venv creation and basic deployment. One
could become a concise "quick start" and the other a detailed reference.

'''4. Cross-pollinate Django knowledge.''' The production Django concerns (ToolsDB,
WhiteNoise, CSRF, migrations) should also be noted on [[Help:Toolforge/Web/Python]]
since that's where the traditional Django deployment is documented.

'''5. (Longer term) Add a "Choosing your deployment path" decision tree.''' A short
flowchart or table at the top of [[Help:Toolforge/Python]] that asks:
* New or existing tool?
* Need async (FastAPI) or sync (Flask/Django)?
* → Points to the right tutorial.

I'm happy to help draft any of these changes if there's interest. I've been working
on a Python-on-Toolforge reference that's helped me navigate this, so I have a clear
picture of what tripped me up as a newcomer.

— ~~~~
