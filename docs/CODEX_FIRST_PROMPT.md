# First Prompt for Codex

Use this after placing the repository setup on your machine.

---

Read `AGENTS.md`, `README.md`, and all `docs/` files before making changes.

We are starting TC1 from a clean standalone repository on this machine. Do not assume access to the old DMS workspace or any absolute path mentioned in previous environments.

Start with **WP0 only**.

Your task:

1. Inspect the current repository structure.
2. Verify which of Git, Python, and .NET are available locally.
3. Do not install or modify global machine configuration automatically.
4. Propose the smallest repository changes needed to establish the intended TC1 structure.
5. Create a minimal controlled C#/.NET sample under `sample-dotnet/` only if the environment supports it.
6. Add a minimal test project with a few deterministic branches.
7. Run the existing/new sample tests.
8. Do not implement the TC1 mapper yet.
9. Update `docs/10_DECISION_LOG.md` with only decisions actually confirmed by the environment.
10. Report:
   - environment findings;
   - files created/changed;
   - commands run;
   - test result;
   - blockers;
   - exact next step for WP1.

Do not add LLMs, agents, Graft, OpenCodeReview integration, database, frontend, Docker, CI gates, or multi-language support.
