import { ModuleWorkspace } from "@/components/modules/ModuleWorkspace";

export default async function ModulePage({params}:{params:Promise<{slug:string[]}>}){
  const {slug}=await params;
  return <ModuleWorkspace moduleKey={slug.join("/")}/>;
}
