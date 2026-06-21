export interface NavItem { label: string; href: string; roles?: string[] }
export interface NavGroup { label: string; items: NavItem[] }
const operational=["Admin","Manager","Data Entry Operator","Viewer"];
export const navigation: NavGroup[] = [
  {label:"Main",items:[{label:"Dashboard",href:"/dashboard",roles:operational}]},
  {label:"Child Management",items:[{label:"Children",href:"/dashboard/children",roles:operational},{label:"Admission Documents",href:"/dashboard/admission-documents",roles:operational}]},
  {label:"Sponsorship",items:[{label:"Sponsors",href:"/dashboard/sponsors",roles:operational},{label:"Sponsorships",href:"/dashboard/sponsorships",roles:operational}]},
  {label:"Accommodation",items:[{label:"Buildings",href:"/dashboard/buildings",roles:operational},{label:"Rooms & Beds",href:"/dashboard/rooms-beds",roles:operational},{label:"Bed Allocations",href:"/dashboard/bed-allocations",roles:operational}]},
  {label:"Medical",items:["Medical Profiles","Medical Visits","Medications","Vaccinations"].map(label=>({label,href:`/dashboard/${label.toLowerCase().replaceAll(" ","-")}`,roles:operational}))},
  {label:"Education",items:["Schools","Education Records","Results","Attendance"].map(label=>({label,href:`/dashboard/${label.toLowerCase().replaceAll(" ","-")}`,roles:operational}))},
  {label:"Case Management",items:["Case Profiles","Case Notes","Counseling","Incidents","Care Plans","Case Reviews"].map(label=>({label,href:`/dashboard/${label.toLowerCase().replaceAll(" ","-")}`,roles:["Admin","Manager","Data Entry Operator"]}))},
  {label:"Reports",items:[{label:"Consolidated Reports",href:"/dashboard/reports",roles:operational},{label:"Exports",href:"/dashboard/exports",roles:operational},{label:"Imports",href:"/dashboard/imports",roles:["Admin","Manager","Data Entry Operator"]}]},
  {label:"Administration",items:["Users","Roles","Audit Logs","System Status"].map(label=>({label,href:`/dashboard/${label.toLowerCase().replaceAll(" ","-")}`,roles:["Admin"]}))},
];
