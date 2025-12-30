import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { cn } from "../../components/ui/utils";
import { getDisplayName, setDisplayName } from "../../services/identity";
import { fetchGameLeaderboard, submitGameScore, type GameLeaderboardEntry, type GameRoundInfo } from "../../services/games";
import { getAuthHeaders } from "../../services/auth";
import { toast } from "sonner";

type Status = "ready" | "running" | "over";

type Pipe = {
  x: number;
  gapY: number;
  passed: boolean;
};

type GameRuntime = {
  status: Status;
  width: number;
  height: number;
  lastTime: number;
  gravity: number;
  jumpVel: number;
  bird: { x: number; y: number; vy: number; radius: number; tilt: number };
  pipes: Pipe[];
  pipeWidth: number;
  gapSize: number;
  pipeSpacing: number;
  speed: number;
  groundHeight: number;
  score: number;
  best: number;
};

const BEST_KEY = "games:flappy_best";

function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n));
}

function rand(min: number, max: number): number {
  return min + Math.random() * (max - min);
}

export function FlappyBirdGame() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const rafRef = useRef<number | null>(null);
  const runtimeRef = useRef<GameRuntime | null>(null);
  const [status, setStatus] = useState<Status>("ready");
  const [score, setScore] = useState(0);
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
    fetchGameLeaderboard("flappy")
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

  const hint = useMemo(
    () => (status === "ready" ? "Nhấn hoặc chạm để bắt đầu" : status === "over" ? "Hết game" : "Đang chơi"),
    [status],
  );

  const resetRuntime = (w: number, h: number, prevBest: number): GameRuntime => {
    const groundHeight = Math.max(44, Math.floor(h * 0.12));
    const birdRadius = Math.max(10, Math.floor(Math.min(w, h) * 0.03));
    const pipeWidth = Math.max(44, Math.floor(w * 0.12));
    const gapSize = Math.max(120, Math.floor(h * 0.25));

    return {
      status: "ready",
      width: w,
      height: h,
      lastTime: performance.now(),
      gravity: 1600,
      jumpVel: -520,
      bird: { x: Math.floor(w * 0.28), y: Math.floor(h * 0.42), vy: 0, radius: birdRadius, tilt: 0 },
      pipes: [],
      pipeWidth,
      gapSize,
      pipeSpacing: Math.max(220, Math.floor(w * 0.7)),
      speed: Math.max(220, Math.floor(w * 0.55)),
      groundHeight,
      score: 0,
      best: prevBest,
    };
  };

  const syncUiFromRuntime = (rt: GameRuntime) => {
    setStatus(rt.status);
    setScore(rt.score);
    setBest(rt.best);
  };

  const hardReset = () => {
    const rt = runtimeRef.current;
    if (!rt) return;
    const next = resetRuntime(rt.width, rt.height, rt.best);
    runtimeRef.current = next;
    syncUiFromRuntime(next);
  };

  const startGame = () => {
    const rt = runtimeRef.current;
    if (!rt) return;
    if (rt.status === "running") return;

    const next = { ...rt, status: "running", score: 0, pipes: [], bird: { ...rt.bird, y: rt.height * 0.42, vy: 0 } };
    runtimeRef.current = next;
    syncUiFromRuntime(next);
  };

  const flap = () => {
    const rt = runtimeRef.current;
    if (!rt) return;

    if (rt.status === "ready") startGame();
    if (rt.status === "over") {
      hardReset();
      startGame();
    }

    const next = runtimeRef.current;
    if (!next || next.status !== "running") return;
    next.bird.vy = next.jumpVel;
    next.bird.tilt = -0.35;
  };

  const endGame = (rt: GameRuntime) => {
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
      submitGameScore({ game: "flappy", playerName: safeName, score: rt.score })
        .then((data) => {
          setLeaderboard(data.leaderboard.entries);
          setTotalPlayers(data.leaderboard.totalPlayers);
          setRoundInfo(data.leaderboard.round);
        })
        .catch(() => {
          // ignore
        });
    }
    syncUiFromRuntime(rt);
  };

  const draw = (ctx: CanvasRenderingContext2D, rt: GameRuntime) => {
    const { width: w, height: h } = rt;

    ctx.clearRect(0, 0, w, h);

    // background
    const bg = ctx.createLinearGradient(0, 0, 0, h);
    bg.addColorStop(0, "rgba(79,70,229,0.18)"); // primary/18
    bg.addColorStop(0.6, "rgba(249,115,22,0.06)"); // highlight/6
    bg.addColorStop(1, "rgba(2,6,23,0.02)");
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, w, h);

    // subtle stars
    ctx.save();
    ctx.globalAlpha = 0.25;
    for (let i = 0; i < 28; i++) {
      const x = (i * 97) % w;
      const y = ((i * 53) % (h - rt.groundHeight)) * 0.6;
      ctx.fillStyle = "rgba(255,255,255,0.85)";
      ctx.fillRect(x, y, 2, 2);
    }
    ctx.restore();

    // pipes
    for (const p of rt.pipes) {
      const topH = p.gapY - rt.gapSize / 2;
      const bottomY = p.gapY + rt.gapSize / 2;
      const bottomH = (h - rt.groundHeight) - bottomY;

      const pipeGrad = ctx.createLinearGradient(p.x, 0, p.x + rt.pipeWidth, 0);
      pipeGrad.addColorStop(0, "rgba(15,23,42,0.85)");
      pipeGrad.addColorStop(0.5, "rgba(79,70,229,0.75)");
      pipeGrad.addColorStop(1, "rgba(15,23,42,0.85)");

      ctx.fillStyle = pipeGrad;
      // top pipe
      ctx.fillRect(p.x, 0, rt.pipeWidth, topH);
      // bottom pipe
      ctx.fillRect(p.x, bottomY, rt.pipeWidth, bottomH);

      // caps
      ctx.fillStyle = "rgba(248,250,252,0.25)";
      ctx.fillRect(p.x - 4, Math.max(0, topH - 10), rt.pipeWidth + 8, 10);
      ctx.fillRect(p.x - 4, bottomY, rt.pipeWidth + 8, 10);
    }

    // ground
    const groundGrad = ctx.createLinearGradient(0, h - rt.groundHeight, 0, h);
    groundGrad.addColorStop(0, "rgba(2,6,23,0.15)");
    groundGrad.addColorStop(1, "rgba(2,6,23,0.35)");
    ctx.fillStyle = groundGrad;
    ctx.fillRect(0, h - rt.groundHeight, w, rt.groundHeight);

    // bird
    ctx.save();
    ctx.translate(rt.bird.x, rt.bird.y);
    ctx.rotate(rt.bird.tilt);
    const birdGrad = ctx.createRadialGradient(0, 0, 2, 0, 0, rt.bird.radius + 6);
    birdGrad.addColorStop(0, "rgba(249,115,22,0.95)");
    birdGrad.addColorStop(0.6, "rgba(79,70,229,0.9)");
    birdGrad.addColorStop(1, "rgba(15,23,42,0.9)");
    ctx.fillStyle = birdGrad;
    ctx.beginPath();
    ctx.arc(0, 0, rt.bird.radius, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "rgba(255,255,255,0.9)";
    ctx.beginPath();
    ctx.arc(rt.bird.radius * 0.25, -rt.bird.radius * 0.2, Math.max(2, rt.bird.radius * 0.22), 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // score
    ctx.save();
    ctx.fillStyle = "rgba(2,6,23,0.75)";
    ctx.font = "700 18px ui-sans-serif, system-ui";
    ctx.fillText(String(rt.score), 14, 26);
    ctx.fillStyle = "rgba(248,250,252,0.95)";
    ctx.fillText(String(rt.score), 13, 25);
    ctx.restore();
  };

  const step = (now: number) => {
    const canvas = canvasRef.current;
    const rt = runtimeRef.current;
    if (!canvas || !rt) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dt = clamp((now - rt.lastTime) / 1000, 0, 0.033);
    rt.lastTime = now;

    if (rt.status === "running") {
      // update bird
      rt.bird.vy += rt.gravity * dt;
      rt.bird.y += rt.bird.vy * dt;
      rt.bird.tilt = clamp(rt.bird.tilt + 1.6 * dt, -0.45, 0.75);

      // spawn pipes
      const playableH = rt.height - rt.groundHeight;
      const minGapY = Math.max(rt.gapSize * 0.6, 80);
      const maxGapY = playableH - Math.max(rt.gapSize * 0.6, 80);

      if (rt.pipes.length === 0 || rt.pipes[rt.pipes.length - 1]!.x < rt.width - rt.pipeSpacing) {
        rt.pipes.push({
          x: rt.width + 12,
          gapY: rand(minGapY, maxGapY),
          passed: false,
        });
      }

      // move pipes
      for (const p of rt.pipes) p.x -= rt.speed * dt;
      rt.pipes = rt.pipes.filter((p) => p.x + rt.pipeWidth > -20);

      // collisions + scoring
      const birdLeft = rt.bird.x - rt.bird.radius;
      const birdRight = rt.bird.x + rt.bird.radius;
      const birdTop = rt.bird.y - rt.bird.radius;
      const birdBottom = rt.bird.y + rt.bird.radius;

      // world bounds
      if (birdTop <= 0) endGame(rt);
      if (birdBottom >= playableH) endGame(rt);

      for (const p of rt.pipes) {
        const pipeLeft = p.x;
        const pipeRight = p.x + rt.pipeWidth;
        const gapTop = p.gapY - rt.gapSize / 2;
        const gapBottom = p.gapY + rt.gapSize / 2;

        const overlapsX = birdRight > pipeLeft && birdLeft < pipeRight;
        const hitsPipe = overlapsX && (birdTop < gapTop || birdBottom > gapBottom);
        if (hitsPipe) endGame(rt);

        if (!p.passed && pipeRight < rt.bird.x) {
          p.passed = true;
          rt.score += 1;
          setScore(rt.score);
          if (rt.score > rt.best) {
            rt.best = rt.score;
            setBest(rt.best);
            try {
              localStorage.setItem(BEST_KEY, String(rt.best));
            } catch {
              // ignore
            }
          }
        }
      }
    }

    draw(ctx, rt);
    rafRef.current = requestAnimationFrame(step);
  };

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      const rect = container.getBoundingClientRect();
      const w = Math.max(280, Math.floor(rect.width));
      const h = Math.max(360, Math.floor(rect.height));

      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const prevBest = runtimeRef.current?.best ?? best;
      const prevStatus = runtimeRef.current?.status ?? "ready";
      const next = resetRuntime(w, h, prevBest);
      next.status = prevStatus;
      runtimeRef.current = next;
      syncUiFromRuntime(next);
    };

    const ro = new ResizeObserver(resize);
    ro.observe(container);
    resize();

    rafRef.current = requestAnimationFrame(step);

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space" || e.code === "ArrowUp") {
        e.preventDefault();
        flap();
      }
      if (e.code === "Enter" && runtimeRef.current?.status === "over") {
        e.preventDefault();
        hardReset();
      }
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
          <div className="text-lg font-semibold tracking-tight">Flappy Bird</div>
          <div className="text-sm text-muted-foreground">
            Chạm/nhấn hoặc phím Space để bay qua ống. Điểm cao nhất sẽ được lưu.
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
            <span className="rounded-lg border bg-muted/30 px-3 py-2">
              Điểm: <span className="font-semibold text-foreground">{score}</span>
            </span>
            <span className="rounded-lg border bg-muted/30 px-3 py-2">
              Kỷ lục: <span className="font-semibold text-foreground">{best}</span>
            </span>
            <span
              className={cn(
                "rounded-lg border px-3 py-2",
                status === "running" ? "bg-primary/10 text-primary border-primary/20" : "bg-muted/30 text-muted-foreground",
              )}
            >
              {hint}
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
              placeholder="Ví dụ: Minh Khoa"
            />
          </div>
          <Button variant="outline" size="sm" onClick={hardReset} className="h-9">
            Reset
          </Button>
        </div>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="relative rounded-xl border bg-background p-3">
          <div
            ref={containerRef}
            className="relative mx-auto w-full max-w-[420px] aspect-[3/4] overflow-hidden rounded-lg"
            onPointerDown={(e) => {
              e.preventDefault();
              flap();
            }}
          >
            <canvas ref={canvasRef} className="block" />

            {status !== "running" && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="rounded-xl border bg-background/80 px-4 py-3 text-center shadow-sm backdrop-blur">
                  <div className="font-semibold">{status === "over" ? "Hết game" : "Sẵn sàng?"}</div>
                  <div className="mt-1 text-sm text-muted-foreground">
                    Chạm để {status === "over" ? "chơi lại" : "bắt đầu"}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border bg-muted/20 p-4">
            <div className="text-sm font-medium">Phím tắt</div>
            <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
              <li>
                <span className="font-medium text-foreground">Space / ↑</span>: Bay lên
              </li>
              <li>
                <span className="font-medium text-foreground">Enter</span>: Reset (khi hết game)
              </li>
            </ul>
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
