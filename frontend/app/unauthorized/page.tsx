import Link from "next/link";
import { ShieldX } from "lucide-react";
export default function Unauthorized(){return <main className="grid min-h-screen place-items-center bg-slate-50 p-6"><section className="empty-card max-w-lg"><ShieldX size={44} className="text-red-500"/><h1 className="text-2xl font-bold">Access not authorized</h1><p>Your account does not have permission to open this area. Contact a System Administrator if you need access.</p><Link className="primary-button" href="/dashboard">Return to dashboard</Link></section></main>}
