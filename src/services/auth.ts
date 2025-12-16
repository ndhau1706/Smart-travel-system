import { API_URL } from "./config";

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  phone?: string | null;
  avatar?: string | null;
  is_verified: boolean;
  role?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface LoginResponse {
  user: AuthUser;
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export function getAuthHeaders() {
  const stored = localStorage.getItem("auth");
  if (!stored) return {};
  try {
    const parsed = JSON.parse(stored) as { accessToken?: string; access_token?: string; access_token_exp?: number };
    const token = parsed.accessToken || parsed.access_token;
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {};
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  const parseErr = async () => {
    try {
      const data = await res.json();
      return (
        data?.message ||
        data?.error ||
        data?.detail?.[0]?.msg ||
        data?.detail?.msg ||
        res.statusText
      );
    } catch {
      return res.statusText || "Request failed";
    }
  };

  if (!res.ok) {
    const msg = await parseErr();
    const base = msg || res.statusText || "Request failed";
    throw new Error(`${base} (${res.status})`);
  }

  const json = await res.json();
  if (!json.success) {
    throw new Error(json.message || "Request failed");
  }
  return json.data as T;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  return handleResponse<LoginResponse>(res);
}

export async function registerStart(payload: { email: string; name: string; password: string; confirm_password: string }): Promise<{ email: string }> {
  const res = await fetch(`${API_URL}/auth/register/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return handleResponse<{ email: string }>(res);
}

export async function registerVerify(payload: { email: string; otp: string }): Promise<LoginResponse> {
  const res = await fetch(`${API_URL}/auth/register/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return handleResponse<LoginResponse>(res);
}

export async function forgotPassword(email: string): Promise<{ email: string }> {
  const res = await fetch(`${API_URL}/auth/forgot-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  return handleResponse<{ email: string }>(res);
}

export async function resetPassword(payload: { email: string; otp: string; new_password: string; confirm_password: string }): Promise<{ email: string }> {
  const res = await fetch(`${API_URL}/auth/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return handleResponse<{ email: string }>(res);
}

// Profile APIs
export async function getProfile(): Promise<AuthUser> {
  const res = await fetch(`${API_URL}/users/profile`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
  });
  return handleResponse<AuthUser>(res);
}

export async function updateProfile(payload: { name?: string | null; phone?: string | null; avatar?: string | null; theme?: string | null }): Promise<AuthUser> {
  const res = await fetch(`${API_URL}/users/profile`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(payload),
  });
  return handleResponse<AuthUser>(res);
}

export async function uploadAvatar(file: File): Promise<AuthUser> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_URL}/users/avatar`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
    body: form,
  });
  return handleResponse<AuthUser>(res);
}

export async function changePassword(payload: { current_password: string; new_password: string; confirm_password: string }): Promise<{ message: string }> {
  const res = await fetch(`${API_URL}/users/password`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(payload),
  });
  return handleResponse<{ message: string }>(res);
}

export async function refreshSession(refresh_token: string | null | undefined): Promise<AuthTokens> {
  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token }),
  });
  return handleResponse<AuthTokens>(res);
}

export interface UserAddress {
  id: string;
  label?: string | null;
  line1?: string | null;
  line2?: string | null;
  city?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  is_default?: boolean | null;
  created_at?: string;
  updated_at?: string;
}

export interface AddressUpsert {
  label?: string | null;
  line1?: string | null;
  line2?: string | null;
  city?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  is_default?: boolean | null;
}

export async function listAddresses(): Promise<UserAddress[]> {
  const res = await fetch(`${API_URL}/users/addresses`, {
    method: "GET",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
  });
  return handleResponse<UserAddress[]>(res);
}

export async function createAddress(payload: AddressUpsert): Promise<UserAddress> {
  const res = await fetch(`${API_URL}/users/addresses`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(payload),
  });
  return handleResponse<UserAddress>(res);
}

export async function updateAddress(addressId: string, payload: AddressUpsert): Promise<UserAddress> {
  const res = await fetch(`${API_URL}/users/addresses/${encodeURIComponent(addressId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(payload),
  });
  return handleResponse<UserAddress>(res);
}

export async function deleteAddress(addressId: string): Promise<void> {
  const res = await fetch(`${API_URL}/users/addresses/${encodeURIComponent(addressId)}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
  });
  await handleResponse<unknown>(res);
}
