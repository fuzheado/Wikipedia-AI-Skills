{{draft article|subject=computing}}

'''Pi''' (stylized '''pi''') is an [[open-source]] [[AI agent|artificial intelligence agent]] harness and coding assistant developed by Mario Zechner and released under the [[MIT License]]. It is designed as a minimal command-line tool for code generation, [[software testing|testing]], and [[debugging]] via interaction with [[large language model]]s (LLMs). The project has been noted for its small system prompt and architecture that allows users to extend its capabilities by having the agent modify its own source code.<ref name="register_howto">{{cite web |last1=Mann |first1=Tobias |last2=Claburn |first2=Thomas |title=How to roll your own local AI coding agents |url=https://www.theregister.com/software/2026/05/02/how-to-roll-your-own-local-ai-coding-agents/5230018/ |website=The Register |date=2 May 2026 |access-date=28 May 2026}}</ref><ref name="neuron">{{cite web |last=Harvey |first=Grant |title=The 4-tool agent quietly powering OpenClaw |url=https://www.theneurondaily.com/p/the-4-tool-agent-quietly-powering-openclaw |website=The Neuron Daily |date=1 May 2026 |access-date=28 May 2026}}</ref>

Pi gained wider attention in early 2026 after it was revealed to be the underlying agent framework powering OpenClaw, a [[WhatsApp]]-based personal AI assistant that experienced rapid adoption.<ref name="eweek">{{cite web |title=OpenClaw's Secret Sauce? The Pi Coding Agent and Why AI Tools Need a 'Neuron' |url=https://www.eweek.com/news/openclaw-pi-coding-agent-ai-tools-neuron/ |website=eWeek |date=2026 |access-date=28 May 2026}}</ref><ref name="neuron" />

== Features ==

Pi ships with four built-in tools: file read, file write, file edit, and [[Bash (Unix shell)|bash]] shell access.<ref name="register_howto" /> All additional capabilities — such as planning modes, integrations, and custom interfaces — are implemented by users instructing the agent to modify its own code. Zechner describes this design philosophy as "ship a tiny core, let users build what they need."<ref name="neuron" />

The agent supports multiple LLM providers including [[OpenAI]], [[Anthropic]], [[Google AI|Google]], and locally-hosted models through frameworks such as [[Llama.cpp]], [[Ollama]], and [[MLX (machine learning framework)|MLX]].<ref name="register_howto" />

== Architecture ==

Pi is structured as a [[monorepo]] containing several [[npm]] packages:

* '''@earendil-works/pi-coding-agent''' — the command-line coding agent
* '''@earendil-works/pi-agent-core''' — the agent runtime with tool calling and state management
* '''@earendil-works/pi-ai''' — a unified multi-provider LLM API abstraction
* '''@earendil-works/pi-tui''' — a [[terminal user interface]] library

The project is written primarily in [[TypeScript]].<ref name="github">{{cite web |title=earendil-works/pi |url=https://github.com/earendil-works/pi |website=GitHub |access-date=28 May 2026}}</ref>

== Reception ==

In a May 2026 hands-on evaluation, ''[[The Register]]'' described Pi as "lightweight" with a "short enough" system prompt to keep performance snappy on lower-end hardware, while noting that its default autonomous operation mode lacked the [[Sandbox (computer security)|sandboxing]] and safety features found in other coding agents.<ref name="register_howto" />

The [[Hacker News]] community gave significant attention to Zechner's blog post "What I learned building an opinionated and minimal coding agent", which accumulated over 420 points and 170 comments.<ref name="hn_blog">{{cite web |last=Zechner |first=Mario |title=What I learned building an opinionated and minimal coding agent |url=https://mariozechner.at/posts/2025-11-30-pi-coding-agent/ |date=30 November 2025 |access-date=28 May 2026 |via=Hacker News}}</ref>

Zechner's subsequent talk "Slow the F*** Down" at the AI Engineer Europe conference argued that agent swarms create complexity that future AI systems cannot untangle, and received a standing ovation from attendees.<ref name="neuron" />

The agent has attracted a community of third-party developers who have created extensions including an [[Emacs]] front-end,<ref>{{cite web |last=Nouri |first=Daniel |title=Pi-coding-agent: Emacs front end for AI-assisted coding |url=https://github.com/dnouri/pi-coding-agent |website=GitHub |access-date=28 May 2026}}</ref> a remote server access tool (pi-hosts),<ref>{{cite web |title=pi-hosts: Give the Pi coding agent access to your servers |url=https://github.com/hunvreus/pi-hosts |website=GitHub |access-date=28 May 2026}}</ref> and a voice input plugin.<ref>{{cite web |title=pi-listen: Hold-to-talk voice input for Pi Coding Agent |url=https://github.com/codexstar69/pi-listen |website=GitHub |access-date=28 May 2026}}</ref>

== See also ==
* [[Claude Code]]
* [[GitHub Copilot]]
* [[Large language model]]
* [[AI agent]]

== References ==
{{reflist|30em}}

== External links ==
* {{Official website|https://pi.dev}}
* {{GitHub|earendil-works/pi}}
