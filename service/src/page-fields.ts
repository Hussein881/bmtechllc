/**
 * Authoring vocabulary shared with the portal. It lives inside the deployable
 * service package so production bundlers always include it with the handler.
 */
export const TAGS = [
  'ai-strategy', 'rag', 'llm', 'data-engineering', 'machine-learning', 'evaluation',
  'automation', 'infrastructure', 'security', 'scoping', 'discovery', 'delivery',
  'handoff', 'retro', 'onboarding', 'tooling', 'process', 'pricing', 'client-comms',
  'runbook', 'playbook', 'template', 'checklist', 'decision', 'reference', 'postmortem',
] as const;

export const SECTIONS = [
  'guide', 'onboarding', 'methodology', 'playbooks', 'runbooks', 'reference',
  'templates', 'decisions', 'engagements',
] as const;
