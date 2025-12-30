import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Textarea } from "../../components/ui/textarea";
import { Badge } from "../../components/ui/badge";
import { Separator } from "../../components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "../../components/ui/avatar";
import { ImageWithFallback } from "../../components/figma/ImageWithFallback";
import {
  Bookmark,
  Heart,
  Image as ImageIcon,
  MapPin,
  MessageCircle,
  PenSquare,
  Rocket,
  Send,
  Share2,
  Sparkles,
  TrendingUp,
  Users,
} from "lucide-react";
import {
  addFeedComment,
  createFeedPost,
  fetchFeedPosts,
  fetchFeedWall,
  reactToPost,
  shareFeedPost,
  type FeedPost,
  type FeedReaction,
  type FeedWallItem,
} from "../../services/feed";
import { getDisplayName, setDisplayName } from "../../services/identity";
import { getAuthHeaders } from "../../services/auth";

const reactionOptions: Array<{
  key: FeedReaction;
  label: string;
  icon: typeof Heart;
  activeClass: string;
}> = [
  { key: "love", label: "Thả tym", icon: Heart, activeClass: "text-highlight" },
];

const trendingTags = ["Ẩm thực địa phương", "Food tour", "Bếp Việt chuẩn vị", "Văn hóa vùng miền", "Tip đặt bàn"];

const suggestedCreators = [
  { name: "Hoàng Phúc", role: "Restaurant Curator" },
  { name: "Trần My", role: "Travel Editor" },
  { name: "Khánh An", role: "Food Strategist" },
];

