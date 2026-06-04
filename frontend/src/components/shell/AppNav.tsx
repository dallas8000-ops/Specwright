import { NavLink } from "react-router-dom";
import { SPECWRIGHT_NAV } from "@/domain/specwrightNav";
import styles from "./Shell.module.css";

export default function AppNav() {
  return (
    <nav className={styles.nav} aria-label="Main">
      {SPECWRIGHT_NAV.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) => (isActive ? `${styles.navLink} ${styles.active}` : styles.navLink)}
        >
          <Icon size={15} aria-hidden />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
