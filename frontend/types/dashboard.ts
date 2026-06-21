export interface ExecutiveDashboardResponse {
  children_summary: Record<string, number>;
  sponsorship_summary: Record<string, number>;
  accommodation_summary: Record<string, number>;
  medical_summary: Record<string, number>;
  education_summary: Record<string, number>;
  case_management_summary: Record<string, number>;
  document_summary: Record<string, number>;
  alerts_summary: Record<string, number>;
  pending_actions_summary: Record<string, number>;
}
export interface DashboardSummaryCard { label: string; value: number | string; tone?: "default" | "success" | "danger" }
