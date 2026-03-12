import { create } from "zustand";

interface AuthState {
  isAuthenticated: boolean;
  username: string | null;
  login: (accessToken: string, refreshToken: string, username: string) => void;
  logout: () => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  username: null,
  login: (accessToken, refreshToken, username) => {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    localStorage.setItem("username", username);
    set({ isAuthenticated: true, username });
  },
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("username");
    set({ isAuthenticated: false, username: null });
  },
  hydrate: () => {
    const token = localStorage.getItem("access_token");
    const username = localStorage.getItem("username");
    if (token) {
      set({ isAuthenticated: true, username });
    }
  },
}));
