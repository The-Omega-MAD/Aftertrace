# AFTERTRACE
### The incident-response agent that remembers what changed.

<p align="center"><strong>Past incidents are context. They are not verdicts.</strong></p>

AFTERTRACE is a memory-driven incident-continuity assistant for security operations teams. It uses **Hindsight** to retain investigation findings, recall relevant prior incidents, and reason over history when a new alert arrives.

Its defining feature is the **Evidence Delta**: a structured explanation of what matches a previous incident, what has changed, and what remains unknown.

> A familiar alert is not necessarily the same incident. AFTERTRACE remembers the history without blindly repeating the old conclusion.

## The problem

Security analysts repeatedly investigate alerts that resemble earlier cases. Useful context is scattered across tickets, handover notes, chat threads, and post-incident reviews.

When that context is missing, analysts reconstruct work that has already been done. Worse, a superficially similar alert can inherit an earlier benign or malicious conclusion even when the new evidence is materially different.

A stateless chatbot can summarise the alert in front of it. AFTERTRACE asks a different question:

**What did we learn last time, what is different this time, and what should we verify before deciding?**

## The product

AFTERTRACE focuses on one workflow:

1. **Capture** a new incident with structured observations.
2. **Recall** relevant prior investigations from Hindsight.
3. **Compare** current facts with the historical record.
4. **Explain** similarities, differences, and unknowns.
5. **Review** the result with a human analyst.
6. **Retain** the analyst's correction and final outcome for future investigations.

### The Evidence Delta

Most “AI for SOC” prototypes stop at summarisation. AFTERTRACE makes comparison itself the product.

| Dimension | What AFTERTRACE shows |
|---|---|
| Matches | Shared entities, services, event families, or known context |
| Changed evidence | New permissions, actors, timing, source context, or affected assets |
| Unknowns | Facts that have not yet been verified |
| Historical context | Which prior investigation or lesson was recalled |
| Next checks | Evidence-based questions for the analyst, not automatic actions |

A previous outcome is never treated as proof about a new incident.

## The 60-second story

The demo uses synthetic identity-security events.

**First investigation:** an analyst reviews an OAuth application alert. The application is verified as an approved integration in that specific case. No new permission grant is recorded. The analyst retains a qualification: approval in one investigation does not establish that future permission changes are safe.

**A related alert arrives later:** the same application appears, but now a permission change is observed and the actor context is unverified.

| | Previous case | New case |
|---|---|---|
| Application | Same application | Same application |
| Approval context | Verified in that case | Must be re-verified |
| Permission event | No new grant recorded | New permission change observed |
| Disposition | Resolved after review | Undetermined |

AFTERTRACE recalls the earlier investigation and explains:

> “This application appeared in a previously approved investigation. The current event contains a permission change that was not present in that case. The earlier benign outcome does not establish that this event is benign. Verify the permission grant, actor, and business justification before disposition.”

The memory is useful precisely because it remembers both the earlier approval and the warning not to overgeneralise it.

## Why Hindsight is central

Hindsight is the memory layer, not a decorative integration.

| Hindsight operation | AFTERTRACE responsibility |
|---|---|
| **Retain** | Stores incident observations, analyst findings, lessons, and final outcomes. |
| **Recall** | Retrieves prior incidents relevant to a new alert. |
| **Reflect** | Synthesises recalled history into a grounded explanation for the current investigation. |

The learning loop is visible: before history exists, the agent has no prior incident context; after the first investigation, its facts and analyst lesson are retained; on a related alert, Hindsight retrieves relevant history; when evidence differs, the Evidence Delta identifies the change; after analyst review, corrections and outcomes become future context.

## Architecture

```text
             Synthetic security alert
                       |
                       v
              AFTERTRACE interface
                 (Streamlit)
                       |
                       v
              Incident normalisation
                       |
                       v
             Hindsight memory client
                /      |       \
             RETAIN  RECALL   REFLECT
                \      |       /
                       v
             Evidence Delta engine
                       |
                       v
         Similarities / Differences / Unknowns
                       |
                       v
               Human analyst review
                       |
                       v
             Feedback and final outcome
                       |
                       +-------> RETAIN
```

