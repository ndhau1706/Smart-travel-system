import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { cn } from "../../components/ui/utils";
import { ArrowDown, ArrowLeft, ArrowRight, Pause, Play, RotateCw, Space } from "lucide-react";
import { getDisplayName, setDisplayName } from "../../services/identity";
import { fetchGameLeaderboard, submitGameScore, type GameLeaderboardEntry, type GameRoundInfo } from "../../services/games";
import { getAuthHeaders } from "../../services/auth";
import { toast } from "sonner";

type Status = "ready" | "running" | "paused" | "over";

const BEST_KEY = "games:tetris_best";

const COLS = 10;
const ROWS = 20;

type Cell = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7;
type Board = Cell[][];

type PieceKey = "I" | "O" | "T" | "S" | "Z" | "J" | "L";

type Piece = {
  key: PieceKey;
  matrix: number[][];
  x: number;
  y: number;
};

const SHAPES: Record<PieceKey, number[][]> = {
  I: [
    [0, 0, 0, 0],
    [1, 1, 1, 1],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ],
  O: [
    [1, 1],
    [1, 1],
  ],
  T: [
    [0, 1, 0],
    [1, 1, 1],
    [0, 0, 0],
  ],
  S: [
    [0, 1, 1],
    [1, 1, 0],
    [0, 0, 0],
  ],
  Z: [
    [1, 1, 0],
    [0, 1, 1],
    [0, 0, 0],
  ],
  J: [
    [1, 0, 0],
    [1, 1, 1],
    [0, 0, 0],
  ],
  L: [
    [0, 0, 1],
    [1, 1, 1],
    [0, 0, 0],
  ],
};

const COLORS: Record<Cell, { base: string; light: string; dark: string }> = {
  0: { base: "rgba(0,0,0,0)", light: "", dark: "" },
  1: { base: "#4f46e5", light: "#a5b4fc", dark: "#312e81" }, // indigo
  2: { base: "#f97316", light: "#fed7aa", dark: "#9a3412" }, // orange
  3: { base: "#22c55e", light: "#bbf7d0", dark: "#166534" }, // green
  4: { base: "#06b6d4", light: "#a5f3fc", dark: "#155e75" }, // cyan
  5: { base: "#e11d48", light: "#fecdd3", dark: "#881337" }, // rose
  6: { base: "#a855f7", light: "#e9d5ff", dark: "#581c87" }, // purple
  7: { base: "#facc15", light: "#fef9c3", dark: "#854d0e" }, // yellow
};

const PIECE_COLOR: Record<PieceKey, Cell> = {
  I: 4,
  O: 2,
  T: 1,
  S: 3,
  Z: 5,
  J: 6,
  L: 7,
};

function createBoard(): Board {
  return Array.from({ length: ROWS }, () => Array.from({ length: COLS }, () => 0 as Cell));
}

function rotateMatrix(m: number[][]): number[][] {
  const rows = m.length;
  const cols = m[0]?.length ?? 0;
  const res = Array.from({ length: cols }, () => Array.from({ length: rows }, () => 0));
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) res[c][rows - 1 - r] = m[r][c] || 0;
  }
  return res;
}

function randomPiece(): Piece {
  const keys: PieceKey[] = ["I", "O", "T", "S", "Z", "J", "L"];
  const key = keys[Math.floor(Math.random() * keys.length)]!;
  const matrix = SHAPES[key].map((row) => row.slice());
  const x = Math.floor((COLS - matrix[0].length) / 2);
  return { key, matrix, x, y: 0 };
}

function collides(board: Board, piece: Piece): boolean {
  for (let r = 0; r < piece.matrix.length; r++) {
    for (let c = 0; c < piece.matrix[r].length; c++) {
      if (!piece.matrix[r][c]) continue;
      const x = piece.x + c;
      const y = piece.y + r;
      if (x < 0 || x >= COLS || y >= ROWS) return true;
      if (y >= 0 && board[y][x] !== 0) return true;
    }
  }
  return false;
}

