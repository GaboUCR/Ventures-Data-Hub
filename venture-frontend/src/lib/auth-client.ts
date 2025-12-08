// src/lib/auth-client.ts
import { API_BASE_URL } from "./config";

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user_id: string;
  company_id?: string | null;
  full_name?: string | null;
  global_role: string;
};

export type SignupPayload = {
  email: string;
  password: string;
  full_name: string;
  company_name: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

async function handleAuthResponse(res: Response): Promise<AuthResponse> {
  if (!res.ok) {
    let message = "Authentication failed";
    try {
      const body = await res.json();
      if (body?.detail) {
        message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(message);
  }
  return res.json();
}

export async function signup(payload: SignupPayload): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleAuthResponse(res);
}

export async function login(payload: LoginPayload): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleAuthResponse(res);
}