| Layer | Technology | Responsibility |
|---|---|---|
| Interface | Streamlit | Incident intake, comparison, memory trail, analyst feedback |
| Application | Python | Validation, orchestration, evidence comparison |
| Persistent memory | Hindsight | Retain, recall, and reflect |
| Demo data | Synthetic JSON | Repeatable and safe incident scenarios |

The application uses the documented Hindsight Python client, `hindsight-client`, and its `Hindsight` client with `create_bank`, `retain`, `recall`, and `reflect`.

## Run locally

**Requirements:** Python 3.10+, a Hindsight Cloud account/API key or reachable Hindsight deployment, and a configured LLM provider in Hindsight for Reflect.

```bash
git clone https://github.com/<your-username>/exordium-aftertrace.git
cd exordium-aftertrace
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your credentials:

```env
HINDSIGHT_API_KEY=your_key
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
HINDSIGHT_BANK_ID=aftertrace-exordium
```

Never commit `.env` or API keys.

```bash
streamlit run app.py
```

Demo sequence:
1. Connect Hindsight.
2. Seed the first synthetic investigation.
3. Investigate the related alert.
4. Inspect recalled memories and the Evidence Delta.
5. Add an analyst finding, lesson, and outcome.
6. Retain that feedback for a future investigation.

The exact reflection depends on the configured Hindsight deployment and its LLM provider.

## Project structure

```text
aftertrace/
├── app.py
├── aftertrace/
│   ├── __init__.py
│   ├── engine.py
│   └── sample_data.py
├── data/sample_incidents.json
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEMO_SCRIPT.md
│   ├── CONTENT_CHECKLIST.md
│   ├── ARTICLE.md
│   ├── LINKEDIN_POST.md
│   └── VIDEO_SCRIPT.md
├── assets/
├── .env.example
├── .gitignore
└── requirements.txt
```

## Trust and safety boundaries

AFTERTRACE is an investigation-support prototype.

- Included incidents are synthetic.
- It does not connect to or modify production systems.
- It does not execute containment or remediation.
- It does not close, suppress, or declare alerts benign.
- It separates current observations from recalled historical context.
- It surfaces missing evidence.
- A human analyst owns the final decision.

## Judging criteria mapped to evidence

| Criterion | Weight | What the project demonstrates |
|---|---:|---|
| Innovation | 30% | Evidence Delta: explicit comparison of historical and current evidence, including meaningful differences |
| Hindsight Memory | 25% | Retain → recall → reflect, plus a repeatable before/after learning loop |
| Technical Implementation | 20% | Modular Python application, structured incident data, Hindsight integration, validation, and error handling |
| User Experience | 15% | One focused workflow with an incident workspace, memory trail, and clear evidence comparison |
| Real-world Impact | 10% | Better incident handovers, less repeated investigation, and preservation of operational knowledge |

## Implementation status

This repository is an evolving prototype. The application code and synthetic scenarios are the implementation; integrations that require credentials must be configured and tested in the target environment. Planned capabilities must not be presented as completed features.

## References

- [Hindsight documentation](https://hindsight.vectorize.io/)
- [Hindsight Python SDK](https://hindsight.vectorize.io/1.1/sdks/python)
- [Hindsight GitHub repository](https://github.com/vectorize-io/hindsight)
- [Vectorize: What is agent memory?](https://vectorize.io/what-is-agent-memory)
- [Band AI](https://www.band.ai)

## Team

**EXORDIUM**
- Michael Abhishek Duggi
- Shreyas Uppin
- Velishala Sai Charan Teja

<p align="center"><strong>Remember the incident. Re-check the evidence. Never inherit the conclusion.</strong></p>
