import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { cn } from "../../components/ui/utils";
import {
  createCaroRoom,
  getCaroGame,
  joinCaroRoom,
  makeCaroMove,
  fetchGameLeaderboard,
  submitGameScore,
  type CaroGamePublic as OnlineCaroGame,
  type CaroMove as OnlineCaroMove,
  type CaroYou as OnlineCaroYou,
  type GameLeaderboardEntry,
  type GameRoundInfo,
} from "../../services/games";
import { getAuthHeaders } from "../../services/auth";
import { getDisplayName } from "../../services/identity";

type Player = "X" | "O";
type Cell = Player | null;
type Pos = { r: number; c: number };
type Mode = "pvp" | "pve";

const DEFAULT_BOARD_SIZE = 15;
const MIN_BOARD_SIZE = 11;
const MAX_BOARD_SIZE = 30;
const WIN_LENGTH = 5;
const SCORE_WIN = 1_000_000_000;
const AI_TIME_BUDGET_MS = 700;
const AI_MAX_DEPTH = 6;
const AI_ROOT_MAX_CANDIDATES = 18;
const AI_BRANCH_MAX_CANDIDATES = 12;
const AI_PLAYER_STARTS_IN_PVE = false;

function createBoard(size: number): Cell[][] {
  return Array.from({ length: size }, () => Array.from({ length: size }, () => null));
}

function inBounds(r: number, c: number, size: number): boolean {
  return r >= 0 && r < size && c >= 0 && c < size;
}

function getCenter(size: number): Pos {
  const mid = Math.floor(size / 2);
  return { r: mid, c: mid };
}

function buildLine(start: Pos, dir: Pos, length: number): Pos[] {
  return Array.from({ length }, (_, i) => ({ r: start.r + dir.r * i, c: start.c + dir.c * i }));
}

function findWin(board: Cell[][], last: Pos, player: Player): Pos[] | null {
  const size = board.length;
  const directions: Pos[] = [
    { r: 0, c: 1 },
    { r: 1, c: 0 },
    { r: 1, c: 1 },
    { r: 1, c: -1 },
  ];

  for (const dir of directions) {
    let minK = 0;
    let maxK = 0;

    // walk backward
    for (let k = 1; k < WIN_LENGTH; k++) {
      const r = last.r - dir.r * k;
      const c = last.c - dir.c * k;
      if (!inBounds(r, c, size) || board[r][c] !== player) break;
      minK = -k;
    }

    // walk forward
    for (let k = 1; k < WIN_LENGTH; k++) {
      const r = last.r + dir.r * k;
      const c = last.c + dir.c * k;
      if (!inBounds(r, c, size) || board[r][c] !== player) break;
      maxK = k;
    }

    const span = maxK - minK + 1;
    if (span < WIN_LENGTH) continue;

    // choose a concrete 5-length segment that contains last move
    const startKMin = Math.max(minK, -WIN_LENGTH + 1);
    const startKMax = Math.min(maxK - WIN_LENGTH + 1, 0);
    const startK = startKMin <= startKMax ? startKMin : minK;

    const start: Pos = { r: last.r + dir.r * startK, c: last.c + dir.c * startK };
    const line = buildLine(start, dir, WIN_LENGTH);
    if (line.every((p) => inBounds(p.r, p.c, size) && board[p.r][p.c] === player)) return line;
  }

  return null;
}

function collectCandidates(board: Cell[][]): Pos[] {
  const size = board.length;
  const set = new Set<string>();
  let hasStone = false;

  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      if (!board[r][c]) continue;
      hasStone = true;
      for (let dr = -2; dr <= 2; dr++) {
        for (let dc = -2; dc <= 2; dc++) {
          const rr = r + dr;
          const cc = c + dc;
          if (!inBounds(rr, cc, size)) continue;
          if (board[rr][cc]) continue;
          set.add(`${rr}:${cc}`);
        }
      }
    }
  }

  if (!hasStone) return [getCenter(size)];

  const out: Pos[] = [];
  for (const key of set) {
    const [r, c] = key.split(":").map((n) => Number(n));
    if (!Number.isFinite(r) || !Number.isFinite(c)) continue;
    out.push({ r, c });
  }
  return out;
}

function evaluateAt(board: Cell[][], pos: Pos, player: Player): number {
  const size = board.length;
  if (board[pos.r]?.[pos.c]) return -Infinity;

  const directions: Pos[] = [
    { r: 0, c: 1 },
    { r: 1, c: 0 },
    { r: 1, c: 1 },
    { r: 1, c: -1 },
  ];

  let score = 0;
  let openThrees = 0;
  let openFours = 0;

  for (const dir of directions) {
    let countA = 0;
    let rr = pos.r + dir.r;
    let cc = pos.c + dir.c;
    while (inBounds(rr, cc, size) && board[rr][cc] === player) {
      countA++;
      rr += dir.r;
      cc += dir.c;
    }
    const openA = inBounds(rr, cc, size) && board[rr][cc] === null;

    let countB = 0;
    rr = pos.r - dir.r;
    cc = pos.c - dir.c;
    while (inBounds(rr, cc, size) && board[rr][cc] === player) {
      countB++;
      rr -= dir.r;
      cc -= dir.c;
    }
    const openB = inBounds(rr, cc, size) && board[rr][cc] === null;

    const count = countA + countB + 1;
    const openEnds = (openA ? 1 : 0) + (openB ? 1 : 0);

    if (count >= WIN_LENGTH) return SCORE_WIN;

    // Pattern scoring (simple Gomoku-like heuristics)
    if (count === 4 && openEnds === 2) {
      score += 2_800_000;
      openFours++;
    } else if (count === 4 && openEnds === 1) {
      score += 320_000;
    } else if (count === 3 && openEnds === 2) {
      score += 90_000;
      openThrees++;
    } else if (count === 3 && openEnds === 1) {
      score += 12_000;
    } else if (count === 2 && openEnds === 2) {
      score += 1_800;
    } else if (count === 2 && openEnds === 1) {
      score += 320;
    } else if (count === 1 && openEnds === 2) {
      score += 80;
    } else {
      score += 10;
    }
  }

  // Bonus for multi-threat shapes
  if (openFours >= 2) score += 5_000_000;
  if (openThrees >= 2) score += 240_000;

  // Prefer being near center (slightly)
  const center = getCenter(size);
  const centerDist = Math.abs(pos.r - center.r) + Math.abs(pos.c - center.c);
  score += Math.max(0, 40 - centerDist);

  return score;
}

