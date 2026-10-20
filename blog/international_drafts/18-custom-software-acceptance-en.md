---
lang: "en"
pair: "custom-software-acceptance"
slug_en: "custom-software-acceptance-criteria-us"
title_en: "Custom Software Acceptance Criteria"
summary_en: "Set custom software acceptance criteria before delivery: define user scenarios, evidence, defect handling, scope changes and US operating details."
tags: ["Software development", "Project delivery", "Business guides"]
target_keywords: ["custom software acceptance criteria", "software delivery checklist", "user acceptance testing checklist", "UAT criteria for custom software"]
status: "draft-unreviewed"
---
Custom software acceptance criteria should say who checks which outcome, under what conditions. Statements such as “the page should work well” or “the system should be fast” leave room for different interpretations by the client and delivery team. This guide turns expectations into observable scenarios so scope, testing and defect handling are clear before a US project reaches handoff.

## Acceptance criteria are not a feature list

A feature says what the system can do. An acceptance criterion says what result is required to accept that feature. “A user can create a quote” is a feature. A more testable criterion could say: “When an authorized sales user selects a customer and available items, the saved quote shows a traceable identifier and the expected total, appears in the customer history, and cannot be edited by a user without permission.” Adapt the details to the product and contract.

## Write a testable scenario

Use a “given, when, then” structure. Record the user role, input data, visible result and failure case. For example:

| Part | Example criterion |
|---|---|
| Role | A sales user authorized to create quotes |
| Given | The customer and sellable item exist |
| When | The user selects the item and saves a quote |
| Then | The identifier, item and total appear in the quote and customer history |
| Negative case | A user without permission cannot change the record |

For non-functional requirements, name the observation method as well. If mobile usability, accessibility, backup or security matters, state the test environment, reviewer and evidence expected. Avoid “fully secure.” Name the control, owner and verification evidence. The [NIST Cybersecurity Framework 2.0](https://www.nist.gov/cyberframework) can structure a security-risk discussion; by itself it is not a certification or product approval.

## Agree on the handoff package early

Delivery may include more than a final application build. Decide whether the agreement includes a runnable release, access credentials, setup documentation, backup and restoration steps, active integrations, permitted test data, out-of-scope items and post-launch support ownership. If source code, a repository, domain or cloud account is part of the handoff, document ownership and transfer steps before work starts. Do not assume an item is included if the contract or project record does not say so.

## Handle defects and scope changes separately

For each test, record pass or fail, environment and version, evidence, business impact and follow-up owner. Agree in advance who classifies a defect, what blocks acceptance and how a fix will be retested. Keep a new feature request separate from a defect: the former may require a scope change and revised estimate; the latter is a mismatch with an agreed criterion. Do not copy a severity threshold or defect count from another article. Set it for the risk and contract of this project.

## US project details to verify

Run scenarios using the actual time zones, date display, USD formatting, address and phone fields, and integrations the organization uses. For invoice or tax workflows, confirm the relevant states and local jurisdictions with the finance owner or an authoritative source. This guide does not interpret tax or legal obligations. Test a payment or messaging integration in an environment and account that reflect the real configuration; a screenshot or mockup is not proof of a live connection.

For security expectations, identify the business data involved, access boundaries, backup and recovery responsibilities, and how an incident is escalated. NIST CSF 2.0 is a voluntary framework that can help organize these outcomes. Any contractual, industry or legal obligation still needs its own review. The framework’s [official overview](https://www.nist.gov/cyberframework) explains its role and structure.

## Make the acceptance session repeatable

Name a representative user, keep the test version and data consistent, run each scenario in the agreed order and record the outcome with the project owners. For a failed case, write the reproduction steps and expected result. After a fix, rerun the same case and check related workflows for side effects. A short record of the version, accepted items, open issues and final decision reduces disagreement later.

See [Rvion’s CRM overview](/en/crm/) and the [illustrative Kimia demonstration](/en/projects/demos/kimia-medical-crm/) for an example workflow. The company and records in the demo are fictional, not a real customer delivery. For a custom application, review [web application development services](/en/services/custom-web-application/) or contact the team through the [English contact page](/en/contact/).

## Frequently asked questions

### Who writes the acceptance criteria?

The process owner and user representative define the business outcome. The technical team helps express it as testable behavior. One party should not decide the other party’s assumptions alone.

### Must every issue be closed before acceptance?

That depends on the agreement and the effect of each issue on the work. Define the difference between an acceptance blocker, a tracked defect and a new development request before testing, then record the decision.

### Does a passed acceptance test prove complete security or quality?

No. A test covers the named scenarios and version. Document test boundaries, limitations and post-handoff ownership.

## Sources and scope

The [NIST Guide to Software Acceptance](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication500-180.pdf) highlights user involvement in developing requirements and acceptance criteria. [NIST CSF 2.0](https://www.nist.gov/cyberframework) provides a reference for discussing cybersecurity outcomes. Neither replaces the contract, independent testing or specialist review.
