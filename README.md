# BMTech workspace

This repository holds the public BMTech site, internal tools, and the consulting firm's future project work.

## Repository map

```text
.
├── projects/
│   ├── client-delivery/     Client-specific engagements
│   ├── company-platforms/
│   │   └── website/         Public BMTech website
│   ├── internal-tools/
│   │   └── work-knowledge-agent/
│   └── experiments/         Time-boxed prototypes and technical spikes
├── docs/
│   ├── setup/               Firm-wide environment and onboarding guides
│   ├── operations/          Company operating documentation
│   └── standards/           Engineering and delivery standards
├── shared/
│   ├── brand/               Approved brand assets and guidance
│   ├── templates/           Reusable project and delivery templates
│   └── playbooks/           Repeatable consulting processes
└── archive/                 Completed or retired work
```

Project-specific documentation stays with its project. Firm-wide documentation belongs in `docs/`. The website deployment workflow follows its location under `projects/company-platforms/website/`.

## Naming conventions

- Use lowercase, hyphenated directory names: `inventory-automation`.
- Use a short client code for client work when confidentiality permits: `client-code-project-name`.
- Give every project its own `README.md` describing its owner, status, purpose, and setup.
- Keep credentials, client exports, production data, and private documents out of Git.
- Move finished work to `archive/` only after documenting its final state and dependencies.