function formatTimeAgo(input: string): string {
  const time = parseTimestamp(input);
  if (!Number.isFinite(time)) return "Vừa xong";
  const diff = Date.now() - time;
  if (diff < 60_000) return "Vừa xong";
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 60) return `${minutes} phút trước`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days} ngày trước`;
  return new Date(time).toLocaleDateString("vi-VN", { day: "2-digit", month: "short", year: "numeric" });
}

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

function getInitials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "ST";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

export function BlogsPage() {
  const navigate = useNavigate();
  const [displayName, setDisplayNameState] = useState(() => getDisplayName());
  const [posts, setPosts] = useState<FeedPost[]>([]);
  const [wall, setWall] = useState<FeedWallItem[]>([]);
  const [totalPosts, setTotalPosts] = useState(0);
  const [draftTitle, setDraftTitle] = useState("");
  const [draftBody, setDraftBody] = useState("");
  const [draftImage, setDraftImage] = useState("");
  const [draftTags, setDraftTags] = useState("");
  const [expandedPosts, setExpandedPosts] = useState<Set<string>>(() => new Set());
  const [commentDrafts, setCommentDrafts] = useState<Record<string, string>>({});
  const [isLoadingPosts, setIsLoadingPosts] = useState(true);
  const [isLoadingWall, setIsLoadingWall] = useState(true);
  const [isPosting, setIsPosting] = useState(false);
  const [postsError, setPostsError] = useState<string | null>(null);
  const [wallError, setWallError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(() =>
    Boolean((getAuthHeaders() as Record<string, string>).Authorization),
  );
  const interactionLocked = !isAuthenticated;

  const profileAvatar = "";

  useEffect(() => {
    setDisplayName(displayName);
  }, [displayName]);

  useEffect(() => {
    const updateAuth = () => {
      setIsAuthenticated(Boolean((getAuthHeaders() as Record<string, string>).Authorization));
      setDisplayNameState(getDisplayName());
    };
    window.addEventListener("auth:updated", updateAuth as EventListener);
    return () => window.removeEventListener("auth:updated", updateAuth as EventListener);
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      window.dispatchEvent(new Event("auth:open"));
    }
  }, [isAuthenticated]);

  useEffect(() => {
    let active = true;
    setIsLoadingPosts(true);
    setPostsError(null);
    fetchFeedPosts({ page: 1, limit: 12 })
      .then((result) => {
        if (!active) return;
        setPosts(result.posts);
        setTotalPosts(result.pagination?.total ?? result.posts.length);
      })
      .catch((err: any) => {
        if (!active) return;
        setPostsError(err?.message || "Không tải được blog");
      })
      .finally(() => {
        if (active) setIsLoadingPosts(false);
      });
    return () => {
      active = false;
    };
  }, [isAuthenticated]);

  useEffect(() => {
    let active = true;
    if (!isAuthenticated) {
      setWall([]);
      setIsLoadingWall(false);
      setWallError(null);
      return;
    }
    setIsLoadingWall(true);
    setWallError(null);
    fetchFeedWall({ limit: 6 })
      .then((items) => {
        if (!active) return;
        setWall(items);
      })
      .catch((err: any) => {
        if (!active) return;
        setWallError(err?.message || "Không tải được tường cá nhân");
      })
      .finally(() => {
        if (active) setIsLoadingWall(false);
      });
    return () => {
      active = false;
    };
  }, [isAuthenticated]);

  const totalReactions = useMemo(() => {
    return posts.reduce((acc, post) => acc + Object.values(post.reactions).reduce((sum, v) => sum + v, 0), 0);
  }, [posts]);

  const requireAuth = (message: string) => {
    if (isAuthenticated) return true;
    toast.error(message);
    window.dispatchEvent(new Event("auth:open"));
    return false;
  };

  const handleAuthFocus = (message: string) => {
    if (!isAuthenticated) {
      requireAuth(message);
    }
  };

  const handleCreatePost = async () => {
    if (isPosting) return;
    if (!requireAuth("Vui lòng đăng nhập để đăng bài")) return;
    const title = draftTitle.trim();
    const body = draftBody.trim();
    if (!title && !body) return;

    const tags = draftTags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean)
      .slice(0, 4);

    setIsPosting(true);
    try {
      const created = await createFeedPost({
        authorName: displayName || "Khách",
        authorRole: displayName === "Khách" ? "Thành viên khách" : "Thành viên",
        title: title || "Chia sẻ nhanh",
        body,
        tags,
        image: draftImage.trim() || null,
      });
      setPosts((prev) => [created, ...prev]);
      setDraftTitle("");
      setDraftBody("");
      setDraftImage("");
      setDraftTags("");
      toast.success(
        "Đăng bài thành công",
        "Bài viết từ 150 ký tự có kèm ảnh sẽ nhận voucher ngẫu nhiên 5-15% trong Ví voucher.",
      );
    } catch (err: any) {
      toast.error(err?.message || "Không thể đăng bài");
    } finally {
      setIsPosting(false);
    }
  };

  const toggleReaction = async (post: FeedPost, reaction: FeedReaction) => {
    if (!requireAuth("Vui lòng đăng nhập để thả cảm xúc")) return;
    const nextReaction = post.myReaction === reaction ? null : reaction;
    try {
      const updated = await reactToPost({
        postId: post.id,
        reaction: nextReaction,
      });
      setPosts((prev) =>
        prev.map((item) =>
          item.id === post.id
            ? { ...item, reactions: updated.reactions, myReaction: updated.myReaction }
            : item,
        ),
      );
    } catch (err: any) {
      toast.error(err?.message || "Không thể thả cảm xúc");
    }
  };

  const toggleComments = (postId: string) => {
    setExpandedPosts((prev) => {
      const next = new Set(prev);
      if (next.has(postId)) next.delete(postId);
      else next.add(postId);
      return next;
    });
  };

  const addComment = async (postId: string) => {
    if (!requireAuth("Vui lòng đăng nhập để bình luận")) return;
    const content = (commentDrafts[postId] || "").trim();
    if (!content) return;

    try {
      const result = await addFeedComment({
        postId,
        authorName: displayName || "Khách",
        content,
      });
      setPosts((prev) =>
        prev.map((post) =>
          post.id === postId
            ? { ...post, comments: [...post.comments, result.comment], commentCount: result.commentCount }
            : post,
        ),
      );
      setCommentDrafts((prev) => ({ ...prev, [postId]: "" }));
      setExpandedPosts((prev) => new Set(prev).add(postId));
    } catch (err: any) {
      toast.error(err?.message || "Không thể gửi bình luận");
    }
  };

  const shareToWall = async (postId: string) => {
    if (!requireAuth("Vui lòng đăng nhập để chia sẻ")) return;
    try {
      const result = await shareFeedPost({
        postId,
        sharedBy: displayName || "Khách",
      });
      setPosts((prev) =>
        prev.map((post) => (post.id === postId ? { ...post, shareCount: result.shareCount } : post)),
      );
      if (result.wallItem) {
        setWall((prev) => [result.wallItem!, ...prev].slice(0, 6));
      }
      toast.success("Đã chia sẻ lên tường");
    } catch (err: any) {
      toast.error(err?.message || "Không thể chia sẻ bài");
    }
  };

  return (
    <div className="min-h-dvh bg-[radial-gradient(circle_at_top,_rgba(79,70,229,0.12),_transparent_55%),radial-gradient(circle_at_bottom,_rgba(249,115,22,0.1),_transparent_50%)]">
      <div className="relative max-w-7xl mx-auto p-4 md:p-8 space-y-6 pb-24">
        <div className="relative overflow-hidden rounded-2xl border bg-card p-6 md:p-8 shadow-sm">
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute -top-16 right-0 h-48 w-48 rounded-full bg-primary/10 blur-3xl" />
            <div className="absolute -bottom-20 left-0 h-56 w-56 rounded-full bg-highlight/10 blur-3xl" />
          </div>
          <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full border bg-muted/60 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <TrendingUp className="h-4 w-4" />
                Blog cộng đồng Smart Travel
              </div>
              <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight">
                Blog chia sẻ trải nghiệm ẩm thực & hành trình
              </h1>
              <p className="text-muted-foreground max-w-2xl">
                Không gian để cộng đồng đăng bài, trao đổi, thả cảm xúc và lưu lại các ghi chú chuyên môn.
                Tập trung vào chất lượng nội dung và trải nghiệm thực tế.
              </p>
              <div className="flex flex-wrap gap-3">
                <Button onClick={() => navigate("/restaurants")} className="h-11 px-6 rounded-lg">
                  <Rocket className="h-5 w-5" />
                  Khám phá nhà hàng
                </Button>
                <Button
                  variant="outline"
                  onClick={() => window.dispatchEvent(new Event("chatbot:open"))}
                  className="h-11 px-6 rounded-lg"
                >
                  <Sparkles className="h-5 w-5" />
                  Hỏi AI ngay
                </Button>
              </div>
            </div>

            <div className="grid w-full max-w-md grid-cols-3 gap-3">
              <Card className="rounded-xl border bg-muted/20 p-4 shadow-sm">
                <div className="text-xs uppercase text-muted-foreground">Bài viết</div>
                <div className="mt-2 text-2xl font-semibold">{totalPosts}</div>
              </Card>
              <Card className="rounded-xl border bg-muted/20 p-4 shadow-sm">
                <div className="text-xs uppercase text-muted-foreground">Tương tác</div>
                <div className="mt-2 text-2xl font-semibold">{totalReactions}</div>
              </Card>
              <Card className="rounded-xl border bg-muted/20 p-4 shadow-sm">
                <div className="text-xs uppercase text-muted-foreground">Chia sẻ</div>
                <div className="mt-2 text-2xl font-semibold">{wall.length}</div>
              </Card>
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[260px_1fr_280px]">
          <div className="space-y-6">
            <Card className="rounded-2xl border bg-card p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <Avatar className="h-12 w-12">
                  <AvatarImage src={profileAvatar || undefined} alt={displayName} />
                  <AvatarFallback>{getInitials(displayName)}</AvatarFallback>
                </Avatar>
                <div>
                  <div className="text-base font-semibold">{displayName || "Khách"}</div>
                  <div className="text-xs text-muted-foreground">Thành viên cộng đồng</div>
                </div>
              </div>
              <div className="mt-4 space-y-3 text-sm text-muted-foreground">
                <div className="flex items-center justify-between">
                  <span>Bài viết</span>
                  <span className="font-semibold text-foreground">{totalPosts}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Tương tác</span>
                  <span className="font-semibold text-foreground">{totalReactions}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Chia sẻ</span>
                  <span className="font-semibold text-foreground">{wall.length}</span>
                </div>
              </div>
              <Separator className="my-4" />
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase text-muted-foreground">Tên hiển thị</label>
                <Input
                  value={displayName}
                  onChange={(e) => setDisplayNameState(e.target.value)}
                  placeholder="Ví dụ: Trà My"
                  readOnly={interactionLocked}
                  onFocus={() => handleAuthFocus("Vui lòng đăng nhập để chỉnh sửa hồ sơ")}
                />
              </div>
            </Card>

            <Card className="rounded-2xl border bg-card p-5 shadow-sm">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <TrendingUp className="h-4 w-4 text-primary" />
                Chủ đề đang được quan tâm
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {trendingTags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="rounded-full">
                    {tag}
                  </Badge>
                ))}
              </div>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="rounded-2xl border bg-card p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <PenSquare className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-base font-semibold">Đăng bài mới</div>
                  <div className="text-xs text-muted-foreground">Chia sẻ trải nghiệm, review hoặc insight.</div>
                </div>
              </div>

              <div className="mt-4 space-y-3">
                <Input
                  value={draftTitle}
                  onChange={(e) => setDraftTitle(e.target.value)}
                  placeholder="Tiêu đề nổi bật"
                  readOnly={interactionLocked}
                  onFocus={() => handleAuthFocus("Vui lòng đăng nhập để đăng bài")}
                />
                <Textarea
                  value={draftBody}
                  onChange={(e) => setDraftBody(e.target.value)}
                  placeholder="Viết điều bạn muốn chia sẻ..."
                  className="min-h-28"
                  readOnly={interactionLocked}
                  onFocus={() => handleAuthFocus("Vui lòng đăng nhập để đăng bài")}
                />
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="relative">
                    <ImageIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      value={draftImage}
                      onChange={(e) => setDraftImage(e.target.value)}
                      placeholder="Link ảnh minh họa"
                      className="pl-9"
                      readOnly={interactionLocked}
                      onFocus={() => handleAuthFocus("Vui lòng đăng nhập để đăng bài")}
                    />
                  </div>
                  <Input
                    value={draftTags}
                    onChange={(e) => setDraftTags(e.target.value)}
                    placeholder="Tag (phân cách bằng dấu phẩy)"
                    readOnly={interactionLocked}
                    onFocus={() => handleAuthFocus("Vui lòng đăng nhập để đăng bài")}
                  />
                </div>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="text-xs text-muted-foreground">
                    Bài viết hiển thị công khai. Từ 150 ký tự kèm ảnh sẽ nhận voucher ngẫu nhiên 5-15% trong Ví voucher.
                  </div>
                  <Button onClick={handleCreatePost} className="rounded-lg" disabled={isPosting}>
                    <Send className="h-4 w-4" />
                    {isPosting ? "Đang đăng..." : "Đăng bài"}
                  </Button>
                </div>
                {interactionLocked && (
                  <div className="rounded-lg border border-dashed bg-muted/30 p-3 text-xs text-muted-foreground">
                    Vui lòng đăng nhập để đăng bài và tương tác.{" "}
                    <button
                      type="button"
                      className="font-semibold text-primary underline-offset-2 hover:underline"
                      onClick={() => requireAuth("Vui lòng đăng nhập để sử dụng blog")}
                    >
                      Đăng nhập ngay
                    </button>
                    .
                  </div>
                )}
              </div>
            </Card>

            <div className="space-y-6">
              {isLoadingPosts && posts.length === 0 && (
                <Card className="rounded-2xl border bg-card p-5 shadow-sm">
                  <div className="space-y-3">
                    <div className="h-4 w-32 animate-pulse rounded bg-muted" />
                    <div className="h-3 w-56 animate-pulse rounded bg-muted" />
                    <div className="h-32 w-full animate-pulse rounded bg-muted" />
                  </div>
                </Card>
              )}

              {postsError && (
                <Card className="rounded-2xl border border-dashed bg-muted/10 p-5 text-sm text-muted-foreground">
                  {postsError}
                </Card>
              )}

              {!isLoadingPosts && posts.length === 0 && !postsError && (
                <Card className="rounded-2xl border border-dashed bg-muted/10 p-5 text-sm text-muted-foreground">
                  Chưa có bài viết nào. Hãy là người đầu tiên chia sẻ trải nghiệm.
                </Card>
              )}

              {posts.map((post) => {
                const isExpanded = expandedPosts.has(post.id);
                return (
                  <Card key={post.id} className="rounded-2xl border bg-card p-5 shadow-sm">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <Avatar className="h-11 w-11">
                          <AvatarImage src={post.avatar || undefined} alt={post.author} />
                          <AvatarFallback>{getInitials(post.author)}</AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="font-semibold">{post.author}</div>
                          <div className="text-xs text-muted-foreground">{post.role || "Thành viên"}</div>
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground">{formatTimeAgo(post.createdAt)}</div>
                    </div>

                    <div className="mt-4 space-y-3">
                      <div className="text-lg font-semibold tracking-tight">{post.title}</div>
                      {post.body && <p className="text-sm text-muted-foreground">{post.body}</p>}
                      {post.location ? (
                        <div className="inline-flex items-center gap-2 rounded-full border bg-muted/40 px-3 py-1 text-xs text-muted-foreground">
                          <MapPin className="h-3.5 w-3.5" />
                          {post.location}
                        </div>
                      ) : null}
                      {post.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {post.tags.map((tag) => (
                            <Badge key={tag} variant="secondary" className="rounded-full">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                      {post.image && (
                        <div className="overflow-hidden rounded-xl border">
                          <ImageWithFallback
                            src={post.image}
                            alt={post.title}
                            className="h-56 w-full object-cover"
                            loading="lazy"
                            decoding="async"
                          />
                        </div>
                      )}
                    </div>

                    <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
                      <div className="flex items-center gap-3">
                        <span>{post.commentCount} bình luận</span>
                        <span>{post.shareCount} lượt chia sẻ</span>
                      </div>
                      <button type="button" className="inline-flex items-center gap-2 hover:text-foreground">
                        <Bookmark className="h-4 w-4" />
                        Lưu bài
                      </button>
                    </div>

                    <Separator className="my-4" />

                    <div className="flex flex-wrap items-center gap-2">
                      {reactionOptions.map((reaction) => {
                        const active = post.myReaction === reaction.key;
                        const Icon = reaction.icon;
                        return (
                          <button
                            key={reaction.key}
                            type="button"
                            onClick={() => toggleReaction(post, reaction.key)}
                            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs transition ${
                              active ? "border-transparent bg-primary/10 text-primary" : "bg-muted/20 hover:bg-muted/40"
                            }`}
                          >
                            <Icon className={`h-4 w-4 ${active ? reaction.activeClass : "text-muted-foreground"}`} />
                            <span>{reaction.label}</span>
                            <span className="font-semibold text-foreground">{post.reactions[reaction.key]}</span>
                          </button>
                        );
                      })}
                      <button
                        type="button"
                        onClick={() => toggleComments(post.id)}
                        className="inline-flex items-center gap-2 rounded-full border bg-muted/20 px-3 py-1.5 text-xs hover:bg-muted/40"
                      >
                        <MessageCircle className="h-4 w-4 text-muted-foreground" />
                        Bình luận
                      </button>
                      <button
                        type="button"
                        onClick={() => shareToWall(post.id)}
                        className="inline-flex items-center gap-2 rounded-full border bg-muted/20 px-3 py-1.5 text-xs hover:bg-muted/40"
                      >
                        <Share2 className="h-4 w-4 text-muted-foreground" />
                        Chia sẻ về tường
                      </button>
                    </div>

                    {isExpanded && (
                      <div className="mt-4 space-y-4">
                        <div className="space-y-3">
                          {post.comments.length === 0 && (
                            <div className="rounded-lg border border-dashed bg-muted/20 p-4 text-sm text-muted-foreground">
                              Chưa có bình luận. Hãy là người đầu tiên chia sẻ cảm nhận.
                            </div>
                          )}
                          {post.comments.map((comment) => (
                            <div key={comment.id} className="rounded-lg border bg-muted/10 p-3">
                              <div className="flex items-center justify-between text-xs text-muted-foreground">
                                <span className="font-semibold text-foreground">{comment.author}</span>
                                <span>{formatTimeAgo(comment.createdAt)}</span>
                              </div>
                              <p className="mt-2 text-sm text-muted-foreground">{comment.content}</p>
                            </div>
                          ))}
                        </div>
                        <div className="flex flex-wrap items-start gap-2">
                        <Textarea
                          value={commentDrafts[post.id] || ""}
                          onChange={(e) =>
                            setCommentDrafts((prev) => ({ ...prev, [post.id]: e.target.value }))
                          }
                          placeholder="Viết bình luận..."
                          className="min-h-20 flex-1"
                          readOnly={interactionLocked}
                          onFocus={() => handleAuthFocus("Vui lòng đăng nhập để bình luận")}
                        />
                          <Button onClick={() => addComment(post.id)} className="self-stretch rounded-lg px-4">
                            Gửi
                          </Button>
                        </div>
                      </div>
                    )}
                  </Card>
                );
              })}
            </div>
          </div>

          <div className="space-y-6">
            <Card className="rounded-2xl border bg-card p-5 shadow-sm">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Users className="h-4 w-4 text-primary" />
                Tường của bạn
              </div>
              <div className="mt-4 space-y-3">
                {isLoadingWall && (
                  <div className="rounded-lg border bg-muted/10 p-4 text-sm text-muted-foreground">
                    Đang tải tường cá nhân...
                  </div>
                )}
                {wallError && (
                  <div className="rounded-lg border border-dashed bg-muted/20 p-4 text-sm text-muted-foreground">
                    {wallError}
                  </div>
                )}
                {!isAuthenticated && (
                  <div className="rounded-lg border border-dashed bg-muted/20 p-4 text-sm text-muted-foreground">
                    Đăng nhập để xem tường cá nhân của bạn.
                  </div>
                )}
                {isAuthenticated && !isLoadingWall && wall.length === 0 && !wallError && (
                  <div className="rounded-lg border border-dashed bg-muted/20 p-4 text-sm text-muted-foreground">
                    Chưa có bài viết nào được chia sẻ về tường.
                  </div>
                )}
                {wall.map((item) => (
                  <div key={item.id} className="rounded-lg border bg-muted/10 p-3">
                    <div className="text-xs text-muted-foreground">{formatTimeAgo(item.sharedAt)}</div>
                    <div className="mt-1 text-sm font-semibold">{item.postTitle || "Bài viết đã ẩn"}</div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      Chia sẻ bởi {item.sharedBy}
                      {item.postAuthor ? ` • ${item.postAuthor}` : ""}
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="rounded-2xl border bg-card p-5 shadow-sm">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Users className="h-4 w-4 text-primary" />
                Gợi ý kết nối
              </div>
              <div className="mt-4 space-y-3">
                {suggestedCreators.map((creator) => (
                  <div key={creator.name} className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold">{creator.name}</div>
                      <div className="text-xs text-muted-foreground">{creator.role}</div>
                    </div>
                    <Button variant="outline" size="sm">
                      Theo dõi
                    </Button>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
