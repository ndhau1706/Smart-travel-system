import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { User, Mail, Lock, Sparkles } from "lucide-react";
import { login, loginWithFirebase, registerStart, registerVerify, forgotPassword, resetPassword } from "../services/auth";
import type { LoginResponse } from "../services/auth";
import {
  firebaseEnabled,
  firebaseGetIdToken,
  firebaseHandleRedirectResult,
  firebaseSendPasswordReset,
  firebaseSignInEmailPassword,
  firebaseSignInGoogle,
  firebaseSignUpEmailPassword,
} from "../services/firebase";

interface AuthDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onLogin: (payload: LoginResponse) => void;
}

export function AuthDialog({ open, onOpenChange, onLogin }: AuthDialogProps) {
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerName, setRegisterName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerConfirm, setRegisterConfirm] = useState("");
  const [registerOtp, setRegisterOtp] = useState("");
  const [registerStep, setRegisterStep] = useState<"form" | "otp">("form");
  const [forgotMode, setForgotMode] = useState(false);
  const [forgotOtp, setForgotOtp] = useState("");
  const [forgotNewPass, setForgotNewPass] = useState("");
  const [forgotConfirmPass, setForgotConfirmPass] = useState("");
  const [loading, setLoading] = useState(false);
  const [info, setInfo] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!firebaseEnabled) return;
    if (!open) return;

    // Handle Google sign-in redirect (mobile fallback).
    let cancelled = false;
    const run = async () => {
      try {
        const user = await firebaseHandleRedirectResult();
        if (!user || cancelled) return;
        const idToken = await user.getIdToken();
        const payload = await loginWithFirebase(idToken);
        if (cancelled) return;
        onLogin(payload);
        onOpenChange(false);
      } catch {
        // ignore (not a redirect flow)
      }
    };

    void run();
    return () => {
      cancelled = true;
    };
  }, [open, onLogin, onOpenChange]);

  const resetMessages = () => {
    setInfo(null);
    setError(null);
  };

  const formatFirebaseError = (err: any): string => {
    const code = String(err?.code || "");
    if (code === "auth/invalid-email") return "Email không hợp lệ";
    if (code === "auth/user-not-found") return "Không tìm thấy tài khoản";
    if (code === "auth/wrong-password") return "Mật khẩu không đúng";
    if (code === "auth/invalid-credential") return "Thông tin đăng nhập không đúng";
    if (code === "auth/email-already-in-use") return "Email đã được sử dụng";
    if (code === "auth/weak-password") return "Mật khẩu quá yếu (tối thiểu 6 ký tự)";
    if (code === "auth/popup-closed-by-user") return "Bạn đã đóng cửa sổ đăng nhập";
    if (code === "auth/popup-blocked") return "Trình duyệt đang chặn popup đăng nhập";
    return err?.message || "Xác thực Firebase thất bại";
  };

  const exchangeFirebaseToBackend = async (idToken: string) => {
    const payload = await loginWithFirebase(idToken);
    onLogin(payload);
    onOpenChange(false);
  };

  const handleGoogleLogin = async () => {
    resetMessages();
    if (!firebaseEnabled) {
      setError("Firebase chưa được cấu hình.");
      return;
    }
    try {
      setLoading(true);
      const user = await firebaseSignInGoogle();
      if (!user) {
        setInfo("Đang chuyển hướng đăng nhập Google...");
        onOpenChange(false);
        return;
      }
      const idToken = await firebaseGetIdToken(user);
      await exchangeFirebaseToBackend(idToken);
    } catch (err: any) {
      setError(formatFirebaseError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();
    try {
      setLoading(true);

      if (firebaseEnabled) {
        const user = await firebaseSignInEmailPassword(loginEmail, loginPassword);
        const idToken = await firebaseGetIdToken(user);
        await exchangeFirebaseToBackend(idToken);
      } else {
        const data = await login(loginEmail, loginPassword);
        onLogin(data);
        onOpenChange(false);
      }

      setLoginEmail("");
      setLoginPassword("");
    } catch (err: any) {
      setError(firebaseEnabled ? formatFirebaseError(err) : err?.message || "Đăng nhập thất bại");
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterStart = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();
    if (registerPassword !== registerConfirm) {
      setError("Mật khẩu xác nhận không khớp");
      return;
    }

    if (firebaseEnabled) {
      try {
        setLoading(true);
        const user = await firebaseSignUpEmailPassword({
          email: registerEmail,
          password: registerPassword,
          displayName: registerName,
          sendVerificationEmail: true,
        });
        const idToken = await user.getIdToken(true);
        await exchangeFirebaseToBackend(idToken);
        setRegisterName("");
        setRegisterEmail("");
        setRegisterPassword("");
        setRegisterConfirm("");
      } catch (err: any) {
        setError(formatFirebaseError(err));
      } finally {
        setLoading(false);
      }
      return;
    }

    try {
      setLoading(true);
      await registerStart({
        email: registerEmail,
        name: registerName,
        password: registerPassword,
        confirm_password: registerConfirm,
      });
      setRegisterStep("otp");
      setInfo("Đã gửi OTP đến email của bạn");
    } catch (err: any) {
      setError(err?.message || "Gửi OTP thất bại");
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();
    try {
      setLoading(true);
      const data = await registerVerify({ email: registerEmail, otp: registerOtp });
      onLogin(data);
      onOpenChange(false);
      setRegisterStep("form");
      setRegisterOtp("");
      setRegisterName("");
      setRegisterEmail("");
      setRegisterPassword("");
      setRegisterConfirm("");
    } catch (err: any) {
      setError(err?.message || "Xác thực OTP thất bại");
    } finally {
      setLoading(false);
    }
  };

  const handleForgotSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();
    try {
      setLoading(true);

      if (firebaseEnabled) {
        await firebaseSendPasswordReset(registerEmail);
        setInfo("Đã gửi email đặt lại mật khẩu. Hãy kiểm tra hộp thư của bạn.");
        setForgotMode(false);
      } else {
        await forgotPassword(registerEmail);
        setInfo("Đã gửi OTP đặt lại mật khẩu");
        setForgotMode(true);
      }
    } catch (err: any) {
      setError(err?.message || "Gửi OTP thất bại");
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();
    if (forgotNewPass !== forgotConfirmPass) {
      setError("Mật khẩu xác nhận không khớp");
      return;
    }
    try {
      setLoading(true);
      await resetPassword({
        email: registerEmail,
        otp: forgotOtp,
        new_password: forgotNewPass,
        confirm_password: forgotConfirmPass,
      });
      setInfo("Đặt lại mật khẩu thành công, hãy đăng nhập");
      setForgotMode(false);
      setForgotOtp("");
      setForgotNewPass("");
      setForgotConfirmPass("");
    } catch (err: any) {
      setError(err?.message || "Đặt lại mật khẩu thất bại");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-center gap-2">
            <Sparkles className="h-5 w-5 text-highlight" />
            Chào mừng đến với Smart Travel
          </DialogTitle>
          <DialogDescription className="text-center text-muted-foreground">
            Đăng nhập hoặc Tạo tài khoản để khám phá ẩm thực Việt Nam
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="login" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger
              value="login"
              className="font-medium"
            >
              Đăng nhập
            </TabsTrigger>
            <TabsTrigger
              value="register"
              className="font-medium"
            >
              Đăng ký
            </TabsTrigger>
          </TabsList>

          <TabsContent value="login" className="space-y-4 mt-2">
            <form onSubmit={handleLogin} className="space-y-4">
              {firebaseEnabled && (
                <Button
                  type="button"
                  variant="outline"
                  className="w-full rounded-lg"
                  onClick={() => void handleGoogleLogin()}
                  disabled={loading}
                >
                  Đăng nhập với Google
                </Button>
              )}
              <div className="space-y-2">
                <Label htmlFor="login-email">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="login-email"
                    type="email"
                    placeholder="Email@example.com"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    className="pl-10 rounded-lg"
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="login-password">Mật khẩu</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="login-password"
                    type="password"
                    placeholder="••••••••"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    className="pl-10 rounded-lg"
                    required
                  />
                </div>
              </div>
              {!forgotMode && (
                <Button
                  type="submit"
                  className="w-full rounded-lg"
                  disabled={loading}
                >
                  <Sparkles className= "h-4 w-4 font-bold" />
                  Đăng nhập
                </Button>
              )}
              <div className="text-right text-sm">
                <button
                  type="button"
                  className="text-muted-foreground hover:text-foreground hover:underline"
                  onClick={() => {
                    setForgotMode(true);
                    resetMessages();
                  }}
                >
                  {firebaseEnabled ? "Quên mật khẩu?" : "Quên mật khẩu?"}
                </button>
              </div>
            </form>

            {forgotMode && (
              <div className="space-y-4 rounded-lg border bg-muted/40 p-4">
                <p className="font-medium">Đặt lại mật khẩu</p>
                {firebaseEnabled ? (
                  <div className="space-y-3">
                    <Label>Email</Label>
                    <Input
                      type="email"
                      value={registerEmail}
                      onChange={(e) => setRegisterEmail(e.target.value)}
                      placeholder="Email@example.com"
                      className="rounded-lg"
                      required
                    />
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        className="flex-1 rounded-lg"
                        onClick={handleForgotSendOtp}
                        disabled={loading}
                      >
                        Gửi email đặt lại
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        className="rounded-lg"
                        onClick={() => setForgotMode(false)}
                      >
                        Đóng
                      </Button>
                    </div>
                  </div>
                ) : (
                  <form onSubmit={handleResetPassword} className="space-y-3">
                    <Label>Email</Label>
                    <Input
                      type="email"
                      value={registerEmail}
                      onChange={(e) => setRegisterEmail(e.target.value)}
                      placeholder="Email@example.com"
                      className="rounded-lg"
                      required
                    />
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        className="flex-1 rounded-lg"
                        onClick={handleForgotSendOtp}
                        disabled={loading}
                      >
                        Gửi OTP
                      </Button>
                      <Input
                        type="text"
                        value={forgotOtp}
                        onChange={(e) => setForgotOtp(e.target.value)}
                        placeholder="Nhập OTP"
                        className="rounded-lg"
                        required
                      />
                    </div>
                    <Label>Mật khẩu mới</Label>
                    <Input
                      type="password"
                      value={forgotNewPass}
                      onChange={(e) => setForgotNewPass(e.target.value)}
                      placeholder="Mật khẩu mới"
                      className="rounded-lg"
                      required
                    />
                    <Input
                      type="password"
                      value={forgotConfirmPass}
                      onChange={(e) => setForgotConfirmPass(e.target.value)}
                      placeholder="Xác nhận mật khẩu"
                      className="rounded-lg"
                      required
                    />
                    <div className="flex gap-2">
                      <Button
                        type="submit"
                        className="flex-1 rounded-lg"
                        disabled={loading}
                      >
                        Đặt lại mật khẩu
                      </Button>
                      <Button type="button" variant="outline" className="rounded-lg" onClick={() => setForgotMode(false)}>
                        Đóng
                      </Button>
                    </div>
                  </form>
                )}
              </div>
            )}
          </TabsContent>

          <TabsContent value="register" className="space-y-4 mt-2">
            {firebaseEnabled ? (
              <form onSubmit={handleRegisterStart} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="register-name">Tên hiển thị</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="register-name"
                      type="text"
                      placeholder="Nguyễn Văn A"
                      value={registerName}
                      onChange={(e) => setRegisterName(e.target.value)}
                      className="pl-10 rounded-lg"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-email">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="register-email"
                      type="email"
                      placeholder="Email@example.com"
                      value={registerEmail}
                      onChange={(e) => setRegisterEmail(e.target.value)}
                      className="pl-10 rounded-lg"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-password">Mật khẩu</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="register-password"
                      type="password"
                      placeholder="••••••••"
                      value={registerPassword}
                      onChange={(e) => setRegisterPassword(e.target.value)}
                      className="pl-10 rounded-lg"
                      required
                    />
                  </div>
                </div>
                <Input
                  type="password"
                  placeholder="Xác nhận mật khẩu"
                  value={registerConfirm}
                  onChange={(e) => setRegisterConfirm(e.target.value)}
                  className="rounded-lg"
                  required
                />
                <Button
                  type="submit"
                  className="w-full rounded-lg"
                  disabled={loading}
                >
                  <Sparkles className="h-4 w-4" />
                  Đăng ký
                </Button>
                <p className="text-xs text-muted-foreground">
                  Firebase sẽ gửi email xác minh (nếu được bật trong project).
                </p>
              </form>
            ) : (
              <>
                {registerStep === "form" ? (
                  <form onSubmit={handleRegisterStart} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="register-name">Tên hiển thị</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="register-name"
                          type="text"
                          placeholder="Nguyễn Văn A"
                          value={registerName}
                          onChange={(e) => setRegisterName(e.target.value)}
                          className="pl-10 rounded-lg"
                          required
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="register-email">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="register-email"
                          type="email"
                          placeholder="Email@example.com"
                          value={registerEmail}
                          onChange={(e) => setRegisterEmail(e.target.value)}
                          className="pl-10 rounded-lg"
                          required
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="register-password">Mật khẩu</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="register-password"
                          type="password"
                          placeholder="••••••••"
                          value={registerPassword}
                          onChange={(e) => setRegisterPassword(e.target.value)}
                          className="pl-10 rounded-lg"
                          required
                        />
                      </div>
                    </div>
                    <Input
                      type="password"
                      placeholder="Xác nhận mật khẩu"
                      value={registerConfirm}
                      onChange={(e) => setRegisterConfirm(e.target.value)}
                      className="rounded-lg"
                      required
                    />
                    <Button
                      type="submit"
                      className="w-full rounded-lg"
                      disabled={loading}
                    >
                      <Sparkles className="h-4 w-4" />
                      Gửi OTP
                    </Button>
                  </form>
                ) : (
                  <form onSubmit={handleRegisterVerify} className="space-y-4">
                    <p className="text-sm text-muted-foreground">Nhập OTP đã gửi tới {registerEmail}</p>
                    <Input
                      type="text"
                      placeholder="Mã OTP"
                      value={registerOtp}
                      onChange={(e) => setRegisterOtp(e.target.value)}
                      className="rounded-lg"
                      required
                    />
                    <div className="flex gap-2">
                      <Button
                        type="submit"
                        className="flex-1 rounded-lg"
                        disabled={loading}
                      >
                        Xác thực
                      </Button>
                      <Button
                        type="button"
                        variant="secondary"
                        className="rounded-lg"
                        onClick={() => setRegisterStep("form")}
                      >
                        Quay lại
                      </Button>
                    </div>
                  </form>
                )}
              </>
            )}
          </TabsContent>
        </Tabs>

        {(info || error) && (
          <div
            className={`text-sm rounded-xl border px-3 py-2 ${
              info ? "bg-green-50 border-green-200 text-green-700" : "bg-red-50 border-red-200 text-red-700"
            }`}
          >
            {info || error}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
