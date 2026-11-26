# AfyaHer product context

## Audience and purpose

Mobile-first reproductive-health education for adults 18+, Kenya first and
English first. Help people understand PCOS, ovarian cysts and ovarian torsion,
inspect sources and prepare questions for a qualified clinician. Expansion
across Africa is an ambition, not a claim of validated local applicability.

Confusing information, access barriers and isolation are problem hypotheses,
not findings from completed user research. Aesthetic quality is not evidence of
clinical efficacy or improved health outcomes.

## Platform and current capabilities

Responsive web: Next.js App Router, React, TypeScript and Tailwind; FastAPI owns
backend validation, evidence retrieval and future safety/generation. Reuse the
existing modular architecture. No account is required. No new dependencies,
backend infrastructure or paid APIs are part of this redesign.

Working journeys: three editorial condition guides with source details; local
fixed assistant examples; a validated education API that returns unavailable;
PCOS source metadata catalogue with review/permission status; appointment
questions that can be edited and copied. Drafts/conversations use memory only.
There is no clinically approved medical passage corpus or live answer generation.

## Homepage promise

Find a guide immediately, with or without typing. Guide search filters existing
editorial titles and example questions locally. It is navigation, not a question
answering service, symptom classifier, evidence search or safety screen. A miss
says nothing about a person's safety. Never send the search query through a URL,
analytics, logs or a provider. Show useful existing routes when no match exists.

## Non-negotiable boundaries

Education only; no diagnosis, symptom assessment, individualized treatment,
fertility predictions, medication advice or emergency triage. Static urgent-care
guidance must be discoverable without the assistant; it cannot rule out danger.
Existing medical text and urgency wording still need qualified clinical review.
Source authority, permission, passage approval and claim support are independent.
Never imply publisher endorsement or clinical approval. No community exists;
moderated stories/support remain a future research direction.

This is a private engineering prototype for synthetic scenarios. No public
publication, real-patient invitation, sensitive uploads, persistent chat, tracking
or authentication is authorized by the UI redesign.

## Specifications

Follow AGENTS.md and the current architecture/system-design documents.
`docs/PRD.md` is absent. `AfyaHer_PRD.docx` and `AfyaHer_Architecture.docx` are
version 0.1 drafts dated 4 November 2026, not reviewed specifications. The Word
architecture predates Typesense; it differs from the current Markdown retrieval
design. This homepage change does not resolve or alter that architectural choice.
Request a reviewed canonical PRD before deriving new clinical capabilities.

## Validation still needed

With consented adult participants and fictional tasks, measure purpose/scope
comprehension, guide discovery, source-status interpretation and appointment
preparation. Ask clinicians to review educational and urgent-care wording
separately. Establish privacy, security, accessibility and regulatory release
gates before external patient use. No validation or approval is claimed here.
