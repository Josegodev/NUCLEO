# PolicyEngine

## Layer

Verified architecture

## Purpose

Validate whether a planned production tool execution is allowed before reaching the execution stage.

## Verified Current Behavior

`PolicyEngine.evaluate(...)` currently:

- denies unauthenticated requests
- allows `echo`
- allows `disk_info`
- allows `system_info` only when `admin` is present in roles
- denies any other tool name

It returns a `PolicyDecision` with:

- `decision`: `PolicyDecisionValue.ALLOW` or `PolicyDecisionValue.DENY`
- `reason`
- `validated_fields`
- `version`

`PolicyDecision` is strict and rejects ambiguous input:

- `decision` must be a `PolicyDecisionValue` enum, not a free string
- `validated_fields` must contain `PolicyValidatedField` enum values
- unknown fields are rejected with `extra="forbid"`

## Approval Flow

`PolicyEngine` is invoked twice in the controlled proposal flow:

- during `POST /agent/run` before returning a dry-run proposal
- during `POST /agent/approve` before executing the persisted proposal

The approval path passes `dry_run=False` to `PolicyEngine`. If the decision is
`PolicyDecisionValue.DENY`, the proposal moves to `DENIED` and `tool.run(...)`
is not called.

The approval endpoint does not reuse the initial policy decision as execution
authority. The initial decision is persisted for audit context only.

## What It Does Not Currently Do

- it does not validate payload shape against the selected tool contract
- it does not make different decisions for `dry_run`; runtime enforces non-execution
- it does not use `read_only` or `risk_level`
- it does not govern lab artifact generation directly

## Strengths

- deny-by-default shape
- clear separation from execution
- authenticated context is part of decision path

## Status Label

- Production authorization: implemented
- Metadata-aware policy: not implemented
- Lab promotion control: not implemented
