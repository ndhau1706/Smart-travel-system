const CLIENT_ID_KEY = "profile:client_id";
const DISPLAY_NAME_KEY = "profile:display_name";

function generateId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function readAuthName(): string {
  try {
    const stored = localStorage.getItem("auth");
    if (!stored) return "";
    const parsed = JSON.parse(stored) as { user?: { name?: string } };
    return (parsed?.user?.name || "").trim();
  } catch {
    return "";
  }
}

export function getClientId(): string {
  try {
    const stored = localStorage.getItem(CLIENT_ID_KEY);
    if (stored) return stored;
    const next = generateId();
    localStorage.setItem(CLIENT_ID_KEY, next);
    return next;
  } catch {
    return generateId();
  }
}

export function getDisplayName(): string {
  try {
    const stored = localStorage.getItem(DISPLAY_NAME_KEY);
    if (stored && stored.trim()) return stored.trim();
    const legacyFeed = localStorage.getItem("newsfeed:display_name");
    if (legacyFeed && legacyFeed.trim()) return legacyFeed.trim();
    const legacyGame = localStorage.getItem("games:display_name");
    if (legacyGame && legacyGame.trim()) return legacyGame.trim();
  } catch {
    // ignore
  }
  const authName = readAuthName();
  return authName || "Khách";
}

export function setDisplayName(name: string) {
  try {
    const trimmed = name.trim();
    if (trimmed) {
      localStorage.setItem(DISPLAY_NAME_KEY, trimmed);
    } else {
      localStorage.removeItem(DISPLAY_NAME_KEY);
    }
  } catch {
    // ignore
  }
}