function merge(board: Board, piece: Piece): Board {
  const next = board.map((row) => row.slice()) as Board;
  const color = PIECE_COLOR[piece.key];
  for (let r = 0; r < piece.matrix.length; r++) {
    for (let c = 0; c < piece.matrix[r].length; c++) {
      if (!piece.matrix[r][c]) continue;
      const x = piece.x + c;
      const y = piece.y + r;
      if (y >= 0 && y < ROWS && x >= 0 && x < COLS) next[y][x] = color;
    }
  }
  return next;
}

function clearLines(board: Board): { board: Board; cleared: number; clearedRows: number[] } {
  const kept: Board = [];
  const clearedRows: number[] = [];
  for (let r = 0; r < ROWS; r++) {
    const full = board[r].every((c) => c !== 0);
    if (full) clearedRows.push(r);
    else kept.push(board[r]);
  }
  const cleared = ROWS - kept.length;
  while (kept.length < ROWS) kept.unshift(Array.from({ length: COLS }, () => 0 as Cell));
  return { board: kept, cleared, clearedRows };
}

type Runtime = {
  status: Status;
  board: Board;
  piece: Piece;
  next: Piece;
  score: number;
  lines: number;
  level: number;
  dropAccum: number;
  lastTime: number;
  best: number;
  flashRows: number[] | null;
  flashUntil: number;
};

function computeDropMs(level: number): number {
  const base = 800;
  const min = 120;
  return Math.max(min, base - (level - 1) * 65);
}

