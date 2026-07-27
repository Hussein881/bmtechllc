# BMTech workspace

This repository holds the public BMTech site, internal tools, and the consulting firm's future project work.

## Repository map

```text
.
├── website/                 Public BMTech website
├── work_knowledge_agent/    Existing internal knowledge-agent project
├── projects/
│   ├── client-delivery/     Client-specific engagements
│   ├── internal-tools/      Products and utilities used by BMTech
│   └── experiments/         Time-boxed prototypes and technical spikes
├── shared/
│   ├── brand/               Approved brand assets and guidance
│   ├── templates/           Reusable project and delivery templates
│   └── playbooks/           Repeatable consulting processes
└── archive/                 Completed or retired work
```

The existing `website/` and `work_knowledge_agent/` directories remain at the repository root to avoid breaking their current build paths and documentation. New work should follow the structure under `projects/`.

## Naming conventions

- Use lowercase, hyphenated directory names: `inventory-automation`.
- Use a short client code for client work when confidentiality permits: `client-code-project-name`.
- Give every project its own `README.md` describing its owner, status, purpose, and setup.
- Keep credentials, client exports, production data, and private documents out of Git.
- Move finished work to `archive/` only after documenting its final state and dependencies.
