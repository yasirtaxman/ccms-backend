import { API_BASE_URL, api } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { OrganizationProfile, OrganizationProfilePayload } from "@/types/organization";

export async function getOrganizationProfile(): Promise<OrganizationProfile> {
  const response = await api.get<OrganizationProfile>("/organization-profile");
  return response.data;
}

export async function saveOrganizationProfile(payload: OrganizationProfilePayload): Promise<OrganizationProfile> {
  const response = await api.put<OrganizationProfile>("/organization-profile", payload);
  return response.data;
}

export async function uploadOrganizationLogo(file: File): Promise<OrganizationProfile> {
  const form = new FormData();
  form.append("file", file);
  const response = await api.post<OrganizationProfile>("/organization-profile/logo", form);
  return response.data;
}

export async function deleteOrganizationLogo(): Promise<OrganizationProfile> {
  const response = await api.delete<OrganizationProfile>("/organization-profile/logo");
  return response.data;
}

export async function loadOrganizationLogoBlob(): Promise<string | null> {
  const token = getToken();
  if (!token) return null;
  const response = await fetch(`${API_BASE_URL}/organization-profile/logo`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) return null;
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}
