import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { User, Mail, Lock, Sparkles } from "lucide-react";

interface AuthDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onLogin: (email: string, name: string) => void;
}

export function AuthDialog({ open, onOpenChange, onLogin }: AuthDialogProps) {
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerName, setRegisterName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (loginEmail && loginPassword) {
      // Mock login - in real app, validate against backend
      const name = loginEmail.split("@")[0];
      onLogin(loginEmail, name);
      onOpenChange(false);
      // Reset form
      setLoginEmail("");
      setLoginPassword("");
    }
  };

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    if (registerName && registerEmail && registerPassword) {
      // Mock registration - in real app, create account in backend
      onLogin(registerEmail, registerName);
      onOpenChange(false);
      // Reset form
      setRegisterName("");
      setRegisterEmail("");
      setRegisterPassword("");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent 
        className="sm:max-w-[425px] bg-gradient-to-br from-pink-50 via-purple-50 to-fuchsia-50 border-2 border-pink-300 shadow-2xl rounded-3xl"
        style={{ boxShadow: '0 0 40px rgba(255,182,193,0.5), inset 0 0 30px rgba(255,255,255,0.5)' }}
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-pink-700">
            <Sparkles className="h-5 w-5" />
            Chào mừng đến với Cosmic Food
          </DialogTitle>
          <DialogDescription className="text-pink-600">
            Đăng nhập hoặc tạo tài khoản để bắt đầu khám phá ẩm thực Việt Nam
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="login" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-pink-200/50">
            <TabsTrigger 
              value="login"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-pink-300 data-[state=active]:to-rose-300 data-[state=active]:text-white rounded-xl"
            >
              Đăng nhập
            </TabsTrigger>
            <TabsTrigger 
              value="register"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-pink-300 data-[state=active]:to-rose-300 data-[state=active]:text-white rounded-xl"
            >
              Đăng ký
            </TabsTrigger>
          </TabsList>

          <TabsContent value="login" className="space-y-4 mt-4">
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="login-email" className="text-pink-700">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-pink-400" />
                  <Input
                    id="login-email"
                    type="email"
                    placeholder="email@example.com"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    className="pl-10 bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="login-password" className="text-pink-700">Mật khẩu</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-pink-400" />
                  <Input
                    id="login-password"
                    type="password"
                    placeholder="••••••••"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    className="pl-10 bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                    required
                  />
                </div>
              </div>
              <Button
                type="submit"
                className="w-full bg-gradient-to-r from-pink-400 via-rose-400 to-fuchsia-400 hover:from-pink-300 hover:via-rose-300 hover:to-fuchsia-300 text-white shadow-xl rounded-2xl border-2 border-pink-200"
                style={{ boxShadow: '0 0 20px rgba(255,182,193,0.5)' }}
              >
                <Sparkles className="mr-2 h-4 w-4" />
                Đăng nhập
              </Button>
            </form>
          </TabsContent>

          <TabsContent value="register" className="space-y-4 mt-4">
            <form onSubmit={handleRegister} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="register-name" className="text-pink-700">Tên</Label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-pink-400" />
                  <Input
                    id="register-name"
                    type="text"
                    placeholder="Nguyễn Văn A"
                    value={registerName}
                    onChange={(e) => setRegisterName(e.target.value)}
                    className="pl-10 bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="register-email" className="text-pink-700">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-pink-400" />
                  <Input
                    id="register-email"
                    type="email"
                    placeholder="email@example.com"
                    value={registerEmail}
                    onChange={(e) => setRegisterEmail(e.target.value)}
                    className="pl-10 bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="register-password" className="text-pink-700">Mật khẩu</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-pink-400" />
                  <Input
                    id="register-password"
                    type="password"
                    placeholder="••••••••"
                    value={registerPassword}
                    onChange={(e) => setRegisterPassword(e.target.value)}
                    className="pl-10 bg-white/80 border-2 border-pink-300 focus:border-pink-400 rounded-2xl"
                    required
                  />
                </div>
              </div>
              <Button
                type="submit"
                className="w-full bg-gradient-to-r from-pink-400 via-rose-400 to-fuchsia-400 hover:from-pink-300 hover:via-rose-300 hover:to-fuchsia-300 text-white shadow-xl rounded-2xl border-2 border-pink-200"
                style={{ boxShadow: '0 0 20px rgba(255,182,193,0.5)' }}
              >
                <Sparkles className="mr-2 h-4 w-4" />
                Tạo tài khoản
              </Button>
            </form>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
