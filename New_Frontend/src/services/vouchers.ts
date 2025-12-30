import { API_URL } from "./config";
import { clearStoredAuth, getAuthHeaders, refreshAuthTokens } from "./auth";

type ApiErrorShape = {
  code?: string;
  message?: string;
  details?: any;
};

type ApiResponse<T> = {
  success: boolean;
  data: T;
  message?: string;
  error?: ApiErrorShape | null;
};

export type VoucherSource = "blog" | "game";

export type VoucherItem = {
  id: string;
  source: VoucherSource;
  title: string;
  code: string;
  percent: number;
  status: string;
  createdAt: string;
  sentAt?: string | null;
};

type ApiVoucherItem = {
  id: string;
  source: VoucherSource;
  title: string;
  code: string;
  percent: number;
  status: string;
  created_at: string;
  sent_at?: string | null;
};

type ApiVoucherResponse = {
  items: ApiVoucherItem[];
  total: number;
};

async function parseJsonSafe(res: Response): Promise<any | null> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

function getErrorMessage(payload: any, fallback: string): string {
  const msg =
    payload?.message ||
    payload?.error?.message ||
    payload?.detail?.[0]?.msg ||
    payload?.detail?.msg ||
    fallback;
  return String(msg || fallback);
}

async function handleApi<T>(res: Response): Promise<T> {
  const payload = (await parseJsonSafe(res)) as ApiResponse<T> | null;
  if (!res.ok) {
    throw new Error(getErrorMessage(payload, `HTTP error! status: ${res.status}`));
  }
  if (!payload?.success) {
    throw new Error(getErrorMessage(payload, "Request failed"));
  }
  return payload.data as T;
}

async function fetchWithAuth(input: RequestInfo, init?: RequestInit): Promise<Response> {
  const res = await fetch(input, {
    ...init,
    headers: { ...(init?.headers || {}), ...getAuthHeaders() },
  });
  if (res.status !== 401) return res;

  const refreshed = await refreshAuthTokens();
  if (!refreshed) {
    clearStoredAuth();
    return res;
  }

  return fetch(input, {
    ...init,
    headers: { ...(init?.headers || {}), ...getAuthHeaders() },
  });
}

function mapVoucher(item: ApiVoucherItem): VoucherItem {
  return {
    id: item.id,
    source: item.source,
    title: item.title,
    code: item.code,
    percent: item.percent,
    status: item.status,
    createdAt: item.created_at,
    sentAt: item.sent_at ?? null,
  };
}

export async function fetchVouchers(): Promise<{ items: VoucherItem[]; total: number }> {
  const res = await fetchWithAuth(`${API_URL}/vouchers`);
  const data = await handleApi<ApiVoucherResponse>(res);
  return {
    items: (data.items || []).map(mapVoucher),
    total: data.total ?? (data.items || []).length,
  };
}
