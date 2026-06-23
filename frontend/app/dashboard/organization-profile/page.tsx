"use client";

import { useEffect, useMemo, useState } from "react";
import { Building2, ImagePlus, Save, Trash2 } from "lucide-react";
import { apiErrorMessage } from "@/lib/api";
import { deleteOrganizationLogo, getOrganizationProfile, loadOrganizationLogoBlob, saveOrganizationProfile, uploadOrganizationLogo } from "@/lib/organization";
import { usePermissions } from "@/hooks/usePermissions";
import type { OrganizationProfile, OrganizationProfilePayload } from "@/types/organization";

const defaults: OrganizationProfilePayload = {
  organization_name: "Child Care Management System",
  short_name: "CCMS",
  address: "",
  city: "",
  district: "",
  province: "",
  country: "",
  phone: "",
  email: "",
  website: "",
  registration_no: "",
  ntn_or_tax_no: "",
  report_footer_text: "This report is system generated.",
  report_watermark_text: "",
  primary_color: "#174A7E",
  secondary_color: "#EAF2F9",
  authorized_signatory_name: "",
  authorized_signatory_designation: "",
  is_active: true,
};

const field = (profile: OrganizationProfile): OrganizationProfilePayload => ({
  organization_name: profile.organization_name ?? defaults.organization_name,
  short_name: profile.short_name ?? defaults.short_name,
  address: profile.address ?? "",
  city: profile.city ?? "",
  district: profile.district ?? "",
  province: profile.province ?? "",
  country: profile.country ?? "",
  phone: profile.phone ?? "",
  email: profile.email ?? "",
  website: profile.website ?? "",
  registration_no: profile.registration_no ?? "",
  ntn_or_tax_no: profile.ntn_or_tax_no ?? "",
  report_footer_text: profile.report_footer_text ?? defaults.report_footer_text,
  report_watermark_text: profile.report_watermark_text ?? "",
  primary_color: profile.primary_color ?? defaults.primary_color,
  secondary_color: profile.secondary_color ?? defaults.secondary_color,
  authorized_signatory_name: profile.authorized_signatory_name ?? "",
  authorized_signatory_designation: profile.authorized_signatory_designation ?? "",
  is_active: profile.is_active,
});

