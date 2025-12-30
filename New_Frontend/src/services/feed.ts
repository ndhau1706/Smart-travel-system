import { API_URL } from "./config";
import { getAuthHeaders } from "./auth";

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
  meta?: {
    pagination?: {
      page: number;
      limit: number;
      total: number;
      total_pages: number;
      has_next: boolean;
      has_prev: boolean;
    };
  };
};

export type FeedReaction = "like" | "love" | "wow" | "insightful";

export type FeedComment = {
  id: string;
  author: string;
  content: string;
  createdAt: string;
};

export type FeedPost = {
  id: string;
  author: string;
  role?: string | null;
  avatar?: string | null;
  title: string;
  body?: string | null;
  tags: string[];
  location?: string | null;
  image?: string | null;
  createdAt: string;
  reactions: Record<FeedReaction, number>;
  myReaction?: FeedReaction | null;
  comments: FeedComment[];
  commentCount: number;
  shareCount: number;
};

export type FeedWallItem = {
  id: string;
  postId: string;
  sharedBy: string;
  sharedAt: string;
  postTitle?: string | null;
  postAuthor?: string | null;
};

type ApiFeedComment = {
  id: string;
  author_name: string;
  content: string;
  created_at: string;
};

type ApiFeedPost = {
  id: string;
  author_name: string;
  author_role?: string | null;
  author_avatar?: string | null;
  title: string;
  body?: string | null;
  tags?: string[] | null;
  location?: string | null;
  image?: string | null;
  reactions: Record<FeedReaction, number>;
  my_reaction?: FeedReaction | null;
  comments?: ApiFeedComment[];
  comment_count?: number;
  share_count?: number;
  created_at: string;
};

type ApiWallItem = {
  id: string;
  post_id: string;
  shared_by: string;
  shared_at: string;
  post?: {
    id: string;
    title: string;
    author_name: string;
  } | null;
};

function mapFeedComment(comment: ApiFeedComment): FeedComment {
  return {
    id: comment.id,
    author: comment.author_name,
    content: comment.content,
    createdAt: comment.created_at,
  };
}

function mapFeedPost(post: ApiFeedPost): FeedPost {
  return {
    id: post.id,
    author: post.author_name,
    role: post.author_role ?? null,
    avatar: post.author_avatar ?? null,
    title: post.title,
    body: post.body ?? null,
    tags: post.tags ?? [],
    location: post.location ?? null,
    image: post.image ?? null,
    createdAt: post.created_at,
    reactions: {
      like: post.reactions?.like ?? 0,
      love: post.reactions?.love ?? 0,
      wow: post.reactions?.wow ?? 0,
      insightful: post.reactions?.insightful ?? 0,
    },
    myReaction: post.my_reaction ?? null,
    comments: (post.comments || []).map(mapFeedComment),
    commentCount: post.comment_count ?? (post.comments?.length || 0),
    shareCount: post.share_count ?? 0,
  };
}

function mapWallItem(item: ApiWallItem): FeedWallItem {
  return {
    id: item.id,
    postId: item.post_id,
    sharedBy: item.shared_by,
    sharedAt: item.shared_at,
    postTitle: item.post?.title ?? null,
    postAuthor: item.post?.author_name ?? null,
  };
}

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

async function handleApi<T>(res: Response): Promise<ApiResponse<T>> {
  const payload = (await parseJsonSafe(res)) as ApiResponse<T> | null;
  if (!res.ok) {
    throw new Error(getErrorMessage(payload, `HTTP error! status: ${res.status}`));
  }
  if (!payload?.success) {
    throw new Error(getErrorMessage(payload, "Request failed"));
  }
  return payload;
}

export async function fetchFeedPosts(params: {
  page?: number;
  limit?: number;
  viewerId?: string;
}): Promise<{ posts: FeedPost[]; pagination?: ApiResponse<unknown>["meta"]["pagination"] }> {
  const query = new URLSearchParams();
  query.set("page", String(params.page ?? 1));
  query.set("limit", String(params.limit ?? 10));
  if (params.viewerId) query.set("viewer_id", params.viewerId);

  const res = await fetch(`${API_URL}/feed/posts?${query.toString()}`, {
    headers: { ...getAuthHeaders() },
  });
  const payload = await handleApi<ApiFeedPost[]>(res);
  return {
    posts: (payload.data || []).map(mapFeedPost),
    pagination: payload.meta?.pagination,
  };
}

export async function createFeedPost(payload: {
  authorName: string;
  authorRole?: string | null;
  authorAvatar?: string | null;
  title?: string | null;
  body?: string | null;
  tags?: string[];
  location?: string | null;
  image?: string | null;
}): Promise<FeedPost> {
  const res = await fetch(`${API_URL}/feed/posts`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({
      author_name: payload.authorName,
      author_role: payload.authorRole ?? null,
      author_avatar: payload.authorAvatar ?? null,
      title: payload.title ?? null,
      body: payload.body ?? null,
      tags: payload.tags ?? [],
      location: payload.location ?? null,
      image: payload.image ?? null,
    }),
  });
  const response = await handleApi<ApiFeedPost>(res);
  return mapFeedPost(response.data);
}

export async function reactToPost(payload: {
  postId: string;
  reaction: FeedReaction | null;
}): Promise<{ reactions: FeedPost["reactions"]; myReaction: FeedReaction | null }> {
  const res = await fetch(`${API_URL}/feed/posts/${encodeURIComponent(payload.postId)}/reactions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({
      reaction: payload.reaction,
    }),
  });
  const response = await handleApi<{
    post_id: string;
    reactions: Record<FeedReaction, number>;
    my_reaction?: FeedReaction | null;
  }>(res);
  return {
    reactions: response.data.reactions,
    myReaction: response.data.my_reaction ?? null,
  };
}

export async function addFeedComment(payload: {
  postId: string;
  authorName: string;
  content: string;
}): Promise<{ comment: FeedComment; commentCount: number }> {
  const res = await fetch(`${API_URL}/feed/posts/${encodeURIComponent(payload.postId)}/comments`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({
      author_name: payload.authorName,
      content: payload.content,
    }),
  });
  const response = await handleApi<{
    post_id: string;
    comment: ApiFeedComment;
    comment_count: number;
  }>(res);
  return {
    comment: mapFeedComment(response.data.comment),
    commentCount: response.data.comment_count,
  };
}

export async function shareFeedPost(payload: {
  postId: string;
  sharedBy: string;
}): Promise<{ shareCount: number; wallItem?: FeedWallItem | null }> {
  const res = await fetch(`${API_URL}/feed/posts/${encodeURIComponent(payload.postId)}/shares`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({
      shared_by: payload.sharedBy,
    }),
  });
  const response = await handleApi<{
    post_id: string;
    share_id: string;
    share_count: number;
    wall_item?: ApiWallItem | null;
  }>(res);
  return {
    shareCount: response.data.share_count,
    wallItem: response.data.wall_item ? mapWallItem(response.data.wall_item) : null,
  };
}

export async function fetchFeedWall(payload: { limit?: number } = {}): Promise<FeedWallItem[]> {
  const query = new URLSearchParams();
  if (payload.limit) query.set("limit", String(payload.limit));

  const res = await fetch(`${API_URL}/feed/wall?${query.toString()}`, {
    headers: { ...getAuthHeaders() },
  });
  const response = await handleApi<ApiWallItem[]>(res);
  return (response.data || []).map(mapWallItem);
}
