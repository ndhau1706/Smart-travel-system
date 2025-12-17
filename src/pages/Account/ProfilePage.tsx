import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  ArrowLeft,
  Image as ImageIcon,
  LocateFixed,
  Mail,
  MapPin,
  Pencil,
  Phone,
  Plus,
  Save,
  Trash2,
  User as UserIcon,
} from "lucide-react";

import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Badge } from "../../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../../components/ui/dialog";
import { Switch } from "../../components/ui/switch";
import { Avatar, AvatarFallback, AvatarImage } from "../../components/ui/avatar";
import {
  createAddress,
  deleteAddress,
  getProfile,
  listAddresses,
  refreshSession,
  uploadAvatar,
  updateAddress,
  updateProfile,
} from "../../services/auth";
import type { AddressUpsert, AuthUser, UserAddress } from "../../services/auth";

type StoredAuth = {
  user?: { email?: string; name?: string; avatar?: string | null };
  accessToken?: string;
  refreshToken?: string;
  expiresIn?: number;
  access_token?: string;
  refresh_token?: string;
  expires_in?: number;
};

function readStoredAuth(): StoredAuth | null {
  const stored = localStorage.getItem("auth");
  if (!stored) return null;
  try {
    return JSON.parse(stored) as StoredAuth;
  } catch {
    return null;
  }
}

function writeStoredAuth(next: StoredAuth) {
  localStorage.setItem("auth", JSON.stringify(next));
}

function isUnauthorized(err: unknown): boolean {
  const msg = String((err as any)?.message || "");
  return msg.includes("(401)") || msg.toLowerCase().includes("unauthorized");
}

