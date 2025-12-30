import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Avatar, AvatarFallback, AvatarImage } from "../../components/ui/avatar";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { ScrollArea } from "../../components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { Textarea } from "../../components/ui/textarea";
import { toast } from "sonner";

import {
  changePassword,
  createAddress,
  deleteAddress,
  getProfile,
  listAddresses,
  updateAddress,
  updateProfile,
  uploadAvatar,
  type AddressUpsert,
  type AuthUser,
  type UserAddress,
} from "../../services/auth";
import { fetchMyReviews, type ApiReview } from "../../services/api";
import { cn } from "../../components/ui/utils";
import { Camera, Lock, LogOut, MapPin, Settings2, Shield, Sparkles, User } from "lucide-react";

type ProfileTab = "general" | "taste" | "activity" | "security";

type TasteProfile = {
  spicy: boolean;
  sweet: boolean;
  eatClean: boolean;
  highProtein: boolean;
  lovesVeggies: boolean;
  diet: "normal" | "vegetarian" | "keto";
  allergies: {
    seafood: boolean;
    peanut: boolean;
    milk: boolean;
    gluten: boolean;
  };
  priceSegment: 1 | 2 | 3;
  notes: string;
};

const defaultTasteProfile: TasteProfile = {
  spicy: false,
  sweet: false,
  eatClean: false,
  highProtein: false,
  lovesVeggies: false,
  diet: "normal",
  allergies: { seafood: false, peanut: false, milk: false, gluten: false },
  priceSegment: 2,
  notes: "",
};

function initialsFromName(name: string): string {
  const parts = (name || "").trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "U";
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1]?.[0] ?? "" : "";
  return `${first}${last}`.toUpperCase();
}

function getTasteStorageKey(user: AuthUser | null): string {
  const email = user?.email?.trim();
  return email ? `taste_profile:${email}` : "taste_profile:guest";
}

