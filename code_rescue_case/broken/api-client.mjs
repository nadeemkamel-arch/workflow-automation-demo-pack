export function createApiClient({ request, refreshToken, getToken, setToken }) {
  return {
    async get(path) {
      const response = await request(path, getToken());

      if (response.status !== 401) {
        return response;
      }

      const token = await refreshToken();
      setToken(token);
      return request(path, token);
    },
  };
}
