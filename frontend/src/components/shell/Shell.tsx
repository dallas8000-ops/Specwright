import { Link, Outlet } from "react-router-dom";
import { Zap } from "lucide-react";
import AppFooter from "./AppFooter";
import AppNav from "./AppNav";
import styles from "./Shell.module.css";

export default function Shell() {
  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <Link to="/dashboard" className={styles.brand}>
          <span className={styles.mark}>
            <Zap size={16} />
          </span>
          <div>
            <strong>Specwright</strong>
            <span>Documentation layer — auto-sync</span>
          </div>
        </Link>
        <AppNav />
      </header>
      <main className={styles.main}>
        <Outlet />
      </main>
      <AppFooter />
    </div>
  );
}
