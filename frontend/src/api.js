/**
 * Central API base URL config.
 * In development, Vite proxies requests to localhost:8000.
 * In production (Vercel), set VITE_API_URL to your Railway backend URL.
 * e.g. VITE_API_URL=https://your-app.up.railway.app
 */
const BASE_URL = import.meta.env.VITE_API_URL || '';

export const api = {
  get: (path) => fetch(`${BASE_URL}${path}`),
  post: (path, body) => fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }),
  delete: (path) => fetch(`${BASE_URL}${path}`, { method: 'DELETE' }),
};
