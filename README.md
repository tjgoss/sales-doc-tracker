# sales-doc-tracker

An AI agent that reads enterprise sales deal emails and tracks every document it takes to close a deal (NDAs, MSAs, SOWs, DPAs, IT security questionnaires, SOC 2 reports) without anyone typing in status updates.

For each document, the agent works out:

- **Type**: NDA, MSA, SOW, DPA, security questionnaire, SOC 2
- **Current holder**: our rep, our legal, our security, or the customer's legal, procurement, or security team
- **Status**: requested, sent, in review, redlines back, signed, done
- **Deadlines**: the last time it moved, any due date mentioned, and how long it has sat with the current holder
- **Evidence**: a confidence score and the email line that supports the answer

Results sync to Salesforce as a `Deal_Document__c` record on each Opportunity, so reps and managers can see who's holding the ball on every deal.

## Status

Work in progress. Week one is underway: building the synthetic dataset, the multi-agent pipeline (Python, Google ADK, Gemini), an accuracy evaluation on hand-labeled threads, and a Salesforce Developer Edition sync. Accuracy results will be published here once they're measured.

## Data

This project uses **synthetic data only**. It contains no real customer, employer, or deal data.

## Author

TJ Goss · [LinkedIn](https://www.linkedin.com/in/tjgoss)