export default function OrganizationProfilePage() {
  const { isAdmin, loading: permissionLoading } = usePermissions();
  const [form, setForm] = useState<OrganizationProfilePayload>(defaults);
  const [profile, setProfile] = useState<OrganizationProfile | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const admin = isAdmin();

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await getOrganizationProfile();
        if (!active) return;
        setProfile(data);
        setForm(field(data));
        const logo = data.logo_url ? await loadOrganizationLogoBlob() : null;
        if (active) setLogoPreview(logo);
      } catch (err) {
        if (active) setError(apiErrorMessage(err));
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, []);

  const contactLine = useMemo(() => [form.address, form.city, form.district, form.province, form.country].filter(Boolean).join(", ") || "Address not configured", [form]);
  const setValue = (key: keyof OrganizationProfilePayload, value: string | boolean) => setForm((current) => ({ ...current, [key]: value }));
  const textValue = (key: keyof OrganizationProfilePayload) => String(form[key] ?? "");

  async function save() {
    if (!admin) return;
    setSaving(true);
    setMessage("");
    setError("");
    try {
      const saved = await saveOrganizationProfile(form);
      setProfile(saved);
      setForm(field(saved));
      setMessage("Organization profile saved successfully.");
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function upload(file: File | null) {
    if (!file || !admin) return;
    setSaving(true);
    setMessage("");
    setError("");
    try {
      const saved = await uploadOrganizationLogo(file);
      setProfile(saved);
      const nextPreview = await loadOrganizationLogoBlob();
      setLogoPreview(nextPreview);
      setMessage("Organization logo uploaded successfully.");
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function removeLogo() {
    if (!admin) return;
    setSaving(true);
    setMessage("");
    setError("");
    try {
      const saved = await deleteOrganizationLogo();
      setProfile(saved);
      setLogoPreview(null);
      setMessage("Organization logo removed successfully.");
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (permissionLoading || loading) return <div className="panel">Loading organization profile…</div>;
  if (!admin) return <div className="notice-error">Only Admin users can manage Organization Profile settings.</div>;

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p className="eyebrow">Administration</p>
          <h1 className="page-title">Organization Profile</h1>
          <p className="page-subtitle">Configure the organization identity used in official CCMS PDF report headers and footers.</p>
        </div>
        <button className="primary-button" onClick={save} disabled={saving}><Save size={16} />{saving ? "Saving…" : "Save Profile"}</button>
      </header>

      {error && <div className="notice-error">{error}</div>}
      {message && <div className="notice-success">{message}</div>}

      <section className="grid gap-5 xl:grid-cols-[360px_1fr]">
        <div className="panel">
          <h2 className="text-lg font-bold text-slate-900">Organization identity</h2>
          <div className="mt-5 rounded-2xl border border-slate-200 p-5" style={{ background: form.secondary_color || "#EAF2F9" }}>
            <div className="flex items-center gap-4">
              <div className="grid size-20 place-items-center overflow-hidden rounded-2xl text-white shadow-sm" style={{ background: form.primary_color || "#174A7E" }}>
                {logoPreview ? <img src={logoPreview} alt="Organization logo" className="h-full w-full object-contain bg-white" /> : <Building2 size={34} />}
              </div>
              <div>
                <div className="text-xl font-bold text-slate-950">{form.organization_name || "Child Care Management System"}</div>
                <div className="text-sm font-semibold text-slate-600">{form.short_name || "CCMS"}</div>
              </div>
            </div>
            <p className="mt-4 text-sm text-slate-600">{contactLine}</p>
            <p className="mt-2 text-xs text-slate-500">{[form.phone, form.email].filter(Boolean).join(" | ") || "Contact details not configured"}</p>
          </div>
          <div className="mt-5 space-y-3">
            <label className="secondary-button cursor-pointer justify-center">
              <ImagePlus size={16} /> Upload / Change Logo
              <input className="hidden" type="file" accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp" onChange={(event) => void upload(event.target.files?.[0] ?? null)} />
            </label>
            {profile?.logo_url && <button className="secondary-button w-full justify-center text-red-600" onClick={removeLogo} disabled={saving}><Trash2 size={16} /> Delete Logo</button>}
            <p className="text-xs text-slate-500">Supported formats: PNG, JPG, JPEG, WEBP. File size follows the backend upload limit.</p>
          </div>
        </div>

        <div className="space-y-5">
          <FormSection title="Basic Information">
            <Input label="Organization Name" value={textValue("organization_name")} onChange={(value) => setValue("organization_name", value)} required />
            <Input label="Short Name" value={textValue("short_name")} onChange={(value) => setValue("short_name", value)} required />
            <Input label="Registration No." value={textValue("registration_no")} onChange={(value) => setValue("registration_no", value)} />
            <Input label="NTN / Tax No." value={textValue("ntn_or_tax_no")} onChange={(value) => setValue("ntn_or_tax_no", value)} />
          </FormSection>
          <FormSection title="Address">
            <Input label="Address" value={textValue("address")} onChange={(value) => setValue("address", value)} wide />
            <Input label="City" value={textValue("city")} onChange={(value) => setValue("city", value)} />
            <Input label="District" value={textValue("district")} onChange={(value) => setValue("district", value)} />
            <Input label="Province" value={textValue("province")} onChange={(value) => setValue("province", value)} />
            <Input label="Country" value={textValue("country")} onChange={(value) => setValue("country", value)} />
          </FormSection>
          <FormSection title="Contact Details">
            <Input label="Phone" value={textValue("phone")} onChange={(value) => setValue("phone", value)} />
            <Input label="Email" value={textValue("email")} onChange={(value) => setValue("email", value)} />
            <Input label="Website" value={textValue("website")} onChange={(value) => setValue("website", value)} />
          </FormSection>
          <FormSection title="Report Branding">
            <Input label="Report Footer Text" value={textValue("report_footer_text")} onChange={(value) => setValue("report_footer_text", value)} wide />
            <Input label="Watermark Text" value={textValue("report_watermark_text")} onChange={(value) => setValue("report_watermark_text", value)} />
            <Input label="Primary Color" type="color" value={textValue("primary_color") || "#174A7E"} onChange={(value) => setValue("primary_color", value)} />
            <Input label="Secondary Color" type="color" value={textValue("secondary_color") || "#EAF2F9"} onChange={(value) => setValue("secondary_color", value)} />
          </FormSection>
          <FormSection title="Authorized Signatory">
            <Input label="Authorized Signatory Name" value={textValue("authorized_signatory_name")} onChange={(value) => setValue("authorized_signatory_name", value)} />
            <Input label="Authorized Signatory Designation" value={textValue("authorized_signatory_designation")} onChange={(value) => setValue("authorized_signatory_designation", value)} />
          </FormSection>
        </div>
      </section>
    </div>
  );
}

function FormSection({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="panel"><h2 className="text-lg font-bold text-slate-900">{title}</h2><div className="mt-5 grid gap-4 md:grid-cols-2">{children}</div></section>;
}

function Input({ label, value, onChange, required = false, wide = false, type = "text" }: { label: string; value: string; onChange: (value: string) => void; required?: boolean; wide?: boolean; type?: string }) {
  return (
    <label className={`form-field ${wide ? "md:col-span-2" : ""}`}>
      <span>{label}{required && <em className="ml-1 text-red-500">*</em>}</span>
      <input className="field-control" type={type} value={value} onChange={(event) => onChange(event.target.value)} required={required} />
    </label>
  );
}
