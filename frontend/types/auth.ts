export interface User {
  id: number;
  username: string;
  email: string | null;
  full_name: string | null;
  is_active: boolean;
  roles: string[];
}

export interface LoginResponse { access_token: string; token_type: string }
export interface PermissionSummary {
  user_id: number;
  username: string;
  roles: string[];
  effective_permissions: string[];
}
export interface AuthState {
  user: User | null;
  permissions: PermissionSummary | null;
  loading: boolean;
  authenticated: boolean;
}
