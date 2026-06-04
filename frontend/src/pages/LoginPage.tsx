import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import styles from "./LoginPage.module.css";

const TENANTS = [
  { user: "legal.sam", product: "CounselFlow AI", vertical: "Legal contracts only" },
  { user: "hr.jordan", product: "PeopleOps AI", vertical: "HR / people ops only" },
  { user: "logistics.alex", product: "FreightPulse AI", vertical: "Shipment exceptions only" },
];

export default function LoginPage() {
  const [username, setUsername] = useState("legal.sam");
  const [password, setPassword] = useState("changeme-in-production");
  const [error, setError] = useState("");
  const setTokens = useAuthStore((s) => s.setTokens);
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const { data } = await axios.post("/api/auth/token/", { username, password });
      setTokens(data.access, data.refresh);
      navigate("/");
    } catch {
      setError("Invalid credentials.");
    }
  }

  return (
    <div className={styles.page}>
      <form className={styles.card} onSubmit={handleSubmit}>
        <div className={styles.hero}>
          <span className={styles.badge}>Serious vertical AI ops</span>
          <h1>One product. One domain. AI inside.</h1>
          <p>Not a generic three-department board — each tenant is a dedicated AI product.</p>
        </div>
        <ul className={styles.tenants}>
          {TENANTS.map((t) => (
            <li key={t.user}>
              <button type="button" onClick={() => setUsername(t.user)}>
                <strong>{t.product}</strong>
                <span>{t.user}</span>
                <small>{t.vertical}</small>
              </button>
            </li>
          ))}
        </ul>
        <label>
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </label>
        {error && <p className={styles.error}>{error}</p>}
        <button type="submit">Sign in</button>
      </form>
    </div>
  );
}
