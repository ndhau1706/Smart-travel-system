import { API_URL } from "./config";
import { clearStoredAuth, getAuthHeaders, refreshAuthTokens } from "./auth";

export type CaroPlayer = "X" | "O";
export type CaroWinner = CaroPlayer | "draw";

export type CaroPos = { r: number; c: number };
export type CaroMove = CaroPos & { p: CaroPlayer };

export type CaroGamePublic = {
  id: string;
  status: "waiting" | "playing" | "finished" | string;
  board_size: number;
  win_length: number;
  player_x_name?: string | null;
  player_o_name?: string | null;
  turn: CaroPlayer;
  winner?: CaroWinner | null;
  moves: CaroMove[];
  win_line: CaroPos[];
  version: number;
  created_at: string;
  updated_at: string;
};

export type CaroYou = {
  player: CaroPlayer | null;
  token: string | null;
};

export type CaroGameEnvelope = {
  game: CaroGamePublic;
  you: CaroYou;
};

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

export async function createCaroRoom(playerName?: string, boardSize?: number): Promise<CaroGameEnvelope> {
  const res = await fetch(`${API_URL}/games/caro`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player_name: playerName || null, board_size: boardSize ?? null }),
  });
  return handleApi<CaroGameEnvelope>(res);
}

export async function joinCaroRoom(gameId: string, playerName?: string): Promise<CaroGameEnvelope> {
  const res = await fetch(`${API_URL}/games/caro/${encodeURIComponent(gameId)}/join`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player_name: playerName || null }),
  });
  return handleApi<CaroGameEnvelope>(res);
}

export async function getCaroGame(gameId: string): Promise<CaroGamePublic> {
  const res = await fetch(`${API_URL}/games/caro/${encodeURIComponent(gameId)}`);
  return handleApi<CaroGamePublic>(res);
}

export async function makeCaroMove(payload: {
  gameId: string;
  token: string;
  r: number;
  c: number;
  expectedVersion: number;
}): Promise<CaroGamePublic> {
  const res = await fetch(`${API_URL}/games/caro/${encodeURIComponent(payload.gameId)}/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      token: payload.token,
      r: payload.r,
      c: payload.c,
      expected_version: payload.expectedVersion,
    }),
  });
  return handleApi<CaroGamePublic>(res);
}

export type GameKey = "flappy" | "tetris" | "caro_pve";

export type GameRoundInfo = {
  index: number;
  startAt: string;
  endAt: string;
  secondsRemaining: number;
};

type ApiLeaderboardEntry = {
  id: string;
  player_name: string;
  score: number;
  updated_at: string;
  voucher_code?: string | null;
  voucher_percent?: number | null;
};

type ApiLeaderboardResponse = {
  game: GameKey;
  entries: ApiLeaderboardEntry[];
  total_players: number;
  round?: {
    index: number;
    start_at: string;
    end_at: string;
    seconds_remaining: number;
  };
};

type ApiSubmitScoreResponse = {
  entry: ApiLeaderboardEntry;
  leaderboard: ApiLeaderboardResponse;
};

export type GameLeaderboardEntry = {
  id: string;
  name: string;
  score: number;
  updatedAt: string;
  voucherCode?: string | null;
  voucherPercent?: number | null;
};

function mapRoundInfo(round?: ApiLeaderboardResponse["round"]): GameRoundInfo | null {
  if (!round) return null;
  return {
    index: round.index,
    startAt: round.start_at,
    endAt: round.end_at,
    secondsRemaining: round.seconds_remaining,
  };
}

function mapLeaderboardEntry(entry: ApiLeaderboardEntry): GameLeaderboardEntry {
  return {
    id: entry.id,
    name: entry.player_name,
    score: entry.score,
    updatedAt: entry.updated_at,
    voucherCode: entry.voucher_code ?? null,
    voucherPercent: entry.voucher_percent ?? null,
  };
}

export async function fetchGameLeaderboard(
  game: GameKey,
  limit: number = 200,
): Promise<{ entries: GameLeaderboardEntry[]; totalPlayers: number; round: GameRoundInfo | null }> {
  const res = await fetchWithAuth(`${API_URL}/games/leaderboard/${game}?limit=${encodeURIComponent(String(limit))}`);
  const data = await handleApi<ApiLeaderboardResponse>(res);
  return {
    entries: (data.entries || []).map(mapLeaderboardEntry),
    totalPlayers: data.total_players ?? (data.entries || []).length,
    round: mapRoundInfo(data.round),
  };
}

export async function submitGameScore(payload: {
  game: GameKey;
  playerName: string;
  score: number;
}): Promise<{
  entry: GameLeaderboardEntry;
  leaderboard: { entries: GameLeaderboardEntry[]; totalPlayers: number; round: GameRoundInfo | null };
}> {
  const res = await fetchWithAuth(`${API_URL}/games/leaderboard/${payload.game}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      player_name: payload.playerName,
      score: payload.score,
    }),
  });

  const data = await handleApi<ApiSubmitScoreResponse>(res);
  return {
    entry: mapLeaderboardEntry(data.entry),
    leaderboard: {
      entries: (data.leaderboard.entries || []).map(mapLeaderboardEntry),
      totalPlayers: data.leaderboard.total_players ?? data.leaderboard.entries.length,
      round: mapRoundInfo(data.leaderboard.round),
    },
  };
}
