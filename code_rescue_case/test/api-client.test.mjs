import assert from "node:assert/strict";
import test from "node:test";

import {
  AuthenticationError,
  createApiClient,
} from "../fixed/api-client.mjs";

test("concurrent unauthorized requests share one token refresh", async () => {
  let token = "expired";
  let refreshCalls = 0;
  const requestCalls = [];

  const client = createApiClient({
    getToken: () => token,
    setToken: (value) => {
      token = value;
    },
    refreshToken: async () => {
      refreshCalls += 1;
      await Promise.resolve();
      return "fresh";
    },
    request: async (path, requestToken) => {
      requestCalls.push([path, requestToken]);
      return requestToken === "fresh"
        ? { status: 200, path }
        : { status: 401, path };
    },
  });

  const responses = await Promise.all([client.get("/profile"), client.get("/settings")]);

  assert.equal(refreshCalls, 1);
  assert.deepEqual(
    responses.map((response) => response.status),
    [200, 200],
  );
  assert.equal(requestCalls.filter(([, requestToken]) => requestToken === "fresh").length, 2);
});

test("a failed refresh is cleared so a later request can try again", async () => {
  let token = "expired";
  let refreshCalls = 0;

  const client = createApiClient({
    getToken: () => token,
    setToken: (value) => {
      token = value;
    },
    refreshToken: async () => {
      refreshCalls += 1;
      if (refreshCalls === 1) {
        throw new Error("refresh service unavailable");
      }
      return "fresh";
    },
    request: async (_path, requestToken) => ({
      status: requestToken === "fresh" ? 200 : 401,
    }),
  });

  await assert.rejects(client.get("/profile"), /refresh service unavailable/);
  assert.equal((await client.get("/profile")).status, 200);
  assert.equal(refreshCalls, 2);
});

test("a second unauthorized response stops instead of looping", async () => {
  let token = "expired";
  let requestCalls = 0;

  const client = createApiClient({
    getToken: () => token,
    setToken: (value) => {
      token = value;
    },
    refreshToken: async () => "fresh",
    request: async () => {
      requestCalls += 1;
      return { status: 401 };
    },
  });

  await assert.rejects(client.get("/profile"), AuthenticationError);
  assert.equal(requestCalls, 2);
});
