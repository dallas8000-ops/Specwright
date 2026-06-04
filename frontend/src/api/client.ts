import axios from "axios";
import { useAuthStore } from "@/stores/auth";

export const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = useAuthStore.getState().refreshToken;
      if (refresh) {
        try {
          const { data } = await axios.post("/api/auth/token/refresh/", { refresh });
          useAuthStore.getState().setTokens(data.access, refresh);
          original.headers.Authorization = `Bearer ${data.access}`;
          return api(original);
        } catch {
          useAuthStore.getState().logout();
        }
      }
    }
    return Promise.reject(error);
  }
);

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
