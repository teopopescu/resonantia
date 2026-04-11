I want you to build me a Biomni lab equivalent for lab informatics: Think Agentic OS for lab informatics. 

Use the Playwright MCP (claude mcp add playwright npx @playwright/mcp@latest) to check how the Phylo Bio website (https://phylo.bio) and Biomni Lab (https://biomni.phylo.bio/new) looks like and to explore its features. 

Check this conversation for more context on features: https://claude.ai/share/48072ae0-5d8e-4078-bb73-78485c022134

Use uv and npx for dependency management.

I want you to use the following tech stack:
- My Anthropic subscription for the LLM
- Next.js, Zustand, React Query, localStorage (+other browser-only APIs for front-end)
- Python backend (open to suggestions)
- Pydantic
- Redis for caching
- Postgres for database
- Temporal
- AWS if needed, local for demo purposes for now
- you can use local KIND cluster to run Temporal if needed
- Draw me an architecture diagram 


Make sure you microscopy images and source-destination plate mapping functionality.

Use the Figma MCP to create unique styling, similar to how Phylo Bio created their own styling. 

Evaluate their features.
Prioritise the design of the website and the product, I want a unique, neat styling, similar to Phylo Bio.

Let's start with 5 features and we will build an additional 5 once we have a prototype. 

Build me both the website and the Biomni Lab prototype. 

Use Clerk for authentication and authorization. 
I want to be able to run this locally with Docker, in the future will deploy the UI through Vercel and the rest of the services on AWS via Terraform.


Let me know when it's done.
