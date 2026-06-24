# Rescue Report: Duplicate Token Refresh

## Symptom

When two page requests receive `401 Unauthorized` at the same time, the client starts two token refresh calls. The second refresh can invalidate the token returned by the first one, producing repeated sign-outs or requests that fail again after refresh.

## Root Cause

The original client handles each `401` independently. It has no shared in-flight refresh promise, does not reject an empty refresh result, and retries without stopping a second `401` from becoming another loop elsewhere in the application.

## Repair

- Share one refresh promise across concurrent requests.
- Store the fresh token once.
- Clear the shared promise after success or failure so a later request can retry.
- Stop after one request retry and return an explicit authentication error.

## Verification

The focused tests prove that:

1. Two simultaneous unauthorized requests make one refresh call.
2. A failed refresh does not poison future attempts.
3. A second unauthorized response stops after one retry.

Run:

```bash
node --test code_rescue_case/test/api-client.test.mjs
```

## Handoff

The sample uses injected request and token functions so the concurrency behavior can be tested without credentials or a live authentication provider. A client implementation would connect these functions to its existing fetch, storage, and refresh endpoints after the data and credential boundaries are agreed.