export function ProfilePage() {
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<ProfileTab>("general");
  const [loading, setLoading] = useState(true);
  const [needsLogin, setNeedsLogin] = useState(false);
  const [saving, setSaving] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);

  const [displayName, setDisplayName] = useState("");
  const [phone, setPhone] = useState("");

  const [avatarUploading, setAvatarUploading] = useState(false);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);

  const [addresses, setAddresses] = useState<UserAddress[]>([]);
  const [addressDraft, setAddressDraft] = useState<AddressUpsert>({});
  const [editingAddressId, setEditingAddressId] = useState<string | null>(null);
  const [locatingAddress, setLocatingAddress] = useState(false);
  const [geocodingAddress, setGeocodingAddress] = useState(false);

  const [tasteProfile, setTasteProfile] = useState<TasteProfile>(defaultTasteProfile);

  const [reviews, setReviews] = useState<ApiReview[]>([]);
  const [loadingReviews, setLoadingReviews] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);

  const tasteStorageKey = useMemo(() => getTasteStorageKey(user), [user]);
  const avatarLabel = useMemo(
    () => initialsFromName(displayName || user?.name || "User"),
    [displayName, user?.name],
  );

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      try {
        const stored = localStorage.getItem("auth");
        if (!stored) {
          setNeedsLogin(true);
          setUser(null);
          setLoading(false);
          return;
        }
        setNeedsLogin(false);

        const profile = await getProfile();
        if (cancelled) return;
        setUser(profile);
        setDisplayName(profile.name || "");
        setPhone(profile.phone || "");
        setAvatarPreview(profile.avatar || null);

        try {
          const raw = localStorage.getItem(getTasteStorageKey(profile));
          if (raw) {
            const parsed = JSON.parse(raw) as Partial<TasteProfile>;
            setTasteProfile((prev) => ({ ...prev, ...parsed }));
          }
        } catch {
          // ignore
        }

        try {
          const list = await listAddresses();
          if (!cancelled) setAddresses(Array.isArray(list) ? list : []);
        } catch {
          if (!cancelled) setAddresses([]);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : "Không tải được hồ sơ";
        if (String(message).includes("(401)") || String(message).includes("401")) {
          setNeedsLogin(true);
        }
        toast.error(message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(tasteStorageKey, JSON.stringify(tasteProfile));
    } catch {
      // ignore
    }
  }, [tasteProfile, tasteStorageKey]);

  const isVerified = Boolean(user?.is_verified);

  const handleAvatarPick = async (file: File | null) => {
    if (!file) return;
    setAvatarUploading(true);
    try {
      const next = await uploadAvatar(file);
      setUser(next);
      setAvatarPreview(next.avatar || null);
      toast.success("Cập nhật avatar thành công");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Upload avatar thất bại");
    } finally {
      setAvatarUploading(false);
    }
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      const next = await updateProfile({
        name: displayName.trim() || null,
        phone: phone.trim() || null,
      });
      setUser(next);
      toast.success("Đã lưu hồ sơ");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Lưu hồ sơ thất bại");
    } finally {
      setSaving(false);
    }
  };

  const startNewAddress = () => {
    setEditingAddressId(null);
    setAddressDraft({ label: "", line1: "", line2: "", city: "", is_default: false });
  };

  const startEditAddress = (address: UserAddress) => {
    setEditingAddressId(address.id);
    setAddressDraft({
      label: address.label ?? "",
      line1: address.line1 ?? "",
      line2: address.line2 ?? "",
      city: address.city ?? "",
      latitude: address.latitude ?? null,
      longitude: address.longitude ?? null,
      is_default: Boolean(address.is_default),
    });
  };

  const captureCurrentLocation = () => {
    if (locatingAddress) return;
    if (!("geolocation" in navigator)) {
      toast.error("Thiết bị không hỗ trợ lấy vị trí");
      return;
    }

    setLocatingAddress(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setAddressDraft((prev) => ({
          ...prev,
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
        }));
        toast.success("Đã lấy tọa độ hiện tại");
        setLocatingAddress(false);
      },
      (err) => {
        toast.error(err?.message ? `Không lấy được vị trí: ${err.message}` : "Không lấy được vị trí");
        setLocatingAddress(false);
      },
      { enableHighAccuracy: true, timeout: 12000 },
    );
  };

  const geocodeDraftAddress = async () => {
    if (geocodingAddress) return;
    const query = [addressDraft.line1, addressDraft.line2, addressDraft.city].filter(Boolean).join(", ").trim();
    if (!query) {
      toast.error("Vui lòng nhập địa chỉ trước");
      return;
    }

    setGeocodingAddress(true);
    try {
      const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=${encodeURIComponent(query)}`;
      const res = await fetch(url, { headers: { Accept: "application/json" } });
      if (!res.ok) throw new Error(`Geocode failed (${res.status})`);
      const data = (await res.json()) as Array<{ lat?: string; lon?: string }> | null;
      const hit = Array.isArray(data) ? data[0] : null;
      const lat = hit?.lat ? Number(hit.lat) : NaN;
      const lon = hit?.lon ? Number(hit.lon) : NaN;
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
        toast.error("Không tìm thấy tọa độ phù hợp");
        return;
      }
      setAddressDraft((prev) => ({ ...prev, latitude: lat, longitude: lon }));
      toast.success("Đã tự lấy tọa độ từ địa chỉ");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Không lấy được tọa độ");
    } finally {
      setGeocodingAddress(false);
    }
  };

  const saveAddress = async () => {
    const payload: AddressUpsert = {
      label: addressDraft.label?.trim() || null,
      line1: addressDraft.line1?.trim() || null,
      line2: addressDraft.line2?.trim() || null,
      city: addressDraft.city?.trim() || null,
      latitude: addressDraft.latitude ?? null,
      longitude: addressDraft.longitude ?? null,
      is_default: Boolean(addressDraft.is_default),
    };

    try {
      const saved = editingAddressId
        ? await updateAddress(editingAddressId, payload)
        : await createAddress(payload);

      setAddresses((prev) => {
        const filtered = prev.filter((a) => a.id !== saved.id);
        const next = [saved, ...filtered];
        return next.sort((a, b) => (b.is_default ? 1 : 0) - (a.is_default ? 1 : 0));
      });

      toast.success(editingAddressId ? "Đã cập nhật địa chỉ" : "Đã thêm địa chỉ");
      startNewAddress();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Lưu địa chỉ thất bại");
    }
  };

  const removeAddress = async (id: string) => {
    try {
      await deleteAddress(id);
      setAddresses((prev) => prev.filter((a) => a.id !== id));
      toast.success("Đã xóa địa chỉ");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Xóa địa chỉ thất bại");
    }
  };

  const loadReviews = async () => {
    if (loadingReviews) return;
    setLoadingReviews(true);
    try {
      const list = await fetchMyReviews();
      setReviews(Array.isArray(list) ? list : []);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Không tải được lịch sử đánh giá");
    } finally {
      setLoadingReviews(false);
    }
  };

  useEffect(() => {
    if (activeTab === "activity") void loadReviews();
  }, [activeTab]);

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error("Vui lòng nhập đầy đủ thông tin");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("Mật khẩu mới không khớp");
      return;
    }

    setChangingPassword(true);
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      toast.success("Đã đổi mật khẩu");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Đổi mật khẩu thất bại");
    } finally {
      setChangingPassword(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("auth");
    window.location.href = "/";
  };

  if (loading) {
    return (
      <div className="min-h-dvh flex items-center justify-center p-6">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-muted border-t-primary" />
      </div>
    );
  }

  if (needsLogin) {
    return (
      <div className="min-h-dvh flex items-center justify-center p-6">
        <Card className="w-full max-w-md rounded-xl border bg-card p-6 shadow-sm">
          <h1 className="text-xl font-semibold">Bạn chưa đăng nhập</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Vui lòng đăng nhập để xem và cập nhật hồ sơ cá nhân.
          </p>
          <div className="mt-6 flex flex-col gap-2 sm:flex-row">
            <Button
              className="rounded-lg"
              onClick={() => window.dispatchEvent(new Event("auth:open"))}
            >
              Đăng nhập
            </Button>
            <Button
              variant="outline"
              className="rounded-lg"
              onClick={() => navigate("/")}
            >
              Về trang chủ
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-dvh">
      <ScrollArea className="h-dvh">
        <div className="max-w-6xl mx-auto p-4 md:p-8">
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as ProfileTab)} className="w-full">
            <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
              {/* Left sidebar */}
              <Card className="rounded-xl border bg-card shadow-sm overflow-hidden">
                <div className="p-6 border-b border-border">
                  <div className="flex items-start gap-4">
                    <div className="relative">
                      <Avatar className="h-20 w-20 ring-2 ring-primary/20">
                        <AvatarImage
                          src={avatarPreview ?? undefined}
                          alt={displayName || user?.name || "Avatar"}
                        />
                        <AvatarFallback className="bg-primary/10 text-primary font-semibold">
                          {avatarLabel}
                        </AvatarFallback>
                      </Avatar>
                      <label className="absolute -bottom-2 -right-2 cursor-pointer">
                        <input
                          type="file"
                          accept="image/*"
                          className="sr-only"
                          onChange={(e) => void handleAvatarPick(e.target.files?.[0] ?? null)}
                          disabled={avatarUploading}
                        />
                        <span
                          className={cn(
                            "inline-flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-sm ring-1 ring-primary/20",
                            avatarUploading ? "opacity-60" : "hover:bg-primary/90",
                          )}
                          title="Chọn ảnh"
                        >
                          <Camera className="h-4 w-4" />
                        </span>
                      </label>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h1 className="truncate text-lg font-semibold">
                          {displayName || user?.name || "Tài khoản"}
                        </h1>
                        {isVerified ? (
                          <Badge className="rounded-full bg-green-100 text-green-700 border border-green-200">
                            Đã xác thực
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="rounded-full">
                            Thành viên
                          </Badge>
                        )}
                      </div>
                      <p className="mt-1 truncate text-sm text-muted-foreground">{user?.email}</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <Badge className="rounded-full bg-primary/10 text-primary border border-primary/15">
                          <Sparkles className="h-3.5 w-3.5 mr-1" />
                          Smart Travel
                        </Badge>
                        <Badge variant="secondary" className="rounded-full">
                          Gợi ý theo gu
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-3">
                  <TabsList className="grid w-full grid-cols-2 gap-2 bg-transparent p-0">
                    <TabsTrigger value="general" className="justify-start gap-2 rounded-lg">
                      <User className="h-4 w-4" />
                      <span className="text-sm">Thông tin</span>
                    </TabsTrigger>
                    <TabsTrigger value="taste" className="justify-start gap-2 rounded-lg">
                      <Settings2 className="h-4 w-4" />
                      <span className="text-sm">Sở thích</span>
                    </TabsTrigger>
                    <TabsTrigger value="activity" className="justify-start gap-2 rounded-lg">
                      <MapPin className="h-4 w-4" />
                      <span className="text-sm">Hoạt động</span>
                    </TabsTrigger>
                    <TabsTrigger value="security" className="justify-start gap-2 rounded-lg">
                      <Shield className="h-4 w-4" />
                      <span className="text-sm">Bảo mật</span>
                    </TabsTrigger>
                  </TabsList>
                </div>

                <div className="p-3 border-t border-border">
                  <Button
                    variant="ghost"
                    className="w-full justify-start rounded-lg text-muted-foreground hover:text-foreground"
                    onClick={() => navigate("/account/settings")}
                  >
                    <Settings2 className="h-4 w-4 mr-2" />
                    Cài đặt
                  </Button>
                </div>
              </Card>

              {/* Right content */}
              <div className="space-y-6">
                <TabsContent value="general" className="mt-0 space-y-6">
                  <Card className="rounded-xl border bg-card p-6 shadow-sm">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
                      <div>
                        <h2 className="text-lg font-semibold">Thông tin cá nhân</h2>
                        <p className="mt-1 text-sm text-muted-foreground">
                          Cập nhật hồ sơ để trải nghiệm gợi ý tốt hơn.
                        </p>
                      </div>
                      <Button onClick={() => void handleSaveProfile()} disabled={saving} className="rounded-lg">
                        {saving ? "Đang lưu..." : "Lưu"}
                      </Button>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="profile-name">Họ tên</Label>
                        <Input
                          id="profile-name"
                          value={displayName}
                          onChange={(e) => setDisplayName(e.target.value)}
                          placeholder="Nhập họ tên"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="profile-phone">Số điện thoại</Label>
                        <Input
                          id="profile-phone"
                          value={phone}
                          onChange={(e) => setPhone(e.target.value)}
                          placeholder="Ví dụ: 0912..."
                        />
                      </div>

                      <div className="space-y-2 sm:col-span-2">
                        <Label>Email</Label>
                        <Input value={user?.email ?? ""} readOnly className="bg-muted/40" />
                        <p className="text-xs text-muted-foreground">
                          Email là định danh tài khoản, không thể chỉnh sửa.
                        </p>
                      </div>
                    </div>
                  </Card>

                  <Card className="rounded-xl border bg-card p-6 shadow-sm">
                    <div className="flex items-center justify-between gap-3 mb-4">
                      <div>
                        <h3 className="font-semibold">Địa chỉ</h3>
                        <p className="text-sm text-muted-foreground">
                          Thêm địa chỉ mặc định để gợi ý nhà hàng gần bạn và tính khoảng cách.
                        </p>
                      </div>
                      <Button variant="outline" className="rounded-lg" onClick={startNewAddress}>
                        Thêm
                      </Button>
                    </div>

                    {addresses.length === 0 ? (
                      <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                        Chưa có địa chỉ nào. Hãy thêm địa chỉ để tính khoảng cách.
                      </div>
                    ) : (
                      <div className="grid gap-3">
                        {addresses.map((addr) => (
                          <div
                            key={addr.id}
                            className="flex flex-col gap-3 rounded-lg border bg-background/50 p-4"
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div className="min-w-0">
                                <div className="flex items-center gap-2">
                                  <p className="truncate font-medium">
                                    {addr.label || addr.line1 || "Địa chỉ"}
                                  </p>
                                  {addr.is_default ? (
                                    <Badge className="rounded-full bg-primary/10 text-primary border border-primary/15">
                                      Mặc định
                                    </Badge>
                                  ) : null}
                                </div>
                                <p className="mt-1 text-sm text-muted-foreground">
                                  {[addr.line1, addr.line2, addr.city].filter(Boolean).join(", ") || "—"}
                                </p>
                              </div>
                              <div className="flex gap-2">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="rounded-lg"
                                  onClick={() => startEditAddress(addr)}
                                >
                                  Sửa
                                </Button>
                                <Button
                                  variant="destructive"
                                  size="sm"
                                  className="rounded-lg"
                                  onClick={() => void removeAddress(addr.id)}
                                >
                                  Xóa
                                </Button>
                              </div>
                            </div>
                            {(addr.latitude || addr.longitude) && (
                              <p className="text-xs text-muted-foreground">
                                Tọa độ: {addr.latitude ?? "?"}, {addr.longitude ?? "?"}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="mt-6 rounded-xl border bg-muted/20 p-4">
                      <p className="text-sm font-medium mb-3">
                        {editingAddressId ? "Chỉnh sửa địa chỉ" : "Thêm địa chỉ mới"}
                      </p>
                      <div className="grid gap-4 sm:grid-cols-2">
                        <div className="space-y-2">
                          <Label>Nhãn</Label>
                          <Input
                            value={addressDraft.label ?? ""}
                            onChange={(e) => setAddressDraft((p) => ({ ...p, label: e.target.value }))}
                            placeholder="Ví dụ: Nhà, Công ty..."
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Thành phố</Label>
                          <Input
                            value={addressDraft.city ?? ""}
                            onChange={(e) => setAddressDraft((p) => ({ ...p, city: e.target.value }))}
                            placeholder="Ví dụ: TP.HCM"
                          />
                        </div>
                        <div className="space-y-2 sm:col-span-2">
                          <Label>Địa chỉ</Label>
                          <Input
                            value={addressDraft.line1 ?? ""}
                            onChange={(e) => setAddressDraft((p) => ({ ...p, line1: e.target.value }))}
                            placeholder="Số nhà, đường..."
                          />
                        </div>
                        <div className="space-y-2 sm:col-span-2">
                          <Label>Ghi chú (tùy chọn)</Label>
                          <Input
                            value={addressDraft.line2 ?? ""}
                            onChange={(e) => setAddressDraft((p) => ({ ...p, line2: e.target.value }))}
                            placeholder="Phường, quận..."
                          />
                        </div>
                      </div>

                      <div className="mt-4 flex flex-col gap-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            className="rounded-lg"
                            onClick={captureCurrentLocation}
                            disabled={locatingAddress}
                          >
                            {locatingAddress ? "Đang lấy vị trí..." : "Lấy vị trí hiện tại"}
                          </Button>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            className="rounded-lg"
                            onClick={() => void geocodeDraftAddress()}
                            disabled={geocodingAddress}
                          >
                            {geocodingAddress ? "Đang lấy tọa độ..." : "Tự lấy tọa độ"}
                          </Button>
                          <span className="text-xs text-muted-foreground">
                            {typeof addressDraft.latitude === "number" && typeof addressDraft.longitude === "number"
                              ? `Tọa độ: ${addressDraft.latitude.toFixed(6)}, ${addressDraft.longitude.toFixed(6)}`
                              : "Chưa có tọa độ"}
                          </span>
                        </div>

                        <div className="flex flex-wrap items-center gap-3">
                          <label className="flex items-center gap-2 text-sm text-muted-foreground">
                            <input
                              type="checkbox"
                              checked={Boolean(addressDraft.is_default)}
                              onChange={(e) => setAddressDraft((p) => ({ ...p, is_default: e.target.checked }))}
                            />
                            Đặt làm mặc định
                          </label>
                          <div className="ml-auto flex gap-2">
                            <Button variant="outline" className="rounded-lg" onClick={startNewAddress}>
                              Hủy
                            </Button>
                            <Button className="rounded-lg" onClick={() => void saveAddress()}>
                              Lưu
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </Card>
                </TabsContent>

                <TabsContent value="taste" className="mt-0">
                  <Card className="rounded-xl border bg-card p-6 shadow-sm">
                    <h2 className="text-lg font-semibold mb-2">Khẩu vị & Sở thích</h2>
                    <p className="text-sm text-muted-foreground mb-6">
                      Những thông tin này giúp AI gợi ý món ăn sát "gu" của bạn hơn.
                    </p>

                    <div className="grid gap-6 lg:grid-cols-2">
                      <div className="space-y-3">
                        <p className="text-sm font-medium">Sở thích</p>
                        <div className="flex flex-wrap gap-2">
                          {(
                            [
                              { key: "spicy", label: "Ăn cay" },
                              { key: "sweet", label: "Đồ ngọt" },
                              { key: "eatClean", label: "Eat clean" },
                              { key: "highProtein", label: "Nhiều đạm" },
                              { key: "lovesVeggies", label: "Thích rau" },
                            ] as const
                          ).map((item) => (
                            <Button
                              key={item.key}
                              type="button"
                              variant={tasteProfile[item.key] ? "default" : "outline"}
                              size="sm"
                              className="rounded-full"
                              onClick={() =>
                                setTasteProfile((prev) => ({ ...prev, [item.key]: !prev[item.key] }))
                              }
                            >
                              {item.label}
                            </Button>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-3">
                        <p className="text-sm font-medium">Chế độ ăn</p>
                        <div className="flex flex-wrap gap-2">
                          {(
                            [
                              { value: "normal", label: "Bình thường" },
                              { value: "vegetarian", label: "Ăn chay" },
                              { value: "keto", label: "Keto/Lowcarb" },
                            ] as const
                          ).map((item) => (
                            <Button
                              key={item.value}
                              type="button"
                              variant={tasteProfile.diet === item.value ? "default" : "outline"}
                              size="sm"
                              className="rounded-full"
                              onClick={() => setTasteProfile((prev) => ({ ...prev, diet: item.value }))}
                            >
                              {item.label}
                            </Button>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-3 lg:col-span-2">
                        <p className="text-sm font-medium text-destructive">Dị ứng (cảnh báo)</p>
                        <div className="grid gap-2 sm:grid-cols-2">
                          {(
                            [
                              { key: "seafood", label: "Hải sản" },
                              { key: "peanut", label: "Đậu phộng" },
                              { key: "milk", label: "Sữa" },
                              { key: "gluten", label: "Gluten" },
                            ] as const
                          ).map((item) => (
                            <label
                              key={item.key}
                              className="flex items-center gap-2 rounded-lg border bg-background/60 px-3 py-2 text-sm"
                            >
                              <input
                                type="checkbox"
                                checked={tasteProfile.allergies[item.key]}
                                onChange={(e) =>
                                  setTasteProfile((prev) => ({
                                    ...prev,
                                    allergies: { ...prev.allergies, [item.key]: e.target.checked },
                                  }))
                                }
                              />
                              <span>{item.label}</span>
                            </label>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-3 lg:col-span-2">
                        <p className="text-sm font-medium">Phân khúc giá</p>
                        <div className="flex flex-wrap gap-2">
                          {(
                            [
                              { value: 1, label: "Bình dân" },
                              { value: 2, label: "Trung cấp" },
                              { value: 3, label: "Sang trọng" },
                            ] as const
                          ).map((item) => (
                            <Button
                              key={item.value}
                              type="button"
                              variant={tasteProfile.priceSegment === item.value ? "default" : "outline"}
                              size="sm"
                              className="rounded-full"
                              onClick={() => setTasteProfile((prev) => ({ ...prev, priceSegment: item.value }))}
                            >
                              {item.label}
                            </Button>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-2 lg:col-span-2">
                        <Label>Ghi chú cho AI (tùy chọn)</Label>
                        <Textarea
                          value={tasteProfile.notes}
                          onChange={(e) => setTasteProfile((prev) => ({ ...prev, notes: e.target.value }))}
                          placeholder="Ví dụ: thích quán yên tĩnh, ưu tiên món ít dầu mỡ..."
                          className="min-h-[120px]"
                        />
                        <p className="text-xs text-muted-foreground">
                          Hiện tại dữ liệu này được lưu trên thiết bị của bạn (localStorage). Khi backend hỗ trợ, mình
                          sẽ đồng bộ lên server.
                        </p>
                      </div>
                    </div>
                  </Card>
                </TabsContent>

                <TabsContent value="activity" className="mt-0">
                  <Card className="rounded-xl border bg-card p-6 shadow-sm">
                    <h2 className="text-lg font-semibold mb-2">Hoạt động của bạn</h2>
                    <p className="text-sm text-muted-foreground mb-6">
                      Theo dõi các nhà hàng đã lưu và đánh giá của bạn.
                    </p>

                    <div className="grid gap-6 lg:grid-cols-2">
                      <div className="rounded-xl border bg-background/50 p-4">
                        <h3 className="font-semibold mb-2">Danh sách yêu thích</h3>
                        <p className="text-sm text-muted-foreground">
                          Tính năng lưu nhà hàng (wishlist) sẽ được bổ sung trong phiên bản tiếp theo.
                        </p>
                      </div>

                      <div className="rounded-xl border bg-background/50 p-4">
                        <div className="flex items-center justify-between gap-2 mb-3">
                          <h3 className="font-semibold">Lịch sử đánh giá</h3>
                          <Button
                            variant="outline"
                            size="sm"
                            className="rounded-lg"
                            onClick={() => void loadReviews()}
                          >
                            Tải lại
                          </Button>
                        </div>
                        {loadingReviews ? (
                          <div className="text-sm text-muted-foreground">Đang tải...</div>
                        ) : reviews.length === 0 ? (
                          <div className="text-sm text-muted-foreground">Bạn chưa có đánh giá nào.</div>
                        ) : (
                          <div className="space-y-3 max-h-[420px] overflow-auto pr-2">
                            {reviews.map((review) => (
                              <div key={review.id} className="rounded-lg border bg-card p-3">
                                <div className="flex items-start justify-between gap-2">
                                  <div className="min-w-0">
                                    <p className="truncate font-medium">
                                      {review.restaurant_name || "Nhà hàng"}
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                      {review.created_at
                                        ? new Date(review.created_at).toLocaleDateString("vi-VN")
                                        : ""}
                                    </p>
                                  </div>
                                  <Badge variant="secondary" className="rounded-full shrink-0">
                                    {review.rating}/5
                                  </Badge>
                                </div>
                                {review.title ? (
                                  <p className="mt-2 text-sm font-medium">{review.title}</p>
                                ) : null}
                                <p className="mt-1 text-sm text-muted-foreground line-clamp-3">
                                  {review.content || ""}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                </TabsContent>

                <TabsContent value="security" className="mt-0">
                  <Card className="rounded-xl border bg-card p-6 shadow-sm">
                    <h2 className="text-lg font-semibold mb-2">Bảo mật</h2>
                    <p className="text-sm text-muted-foreground mb-6">
                      Đổi mật khẩu và quản lý phiên đăng nhập.
                    </p>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2 sm:col-span-2">
                        <Label>Mật khẩu hiện tại</Label>
                        <Input
                          type="password"
                          value={currentPassword}
                          onChange={(e) => setCurrentPassword(e.target.value)}
                          placeholder="Nhập mật khẩu hiện tại"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Mật khẩu mới</Label>
                        <Input
                          type="password"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          placeholder="Mật khẩu mới"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Nhập lại mật khẩu mới</Label>
                        <Input
                          type="password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          placeholder="Nhập lại mật khẩu"
                        />
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap items-center gap-3">
                      <Button
                        onClick={() => void handleChangePassword()}
                        disabled={changingPassword}
                        className="rounded-lg"
                      >
                        <Lock className="h-4 w-4 mr-2" />
                        {changingPassword ? "Đang đổi..." : "Đổi mật khẩu"}
                      </Button>
                      <Button variant="outline" className="rounded-lg" onClick={handleLogout}>
                        <LogOut className="h-4 w-4 mr-2" />
                        Đăng xuất
                      </Button>
                    </div>

                    <div className="mt-8 rounded-xl border border-destructive/30 bg-destructive/5 p-4">
                      <div className="flex items-start gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-destructive/10 text-destructive">
                          <Shield className="h-5 w-5" />
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold text-destructive">Danger Zone</p>
                          <p className="text-sm text-muted-foreground">
                            Tính năng xóa tài khoản sẽ được bổ sung sau (cần xác thực lại).
                          </p>
                        </div>
                      </div>
                      <Button variant="destructive" className="mt-4 rounded-lg" disabled>
                        Xóa tài khoản (sắp có)
                      </Button>
                    </div>
                  </Card>
                </TabsContent>
              </div>
            </div>
          </Tabs>
        </div>
      </ScrollArea>
    </div>
  );
}
