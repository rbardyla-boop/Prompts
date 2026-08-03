# Local OpenAI-Compatible Adapter

Adapter ID: `local.openai-compatible`  
Status: implementation profile.

## Purpose

Use a local model server exposing an OpenAI-compatible API without making the model or endpoint canonical project state.

## Required configuration

```text
base_url
model_id
quantization
context_limit
sampling_parameters
request_timeout
network_policy
```

Store configuration hashes in the run receipt. Do not store bearer tokens or private prompt contents in public logs.

## Local-only mode

Local-only mode requires:

- endpoint restricted to loopback or an approved local network address;
- no fallback to a cloud provider;
- explicit request timeouts;
- zero unauthorized network egress verified outside the model process;
- model identity and quantization recorded;
- identical configuration for fair comparison arms.

## Small-model output control

When a small model struggles with broad rankings or verbose schemas:

- reduce the decision to one atomic action;
- use independently named fields rather than fixed first-option rankings;
- preserve raw structured output;
- validate against an exact schema;
- count parser or model failure separately from task failure.

Do not change the model between comparison arms unless the contract explicitly studies model differences.

## Authority boundary

The local model may plan, classify or draft. It cannot change permissions, trust tiers, completion rules or terminal state.