function otherPlayer(p: Player): Player {
  return p === "X" ? "O" : "X";
}

function orderCandidates(
  board: Cell[][],
  candidates: Pos[],
  aiPlayer: Player,
  humanPlayer: Player,
  max: number,
): Pos[] {
  const center = getCenter(board.length);
  const scored = candidates
    .map((pos) => {
      const attack = evaluateAt(board, pos, aiPlayer);
      const defend = evaluateAt(board, pos, humanPlayer);
      const centerDist = Math.abs(pos.r - center.r) + Math.abs(pos.c - center.c);
      const score =
        Math.max(attack, defend * 0.95) + attack * 0.1 + defend * 0.08 + Math.max(0, 25 - centerDist);
      return { pos, score };
    })
    .sort((a, b) => b.score - a.score);

  return scored.slice(0, Math.min(max, scored.length)).map((s) => s.pos);
}

function evaluateBoard(board: Cell[][], aiPlayer: Player, humanPlayer: Player): number {
  const candidates = collectCandidates(board);
  if (candidates.length === 0) return 0;

  let bestAi = -Infinity;
  let bestHuman = -Infinity;
  let aiTop1 = -Infinity;
  let aiTop2 = -Infinity;
  let aiTop3 = -Infinity;
  let humanTop1 = -Infinity;
  let humanTop2 = -Infinity;
  let humanTop3 = -Infinity;

  for (const pos of candidates) {
    const a = evaluateAt(board, pos, aiPlayer);
    const h = evaluateAt(board, pos, humanPlayer);

    bestAi = Math.max(bestAi, a);
    bestHuman = Math.max(bestHuman, h);

    if (a > aiTop1) {
      aiTop3 = aiTop2;
      aiTop2 = aiTop1;
      aiTop1 = a;
    } else if (a > aiTop2) {
      aiTop3 = aiTop2;
      aiTop2 = a;
    } else if (a > aiTop3) {
      aiTop3 = a;
    }

    if (h > humanTop1) {
      humanTop3 = humanTop2;
      humanTop2 = humanTop1;
      humanTop1 = h;
    } else if (h > humanTop2) {
      humanTop3 = humanTop2;
      humanTop2 = h;
    } else if (h > humanTop3) {
      humanTop3 = h;
    }
  }

  if (bestAi >= SCORE_WIN) return SCORE_WIN;
  if (bestHuman >= SCORE_WIN) return -SCORE_WIN;

  const a1 = Number.isFinite(aiTop1) ? aiTop1 : 0;
  const a2 = Number.isFinite(aiTop2) ? aiTop2 : 0;
  const a3 = Number.isFinite(aiTop3) ? aiTop3 : 0;
  const h1 = Number.isFinite(humanTop1) ? humanTop1 : 0;
  const h2 = Number.isFinite(humanTop2) ? humanTop2 : 0;
  const h3 = Number.isFinite(humanTop3) ? humanTop3 : 0;

  // Emphasize urgent defense slightly more than attack to reduce tactical blunders.
  return (a1 * 1.15 + a2 * 0.7 + a3 * 0.4) - (h1 * 1.35 + h2 * 0.85 + h3 * 0.5);
}

