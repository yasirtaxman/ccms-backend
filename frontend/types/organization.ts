export interface OrganizationProfile {
  id: number | null;
  organization_name: string;
  short_name: string;
  logo_url: string | null;
  address: string | null;
  city: string | null;
  district: string | null;
  province: string | null;
  country: string | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  registration_no: string | null;
  ntn_or_tax_no: string | null;
  report_footer_text: string | null;
  report_watermark_text: string | null;
  primary_color: string | null;
  secondary_color: string | null;
  authorized_signatory_name: string | null;
  authorized_signatory_designation: string | null;
  is_active: boolean;
}

export type OrganizationProfilePayload = Omit<OrganizationProfile, "id" | "logo_url">;
