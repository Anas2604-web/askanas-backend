# CRX Kit

## One-line summary
An enterprise CRM built two ways during a Hosho Digital internship: first as a low-code Power Platform app (Dataverse, Power Apps, Power Automate, AI Builder), then independently rebuilt pro-code as a full .NET Core 8 + React application with a Groq-powered AI assistant grounded in live CRM data.

## Problem / context
A selection-phase project simulating a real consulting engagement: manage the customer lifecycle from first contact through to a closed deal, across contact management, sales pipeline, and marketing automation — first proving the design on low-code tooling, then independently proving the same logic could be delivered pro-code with a real relational backend.

## Architecture
**Low-code version:** Power Apps for UI, Dataverse for storage (relational schema across Contacts, Companies, Leads, Deals, Opportunities, Campaigns, Interactions), Power Automate for workflow, AI Builder/OpenAI for intelligence features, Power BI for analytics.

**Pro-code rebuild:** ASP.NET Core 8 Web API backend with EF Core + PostgreSQL, Identity-based auth issuing JWTs (`AuthController` — register/login, claims-based token with configurable expiry), a `GenericCrudController<T>` base class that individual entity controllers (Companies, Contacts, Deals, Campaigns, Opportunities, Leads) inherit from to avoid duplicating standard CRUD logic, and a dedicated `ChatController` that pulls a live CRM data snapshot (lead count, open deal count, total open pipeline value, company count) into the prompt context sent to a `GeminiService`, so the AI assistant answers questions grounded in real, current CRM state rather than generic responses. React frontend.

## Tech stack
**Low-code:** Power Apps, Dataverse, Power Automate, AI Builder, OpenAI, Power BI.
**Pro-code:** ASP.NET Core 8, EF Core, PostgreSQL, ASP.NET Identity, JWT, Gemini API, React.

## Key decisions & why
- **Generic CRUD base controller pattern** — rather than writing near-identical CRUD logic six separate times (Companies, Contacts, Deals, Campaigns, Opportunities, Leads all needed the same create/read/update/delete/list shape), built `GenericCrudController<T>` once and had each entity controller inherit from it with just a few lines — real DRY engineering discipline rather than copy-pasted controllers.
- **Grounding the AI chatbot in a live data snapshot, not a static prompt** — the `ChatController` queries actual current lead/deal/pipeline/company counts from the database on every chat request and injects them into the Gemini prompt, so answers reflect real-time CRM state instead of the AI guessing or hallucinating numbers.
- **Independently rebuilding pro-code after already delivering the low-code version** — nobody asked for this; done specifically to prove the same business logic and data model could be delivered as production-grade code with proper auth, relational schema design, and a real API layer, not just low-code configuration.
- **JWT claims-based auth with configurable expiry** — standard claims (`NameIdentifier`, `Email`, `Name`) issued via `UserManager`/`SignInManager`, expiry configurable via appsettings rather than hardcoded.

## Challenges & fixes
- **EF Core migrations for evolving schema** — built the schema incrementally across multiple migrations (`InitialCreate`, then `AddCoreEntities`), rather than trying to design the entire relational schema perfectly upfront — realistic, iterative schema evolution.
- **12-hour build deadline for the pro-code rebuild** — [Anas: confirm/add detail — what was the actual time pressure context and how did you prioritize what to build first under that constraint?]
- **Switching AI provider mid-build** — the chatbot ended up using Gemini (`GeminiService`) in the pro-code version specifically; [Anas: if this was a switch from an earlier attempt with another provider due to quota/cost, worth noting here as a real problem-solving example, similar to the Groq switch on RepoMind].

## Results / metrics
Full working CRUD API across 6+ entity types, JWT-secured, backed by a real relational PostgreSQL schema via EF Core, with an AI assistant answering natural-language questions grounded in live pipeline data — delivered as an independent addition beyond the original low-code scope, within the internship timeline.
