---
lang: "en"
pair: "crm-discovery-checklist"
slug_en: "us-custom-crm-discovery-checklist"
title_en: "US Custom CRM Discovery Checklist"
summary_en: "Plan a custom CRM before requesting quotes: map workflows, roles, data, reports, integrations, security and US operating details with this checklist."
tags: ["CRM and customer management", "Web applications", "Business guides"]
target_keywords: ["custom CRM requirements checklist", "CRM discovery checklist", "custom CRM development requirements", "CRM implementation planning"]
status: "draft-unreviewed"
---
If you are searching for a custom CRM requirements checklist, you probably want to know what to define before asking a development team for a proposal. Start with the work the system must support, not a shopping list of features. This guide helps a US business turn its day-to-day process into a brief that a product team can discuss, estimate and later verify.

## The short answer

Document the business problem, user roles, workflow, data, decision-making reports, integrations, access boundaries and acceptance criteria. A quote is easier to compare when each vendor is answering the same scope. Do not copy an online performance target or cost estimate as your own requirement without baseline data and a measurement method.

## Start with an observable business problem

Replace “we need a complete CRM” with a concrete situation: inquiries are lost between handoffs, contact history lives in separate files, managers cannot see the next action, or support staff cannot find the sales context. Record how the work happens now and what a better outcome would look like. If you want a numeric target, first record a trustworthy baseline, define the data source and name the person responsible for measuring it. A benchmark from another company is not evidence about your process.

## Map roles and workflow

For each role, describe what records the person can see, create or change; who owns the next action; and when work should be escalated. Sales, support, finance and managers may use the same customer record but need different access. Keep sensitive sample data out of a general requirements document.

Then map one complete workflow, such as inquiry, qualification, proposal, decision and follow-up. For each step, note the trigger, owner, required information, exceptions and condition for moving forward. If your business has multiple sales motions, document where they differ. A new CRM should express the meaning of the work, not merely reproduce the columns in an old spreadsheet.

## Define data and reports

For each record type, list required fields, the source of truth, links to related records, likely duplicates and retention expectations. Use examples like these to make requirements testable:

| Area | Discovery question | Observable check |
|---|---|---|
| Contact history | How are a person and company linked? | An authorized user can find the relevant interactions from the customer record. |
| Sales opportunity | What event changes its stage? | The change is recorded with its owner and timestamp. |
| Reporting | What decision should the report support? | A manager can find open opportunities that have no next action. |

Ask for reports that support decisions, not charts for their own sake. If you need a revenue forecast, define the amount, stage and date rules behind the number before development begins.

## Integrations, security and operations

List systems such as accounting, inventory, email, telephony, website forms and payment services. For each connection, state which data moves in which direction, which system remains authoritative, how failures appear and who resolves them. “Integrate with accounting” is not specific enough to estimate.

Also assign responsibility for user access, backups, restoration, audit events, incident handling and ongoing maintenance. The [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework) can provide a common discussion structure around governance, identifying and protecting resources, detection, response and recovery. It does not replace contractual, legal or industry-specific review.

## US operating details to verify

Test the business’s actual time zones, date display, USD formatting, address and phone fields, and the specific accounting or payment integrations it uses. If the CRM supports invoicing or tax workflows, identify the states and local jurisdictions relevant to the business and confirm the applicable treatment with an accountant or authoritative source. This checklist does not interpret tax rules. Confirm vendor availability, account terms, API access and support for your exact plan; a logo on an integration page does not prove that your account can use it.

## A reusable requirement template

Complete this sentence for every important need: “When [event] happens, [role] must be able to [action]; the system must show or record [observable result] and provide [next step] if [exception] occurs.” Mark whether the item is required for the first release or can wait. These labels are a project prioritization aid, not a universal standard or a price formula.

Review the workflow with the people who do the work, use sanitized sample data, and agree on acceptance checks before development. See [Rvion’s CRM overview](/en/crm/) and the [medical-equipment CRM demonstration](/en/projects/demos/kimia-medical-crm/); its records are illustrative demo data, not a customer implementation. When your requirements are ready, contact Rvion through the [English contact page](/en/contact/).

## Frequently asked questions

### Do we need to define every future feature first?

No. Define the current scope, dependencies and exclusions. Keep future ideas separate so they are not mistaken for first-release commitments.

### How can I make a vague requirement testable?

Write a real scenario with a user role, input and visible result. “A good report” is vague. “A manager can list records with no next action and see their owners” can be checked.

### Does this checklist determine the project price?

No. It helps make scope and assumptions visible. The price for a specific project depends on the agreed design, implementation, integrations, data quality, security, training and support. Ask for those assumptions in a written proposal.

## Sources and scope

This is an operational checklist, not a market price survey or legal opinion. For publishing guidance, see [Google’s people-first content guidance](https://developers.google.com/search/docs/fundamentals/creating-helpful-content): answer the reader’s problem instead of repeating a search phrase.
