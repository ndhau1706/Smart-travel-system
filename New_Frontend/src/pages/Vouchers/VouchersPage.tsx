import { useEffect, useMemo, useState } from "react";
import { Percent, Ticket, Wallet } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { cn } from "../../components/ui/utils";
import { fetchVouchers, type VoucherItem } from "../../services/vouchers";
import { getAuthHeaders } from "../../services/auth";

function parseTimestamp(input: string): number | null {
  if (!input) return null;
  const trimmed = input.trim();
  if (!trimmed) return null;
  let normalized = trimmed.replace(" ", "T");
  normalized = normalized.replace(/(\.\d{3})\d+/, "$1");
  const hasTimezone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(normalized);
  if (!hasTimezone) normalized = `${normalized}Z`;
  const parsed = new Date(normalized);
  const time = parsed.getTime();
  return Number.isFinite(time) ? time : null;
}

function formatDateTime(input: string): string {
  const time = parseTimestamp(input);
  if (!Number.isFinite(time)) return "-";
  return new Date(time).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const sourceLabel: Record<VoucherItem["source"], string> = {
  blog: "Blog",
  game: "Trò chơi",
};

const statusStyles = (status: string) => {
  if (status.toLowerCase().includes("đã gửi") || status.toLowerCase().includes("đã phát hành")) {
    return "border-primary/20 bg-primary/10 text-primary";
  }
  if (status.toLowerCase().includes("chờ")) {
    return "border-highlight/30 bg-highlight/10 text-highlight";
  }
  return "border-muted/40 bg-muted/30 text-muted-foreground";
};

export function VouchersPage() {
  const [items, setItems] = useState<VoucherItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(() =>
    Boolean((getAuthHeaders() as Record<string, string>).Authorization),
  );

  const bestPercent = useMemo(() => {
    if (items.length === 0) return 0;
    return Math.max(...items.map((v) => v.percent));
  }, [items]);

  useEffect(() => {
    const updateAuth = () =>
      setIsAuthenticated(Boolean((getAuthHeaders() as Record<string, string>).Authorization));
    window.addEventListener("auth:updated", updateAuth as EventListener);
    return () => window.removeEventListener("auth:updated", updateAuth as EventListener);
  }, []);

  const reloadVouchers = () => {
    if (!isAuthenticated) return;
    setIsLoading(true);
    setError(null);
    fetchVouchers()
      .then((data) => {
        setItems(data.items);
        setTotal(data.total);
      })
      .catch((err: any) => {
        const message = err?.message || "Không tải được voucher";
        setError(message);
        if (String(message).includes("401")) {
          window.dispatchEvent(new Event("auth:open"));
        }
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  useEffect(() => {
    if (!isAuthenticated) {
      setItems([]);
      setTotal(0);
      setError(null);
      setIsLoading(false);
      return;
    }

    let active = true;
    setIsLoading(true);
    setError(null);
    fetchVouchers()
      .then((data) => {
        if (!active) return;
        setItems(data.items);
        setTotal(data.total);
      })
      .catch((err: any) => {
        if (!active) return;
        const message = err?.message || "Không tải được voucher";
        setError(message);
        if (String(message).includes("401")) {
          window.dispatchEvent(new Event("auth:open"));
        }
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [isAuthenticated]);

  return (
    <div className="min-h-dvh bg-[radial-gradient(circle_at_top,_rgba(79,70,229,0.12),_transparent_60%),radial-gradient(circle_at_bottom,_rgba(249,115,22,0.08),_transparent_50%)]">
      <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-6 pb-24">
        <Card className="relative overflow-hidden rounded-2xl border bg-card p-6 md:p-8 shadow-sm">
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute -top-16 right-0 h-48 w-48 rounded-full bg-primary/10 blur-3xl" />
            <div className="absolute -bottom-20 left-0 h-56 w-56 rounded-full bg-highlight/10 blur-3xl" />
          </div>
          <div className="relative flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 rounded-full border bg-muted/60 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <Wallet className="h-4 w-4" />
                Ví voucher
              </div>
              <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight">Quản lý voucher của bạn</h1>
              <p className="text-sm text-muted-foreground max-w-2xl">
                Lưu trữ voucher nhận được từ blog và bảng xếp hạng trò chơi. Voucher mới sẽ xuất hiện tại đây.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Card className="rounded-xl border bg-muted/20 p-4 shadow-sm">
                <div className="text-xs uppercase text-muted-foreground">Tổng voucher</div>
                <div className="mt-2 text-2xl font-semibold">{total}</div>
              </Card>
              <Card className="rounded-xl border bg-muted/20 p-4 shadow-sm">
                <div className="text-xs uppercase text-muted-foreground">Ưu đãi cao nhất</div>
                <div className="mt-2 text-2xl font-semibold">{bestPercent ? `${bestPercent}%` : "-"}</div>
              </Card>
            </div>
          </div>
        </Card>

        {!isAuthenticated && (
          <Card className="rounded-2xl border border-dashed bg-muted/20 p-6 text-sm text-muted-foreground">
            Vui lòng đăng nhập để xem ví voucher của bạn.{" "}
            <button
              type="button"
              className="font-semibold text-primary underline-offset-2 hover:underline"
              onClick={() => window.dispatchEvent(new Event("auth:open"))}
            >
              Đăng nhập ngay
            </button>
            .
          </Card>
        )}

        {isAuthenticated && (
          <Card className="rounded-2xl border bg-card p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold">Danh sách voucher</div>
                <div className="text-xs text-muted-foreground">
                  Voucher blog được cộng ngay khi đăng bài đủ điều kiện.
                </div>
              </div>
              <span className="rounded-full border bg-muted/20 px-2 py-1 text-xs text-muted-foreground">
                {total} voucher
              </span>
            </div>

            <div className="mt-4">
              {isLoading && (
                <div className="rounded-lg border border-dashed bg-muted/20 p-4 text-sm text-muted-foreground">
                  Đang tải voucher...
                </div>
              )}

              {error && (
                <div className="rounded-lg border border-dashed bg-muted/20 p-4 text-sm text-muted-foreground">
                  {error}
                </div>
              )}

              {!isLoading && !error && items.length === 0 && (
                <div className="rounded-lg border border-dashed bg-muted/20 p-4 text-sm text-muted-foreground">
                  Chưa có voucher nào. Hãy đăng bài hoặc chơi game để nhận voucher.
                </div>
              )}

              {!isLoading && !error && items.length > 0 && (
                <div className="overflow-auto rounded-lg border bg-muted/10">
                  <table className="w-full text-xs">
                    <thead className="sticky top-0 bg-muted/30 text-muted-foreground">
                      <tr>
                        <th className="px-3 py-2 text-left">Nguồn</th>
                        <th className="px-3 py-2 text-left">Mã voucher</th>
                        <th className="px-3 py-2 text-right">Ưu đãi</th>
                        <th className="px-3 py-2 text-left">Trạng thái</th>
                        <th className="px-3 py-2 text-right">Ngày nhận</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((voucher) => (
                        <tr key={voucher.id} className="border-t">
                          <td className="px-3 py-2 text-left">
                            <div className="flex items-center gap-2">
                              <Ticket className="h-4 w-4 text-muted-foreground" />
                              <div>
                                <div className="font-semibold text-foreground">{sourceLabel[voucher.source]}</div>
                                <div className="text-[11px] text-muted-foreground line-clamp-1">{voucher.title}</div>
                              </div>
                            </div>
                          </td>
                          <td className="px-3 py-2 text-left font-mono text-foreground">{voucher.code}</td>
                          <td className="px-3 py-2 text-right font-semibold text-foreground">
                            <span className="inline-flex items-center gap-1">
                              <Percent className="h-3.5 w-3.5 text-highlight" />
                              {voucher.percent}%
                            </span>
                          </td>
                          <td className="px-3 py-2 text-left">
                            <Badge className={cn("rounded-full border px-2 py-0.5", statusStyles(voucher.status))}>
                              {voucher.status}
                            </Badge>
                          </td>
                          <td className="px-3 py-2 text-right text-muted-foreground">
                            {formatDateTime(voucher.createdAt)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </Card>
        )}

        {isAuthenticated && items.length > 0 && (
          <div className="flex justify-end">
            <Button variant="outline" size="sm" onClick={reloadVouchers}>
              Làm mới danh sách
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
