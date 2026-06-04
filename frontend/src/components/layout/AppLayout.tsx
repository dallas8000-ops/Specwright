import { NavLink, Outlet } from "react-router-dom";
import { LogOut, Bell } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth";
import { useRealtimeStore } from "@/stores/realtime";
import LiveFeed from "@/components/LiveFeed";
import { useWorkspace } from "@/hooks/useWorkspace";
import { navForPersona } from "@/domain/navConfig";
import { api, Paginated } from "@/api/client";
import styles from "./AppLayout.module.css";

interface Alert {
  id: number;
  title: string;
}

export default function AppLayout() {
  const logout = useAuthStore((s) => s.logout);
  const rtStatus = useRealtimeStore((s) => s.status);
  const { data: me } = useWorkspace();
  const exp = me?.workspace?.experience;
  const nav = navForPersona(exp?.nav ?? ["home", "cases", "approvals"]);

  const { data: alerts } = useQuery({
    queryKey: ["alerts"],
    queryFn: async () => (await api.get<Paginated<Alert>>("/alerts/?acknowledged=false")).data,
  });
  const alertCount = alerts?.results.length ?? 0;

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <span className={styles.logo}>AF</span>
          <div>
            <strong>{exp?.app_title ?? "AutomationFlow"}</strong>
            <small>{me?.workspace?.department ?? me?.workspace?.organization ?? "Enterprise Ops"}</small>
          </div>
        </div>
        <nav className={styles.nav}>
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) => (isActive ? styles.active : undefined)}
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <button type="button" className={styles.logout} onClick={logout}>
          <LogOut size={16} />
          Sign out
        </button>
      </aside>
      <div className={styles.main}>
        <header className={styles.topbar}>
          <h1>
            {exp?.greeting ?? "Internal operations"}
            {rtStatus === "connected" && <span className={styles.liveDot}>Live</span>}
          </h1>
          <NavLink to="/memory" className={styles.iconBtn} aria-label="Alerts">
            <Bell size={18} />
            {alertCount > 0 && <span className={styles.badge}>{alertCount}</span>}
          </NavLink>
        </header>
        <main className={styles.content}>
          <Outlet />
        </main>
        <LiveFeed />
      </div>
    </div>
  );
}
