export class AuthenticationError extends Error {}

export function createApiClient({ request, refreshToken, getToken, setToken }) {
  let refreshInFlight = null;

  async function getFreshToken() {
    if (!refreshInFlight) {
      refreshInFlight = Promise.resolve()
        .then(refreshToken)
        .then((token) => {
          if (!token) {
            throw new AuthenticationError("Token refresh returned no token");
          }
          setToken(token);
          return token;
        })
        .finally(() => {
          refreshInFlight = null;
        });
    }

    return refreshInFlight;
  }

  return {
    async get(path) {
      const response = await request(path, getToken());

      if (response.status !== 401) {
        return response;
      }

      const token = await getFreshToken();
      const retry = await request(path, token);

      if (retry.status === 401) {
        throw new AuthenticationError("Request remained unauthorized after token refresh");
      }

      return retry;
    },
  };
}