export function ProfilePage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [needsLogin, setNeedsLogin] = useState(false);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);

  const [addresses, setAddresses] = useState<UserAddress[]>([]);
  const [addressesLoading, setAddressesLoading] = useState(false);
  const [addressDialogOpen, setAddressDialogOpen] = useState(false);
  const [addressSaving, setAddressSaving] = useState(false);
  const [addressDeletingId, setAddressDeletingId] = useState<string | null>(null);
  const [editingAddress, setEditingAddress] = useState<UserAddress | null>(null);

  const [form, setForm] = useState(() => {
    const stored = readStoredAuth();
    return {
      name: stored?.user?.name || "",
      phone: "",
      avatar: stored?.user?.avatar || "",
    };
  });

  const avatarInputRef = useRef<HTMLInputElement | null>(null);

  const storedAuth = useMemo(() => readStoredAuth(), []);
  const registeredEmail = profile?.email || storedAuth?.user?.email || "-";

  const avatarPreview = form.avatar;
  const avatarIsDataUrl = avatarPreview.startsWith("data:image/");

  const [addressForm, setAddressForm] = useState({
    label: "Nhà",
    line1: "",
    line2: "",
    city: "",
    latitude: "",
    longitude: "",
    is_default: true,
  });

  const tryRefresh = async (): Promise<boolean> => {
    const current = readStoredAuth();
    const refreshToken = current?.refreshToken || current?.refresh_token;
    if (!refreshToken) return false;

    try {
      const tokens = await refreshSession(refreshToken);
      writeStoredAuth({
        ...(current || {}),
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        expiresIn: tokens.expires_in,
      });
      return true;
    } catch (err: any) {
      toast.error(err?.message || "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại");
      return false;
    }
  };

  const syncStoredUser = (user: AuthUser) => {
    const current = readStoredAuth();
    if (!current) return;
    const next = { ...current, user: { ...(current.user || {}), ...user } };
    writeStoredAuth(next);
    window.dispatchEvent(new CustomEvent("auth:updated", { detail: { user } }));
  };

  const loadAddresses = async (attemptRefresh = true) => {
    setAddressesLoading(true);
    try {
      const data = await listAddresses();
      const sorted = [...(Array.isArray(data) ? data : [])].sort((a, b) => {
        const ad = a?.is_default ? 1 : 0;
        const bd = b?.is_default ? 1 : 0;
        return bd - ad;
      });
      setAddresses(sorted);
    } catch (err: any) {
      if (attemptRefresh && isUnauthorized(err) && (await tryRefresh())) {
        await loadAddresses(false);
        return;
      }
      toast.error(err?.message || "Không tải được danh sách địa chỉ");
    } finally {
      setAddressesLoading(false);
    }
  };

  useEffect(() => {
    const stored = readStoredAuth();
    if (!stored) {
      setNeedsLogin(true);
      setLoading(false);
      return;
    }

    const load = async (attemptRefresh = true) => {
      try {
        const data = await getProfile();
        setProfile(data);
        setForm({
          name: data.name || "",
          phone: data.phone || "",
          avatar: data.avatar || "",
        });
        syncStoredUser(data);
        await loadAddresses(attemptRefresh);
      } catch (err: any) {
        if (attemptRefresh && isUnauthorized(err) && (await tryRefresh())) {
          await load(false);
          return;
        }

        if (isUnauthorized(err)) {
          setNeedsLogin(true);
        }
        toast.error(err?.message || "Không tải được hồ sơ");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const handleSave = async () => {
    try {
      setSaving(true);

      // 1) Update basic profile fields + avatar URL (if user pasted a URL)
      const avatarUrlPayload =
        avatarFile || avatarIsDataUrl
          ? undefined
          : form.avatar.trim()
            ? form.avatar.trim()
            : null;

      await updateProfile({
        name: form.name.trim() || undefined,
        phone: form.phone.trim() || undefined,
        avatar: avatarUrlPayload,
      });

      // 2) If user selected a local file, upload it and let backend persist avatar URL.
      let latest = await getProfile();
      if (avatarFile) {
        latest = await uploadAvatar(avatarFile);
        setAvatarFile(null);
      }

      setProfile(latest);
      setForm({
        name: latest.name || "",
        phone: latest.phone || "",
        avatar: latest.avatar || "",
      });
      syncStoredUser(latest);
      toast.success("Cập nhật hồ sơ thành công");
    } catch (err: any) {
      toast.error(err?.message || "Cập nhật thất bại");
    } finally {
      setSaving(false);
    }
  };

  const handlePickAvatar = () => avatarInputRef.current?.click();

  const handleAvatarFileChange = async (file: File | null) => {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      toast.error("Vui lòng chọn đúng định dạng ảnh");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      toast.error("Ảnh quá lớn (tối đa 2MB)");
      return;
    }

    try {
      setAvatarFile(file);
      const dataUrl = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ""));
        reader.onerror = () => reject(new Error("Không đọc được file ảnh"));
        reader.readAsDataURL(file);
      });
      setForm((prev) => ({ ...prev, avatar: dataUrl }));
    } catch (err: any) {
      toast.error(err?.message || "Không đọc được ảnh");
    }
  };

  const openAddAddress = () => {
    setEditingAddress(null);
    setAddressForm({
      label: "Nhà",
      line1: "",
      line2: "",
      city: "",
      latitude: "",
      longitude: "",
      is_default: addresses.length === 0,
    });
    setAddressDialogOpen(true);
  };

  const openEditAddress = (addr: UserAddress) => {
    setEditingAddress(addr);
    setAddressForm({
      label: addr.label || "Nhà",
      line1: addr.line1 || "",
      line2: addr.line2 || "",
      city: addr.city || "",
      latitude: addr.latitude !== null && addr.latitude !== undefined ? String(addr.latitude) : "",
      longitude: addr.longitude !== null && addr.longitude !== undefined ? String(addr.longitude) : "",
      is_default: Boolean(addr.is_default),
    });
    setAddressDialogOpen(true);
  };

  const getCurrentLocation = async () => {
    if (!("geolocation" in navigator)) {
      toast.error("Trình duyệt không hỗ trợ định vị");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setAddressForm((prev) => ({
          ...prev,
          latitude: String(pos.coords.latitude),
          longitude: String(pos.coords.longitude),
        }));
      },
      () => {
        toast.error("Không lấy được vị trí. Hãy cho phép quyền định vị.");
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  };

  const saveAddress = async () => {
    const payload: AddressUpsert = {
      label: addressForm.label.trim() || null,
      line1: addressForm.line1.trim() || null,
      line2: addressForm.line2.trim() || null,
      city: addressForm.city.trim() || null,
      latitude: addressForm.latitude.trim() ? Number(addressForm.latitude.trim()) : null,
      longitude: addressForm.longitude.trim() ? Number(addressForm.longitude.trim()) : null,
      is_default: addressForm.is_default,
    };

    if (payload.latitude !== null && Number.isNaN(payload.latitude)) {
      toast.error("Vĩ độ (latitude) không hợp lệ");
      return;
    }
    if (payload.longitude !== null && Number.isNaN(payload.longitude)) {
      toast.error("Kinh độ (longitude) không hợp lệ");
      return;
    }

    if (!payload.line1 && !payload.city) {
      toast.error("Vui lòng nhập địa chỉ (ít nhất Line 1 hoặc Thành phố)");
      return;
    }

    setAddressSaving(true);
    try {
      if (editingAddress?.id) {
        await updateAddress(editingAddress.id, payload);
        toast.success("Đã cập nhật địa chỉ");
      } else {
        await createAddress(payload);
        toast.success("Đã thêm địa chỉ");
      }
      setAddressDialogOpen(false);
      await loadAddresses();
    } catch (err: any) {
      if (isUnauthorized(err)) setNeedsLogin(true);
      toast.error(err?.message || "Không lưu được địa chỉ");
    } finally {
      setAddressSaving(false);
    }
  };

  const setDefaultAddress = async (addr: UserAddress) => {
    if (!addr?.id) return;
    setAddressSaving(true);
    try {
      await updateAddress(addr.id, {
        label: addr.label ?? null,
        line1: addr.line1 ?? null,
        line2: addr.line2 ?? null,
        city: addr.city ?? null,
        latitude: addr.latitude ?? null,
        longitude: addr.longitude ?? null,
        is_default: true,
      });
      toast.success("Đã đặt địa chỉ mặc định");
      await loadAddresses();
    } catch (err: any) {
      toast.error(err?.message || "Không đặt được mặc định");
    } finally {
      setAddressSaving(false);
    }
  };

  const removeAddress = async (addr: UserAddress) => {
    if (!addr?.id) return;
    setAddressDeletingId(addr.id);
    try {
      await deleteAddress(addr.id);
      toast.success("Đã xóa địa chỉ");
      await loadAddresses();
    } catch (err: any) {
      toast.error(err?.message || "Không xóa được địa chỉ");
    } finally {
      setAddressDeletingId(null);
    }
  };

  return (
    <div className="h-full overflow-y-auto px-4 sm:px-6 lg:px-10 py-8 pb-24">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate(-1)}
              className="rounded-2xl hover:bg-pink-100 text-pink-700"
              aria-label="Quay lại"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-pink-800">Hồ sơ</h1>
              <p className="text-sm text-pink-600">
                Quản lý thông tin tài khoản của bạn
              </p>
            </div>
          </div>
          <Button
            onClick={handleSave}
            disabled={saving || loading || needsLogin}
            className="bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 text-white rounded-2xl shadow-xl border-2 border-pink-200"
            style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
          >
            <Save className="h-4 w-4" />
            {saving ? "Đang lưu..." : "LƯU"}
          </Button>
        </div>

        <Card className="bg-gradient-to-br from-pink-50/90 via-purple-50/90 to-fuchsia-50/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl shadow-2xl">
          <CardHeader className="border-b border-pink-200/60">
            <CardTitle className="text-pink-800 font-bold flex items-center gap-2">
              <UserIcon className="h-5 w-5 text-pink-500" />
              Thông tin cá nhân
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            {needsLogin ? (
              <div className="space-y-3">
                <p className="text-sm text-pink-600">
                  Bạn cần đăng nhập để xem/chỉnh sửa hồ sơ.
                </p>
                {registeredEmail !== "-" && (
                  <div className="text-sm text-gray-800">
                    Email đăng ký: <span className="font-medium">{registeredEmail}</span>
                  </div>
                )}
                <Button
                  onClick={() => navigate("/")}
                  className="bg-gradient-to-r from-pink-400 to-rose-400 text-white rounded-2xl border-2 border-pink-200"
                >
                  Về trang chủ
                </Button>
              </div>
            ) : loading ? (
              <div className="text-pink-600">Đang tải...</div>
            ) : (
              <>
                <div className="flex items-start gap-4">
                  <div className="flex flex-col items-center gap-2">
                    <Avatar className="h-20 w-20 border-2 border-pink-200 shadow-lg">
                      {avatarPreview ? (
                        <AvatarImage src={avatarPreview} alt={form.name || "Avatar"} />
                      ) : null}
                      <AvatarFallback className="bg-gradient-to-br from-pink-400 to-rose-400 text-white text-xl">
                        {(form.name || profile?.name || "U")
                          .trim()
                          .split(" ")
                          .map((n) => n[0])
                          .join("")
                          .toUpperCase()
                          .slice(0, 2)}
                      </AvatarFallback>
                    </Avatar>

                    <input
                      ref={avatarInputRef}
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0] || null;
                        void handleAvatarFileChange(file);
                        e.target.value = "";
                      }}
                    />

                    <div className="flex flex-wrap gap-2 justify-center">
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={handlePickAvatar}
                        className="rounded-2xl bg-white border border-pink-200 hover:bg-pink-50"
                      >
                        <ImageIcon className="h-4 w-4" />
                        Tải ảnh
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={() => {
                          setAvatarFile(null);
                          setForm((p) => ({ ...p, avatar: "" }));
                        }}
                        className="rounded-2xl text-pink-700 hover:bg-pink-100"
                        disabled={!avatarPreview}
                      >
                        Xóa
                      </Button>
                    </div>
                    {avatarIsDataUrl && (
                      <p className="text-xs text-pink-600 text-center max-w-[14rem]">
                        Ảnh đang dùng là ảnh bạn tải lên. Nhấn “Lưu” để upload và cập nhật avatar (hoặc dán URL ảnh bên dưới).
                      </p>
                    )}
                  </div>

                  <div className="flex-1 space-y-3">
                    <div className="space-y-2">
                      <Label className="text-pink-700">Avatar URL (tuỳ chọn)</Label>
                      <Input
                        value={avatarIsDataUrl ? "" : form.avatar}
                        onChange={(e) => {
                          setAvatarFile(null);
                          setForm((prev) => ({ ...prev, avatar: e.target.value }));
                        }}
                        placeholder="https://... hoặc để trống"
                        className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                      />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-pink-700 flex items-center gap-2">
                      <Mail className="h-4 w-4 text-pink-400" />
                      Email
                    </Label>
                    <div className="bg-white/70 border-2 border-pink-200 rounded-2xl px-3 py-2 text-gray-800 h-10 flex items-center">
                      {registeredEmail}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-pink-700 flex items-center gap-2">
                      <Phone className="h-4 w-4 text-pink-400" />
                      Số điện thoại
                    </Label>
                    <Input
                      value={form.phone}
                      onChange={(e) =>
                        setForm((prev) => ({ ...prev, phone: e.target.value }))
                      }
                      placeholder="Ví dụ: 0912..."
                      className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-pink-700">Họ tên</Label>
                  <Input
                    value={form.name}
                    onChange={(e) =>
                      setForm((prev) => ({ ...prev, name: e.target.value }))
                    }
                    placeholder="Nhập họ tên"
                    className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                  />
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-pink-50/90 via-purple-50/90 to-fuchsia-50/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl shadow-2xl">
          <CardHeader className="border-b border-pink-200/60 flex flex-row items-center justify-between">
            <CardTitle className="text-pink-800 font-bold flex items-center gap-2">
              <MapPin className="h-5 w-5 text-pink-500" />
              Địa chỉ
            </CardTitle>
            <Button
              type="button"
              onClick={openAddAddress}
              disabled={needsLogin}
              className="bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 text-white rounded-2xl shadow-xl border-2 border-pink-200"
              style={{ boxShadow: "0 0 20px rgba(255,182,193,0.35)" }}
            >
              <Plus className="h-4 w-4 mb-1" />
              THÊM
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className=" text-pink-600">
              Đặt <b>địa chỉ mặc định</b> và thêm <b>tọa độ (latitude/longitude)</b> để hệ thống có thể đề xuất quán gần bạn và tính khoảng cách.
            </p>

            {needsLogin ? (
              <div className=" text-pink-600">Bạn cần đăng nhập để quản lý địa chỉ.</div>
            ) : addressesLoading ? (
              <div className="text-pink-600">Đang tải địa chỉ...</div>
            ) : addresses.length === 0 ? (
              <div className="text-pink-600">Chưa có địa chỉ nào. Hãy thêm địa chỉ để tính khoảng cách.</div>
            ) : (
              <div className="space-y-3">
                {addresses.map((addr) => (
                  <div
                    key={addr.id}
                    className="bg-white/70 border-2 border-pink-200 rounded-2xl p-4 flex flex-col gap-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-gray-800 font-medium truncate">
                            {addr.label || "Địa chỉ"}
                          </p>
                          {addr.is_default ? (
                            <Badge className="bg-gradient-to-r from-pink-300 to-rose-300 text-white border-0 rounded-full">
                              Mặc định
                            </Badge>
                          ) : null}
                        </div>
                        <p className="text-sm text-gray-700 break-words">
                          {[addr.line1, addr.line2, addr.city].filter(Boolean).join(", ") || "—"}
                        </p>
                        <p className="text-xs text-pink-600 mt-1">
                          Tọa độ:{" "}
                          {addr.latitude !== null && addr.latitude !== undefined && addr.longitude !== null && addr.longitude !== undefined
                            ? `${addr.latitude}, ${addr.longitude}`
                            : "Chưa có"}
                        </p>
                      </div>

                      <div className="flex items-center gap-2 flex-wrap justify-end">
                        {!addr.is_default && (
                          <Button
                            type="button"
                            variant="secondary"
                            className="bg-white border border-pink-200 rounded-2xl"
                            onClick={() => void setDefaultAddress(addr)}
                            disabled={addressSaving}
                          >
                            Đặt mặc định
                          </Button>
                        )}
                        <Button
                          type="button"
                          variant="ghost"
                          className="rounded-2xl hover:bg-pink-100 text-pink-700"
                          onClick={() => openEditAddress(addr)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          className="rounded-2xl hover:bg-red-100 text-red-600"
                          onClick={() => void removeAddress(addr)}
                          disabled={addressDeletingId === addr.id}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog open={addressDialogOpen} onOpenChange={setAddressDialogOpen}>
        <DialogContent className="sm:max-w-[520px] bg-gradient-to-br from-pink-50 via-purple-50 to-fuchsia-50 border-2 border-pink-300 shadow-2xl rounded-3xl">
          <DialogHeader>
            <DialogTitle className="text-pink-800">
              {editingAddress ? "Sửa địa chỉ" : "Thêm địa chỉ"}
            </DialogTitle>
            <DialogDescription className="text-pink-600">
              Gợi ý: nhấn “Lấy vị trí hiện tại” để tự điền tọa độ (dùng tính khoảng cách).
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-pink-700">Nhãn</Label>
                <Input
                  value={addressForm.label}
                  onChange={(e) => setAddressForm((p) => ({ ...p, label: e.target.value }))}
                  placeholder="Nhà / Công ty / ..."
                  className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-pink-700">Thành phố</Label>
                <Input
                  value={addressForm.city}
                  onChange={(e) => setAddressForm((p) => ({ ...p, city: e.target.value }))}
                  placeholder="TP.HCM / Hà Nội / ..."
                  className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-pink-700">Line 1</Label>
              <Input
                value={addressForm.line1}
                onChange={(e) => setAddressForm((p) => ({ ...p, line1: e.target.value }))}
                placeholder="Số nhà, đường..."
                className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-pink-700">Line 2 (tuỳ chọn)</Label>
              <Input
                value={addressForm.line2}
                onChange={(e) => setAddressForm((p) => ({ ...p, line2: e.target.value }))}
                placeholder="Phường/Xã, Quận/Huyện..."
                className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-pink-700">Latitude</Label>
                <Input
                  value={addressForm.latitude}
                  onChange={(e) => setAddressForm((p) => ({ ...p, latitude: e.target.value }))}
                  placeholder="10.7..."
                  className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                  inputMode="decimal"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-pink-700">Longitude</Label>
                <Input
                  value={addressForm.longitude}
                  onChange={(e) => setAddressForm((p) => ({ ...p, longitude: e.target.value }))}
                  placeholder="106.6..."
                  className="bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                  inputMode="decimal"
                />
              </div>
            </div>

            <div className="flex items-center justify-between gap-3 flex-wrap">
              <Button
                type="button"
                variant="secondary"
                onClick={() => void getCurrentLocation()}
                className="bg-white border border-pink-200 rounded-2xl"
              >
                <LocateFixed className="h-4 w-4" />
                Lấy vị trí hiện tại
              </Button>

              <div className="flex items-center gap-2">
                <Switch
                  checked={addressForm.is_default}
                  onCheckedChange={(checked) => setAddressForm((p) => ({ ...p, is_default: checked }))}
                />
                <span className="text-sm text-pink-700">Đặt làm mặc định</span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setAddressDialogOpen(false)}
                className="rounded-2xl text-pink-700 hover:bg-pink-100"
              >
                Hủy
              </Button>
              <Button
                type="button"
                onClick={() => void saveAddress()}
                disabled={addressSaving}
                className="bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 text-white rounded-2xl shadow-xl border-2 border-pink-200"
                style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
              >
                <Save className="h-4 w-4" />
                {addressSaving ? "Đang lưu..." : "Lưu"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