function chooseAiMove(board: Cell[][], aiPlayer: Player, humanPlayer: Player): Pos | null {
  const working = board.map((row) => row.slice());
  const candidates = collectCandidates(working);
  if (candidates.length === 0) return null;

  // 1) If AI can win immediately, do it.
  for (const pos of candidates) {
    const s = evaluateAt(working, pos, aiPlayer);
    if (s >= SCORE_WIN) return pos;
  }

  // 2) If opponent can win immediately, block it.
  let bestBlock: { pos: Pos; score: number } | null = null;
  for (const pos of candidates) {
    const s = evaluateAt(working, pos, humanPlayer);
    if (s >= SCORE_WIN) {
      if (!bestBlock || s > bestBlock.score) bestBlock = { pos, score: s };
    }
  }
  if (bestBlock) return bestBlock.pos;

  const deadline = performance.now() + AI_TIME_BUDGET_MS;

  const orderedRoot = orderCandidates(
    working,
    candidates,
    aiPlayer,
    humanPlayer,
    Math.min(AI_ROOT_MAX_CANDIDATES, candidates.length),
  );

  const alphabeta = (
    depthRemaining: number,
    alpha: number,
    beta: number,
    playerToMove: Player,
    ply: number,
  ): number => {
    if (performance.now() > deadline) return evaluateBoard(working, aiPlayer, humanPlayer);
    if (depthRemaining <= 0) return evaluateBoard(working, aiPlayer, humanPlayer);

    const localCandidatesAll = collectCandidates(working);
    if (localCandidatesAll.length === 0) return 0;

    const localCandidates = orderCandidates(
      working,
      localCandidatesAll,
      aiPlayer,
      humanPlayer,
      Math.min(AI_BRANCH_MAX_CANDIDATES, localCandidatesAll.length),
    );

    if (playerToMove === aiPlayer) {
      let best = -Infinity;
      for (const pos of localCandidates) {
        if (performance.now() > deadline) break;

        working[pos.r][pos.c] = aiPlayer;
        const win = findWin(working, pos, aiPlayer);
        let score: number;
        if (win) {
          score = SCORE_WIN - ply;
        } else {
          score = alphabeta(depthRemaining - 1, alpha, beta, humanPlayer, ply + 1);
        }
        working[pos.r][pos.c] = null;

        best = Math.max(best, score);
        alpha = Math.max(alpha, best);
        if (alpha >= beta) break;
      }
      return best;
    }

    let best = Infinity;
    for (const pos of localCandidates) {
      if (performance.now() > deadline) break;

      working[pos.r][pos.c] = humanPlayer;
      const win = findWin(working, pos, humanPlayer);
      let score: number;
      if (win) {
        score = -SCORE_WIN + ply;
      } else {
        score = alphabeta(depthRemaining - 1, alpha, beta, aiPlayer, ply + 1);
      }
      working[pos.r][pos.c] = null;

      best = Math.min(best, score);
      beta = Math.min(beta, best);
      if (alpha >= beta) break;
    }
    return best;
  };

  let bestPos: Pos = orderedRoot[0] ?? candidates[0] ?? getCenter(board.length);
  let bestScore = -Infinity;

  for (let depth = 1; depth <= AI_MAX_DEPTH; depth++) {
    if (performance.now() > deadline) break;

    let localBestPos = bestPos;
    let localBestScore = -Infinity;
    let alpha = -Infinity;
    const beta = Infinity;

    for (const pos of orderedRoot) {
      if (performance.now() > deadline) break;

      working[pos.r][pos.c] = aiPlayer;
      const win = findWin(working, pos, aiPlayer);
      let score: number;
      if (win) {
        score = SCORE_WIN - 1;
      } else {
        score = alphabeta(depth - 1, alpha, beta, humanPlayer, 2);
      }
      working[pos.r][pos.c] = null;

      if (score > localBestScore) {
        localBestScore = score;
        localBestPos = pos;
      }
      alpha = Math.max(alpha, localBestScore);
    }

    if (performance.now() <= deadline) {
      bestPos = localBestPos;
      bestScore = localBestScore;
    }

    if (bestScore >= SCORE_WIN - 10) break;
  }

  return bestPos;
}

