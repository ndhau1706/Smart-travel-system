/**
 * React Query hooks for authentication
 * Integrates with Zustand auth store
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queryKeys, invalidateQueries } from '../lib/queryClient';
import { useAuthStore, useAuthActions } from '../stores/authStore';
import {
  login as loginApi,
  registerStart,
  registerVerify,
  forgotPassword,
  resetPassword,
  LoginResponse,
} from '../services/auth';
import { toast } from '../stores/uiStore';

/**
 * Hook for login mutation
 */
export function useLogin() {
  const { login } = useAuthActions();
  
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      loginApi(email, password),
    onSuccess: (data) => {
      login(data);
      toast.success('Đăng nhập thành công', `Chào mừng ${data.user.name}!`);
    },
    onError: (error: Error) => {
      toast.error('Đăng nhập thất bại', error.message);
    },
  });
}

/**
 * Hook for registration start (send OTP)
 */
export function useRegisterStart() {
  return useMutation({
    mutationFn: (payload: {
      email: string;
      name: string;
      password: string;
      confirm_password: string;
    }) => registerStart(payload),
    onSuccess: () => {
      toast.success('Đã gửi mã OTP', 'Vui lòng kiểm tra email của bạn');
    },
    onError: (error: Error) => {
      toast.error('Đăng ký thất bại', error.message);
    },
  });
}

/**
 * Hook for registration verify (verify OTP)
 */
export function useRegisterVerify() {
  const { login } = useAuthActions();
  
  return useMutation({
    mutationFn: (payload: { email: string; otp: string }) =>
      registerVerify(payload),
    onSuccess: (data) => {
      login(data);
      toast.success('Đăng ký thành công', 'Tài khoản của bạn đã được xác thực');
    },
    onError: (error: Error) => {
      toast.error('Xác thực thất bại', error.message);
    },
  });
}

/**
 * Hook for forgot password
 */
export function useForgotPassword() {
  return useMutation({
    mutationFn: (email: string) => forgotPassword(email),
    onSuccess: () => {
      toast.success('Đã gửi mã OTP', 'Vui lòng kiểm tra email để đặt lại mật khẩu');
    },
    onError: (error: Error) => {
      toast.error('Gửi OTP thất bại', error.message);
    },
  });
}

/**
 * Hook for reset password
 */
export function useResetPassword() {
  return useMutation({
    mutationFn: (payload: {
      email: string;
      otp: string;
      new_password: string;
      confirm_password: string;
    }) => resetPassword(payload),
    onSuccess: () => {
      toast.success('Đặt lại mật khẩu thành công', 'Bạn có thể đăng nhập với mật khẩu mới');
    },
    onError: (error: Error) => {
      toast.error('Đặt lại mật khẩu thất bại', error.message);
    },
  });
}

/**
 * Hook for logout
 */
export function useLogout() {
  const { logout } = useAuthActions();
  const queryClient = useQueryClient();
  
  return () => {
    logout();
    // Clear all cached data on logout
    queryClient.clear();
    toast.info('Đã đăng xuất', 'Hẹn gặp lại bạn!');
  };
}

/**
 * Hook to check if user is authenticated
 */
export function useIsAuthenticated() {
  return useAuthStore((state) => state.isAuthenticated);
}

/**
 * Hook to get current user
 */
export function useCurrentUser() {
  return useAuthStore((state) => state.user);
}

/**
 * Hook to get access token
 */
export function useAccessToken() {
  return useAuthStore((state) => state.accessToken);
}

