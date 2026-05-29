<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.

When analyzing architecture or proposing refactors, do not answer generically. For every conclusion, cite the files, components, hooks, and code snippets that support it.

List all components, pages, and hooks that directly or indirectly consume the reference period.

Compare these approaches before recommending one:

- URL Search Params (?month=YYYY-MM)
- React Context
- Zustand
- Redux
- Environment variable

For each option, explain advantages and disadvantages, then recommend only one.

Map all endpoints related to transactions, accounts, categories, and filters. For each endpoint, include the endpoint path, accepted query params, response structure, and identified limitations.

Do not assume the existence of endpoints, hooks, contexts, or global state. If something is not found in the code, state that explicitly.
<!-- END:nextjs-agent-rules -->
