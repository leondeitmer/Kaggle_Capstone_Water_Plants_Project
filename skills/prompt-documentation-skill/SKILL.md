---
name: prompt-documentation-skill
description: Guidelines and instructions for documenting conversation histories, design decisions, and project architectures in structured Markdown logs.
---

# Prompt Documentation Skill

This skill provides a standardized approach for AI agents to document design discussions, architectural decisions, and technical revisions during pair programming sessions with a user.

---

## 1. Documentation Principles

When documenting project details, adhere to the following principles:
- **Language Consistency:** Always write documentation and log files in English, even if the chat discussion occurred in another language.
- **Clear Rationale:** Document not only the final decision but the critiques, trade-offs, and alternatives considered (e.g., local storage vs. hosted cloud databases).
- **Component Demarcation:** Group systems logically into frontend, backend, database/storage, and deployment layers.
- **Traceability:** Include links to relevant source files and diagrams.

---

## 2. Structure of a Conversation Log

Every log file must follow the structure below (modeled on the provided template in `references/example_log.md`):

### Metadata Block
At the top of the file, specify the log metadata:
```markdown
# Conversation Log: [Log Name / Phase]

**Date:** [ISO Date]  
**Participants:** User & [Agent Name]  
**Topic:** [Short summary of the discussion]
```

### Section 1: Project Overview
Outline the primary objectives and the original features requested by the user:
```markdown
## 1. Project Overview
[Brief description of the project goal]

Core features:
1. [Feature 1]
2. [Feature 2]
```

### Section 2: Design Discussion & Revisions
Document the critique process and the resulting improvements:
- **Original Idea:** The user's initial approach.
- **Discussion:** Critiques and suggestions proposed by the agent.
- **Solution:** The agreed-upon design change.
- **Database/Infrastructure Decision:** Why a particular data path (e.g. `localStorage` or PostgreSQL) was selected.

### Section 3: Agreed Architecture
List the components and how they interact:
- **Frontend:** Tech stack and UI state patterns.
- **Backend:** Server engine and AI agent configurations.
- **MCP Server:** Tools and external endpoints.
- **Deployment:** Containers and cloud services.

---

## 3. Reference Files

- Use [example_log.md](references/example_log.md) in the `references/` directory as the template reference for writing future logs.