export function TetrisGame() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const rafRef = useRef<number | null>(null);
  const rtRef = useRef<Runtime | null>(null);

  const [status, setStatus] = useState<Status>("ready");
  const [score, setScore] = useState(0);
  const [lines, setLines] = useState(0);
  const [level, setLevel] = useState(1);
  const [best, setBest] = useState(() => {
    try {
      return Number(localStorage.getItem(BEST_KEY) || "0") || 0;
    } catch {
      return 0;
    }
  });
  const [playerName, setPlayerName] = useState(() => getDisplayName());
  const [leaderboard, setLeaderboard] = useState<GameLeaderboardEntry[]>([]);
  const [totalPlayers, setTotalPlayers] = useState(0);
  const [roundInfo, setRoundInfo] = useState<GameRoundInfo | null>(null);
  const [countdown, setCountdown] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(() =>
    Boolean((getAuthHeaders() as Record<string, string>).Authorization),
  );

  useEffect(() => {
    setDisplayName(playerName);
  }, [playerName]);

  useEffect(() => {
    const updateAuth = () => {
      setIsAuthenticated(Boolean((getAuthHeaders() as Record<string, string>).Authorization));
      setPlayerName(getDisplayName());
    };
    window.addEventListener("auth:updated", updateAuth as EventListener);
    return () => window.removeEventListener("auth:updated", updateAuth as EventListener);
  }, []);

  useEffect(() => {
    let active = true;
    fetchGameLeaderboard("tetris")
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
  }, []);

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

  const syncUi = (rt: Runtime) => {
    setStatus(rt.status);
    setScore(rt.score);
    setLines(rt.lines);
    setLevel(rt.level);
    setBest(rt.best);
  };

  const newRuntime = (w: number, h: number, prevBest: number): Runtime => {
    return {
      status: "ready",
      board: createBoard(),
      piece: randomPiece(),
      next: randomPiece(),
      score: 0,
      lines: 0,
      level: 1,
      dropAccum: 0,
      lastTime: performance.now(),
      best: prevBest,
      flashRows: null,
      flashUntil: 0,
    };
  };

  const reset = () => {
    const rt = rtRef.current;
    if (!rt) return;
    const next = newRuntime(0, 0, rt.best);
    // size will be re-applied by resize observer; keep runtime but preserve best
    rtRef.current = { ...next, lastTime: performance.now(), best: rt.best };
    syncUi(rtRef.current);
  };

  const start = () => {
    const rt = rtRef.current;
    if (!rt) return;
    if (rt.status === "running") return;
    if (rt.status === "over") reset();
    const cur = rtRef.current!;
    cur.status = "running";
    cur.lastTime = performance.now();
    cur.dropAccum = 0;
    syncUi(cur);
  };

  const togglePause = () => {
    const rt = rtRef.current;
    if (!rt) return;
    if (rt.status === "running") rt.status = "paused";
    else if (rt.status === "paused") rt.status = "running";
    rt.lastTime = performance.now();
    syncUi(rt);
  };

  const withRuntime = (fn: (rt: Runtime) => void) => {
    const rt = rtRef.current;
    if (!rt) return;
    fn(rt);
    syncUi(rt);
  };

  const move = (dx: number, dy: number) => {
    const rt = rtRef.current;
    if (!rt || rt.status !== "running") return;
    const nextPiece = { ...rt.piece, x: rt.piece.x + dx, y: rt.piece.y + dy };
    if (!collides(rt.board, nextPiece)) rt.piece = nextPiece;
  };

  const hardDrop = () => {
    const rt = rtRef.current;
    if (!rt || rt.status !== "running") return;
    let p = { ...rt.piece };
    while (!collides(rt.board, { ...p, y: p.y + 1 })) {
      p = { ...p, y: p.y + 1 };
      rt.score += 2;
    }
    rt.piece = p;
    lockPiece(rt);
    syncUi(rt);
  };

  const rotate = () => {
    const rt = rtRef.current;
    if (!rt || rt.status !== "running") return;
    const rotated = rotateMatrix(rt.piece.matrix);
    const base = { ...rt.piece, matrix: rotated };
    const kicks = [0, -1, 1, -2, 2];
    for (const k of kicks) {
      const candidate = { ...base, x: base.x + k };
      if (!collides(rt.board, candidate)) {
        rt.piece = candidate;
        return;
      }
    }
  };

  const gameOver = (rt: Runtime) => {
    if (rt.status === "over") return;
    rt.status = "over";
    if (rt.score > rt.best) {
      rt.best = rt.score;
      try {
        localStorage.setItem(BEST_KEY, String(rt.best));
      } catch {
        // ignore
      }
    }
    if (!isAuthenticated) {
      toast.error("Đăng nhập để ghi nhận điểm số");
      window.dispatchEvent(new Event("auth:open"));
    } else {
      const safeName = playerName.trim() || "Khách";
      submitGameScore({ game: "tetris", playerName: safeName, score: rt.score })
        .then((data) => {
          setLeaderboard(data.leaderboard.entries);
          setTotalPlayers(data.leaderboard.totalPlayers);
          setRoundInfo(data.leaderboard.round);
        })
        .catch((err: any) => {
          const message = err?.message || "Không thể cập nhật bảng xếp hạng";
          toast.error(message);
          if (String(message).includes("401")) {
            window.dispatchEvent(new Event("auth:open"));
          }
        });
    }
    syncUi(rt);
  };

  const lockPiece = (rt: Runtime) => {
    rt.board = merge(rt.board, rt.piece);
    const { board: clearedBoard, cleared, clearedRows } = clearLines(rt.board);
    if (cleared > 0) {
      rt.flashRows = clearedRows;
      rt.flashUntil = performance.now() + 140;
      rt.lines += cleared;
      const add = [0, 100, 300, 500, 800][cleared] ?? 0;
      rt.score += add * rt.level;
      const nextLevel = Math.floor(rt.lines / 10) + 1;
      rt.level = Math.max(1, nextLevel);
      rt.board = clearedBoard;
    }

    rt.piece = rt.next;
    rt.next = randomPiece();
    rt.piece.x = Math.floor((COLS - rt.piece.matrix[0].length) / 2);
    rt.piece.y = 0;

    if (collides(rt.board, rt.piece)) gameOver(rt);
  };

  const drawBlock = (ctx: CanvasRenderingContext2D, x: number, y: number, size: number, cell: Cell, alpha = 1) => {
    if (cell === 0) return;
    const c = COLORS[cell];
    ctx.save();
    ctx.globalAlpha = alpha;
    const grad = ctx.createLinearGradient(x, y, x + size, y + size);
    grad.addColorStop(0, c.light);
    grad.addColorStop(0.55, c.base);
    grad.addColorStop(1, c.dark);
    ctx.fillStyle = grad;
    ctx.fillRect(x, y, size, size);
    ctx.strokeStyle = "rgba(255,255,255,0.15)";
    ctx.lineWidth = 1;
    ctx.strokeRect(x + 0.5, y + 0.5, size - 1, size - 1);
    ctx.restore();
  };

  const draw = (ctx: CanvasRenderingContext2D, rt: Runtime, w: number, h: number) => {
    ctx.clearRect(0, 0, w, h);

    // background
    const bg = ctx.createLinearGradient(0, 0, 0, h);
    bg.addColorStop(0, "rgba(2,6,23,0.06)");
    bg.addColorStop(1, "rgba(79,70,229,0.10)");
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, w, h);

    const padding = 14;
    const playW = w - padding * 2;
    const playH = h - padding * 2;
    const cellSize = Math.floor(Math.min(playW / COLS, playH / ROWS));
    const boardW = cellSize * COLS;
    const boardH = cellSize * ROWS;
    const offsetX = Math.floor((w - boardW) / 2);
    const offsetY = Math.floor((h - boardH) / 2);

    // board panel
    ctx.fillStyle = "rgba(248,250,252,0.55)";
    ctx.strokeStyle = "rgba(15,23,42,0.12)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(offsetX - 10, offsetY - 10, boardW + 20, boardH + 20, 14);
    ctx.fill();
    ctx.stroke();

    // grid
    ctx.strokeStyle = "rgba(15,23,42,0.06)";
    ctx.lineWidth = 1;
    for (let c = 0; c <= COLS; c++) {
      const x = offsetX + c * cellSize;
      ctx.beginPath();
      ctx.moveTo(x, offsetY);
      ctx.lineTo(x, offsetY + boardH);
      ctx.stroke();
    }
    for (let r = 0; r <= ROWS; r++) {
      const y = offsetY + r * cellSize;
      ctx.beginPath();
      ctx.moveTo(offsetX, y);
      ctx.lineTo(offsetX + boardW, y);
      ctx.stroke();
    }

    // flash cleared rows
    const now = performance.now();
    const flashing = rt.flashRows && now < rt.flashUntil;

    // draw locked board
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const cell = rt.board[r][c];
        if (cell === 0) continue;
        const x = offsetX + c * cellSize;
        const y = offsetY + r * cellSize;
        drawBlock(ctx, x, y, cellSize, cell, 1);
      }
    }

    if (flashing && rt.flashRows) {
      ctx.save();
      ctx.globalAlpha = 0.5;
      ctx.fillStyle = "rgba(249,115,22,0.65)";
      for (const r of rt.flashRows) {
        const y = offsetY + r * cellSize;
        ctx.fillRect(offsetX, y, boardW, cellSize);
      }
      ctx.restore();
    } else if (rt.flashRows && now >= rt.flashUntil) {
      rt.flashRows = null;
    }

    // ghost piece
    if (rt.status === "running") {
      let ghost = { ...rt.piece };
      while (!collides(rt.board, { ...ghost, y: ghost.y + 1 })) ghost = { ...ghost, y: ghost.y + 1 };
      const ghostColor = PIECE_COLOR[rt.piece.key];
      for (let r = 0; r < ghost.matrix.length; r++) {
        for (let c = 0; c < ghost.matrix[r].length; c++) {
          if (!ghost.matrix[r][c]) continue;
          const x = offsetX + (ghost.x + c) * cellSize;
          const y = offsetY + (ghost.y + r) * cellSize;
          drawBlock(ctx, x, y, cellSize, ghostColor, 0.2);
        }
      }
    }

    // active piece
    const activeColor = PIECE_COLOR[rt.piece.key];
    for (let r = 0; r < rt.piece.matrix.length; r++) {
      for (let c = 0; c < rt.piece.matrix[r].length; c++) {
        if (!rt.piece.matrix[r][c]) continue;
        const x = offsetX + (rt.piece.x + c) * cellSize;
        const y = offsetY + (rt.piece.y + r) * cellSize;
        if (y < offsetY) continue;
        drawBlock(ctx, x, y, cellSize, activeColor, 1);
      }
    }
  };

  const step = (now: number) => {
    const rt = rtRef.current;
    const canvas = canvasRef.current;
    if (!rt || !canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dt = Math.min(0.05, (now - rt.lastTime) / 1000);
    rt.lastTime = now;

    const w = rtRef.current ? canvas.clientWidth : 0;
    const h = rtRef.current ? canvas.clientHeight : 0;

    if (rt.status === "running") {
      rt.dropAccum += dt * 1000;
      const dropMs = computeDropMs(rt.level);
      if (rt.dropAccum >= dropMs) {
        rt.dropAccum = 0;
        const moved = { ...rt.piece, y: rt.piece.y + 1 };
        if (!collides(rt.board, moved)) rt.piece = moved;
        else lockPiece(rt);

        if (rt.score > rt.best) {
          rt.best = rt.score;
          try {
            localStorage.setItem(BEST_KEY, String(rt.best));
          } catch {
            // ignore
          }
        }
      }
    }

    draw(ctx, rt, canvas.width / (window.devicePixelRatio || 1), canvas.height / (window.devicePixelRatio || 1));
    rafRef.current = requestAnimationFrame(step);
  };

  const instructions = useMemo(
    () => [
      { k: "←/→", v: "Di chuyển" },
      { k: "↓", v: "Rơi nhanh" },
      { k: "↑", v: "Xoay" },
      { k: "Space", v: "Rơi thẳng" },
      { k: "P", v: "Tạm dừng" },
    ],
    [],
  );

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      const rect = container.getBoundingClientRect();
      const w = Math.max(280, Math.floor(rect.width));
      const h = Math.max(420, Math.floor(rect.height));
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const prevBest = rtRef.current?.best ?? best;
      if (!rtRef.current) rtRef.current = newRuntime(w, h, prevBest);
      else rtRef.current.best = prevBest;
      syncUi(rtRef.current);
    };

    const ro = new ResizeObserver(resize);
    ro.observe(container);
    resize();

    rafRef.current = requestAnimationFrame(step);

    const onKeyDown = (e: KeyboardEvent) => {
      const rt = rtRef.current;
      if (!rt) return;
      const isGameKey = ["ArrowLeft", "ArrowRight", "ArrowDown", "ArrowUp", "Space", "KeyP", "Enter"].includes(e.code);
      if (isGameKey) e.preventDefault();

      if (e.code === "Enter") start();
      if (e.code === "KeyP") togglePause();
      if (rt.status !== "running") return;

      if (e.code === "ArrowLeft") move(-1, 0);
      if (e.code === "ArrowRight") move(1, 0);
      if (e.code === "ArrowDown") {
        move(0, 1);
        rt.score += 1;
        setScore(rt.score);
      }
      if (e.code === "ArrowUp") rotate();
      if (e.code === "Space") hardDrop();
    };

    window.addEventListener("keydown", onKeyDown, { passive: false });

    return () => {
      ro.disconnect();
      window.removeEventListener("keydown", onKeyDown);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Card className="rounded-xl border bg-card p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="text-lg font-semibold tracking-tight">Tetris</div>
          <div className="text-sm text-muted-foreground">
            Xếp khối, ăn dòng để ghi điểm. Có ghost piece và hiệu ứng xóa dòng.
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
            <span className="rounded-lg border bg-muted/30 px-3 py-2">Điểm: <span className="font-semibold text-foreground">{score}</span></span>
            <span className="rounded-lg border bg-muted/30 px-3 py-2">Dòng: <span className="font-semibold text-foreground">{lines}</span></span>
            <span className="rounded-lg border bg-muted/30 px-3 py-2">Level: <span className="font-semibold text-foreground">{level}</span></span>
            <span className="rounded-lg border bg-muted/30 px-3 py-2">Kỷ lục: <span className="font-semibold text-foreground">{best}</span></span>
            <span
              className={cn(
                "rounded-lg border px-3 py-2",
                status === "running"
                  ? "bg-primary/10 text-primary border-primary/20"
                  : status === "paused"
                    ? "bg-highlight/10 text-highlight border-highlight/20"
                    : "bg-muted/30 text-muted-foreground",
              )}
            >
              {status === "ready" ? "Sẵn sàng" : status === "running" ? "Đang chơi" : status === "paused" ? "Tạm dừng" : "Hết game"}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-end gap-2">
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Tên hiển thị</label>
            <Input
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              className="h-9 w-40"
              placeholder="Ví dụ: An Nhiên"
            />
          </div>
          {status === "running" ? (
            <Button variant="outline" size="sm" onClick={togglePause} className="h-9">
              <Pause className="h-4 w-4" />
              Pause
            </Button>
          ) : (
            <Button variant="outline" size="sm" onClick={start} className="h-9">
              <Play className="h-4 w-4" />
              Start
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={reset} className="h-9">
            Reset
          </Button>
        </div>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="rounded-xl border bg-background p-3">
          <div
            ref={containerRef}
            className="relative mx-auto w-full max-w-[420px] aspect-[10/16] overflow-hidden rounded-lg"
          >
            <canvas ref={canvasRef} className="block" />

            {status !== "running" && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="rounded-xl border bg-background/80 px-4 py-3 text-center shadow-sm backdrop-blur">
                  <div className="font-semibold">
                    {status === "ready" ? "Nhấn Start hoặc Enter" : status === "paused" ? "Đã tạm dừng" : "Hết game"}
                  </div>
                  <div className="mt-1 text-sm text-muted-foreground">
                    {status === "over" ? "Bấm Start để chơi lại" : "Dùng phím hoặc nút điều khiển bên dưới"}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Touch controls */}
          <div className="mt-4 grid grid-cols-3 gap-2">
            <Button
              variant="outline"
              className="rounded-lg"
              onPointerDown={(e) => {
                e.preventDefault();
                start();
                move(-1, 0);
              }}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              className="rounded-lg"
              onPointerDown={(e) => {
                e.preventDefault();
                start();
                rotate();
              }}
            >
              <RotateCw className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              className="rounded-lg"
              onPointerDown={(e) => {
                e.preventDefault();
                start();
                move(1, 0);
              }}
            >
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              className="rounded-lg col-span-2"
              onPointerDown={(e) => {
                e.preventDefault();
                start();
                move(0, 1);
              }}
            >
              <ArrowDown className="h-4 w-4" />
              Rơi nhanh
            </Button>
            <Button
              variant="outline"
              className="rounded-lg"
              onPointerDown={(e) => {
                e.preventDefault();
                start();
                hardDrop();
              }}
            >
              <Space className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border bg-muted/20 p-4">
            <div className="text-sm font-medium">Phím tắt</div>
            <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
              {instructions.map((it) => (
                <li key={it.k} className="flex items-center justify-between gap-2">
                  <span className="font-medium text-foreground">{it.k}</span>
                  <span>{it.v}</span>
                </li>
              ))}
            </ul>
            <div className="mt-4 text-xs text-muted-foreground">
              Tip: Ghost piece giúp bạn căn chuẩn vị trí rơi.
            </div>
          </div>

          <div className="rounded-xl border bg-card p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold">Bảng xếp hạng</div>
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
                    <span className="font-semibold text-foreground">{leaderboard[0].score}</span>
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
                      <th className="px-3 py-2 text-right">Điểm</th>
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
                          Chưa có dữ liệu. Hãy chơi để ghi tên nhé!
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