function CaroLocalGame({
  isAuthenticated,
  onRequireAuth,
}: {
  isAuthenticated: boolean;
  onRequireAuth: (message: string) => void;
}) {
  const [mode, setMode] = useState<Mode>("pvp");
  const [board, setBoard] = useState<Cell[][]>(() => createBoard(DEFAULT_BOARD_SIZE));
  const boardSize = board.length;
  const [boardSizeInput, setBoardSizeInput] = useState(String(DEFAULT_BOARD_SIZE));
  const [currentPlayer, setCurrentPlayer] = useState<Player>("X");
  const [winner, setWinner] = useState<Player | "draw" | null>(null);
  const [moves, setMoves] = useState<Array<Pos & { p: Player }>>([]);
  const [winLine, setWinLine] = useState<Pos[] | null>(null);
  const [isAiThinking, setIsAiThinking] = useState(false);
  const boardWrapRef = useRef<HTMLDivElement | null>(null);
  const [cellPx, setCellPx] = useState(36);
  const [leaderboard, setLeaderboard] = useState<GameLeaderboardEntry[]>([]);
  const [totalPlayers, setTotalPlayers] = useState(0);
  const [roundInfo, setRoundInfo] = useState<GameRoundInfo | null>(null);
  const [countdown, setCountdown] = useState("");

  useEffect(() => {
    const el = boardWrapRef.current;
    if (!el) return;

    const compute = () => {
      const style = window.getComputedStyle(el);
      const paddingLeft = Number.parseFloat(style.paddingLeft || "0") || 0;
      const paddingRight = Number.parseFloat(style.paddingRight || "0") || 0;
      const contentWidth = Math.max(0, el.clientWidth - paddingLeft - paddingRight);
      const gapPx = 1; // gap-px
      const innerPaddingPx = 2; // p-px (left + right)
      const available = Math.max(0, contentWidth - innerPaddingPx - (boardSize - 1) * gapPx);
      const raw = Math.floor(available / boardSize);
      const next = Math.max(18, Math.min(36, raw));
      setCellPx((prev) => (prev === next ? prev : next));
    };

    compute();
    const ro = new ResizeObserver(compute);
    ro.observe(el);
    return () => ro.disconnect();
  }, [boardSize]);

  useEffect(() => {
    if (mode !== "pve") return;
    let active = true;
    fetchGameLeaderboard("caro_pve")
      .then((data) => {
        if (!active) return;
        setLeaderboard(data.entries);
        setTotalPlayers(data.totalPlayers);
        setRoundInfo(data.round);
      })
      .catch(() => {
        if (!active) return;
        setLeaderboard([]);
        setTotalPlayers(0);
        setRoundInfo(null);
      });
    return () => {
      active = false;
    };
  }, [mode]);

  const formatCountdown = (totalSeconds: number) => {
    const safe = Math.max(0, totalSeconds);
    const days = Math.floor(safe / 86400);
    const hours = Math.floor((safe % 86400) / 3600);
    const minutes = Math.floor((safe % 3600) / 60);
    const seconds = safe % 60;
    const hh = String(hours).padStart(2, "0");
    const mm = String(minutes).padStart(2, "0");
    const ss = String(seconds).padStart(2, "0");
    return days > 0 ? `${days}d ${hh}:${mm}:${ss}` : `${hh}:${mm}:${ss}`;
  };

  useEffect(() => {
    if (!roundInfo?.endAt) {
      setCountdown("");
      return;
    }
    const update = () => {
      const remainingMs = new Date(roundInfo.endAt).getTime() - Date.now();
      const remainingSeconds = Math.max(0, Math.floor(remainingMs / 1000));
      setCountdown(formatCountdown(remainingSeconds));
    };
    update();
    const timer = window.setInterval(update, 1000);
    return () => window.clearInterval(timer);
  }, [roundInfo?.endAt]);

  const aiPlayer: Player = useMemo(() => {
    if (mode !== "pve") return "O";
    return AI_PLAYER_STARTS_IN_PVE ? "X" : "O";
  }, [mode]);

  const humanPlayer: Player = useMemo(() => otherPlayer(aiPlayer), [aiPlayer]);

  const lastMove = moves[moves.length - 1] ?? null;

  const winLookup = useMemo(() => {
    const set = new Set<string>();
    for (const p of winLine ?? []) set.add(`${p.r}:${p.c}`);
    return set;
  }, [winLine]);

  const reset = () => {
    setBoard(createBoard(boardSize));
    setCurrentPlayer("X");
    setWinner(null);
    setMoves([]);
    setWinLine(null);
    setIsAiThinking(false);
  };

  const applyBoardSize = () => {
    const parsed = Number.parseInt(boardSizeInput.trim(), 10);
    if (!Number.isFinite(parsed) || parsed < MIN_BOARD_SIZE || parsed > MAX_BOARD_SIZE) {
      toast.error(
        "Kích thước bàn cờ không hợp lệ",
        `Nhập N là số nguyên từ ${MIN_BOARD_SIZE} đến ${MAX_BOARD_SIZE}`,
      );
      return;
    }
    if (parsed === boardSize) return;
    setBoardSizeInput(String(parsed));
    setBoard(createBoard(parsed));
    setCurrentPlayer("X");
    setWinner(null);
    setMoves([]);
    setWinLine(null);
    setIsAiThinking(false);
  };

  const undo = () => {
    if (moves.length === 0) return;
    if (winner) setWinner(null);
    setWinLine(null);
    setIsAiThinking(false);

    let nextMoves = moves.slice(0, -1);
    const nextPlayerAfterUndo: Player = nextMoves.length % 2 === 0 ? "X" : "O";
    if (mode === "pve" && nextMoves.length > 0 && nextPlayerAfterUndo === aiPlayer) {
      nextMoves = nextMoves.slice(0, -1);
    }
    const newBoard = createBoard(boardSize);
    for (const m of nextMoves) newBoard[m.r][m.c] = m.p;
    setBoard(newBoard);
    setMoves(nextMoves);
    setCurrentPlayer(nextMoves.length % 2 === 0 ? "X" : "O");
  };

  const recordPveWin = async () => {
    if (!isAuthenticated) {
      onRequireAuth("Vui lòng đăng nhập để ghi nhận chiến thắng PvE");
      return;
    }
    const safeName = getDisplayName().trim() || "Khách";
    try {
      const data = await submitGameScore({ game: "caro_pve", playerName: safeName, score: 1 });
      setLeaderboard(data.leaderboard.entries);
      setTotalPlayers(data.leaderboard.totalPlayers);
      setRoundInfo(data.leaderboard.round);
      toast.success("Đã ghi nhận chiến thắng PvE");
    } catch (err: any) {
      const message = err?.message || "Không thể ghi nhận chiến thắng";
      toast.error(message);
      if (String(message).includes("401")) {
        onRequireAuth("Vui lòng đăng nhập để ghi nhận chiến thắng PvE");
      }
    }
  };

  const applyMove = (r: number, c: number, player: Player) => {
    if (winner) return;
    if (board[r]?.[c]) return;

    const nextBoard = board.map((row) => row.slice());
    nextBoard[r][c] = player;

    const nextMoves = [...moves, { r, c, p: player }];
    setBoard(nextBoard);
    setMoves(nextMoves);

    const line = findWin(nextBoard, { r, c }, player);
    if (line) {
      setWinner(player);
      setWinLine(line);
      if (mode === "pve" && player === humanPlayer) {
        void recordPveWin();
      }
      return;
    }

    if (nextMoves.length === boardSize * boardSize) {
      setWinner("draw");
      return;
    }

    setCurrentPlayer(player === "X" ? "O" : "X");
  };

  const place = (r: number, c: number) => {
    if (isAiThinking) return;
    if (mode === "pve" && currentPlayer === aiPlayer) return;
    if (winner) return;
    if (board[r][c]) return;
    applyMove(r, c, currentPlayer);
  };

  useEffect(() => {
    if (mode !== "pve") return;
    if (winner) {
      setIsAiThinking(false);
      return;
    }
    if (currentPlayer !== aiPlayer) {
      setIsAiThinking(false);
      return;
    }

    setIsAiThinking(true);
    const t = window.setTimeout(() => {
      const move = chooseAiMove(board, aiPlayer, humanPlayer);
      if (!move) {
        setIsAiThinking(false);
        return;
      }
      applyMove(move.r, move.c, aiPlayer);
      setIsAiThinking(false);
    }, 350);

    return () => window.clearTimeout(t);
  }, [mode, currentPlayer, winner, board, aiPlayer, humanPlayer]);

  const statusLabel = (() => {
    if (winner === "draw") return "Hòa!";
    if (winner) {
      if (mode === "pve") return winner === humanPlayer ? "Bạn thắng!" : "AI thắng!";
      return `Chiến thắng: ${winner}`;
    }
    if (mode === "pve") {
      if (currentPlayer === humanPlayer) return `Lượt của bạn (${humanPlayer})`;
      return isAiThinking ? "AI đang suy nghĩ..." : `Lượt của AI (${aiPlayer})`;
    }
    return `Lượt của: ${currentPlayer}`;
  })();

  const isInteractionLocked =
    Boolean(winner) || isAiThinking || (mode === "pve" && currentPlayer === aiPlayer);

  return (
    <Card className="rounded-xl border bg-card p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="text-lg font-semibold tracking-tight">Cờ caro</div>
          <div className="text-sm text-muted-foreground">
            Bàn {boardSize}×{boardSize}. Nối {WIN_LENGTH} quân liên tiếp để thắng.{" "}
            {mode === "pve"
              ? `PvE: Đấu với AI (${aiPlayer}) vs Bạn (${humanPlayer}). Thắng AI sẽ ghi vào bảng xếp hạng.`
              : "PvP: 2 người chơi."}
          </div>
          <div className="mt-2 inline-flex items-center gap-2 rounded-lg border bg-muted/30 px-3 py-2 text-sm">
            <span className="text-muted-foreground">Trạng thái:</span>
            <span className="font-medium text-foreground">{statusLabel}</span>
            {isAiThinking ? <span className="text-muted-foreground animate-pulse">…</span> : null}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2">
            <Input
              value={boardSizeInput}
              onChange={(e) => setBoardSizeInput(e.target.value)}
              inputMode="numeric"
              className="w-20"
              disabled={isAiThinking}
              aria-label="Kích thước bàn cờ (N×N)"
            />
            <Button variant="outline" size="sm" onClick={applyBoardSize} disabled={isAiThinking}>
              Áp dụng
            </Button>
          </div>
          <Button
            variant={mode === "pvp" ? "default" : "outline"}
            size="sm"
            onClick={() => {
              setMode("pvp");
              reset();
            }}
            disabled={isAiThinking}
          >
            PvP
          </Button>
          <Button
            variant={mode === "pve" ? "default" : "outline"}
            size="sm"
            onClick={() => {
              setMode("pve");
              reset();
            }}
            disabled={isAiThinking}
          >
            PvE (AI)
          </Button>
          <Button variant="outline" size="sm" onClick={undo} disabled={moves.length === 0 || isAiThinking}>
            Hoàn tác
          </Button>
          <Button variant="outline" size="sm" onClick={reset} disabled={isAiThinking}>
            Chơi lại
          </Button>
        </div>
      </div>

      {!isAuthenticated && (
        <div className="mt-4 rounded-lg border border-dashed bg-muted/20 p-4 text-sm text-muted-foreground">
          Bạn đang chơi với tư cách khách. Kết quả sẽ không được lưu lại.{" "}
          <button
            type="button"
            className="font-semibold text-primary underline-offset-2 hover:underline"
            onClick={() => onRequireAuth("Vui lòng đăng nhập để lưu kết quả chơi")}
          >
            Đăng nhập
          </button>{" "}
          để lưu lịch sử.
        </div>
      )}

      <div className={cn("mt-5 grid gap-4", mode === "pve" && "lg:grid-cols-[1fr_280px]")}>
        <div ref={boardWrapRef} className="overflow-auto rounded-xl border bg-background p-3">
          <div
            className="grid gap-px bg-border p-px rounded-lg"
            style={
              {
                gridTemplateColumns: `repeat(${boardSize}, var(--caro-cell))`,
                ["--caro-cell" as any]: `${cellPx}px`,
              } as any
            }
          >
            {board.map((row, r) =>
              row.map((cell, c) => {
                const isLast = lastMove?.r === r && lastMove?.c === c;
                const isWin = winLookup.has(`${r}:${c}`);

                return (
                  <button
                    key={`${r}-${c}`}
                    type="button"
                    onClick={() => place(r, c)}
                    disabled={isInteractionLocked || Boolean(board[r][c])}
                    className={cn(
                      "relative flex aspect-square w-[var(--caro-cell)] items-center justify-center bg-background text-sm font-semibold transition-colors",
                      "hover:bg-muted/40 disabled:cursor-not-allowed disabled:hover:bg-background",
                      isLast && "ring-2 ring-primary ring-inset",
                      isWin && "ring-2 ring-highlight ring-inset",
                      winner && !isWin && "opacity-90",
                    )}
                    aria-label={`Ô ${r + 1}, ${c + 1}`}
                  >
                    {cell ? (
                      <span
                        className={cn(
                          "select-none animate-in fade-in-0 zoom-in-75 duration-150",
                          cell === "X" ? "text-primary" : "text-highlight",
                        )}
                      >
                        {cell}
                      </span>
                    ) : null}
                  </button>
                );
              }),
            )}
          </div>
        </div>

        {mode === "pve" && (
          <div className="space-y-4">
            <div className="rounded-xl border bg-card p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-semibold">Bảng xếp hạng PvE</div>
                  <div className="text-xs text-muted-foreground">
                    Top 1 mỗi vòng 3 ngày sẽ nhận voucher 15% trong Ví voucher.
                  </div>
                </div>
                <span className="rounded-full border bg-muted/20 px-2 py-1 text-xs text-muted-foreground">
                  {totalPlayers} người chơi
                </span>
              </div>

              <div className="mt-3 space-y-3">
                {leaderboard[0] && (
                  <div className="rounded-lg border bg-muted/10 p-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-semibold">#1 {leaderboard[0].name}</span>
                      <span className="font-semibold text-foreground">{leaderboard[0].score} thắng</span>
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      Voucher 15% sẽ được ghi vào Ví voucher khi kết thúc vòng tính điểm 3 ngày.
                    </div>
                    {countdown && (
                      <div className="mt-1 text-xs text-muted-foreground">
                        Còn {countdown} để chốt thưởng.
                      </div>
                    )}
                  </div>
                )}

                <div className="max-h-44 overflow-auto rounded-lg border bg-muted/10">
                  <table className="w-full text-xs">
                    <thead className="sticky top-0 bg-muted/30 text-muted-foreground">
                      <tr>
                        <th className="px-3 py-2 text-left">Hạng</th>
                        <th className="px-3 py-2 text-left">Người chơi</th>
                        <th className="px-3 py-2 text-right">Số thắng</th>
                      </tr>
                    </thead>
                    <tbody>
                      {leaderboard.map((entry, idx) => (
                        <tr key={`${entry.id}-${entry.score}`} className="border-t">
                          <td className="px-3 py-2 text-left">#{idx + 1}</td>
                          <td className="px-3 py-2 text-left">{entry.name}</td>
                          <td className="px-3 py-2 text-right font-semibold text-foreground">{entry.score}</td>
                        </tr>
                      ))}
                      {leaderboard.length === 0 && (
                        <tr>
                          <td className="px-3 py-3 text-center text-muted-foreground" colSpan={3}>
                            Chưa có dữ liệu. Hãy thắng AI để ghi tên nhé!
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

type OnlineSeat = {
  player: Player;
  token: string;
};

function readStoredName(): string {
  const stored = localStorage.getItem("auth");
  if (!stored) return "";
  try {
    const parsed = JSON.parse(stored) as { user?: { name?: string } };
    return (parsed?.user?.name || "").trim();
  } catch {
    return "";
  }
}

function roomStorageKey(roomId: string): string {
  return `caro_online_room:${roomId}`;
}

function loadSeat(roomId: string): OnlineSeat | null {
  const raw = localStorage.getItem(roomStorageKey(roomId));
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as OnlineSeat;
    if ((parsed.player === "X" || parsed.player === "O") && typeof parsed.token === "string" && parsed.token) {
      return parsed;
    }
    return null;
  } catch {
    return null;
  }
}

function saveSeat(roomId: string, seat: OnlineSeat) {
  localStorage.setItem(roomStorageKey(roomId), JSON.stringify(seat));
}

function buildBoardFromMoves(moves: OnlineCaroMove[], size: number): Cell[][] {
  const next: Cell[][] = Array.from({ length: size }, () => Array.from({ length: size }, () => null));
  for (const m of moves) {
    if (!Number.isFinite(m.r) || !Number.isFinite(m.c)) continue;
    if (m.p !== "X" && m.p !== "O") continue;
    if (m.r < 0 || m.r >= size || m.c < 0 || m.c >= size) continue;
    next[m.r][m.c] = m.p;
  }
  return next;
}

function CaroOnlineGame({
  initialRoomId,
  isAuthenticated,
  onRequireAuth,
}: {
  initialRoomId?: string | null;
  isAuthenticated: boolean;
  onRequireAuth: (message: string) => void;
}) {
  const [playerName, setPlayerName] = useState(() => readStoredName());
  const [boardSizeInput, setBoardSizeInput] = useState(String(DEFAULT_BOARD_SIZE));
  const [roomInput, setRoomInput] = useState(() => (initialRoomId || "").trim());
  const [roomId, setRoomId] = useState<string>(() => (initialRoomId || "").trim());
  const boardWrapRef = useRef<HTMLDivElement | null>(null);
  const [cellPx, setCellPx] = useState(36);

  const [game, setGame] = useState<OnlineCaroGame | null>(null);
  const [you, setYou] = useState<OnlineCaroYou>(() => {
    const rid = (initialRoomId || "").trim();
    if (!rid) return { player: null, token: null };
    const seat = loadSeat(rid);
    return seat ? { player: seat.player, token: seat.token } : { player: null, token: null };
  });

  const [busy, setBusy] = useState(false);
  const [moveBusy, setMoveBusy] = useState(false);
  const onlineLocked = !isAuthenticated;

  useEffect(() => {
    const rid = (initialRoomId || "").trim();
    if (!rid) return;
    setRoomInput(rid);
    setRoomId(rid);
    const seat = loadSeat(rid);
    setYou(seat ? { player: seat.player, token: seat.token } : { player: null, token: null });
  }, [initialRoomId]);

  useEffect(() => {
    if (!roomId) {
      setGame(null);
      return;
    }

    let cancelled = false;
    let timer: number | null = null;

    const tick = async () => {
      try {
        const g = await getCaroGame(roomId);
        if (cancelled) return;
        setGame(g);
      } catch (err: any) {
        if (cancelled) return;
        const msg = err?.message || "Không tải được phòng chơi";
        setGame(null);
        toast.error(msg);
      }
    };

    tick();
    timer = window.setInterval(tick, 900);

    return () => {
      cancelled = true;
      if (timer) window.clearInterval(timer);
    };
  }, [roomId]);

  const boardSize = game?.board_size || DEFAULT_BOARD_SIZE;
  const winLen = game?.win_length || WIN_LENGTH;
  const board = useMemo(() => buildBoardFromMoves(game?.moves || [], boardSize), [game?.moves, boardSize]);
  const lastMove = (game?.moves || [])[game?.moves.length - 1] ?? null;

  const winLookup = useMemo(() => {
    const set = new Set<string>();
    for (const p of game?.win_line || []) set.add(`${p.r}:${p.c}`);
    return set;
  }, [game?.win_line]);

  const statusLabel = (() => {
    if (!game) return "Chưa kết nối";
    if (game.winner === "draw") return "Hòa!";
    if (game.winner) return `Chiến thắng: ${game.winner}`;
    if (game.status === "waiting") return "Đang chờ người chơi thứ 2...";
    if (you.player && game.turn === you.player) return `Lượt của bạn (${you.player})`;
    return `Lượt của: ${game.turn}`;
  })();

  const shareUrl = useMemo(() => {
    if (!roomId) return "";
    return `${window.location.origin}/games?caro=${encodeURIComponent(roomId)}`;
  }, [roomId]);

  const canPlay = Boolean(game && you.player && you.token && !game.winner && game.status !== "finished");
  const isYourTurn = Boolean(canPlay && game && you.player && game.turn === you.player);

  useEffect(() => {
    const el = boardWrapRef.current;
    if (!el) return;

    const compute = () => {
      const style = window.getComputedStyle(el);
      const paddingLeft = Number.parseFloat(style.paddingLeft || "0") || 0;
      const paddingRight = Number.parseFloat(style.paddingRight || "0") || 0;
      const contentWidth = Math.max(0, el.clientWidth - paddingLeft - paddingRight);
      const gapPx = 1; // gap-px
      const innerPaddingPx = 2; // p-px (left + right)
      const available = Math.max(0, contentWidth - innerPaddingPx - (boardSize - 1) * gapPx);
      const raw = Math.floor(available / boardSize);
      const next = Math.max(18, Math.min(36, raw));
      setCellPx((prev) => (prev === next ? prev : next));
    };

    compute();
    const ro = new ResizeObserver(compute);
    ro.observe(el);
    return () => ro.disconnect();
  }, [boardSize]);

  const createRoom = async () => {
    if (onlineLocked) {
      onRequireAuth("Vui lòng đăng nhập để tạo phòng");
      return;
    }
    const parsed = Number.parseInt(boardSizeInput.trim(), 10);
    if (!Number.isFinite(parsed) || parsed < MIN_BOARD_SIZE || parsed > MAX_BOARD_SIZE) {
      toast.error(
        "Kích thước bàn cờ không hợp lệ",
        `Nhập N là số nguyên từ ${MIN_BOARD_SIZE} đến ${MAX_BOARD_SIZE}`,
      );
      return;
    }

    setBusy(true);
    try {
      const env = await createCaroRoom(playerName, parsed);
      setRoomId(env.game.id);
      setRoomInput(env.game.id);
      setGame(env.game);
      setYou(env.you);
      if (env.you.player && env.you.token) saveSeat(env.game.id, { player: env.you.player, token: env.you.token });
      toast.success("Tạo phòng thành công", "Gửi link cho bạn bè để vào chơi");
    } catch (err: any) {
      toast.error(err?.message || "Tạo phòng thất bại");
    } finally {
      setBusy(false);
    }
  };

  const joinRoom = async () => {
    if (onlineLocked) {
      onRequireAuth("Vui lòng đăng nhập để tham gia phòng");
      return;
    }
    const rid = roomInput.trim();
    if (!rid) return;
    setBusy(true);
    try {
      const env = await joinCaroRoom(rid, playerName);
      setRoomId(env.game.id);
      setGame(env.game);
      setYou(env.you);
      if (env.you.player && env.you.token) saveSeat(env.game.id, { player: env.you.player, token: env.you.token });
      if (env.you.player) {
        toast.success("Tham gia thành công", `Bạn đang chơi quân ${env.you.player}`);
      } else {
        toast.info("Phòng đã đủ 2 người", "Bạn đang ở chế độ xem");
      }
    } catch (err: any) {
      toast.error(err?.message || "Tham gia phòng thất bại");
    } finally {
      setBusy(false);
    }
  };

  const leaveRoom = () => {
    setRoomId("");
    setRoomInput("");
    setGame(null);
    setYou({ player: null, token: null });
  };

  const copyLink = async () => {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      toast.success("Đã copy link", "Gửi link này cho người chơi còn lại");
    } catch {
      toast.error("Không copy được", "Trình duyệt không cho phép clipboard");
    }
  };

  const placeOnline = async (r: number, c: number) => {
    if (onlineLocked) {
      onRequireAuth("Vui lòng đăng nhập để chơi online");
      return;
    }
    if (!game || !you.player || !you.token) return;
    if (moveBusy) return;
    if (game.winner) return;
    if (game.turn !== you.player) return;
    if (board[r]?.[c]) return;

    setMoveBusy(true);
    try {
      const updated = await makeCaroMove({
        gameId: game.id,
        token: you.token,
        r,
        c,
        expectedVersion: game.version,
      });
      setGame(updated);
    } catch (err: any) {
      toast.error(err?.message || "Nước đi thất bại");
      try {
        const fresh = await getCaroGame(game.id);
        setGame(fresh);
      } catch {
        // ignore
      }
    } finally {
      setMoveBusy(false);
    }
  };

  return (
    <Card className="rounded-xl border bg-card p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="text-lg font-semibold tracking-tight">Cờ caro (Online)</div>
          <div className="text-sm text-muted-foreground">
            Chơi 2 máy qua mạng. Nối {winLen} quân liên tiếp để thắng.
          </div>
          <div className="mt-2 inline-flex items-center gap-2 rounded-lg border bg-muted/30 px-3 py-2 text-sm">
            <span className="text-muted-foreground">Trạng thái:</span>
            <span className="font-medium text-foreground">{statusLabel}</span>
            {moveBusy ? <span className="text-muted-foreground animate-pulse">…</span> : null}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" onClick={copyLink} disabled={!roomId}>
            Copy link
          </Button>
          <Button variant="outline" size="sm" onClick={leaveRoom} disabled={!roomId}>
            Rời phòng
          </Button>
        </div>
      </div>

      {onlineLocked && (
        <div className="mt-4 rounded-lg border border-dashed bg-muted/20 p-4 text-sm text-muted-foreground">
          Đăng nhập để tạo hoặc tham gia phòng online và lưu lịch sử trận đấu.{" "}
          <button
            type="button"
            className="font-semibold text-primary underline-offset-2 hover:underline"
            onClick={() => onRequireAuth("Vui lòng đăng nhập để chơi online")}
          >
            Đăng nhập ngay
          </button>
          .
        </div>
      )}

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="caro-player-name">Tên hiển thị</Label>
          <Input
            id="caro-player-name"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            placeholder="Ví dụ: Nhật Huy"
            disabled={busy || Boolean(you.player) || onlineLocked}
          />

          <Label htmlFor="caro-board-size">Kích thước bàn cờ (N×N)</Label>
          <Input
            id="caro-board-size"
            value={boardSizeInput}
            onChange={(e) => setBoardSizeInput(e.target.value)}
            placeholder="15"
            inputMode="numeric"
            disabled={busy || Boolean(roomId) || onlineLocked}
          />
          <div className="flex flex-wrap gap-2">
            <Button onClick={createRoom} disabled={busy || Boolean(roomId) || onlineLocked}>
              Tạo phòng
            </Button>
            <div className="text-sm text-muted-foreground self-center">
              {roomId ? (
                <span>
                  Room: <span className="font-mono text-foreground">{roomId}</span>
                </span>
              ) : (
                "Tạo phòng hoặc nhập room để tham gia."
              )}
            </div>
          </div>
          {roomId ? (
            <div className="text-sm text-muted-foreground break-all">
              Link: <span className="font-mono text-foreground">{shareUrl}</span>
            </div>
          ) : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="caro-room">Tham gia phòng</Label>
          <div className="flex gap-2">
            <Input
              id="caro-room"
              value={roomInput}
              onChange={(e) => setRoomInput(e.target.value)}
              placeholder="Dán room id ở đây"
              disabled={busy || Boolean(roomId) || onlineLocked}
            />
            <Button
              variant="outline"
              onClick={joinRoom}
              disabled={busy || Boolean(you.player) || !roomInput.trim() || onlineLocked}
            >
              Tham gia
            </Button>
          </div>
          <div className="text-sm text-muted-foreground">
            {you.player ? (
              <span>
                Bạn đang chơi quân <span className="font-semibold text-foreground">{you.player}</span>
              </span>
            ) : roomId ? (
              "Chưa vào ghế. Nhấn “Tham gia” để vào chơi (nếu phòng còn chỗ)."
            ) : (
              " "
            )}
          </div>
        </div>
      </div>

      <div ref={boardWrapRef} className="mt-5 overflow-auto rounded-xl border bg-background p-3">
        <div
          className="grid gap-px bg-border p-px rounded-lg"
          style={
            {
              gridTemplateColumns: `repeat(${boardSize}, var(--caro-cell))`,
              ["--caro-cell" as any]: `${cellPx}px`,
            } as any
          }
        >
          {board.map((row, r) =>
            row.map((cell, c) => {
              const isLast = lastMove?.r === r && lastMove?.c === c;
              const isWin = winLookup.has(`${r}:${c}`);
              const isDisabled = Boolean(board[r][c]) || !isYourTurn || moveBusy;

              return (
                <button
                  key={`${r}-${c}`}
                  type="button"
                  onClick={() => placeOnline(r, c)}
                  disabled={isDisabled}
                  className={cn(
                    "relative flex aspect-square w-[var(--caro-cell)] items-center justify-center bg-background text-sm font-semibold transition-colors",
                    "hover:bg-muted/40 disabled:cursor-not-allowed disabled:hover:bg-background",
                    isLast && "ring-2 ring-primary ring-inset",
                    isWin && "ring-2 ring-highlight ring-inset",
                    game?.winner && !isWin && "opacity-90",
                  )}
                  aria-label={`Ô ${r + 1}, ${c + 1}`}
                >
                  {cell ? (
                    <span
                      className={cn(
                        "select-none animate-in fade-in-0 zoom-in-75 duration-150",
                        cell === "X" ? "text-primary" : "text-highlight",
                      )}
                    >
                      {cell}
                    </span>
                  ) : null}
                </button>
              );
            }),
          )}
        </div>
      </div>
    </Card>
  );
}

export function CaroGame() {
  const [variant, setVariant] = useState<"local" | "online">("local");
  const [searchParams] = useSearchParams();
  const roomFromUrl = (searchParams.get("caro") || "").trim();
  const [isAuthenticated, setIsAuthenticated] = useState(() =>
    Boolean((getAuthHeaders() as Record<string, string>).Authorization),
  );

  useEffect(() => {
    if (roomFromUrl) setVariant("online");
  }, [roomFromUrl]);

  useEffect(() => {
    const updateAuth = () =>
      setIsAuthenticated(Boolean((getAuthHeaders() as Record<string, string>).Authorization));
    window.addEventListener("auth:updated", updateAuth as EventListener);
    return () => window.removeEventListener("auth:updated", updateAuth as EventListener);
  }, []);

  const requireAuth = (message: string) => {
    if (!isAuthenticated) {
      toast.error(message);
      window.dispatchEvent(new Event("auth:open"));
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Button
          size="sm"
          variant={variant === "local" ? "default" : "outline"}
          onClick={() => setVariant("local")}
        >
          Chơi trên máy
        </Button>
        <Button
          size="sm"
          variant={variant === "online" ? "default" : "outline"}
          onClick={() => setVariant("online")}
        >
          Chơi 2 máy (Online)
        </Button>
      </div>

      {variant === "local" ? (
        <CaroLocalGame isAuthenticated={isAuthenticated} onRequireAuth={requireAuth} />
      ) : (
        <CaroOnlineGame
          initialRoomId={roomFromUrl || null}
          isAuthenticated={isAuthenticated}
          onRequireAuth={requireAuth}
        />
      )}
    </div>
  );
}
