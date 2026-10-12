# PromptShield Threat Model — v0.1

## 1. System overview
PromptShield protects a fictional company AI assistant that retrieves documents and can request limited tool actions. The backend enforces user permissions independently of the language model.

## 2. Assets to protect
- Restricted company documents, such as confidential salary records.
- User identity and role information.
- Tool execution permissions.
- Security policy configuration.
- Audit logs containing access and action decisions.

## 3. Trust boundaries
- User input is untrusted.
- Retrieved document content is untrusted, even when it comes from an internal source.
- LLM output is untrusted and must be validated.
- Only backend policy code may authorise access or execute a tool.
- The model must never be allowed to modify its own permissions.

## 4. Adversaries and attacks
- A user attempts to access a document outside their permissions.
- A user submits direct prompt-injection instructions.
- A retrieved document contains indirect prompt-injection instructions.
- The model proposes a tool call with unauthorised arguments.
- The model fabricates or modifies document identifiers.
- Malformed inputs attempt to bypass validation.
- An attacker attempts to make the assistant reveal restricted information through its answer.

## 5. Security requirements
1. A user cannot retrieve a restricted document without explicit authorisation.
2. Every document retrieval is authorised on the server.
3. Every tool call is validated and authorised before execution.
4. The model cannot grant itself access or bypass server-side checks.
5. Retrieved documents are treated as data, not trusted instructions.
6. Denied actions produce auditable decision records.
7. Security tests run deterministically and report actual outcomes.
8. Safe, authorised requests should continue to work.

## 6. Assumptions
- The initial application uses fictional documents and simulated tool actions.
- User identities and roles are seeded test identities, not production authentication.
- The LLM is a potentially unreliable component.
- The application does not execute arbitrary shell commands or send real messages.

## 7. Out of scope
- Protection against every possible prompt-injection technique.
- Production identity management and enterprise deployment.
- Formal security certification.
- Guaranteed detection of malicious intent from text alone.

## 8. Success criteria
PromptShield must prevent unauthorised document retrieval and tool execution through server-side enforcement, including when the LLM proposes a prohibited action. These properties must be tested independently of the model's willingness to follow instructions.

---

### The three security boundaries that matter most

#### Boundary 1 — Document access
The document service checks the user's permissions before returning content. Hiding a document in the UI or telling the model not to reveal it is not sufficient.

#### Boundary 2 — Tool execution
The model may propose draft_notification, but the backend validates the tool name, arguments and user's authority before performing the simulated action.

#### Boundary 3 — Model output
The model may be manipulated into producing an unsafe answer. PromptShield must not rely solely on the model's refusal to protect restricted data. Sensitive information must not be placed into an untrusted model context without a justified access decision.

> **Important limitation:** Once confidential information has been passed to a model, an output filter cannot guarantee that the information will never be disclosed. Our primary defence is to prevent unauthorised access in the first place.
