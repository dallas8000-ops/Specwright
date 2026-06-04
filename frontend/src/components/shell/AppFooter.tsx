import { Link } from "react-router-dom";
import { SPECWRIGHT_NAV } from "@/domain/specwrightNav";
import styles from "./Shell.module.css";

export default function AppFooter() {
  return (
    <footer className={styles.footer}>
      <span>© Specwright — documentation layer for FastAPI teams</span>
      <div className={styles.footerLinks}>
        {SPECWRIGHT_NAV.map(({ to, label }) => (
          <Link key={to} to={to}>
            {label}
          </Link>
        ))}
        <a href="/api/v1/docs" target="_blank" rel="noreferrer">
          Swagger
        </a>
      </div>
    </footer>
  );
}
