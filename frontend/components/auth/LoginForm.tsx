"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Eye, EyeOff, LockKeyhole, UserRound } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { loginErrorMessage } from "@/lib/api";
import { clearRememberedUsername, getRememberedUsername, setRememberedUsername } from "@/lib/auth";

const schema = z.object({
  username: z.string().min(1, "Enter your username"),
  password: z.string().min(1, "Enter your password"),
  rememberUsername: z.boolean(),
});
type Values = z.infer<typeof schema>;

export function LoginForm() {
  const router = useRouter();
  const { login, authenticated, loading } = useAuth();
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { username: "", password: "", rememberUsername: false },
  });

  useEffect(() => {
    const remembered = getRememberedUsername();
    if (remembered) {
      setValue("username", remembered);
      setValue("rememberUsername", true);
    }
  }, [setValue]);

  useEffect(() => {
    if (!loading && authenticated) router.replace("/dashboard");
  }, [loading, authenticated, router]);

  const submit = async (values: Values) => {
    setError("");
    try {
      await login(values.username, values.password);
      if (values.rememberUsername) setRememberedUsername(values.username);
      else clearRememberedUsername();
      router.replace("/dashboard");
    } catch (e) {
      setError(loginErrorMessage(e));
    }
  };

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-5" noValidate>
      {error && (
        <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </div>
      )}
      <label className="block text-sm font-semibold text-slate-700">
        Username
        <div className="input-wrap bg-white">
          <UserRound size={18} />
          <input autoComplete="username" {...register("username")} placeholder="Enter username" />
        </div>
        {errors.username && <span className="field-error">{errors.username.message}</span>}
      </label>
      <label className="block text-sm font-semibold text-slate-700">
        Password
        <div className="input-wrap bg-white">
          <LockKeyhole size={18} />
          <input type={showPassword ? "text" : "password"} autoComplete="current-password" {...register("password")} placeholder="Enter password" />
          <button type="button" className="rounded-md p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-700" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>
        {errors.password && <span className="field-error">{errors.password.message}</span>}
      </label>
      <div className="flex items-center justify-between gap-3 text-sm">
        <label className="inline-flex items-center gap-2 text-slate-600">
          <input type="checkbox" className="size-4 rounded border-slate-300" {...register("rememberUsername")} />
          Remember username
        </label>
        <span className="text-xs font-medium text-slate-400">Secure system</span>
      </div>
      <button disabled={isSubmitting} className="primary-button h-12 w-full rounded-xl">
        {isSubmitting ? (
          <>
            <span className="small-spinner" />
            Signing in...
          </>
        ) : (
          "Sign in"
        )}
      </button>
    </form>
  );
}
