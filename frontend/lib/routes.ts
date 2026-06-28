export interface NavItem { label: string; href: string; roles?: string[];permission?:string }
export interface NavGroup { label: string; items: NavItem[] }
const operational=["Admin","Manager","Data Entry Operator","Viewer"];
const wardenOperational=[...operational,"Warden"];
export const navigation: NavGroup[] = [
  {label:"Main",items:[{label:"Dashboard",href:"/dashboard",roles:wardenOperational,permission:"dashboard.view"}]},
  {label:"Child Management",items:[
    {label:"Children",href:"/dashboard/children",roles:wardenOperational,permission:"children.view"},
    {label:"Admission Documents",href:"/dashboard/admission-documents",roles:operational,permission:"children.documents.view"},
    {label:"Daily Attendance",href:"/dashboard/children/attendance",roles:wardenOperational,permission:"daily_attendance.view"},
    {label:"Attendance Reports",href:"/dashboard/children/attendance/reports",roles:operational,permission:"daily_attendance.view"},
    {label:"Import Children",href:"/dashboard/children/import",roles:["Admin","Manager","Data Entry Operator"],permission:"imports.view"},
  ]},
  {label:"Visitors",items:[{label:"Visitors",href:"/dashboard/visitors",roles:wardenOperational,permission:"visitors.view"},{label:"Child Visits",href:"/dashboard/child-visits",roles:wardenOperational,permission:"child_visits.view"},{label:"Visitor Reports",href:"/dashboard/visitor-reports",roles:operational,permission:"child_visits.export"}]},
  {label:"Development Profile",items:[{label:"Observations",href:"/dashboard/development/observations",roles:wardenOperational,permission:"development.view"},{label:"New Observation",href:"/dashboard/development/observations/new",roles:["Admin","Manager","Data Entry Operator","Warden","Counselor"],permission:"development.create"},{label:"AI Summaries",href:"/dashboard/development/ai-summaries",roles:["Admin","Manager","Counselor"],permission:"development.ai_summary.view"},{label:"Indicators",href:"/dashboard/development/indicators",roles:["Admin"],permission:"development.indicators.view"},{label:"Development Reports",href:"/dashboard/development/reports",roles:["Admin","Manager","Counselor"],permission:"development.export"}]},
  {label:"Sponsorship",items:[{label:"Sponsors",href:"/dashboard/sponsors",roles:operational,permission:"sponsors.view"},{label:"Sponsorships",href:"/dashboard/sponsorships",roles:operational,permission:"sponsorships.view"}]},
  {label:"Accommodation",items:[{label:"Buildings",href:"/dashboard/buildings",roles:operational,permission:"accommodation.view"},{label:"Rooms & Beds",href:"/dashboard/rooms-beds",roles:operational,permission:"accommodation.view"},{label:"Bed Allocations",href:"/dashboard/bed-allocations",roles:operational,permission:"accommodation.view"}]},
  {label:"Medical",items:["Medical Profiles","Medical Visits","Medications","Vaccinations"].map(label=>({label,href:`/dashboard/${label.toLowerCase().replaceAll(" ","-")}`,roles:operational,permission:"medical.view"}))},
  {label:"Education",items:["Schools","Education Records","Results","Attendance"].map(label=>({label,href:`/dashboard/${label.toLowerCase().replaceAll(" ","-")}`,roles:operational,permission:"education.view"}))},
  {label:"Case Management",items:["Case Profiles","Case Notes","Counseling","Incidents","Care Plans","Case Reviews"].map(label=>({label,href:`/dashboard/${label.toLowerCase().replaceAll(" ","-")}`,roles:operational,permission:"case_management.view"}))},
  {label:"Reports",items:[{label:"Consolidated Reports",href:"/dashboard/reports",roles:operational,permission:"reports.view"},{label:"Exports",href:"/dashboard/exports",roles:operational,permission:"reports.export"},{label:"Imports",href:"/dashboard/imports",roles:["Admin","Manager","Data Entry Operator"],permission:"imports.view"}]},
  {label:"Administration",items:[{label:"Organization Profile",href:"/dashboard/organization-profile",roles:["Admin"]},{label:"Users",href:"/dashboard/users",roles:["Admin"],permission:"users.view"},{label:"Roles",href:"/dashboard/roles",roles:["Admin"],permission:"roles.view"},{label:"Audit Logs",href:"/dashboard/audit-logs",roles:["Admin"],permission:"audit_logs.view"},{label:"System Status",href:"/dashboard/system-status",roles:["Admin"],permission:"system_status.view"}]},
];
