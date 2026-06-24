import {
  Bot,
  GitCompare,
  History,
  LayoutDashboard,
  LogOut,
  Luggage,
  Menu,
  Plane,
  PlusCircle,
  User,
  WalletCards,
  X
} from "lucide-react";
import { ReactNode, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/create-trip", label: "Create Trip", icon: PlusCircle },
  { to: "/history", label: "Trip History", icon: History },
  { to: "/expenses", label: "Expenses", icon: WalletCards },
  { to: "/assistant", label: "AI Assistant", icon: Bot },
  { to: "/compare", label: "Compare", icon: GitCompare },
  { to: "/packing", label: "Packing", icon: Luggage },
  { to: "/profile", label: "Profile", icon: User }
];

function SidebarContent({ onNavigate }: { readonly onNavigate?: () => void }) {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="flex h-full flex-col bg-zinc-950 text-white">
      <div className="flex h-16 items-center gap-3 border-b border-white/10 px-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-600">
          <Plane className="h-5 w-5" aria-hidden="true" />
        </div>
        <div>
          <p className="text-sm font-semibold">AI Travel Planner</p>
          <p className="text-xs text-zinc-400">{user?.name ?? "Traveler"}</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onNavigate}
              className={({ isActive }) =>
                [
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition",
                  isActive ? "bg-white text-zinc-950" : "text-zinc-300 hover:bg-white/10 hover:text-white"
                ].join(" ")
              }
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="border-t border-white/10 p-3">
        <button type="button" onClick={handleLogout} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-zinc-300 transition hover:bg-white/10 hover:text-white">
          <LogOut className="h-4 w-4" aria-hidden="true" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
}

function PageShell({ children }: { readonly children: ReactNode }) {
  return <main className="min-h-screen flex-1 overflow-y-auto bg-zinc-100 px-4 py-5 md:px-6 lg:px-8">{children}</main>;
}

export default function Layout() {
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen bg-zinc-100">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 lg:block">
        <SidebarContent />
      </aside>

      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button type="button" aria-label="Close navigation overlay" className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />
          <div className="relative h-full w-72 shadow-panel">
            <SidebarContent onNavigate={() => setOpen(false)} />
          </div>
        </div>
      )}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-zinc-200 bg-white px-4 lg:hidden">
          <button type="button" aria-label="Open navigation" className="rounded-lg border border-zinc-200 p-2 text-zinc-800" onClick={() => setOpen(true)}>
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
          <span className="text-sm font-semibold text-zinc-900">AI Travel Planner</span>
          <button type="button" aria-label="Close navigation" className="rounded-lg border border-transparent p-2 text-zinc-400" onClick={() => setOpen(false)}>
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </header>
        <PageShell>
          <Outlet />
        </PageShell>
      </div>
    </div>
  );
}
