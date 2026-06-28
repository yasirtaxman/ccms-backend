"use client";

import { useState } from "react";
import { Eye, EyeOff, KeyRound, LogOut, UserRound, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { apiErrorMessage, changePassword } from "@/lib/api";

export function UserMenu() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [openPassword, setOpenPassword] = useState(false);
  const leave = () => {
    logout();
    router.replace("/login");
  };
  return (
    <>
      <details className="relative">
        <summary className="flex cursor-pointer list-none items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2 hover:bg-slate-50">
          <div className="grid size-9 place-items-center rounded-full bg-blue-100 text-blue-700"><UserRound size={18} /></div>
          <div className="hidden text-left sm:block">
            <div className="text-sm font-semibold text-slate-800">{user?.username}</div>
            <div className="max-w-40 truncate text-xs text-slate-500">{user?.roles.join(", ")}</div>
          </div>
        </summary>
        <div className="absolute right-0 z-40 mt-2 w-64 rounded-xl border border-slate-200 bg-white p-2 shadow-xl">
          <div className="border-b border-slate-100 px-3 py-2">
            <p className="text-sm font-semibold">{user?.full_name || user?.username || "System Administrator"}</p>
            <p className="text-xs text-slate-500">{user?.roles.join(" • ") || "Role not recorded"}</p>
          </div>
          <button onClick={() => setOpenPassword(true)} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
            <KeyRound size={16} />
            Change Password
          </button>
          <button onClick={leave} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50">
            <LogOut size={16} />
            Log out
          </button>
        </div>
      </details>
      {openPassword && <ChangePasswordModal onClose={() => setOpenPassword(false)} onLogout={leave} />}
    </>
  );
}

function ChangePasswordModal({ onClose, onLogout }: { onClose: () => void; onLogout: () => void }) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [show, setShow] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const validate = () => {
    if (!currentPassword) return "Current password is required.";
    if (!newPassword) return "New password is required.";
    if (!confirmPassword) return "Confirm new password is required.";
    if (newPassword.length < 8) return "New password must be at least 8 characters.";
    if (newPassword !== confirmPassword) return "New password and confirm password must match.";
    if (newPassword === currentPassword) return "New password must be different from current password.";
    return "";
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    const message = validate();
    if (message) {
      setError(message);
      return;
    }
    setSubmitting(true);
    try {
      await changePassword(currentPassword, newPassword);
      setSuccess("Password changed successfully.");
      window.setTimeout(onLogout, 900);
    } catch (e) {
      const message = apiErrorMessage(e);
      setError(message.includes("Password") ? message : "Unable to change password. Please check your current password.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4">
      <form onSubmit={submit} className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl" noValidate>
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Change Password</h2>
            <p className="mt-1 text-sm text-slate-500">Update your password for this CCMS account.</p>
          </div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close change password dialog"><X size={16} /></button>
        </div>
        {error && <div className="notice-error mb-4">{error}</div>}
        {success && <div className="notice-success mb-4">{success}</div>}
        <div className="space-y-4">
          <PasswordField label="Current Password" value={currentPassword} onChange={setCurrentPassword} visible={Boolean(show.current)} onToggle={() => setShow((state) => ({ ...state, current: !state.current }))} autoComplete="current-password" />
          <PasswordField label="New Password" value={newPassword} onChange={setNewPassword} visible={Boolean(show.next)} onToggle={() => setShow((state) => ({ ...state, next: !state.next }))} autoComplete="new-password" />
          <PasswordField label="Confirm New Password" value={confirmPassword} onChange={setConfirmPassword} visible={Boolean(show.confirm)} onToggle={() => setShow((state) => ({ ...state, confirm: !state.confirm }))} autoComplete="new-password" />
        </div>
        <div className="mt-6 flex justify-end gap-2">
          <button type="button" className="secondary-button" onClick={onClose}>Cancel</button>
          <button type="submit" className="primary-button" disabled={submitting}>
            {submitting ? <><span className="small-spinner" />Changing...</> : "Change Password"}
          </button>
        </div>
      </form>
    </div>
  );
}

function PasswordField({ label, value, onChange, visible, onToggle, autoComplete }: { label: string; value: string; onChange: (value: string) => void; visible: boolean; onToggle: () => void; autoComplete: string }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <div className="input-wrap mt-0">
        <input type={visible ? "text" : "password"} value={value} onChange={(event) => onChange(event.target.value)} autoComplete={autoComplete} />
        <button type="button" className="rounded-md p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-700" onClick={onToggle} aria-label={visible ? `Hide ${label}` : `Show ${label}`}>
          {visible ? <EyeOff size={18} /> : <Eye size={18} />}
        </button>
      </div>
    </label>
  );
}
