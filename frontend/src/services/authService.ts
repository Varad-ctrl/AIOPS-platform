import { api } from "./api";
import type { LoginPayload, RegisterPayload, Token, User } from "@/types";

export async function login(payload: LoginPayload): Promise<Token> {
  const { data } = await api.post<Token>("/auth/login", payload);
  return data;
}

export async function register(payload: RegisterPayload): Promise<User> {
  const { data } = await api.post<User>("/auth/register", payload);
  return data;
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export async function logout(): Promise<void> {
  await api.post("/auth/logout");
}
