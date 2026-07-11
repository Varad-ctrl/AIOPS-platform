export type Role = "admin" | "devops_engineer" | "viewer";

export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  role: Role;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  full_name: string;
  password: string;
  role: Role;
}
