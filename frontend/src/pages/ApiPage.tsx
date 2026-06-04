import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  Braces,
  ExternalLink,
  FileJson,
  HeartPulse,
  Map,
  Server,
} from "lucide-react";
import { specwright } from "@/api/specwright";
import styles from "./ApiPage.module.css";

type ApiLink = {
  title: string;
  description: string;
  href: string;
  code: string;
  icon: typeof Braces;
  external?: boolean;
};

const ENDPOINTS: ApiLink[] = [
  {
    title: "Swagger UI",
    description: "Interactive REST explorer for all Specwright endpoints.",
    href: "/api/v1/docs",
    code: "/api/v1/docs",
    icon: BookOpen,
    external: true,
  },
  {
    title: "ReDoc",
    description: "Readable API reference with grouped operations.",
    href: "/api/v1/redoc",
    code: "/api/v1/redoc",
    icon: BookOpen,
    external: true,
  },
  {
    title: "OpenAPI schema",
    description: "Machine-readable definition of this API.",
    href: "/api/v1/openapi.json",
    code: "openapi.json",
    icon: FileJson,
    external: true,
  },
  {
    title: "Health check",
    description: "Liveness probe — returns status and product name.",
    href: "/api/v1/health",
    code: "/api/v1/health",
    icon: HeartPulse,
  },
  {
    title: "Product metadata",
    description: "Tagline, artifact outputs, and shipped features.",
    href: "/api/v1/product",
    code: "/api/v1/product",
    icon: Server,
  },
  {
    title: "Framework roadmap",
    description: "Live and planned analyzer support by framework.",
    href: "/api/v1/roadmap",
    code: "/api/v1/roadmap",
    icon: Map,
  },
];

export default function ApiPage() {
  const { data: health } = useQuery({
    queryKey: ["api-health"],
    queryFn: async () => (await specwright.get<{ status: string; product: string }>("/health")).data,
  });

  const { data: product } = useQuery({
    queryKey: ["api-product"],
    queryFn: async () =>
      (
        await specwright.get<{
          name: string;
          tagline: string;
          stack: string;
          outputs: string[];
        }>("/product")
      ).data,
  });

  return (
    <main className={styles.page}>
      <header className={styles.hero}>
        <p className={styles.eyebrow}>
          <Braces size={14} /> Backend reference
        </p>
        <h1>
          Specwright <span>API</span>
        </h1>
        <p className={styles.lead}>
          {product?.tagline ??
            "The documentation layer for FastAPI teams — automatically."}{" "}
          Endpoints are proxied to port <code>8080</code> in development.
        </p>
        {health && (
          <p className={styles.status}>
            <span className={styles.statusDot} aria-hidden />
            {health.product} · {health.status}
          </p>
        )}
        <Link to="/" className={styles.heroLink}>
          Back to projects <ArrowRight size={14} />
        </Link>
      </header>

      {product && (
        <section className={styles.meta}>
          <div>
            <span className={styles.metaLabel}>Stack</span>
            <strong>{product.stack}</strong>
          </div>
          <div>
            <span className={styles.metaLabel}>Outputs</span>
            <strong>{product.outputs.join(", ")}</strong>
          </div>
        </section>
      )}

      <section className={styles.grid}>
        <h2>Endpoints</h2>
        <ul>
          {ENDPOINTS.map((item) => {
            const Icon = item.icon;
            const inner = (
              <>
                <span className={styles.cardIcon}>
                  <Icon size={18} />
                </span>
                <div className={styles.cardBody}>
                  <strong>{item.title}</strong>
                  <p>{item.description}</p>
                </div>
                <code className={styles.cardCode}>{item.code}</code>
                {item.external && <ExternalLink size={14} className={styles.ext} />}
              </>
            );
            return (
              <li key={item.href}>
                {item.external ? (
                  <a
                    href={item.href}
                    target="_blank"
                    rel="noreferrer"
                    className={styles.card}
                  >
                    {inner}
                  </a>
                ) : (
                  <a href={item.href} className={styles.card}>
                    {inner}
                  </a>
                )}
              </li>
            );
          })}
        </ul>
      </section>

      <p className={styles.note}>
        Direct backend root:{" "}
        <a href="http://localhost:8080/" target="_blank" rel="noreferrer">
          http://localhost:8080
        </a>{" "}
        — same styling as this hub. Use Swagger for trying authenticated flows and webhooks.
      </p>
    </main>
  );
}
