import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Check,
  X,
  Shield,
  Sparkles,
  Github,
  Zap,
  Lock,
  ArrowRight,
  Loader2,
  Building2,
} from "lucide-react";
import { specwright, BillingStatus, startCheckout } from "@/api/specwright";
import styles from "./BillingPage.module.css";

type Tier = "starter" | "pro";

export default function BillingPage() {
  const [params, setSearchParams] = useSearchParams();
  const [billingCycle, setBillingCycle] = useState<"monthly" | "annual">("monthly");
  const qc = useQueryClient();
  const success = params.get("success") === "1";
  const successTier = params.get("tier") ?? "pro";
  const canceled = params.get("canceled") === "1";

  const { data: status, isLoading } = useQuery({
    queryKey: ["billing"],
    queryFn: async () => (await specwright.get<BillingStatus>("/billing/status")).data,
  });

  const checkout = useMutation({
    mutationFn: async (tier: Tier) =>
      (await startCheckout(tier, billingCycle === "annual")).data,
    onSuccess: (data) => {
      if (data.url) {
        if (data.mode === "mock") {
          qc.invalidateQueries({ queryKey: ["billing"] });
          setSearchParams({ success: "1", tier: data.tier ?? "pro" });
        } else {
          window.location.href = data.url;
        }
      }
    },
  });

  const catalog = status?.catalog;
  const discount = catalog?.annual_discount_percent ?? 20;
  const starterMonthly = catalog?.starter_price_usd ?? 29;
  const proMonthly = catalog?.pro_price_usd ?? 79;
  const starterDisplay =
    billingCycle === "annual"
      ? Math.round((catalog?.starter_annual_usd ?? starterMonthly * 12 * 0.8) / 12)
      : starterMonthly;
  const proDisplay =
    billingCycle === "annual"
      ? Math.round((catalog?.pro_annual_usd ?? proMonthly * 12 * 0.8) / 12)
      : proMonthly;
  const currentPlan = status?.plan ?? "starter";

  return (
    <main className={styles.page}>
      <header className={styles.hero}>
        <p className={styles.eyebrow}>Pricing</p>
        <h1>
          Document every API
          <span> before the next sprint slips</span>
        </h1>
        <p className={styles.lead}>
          Starter for builders. Pro for teams shipping weekly. Enterprise when compliance
          and scale demand it.
        </p>
        <div className={styles.heroLinks}>
          <Link to="/" className={styles.heroLink}>
            Start with a free scan <ArrowRight size={14} />
          </Link>
          <Link to="/api" className={styles.heroLinkMuted}>
            API reference
          </Link>
        </div>
      </header>

      {success && (
        <div className={styles.alertSuccess} role="status">
          <Check size={18} />
          <div>
            <strong>
              Welcome to Specwright {successTier === "starter" ? "Starter" : "Pro"}
            </strong>
            <p>Your plan is active. Head back to your project to use your new features.</p>
          </div>
          <Link to="/" className={styles.alertCta}>
            Open workspace <ArrowRight size={14} />
          </Link>
        </div>
      )}

      {canceled && !success && (
        <div className={styles.alertMuted} role="status">
          Checkout canceled — you were not charged.
        </div>
      )}

      {checkout.isError && (
        <div className={styles.alertError} role="alert">
          We couldn&apos;t start checkout. Email sales@specwright.dev and we&apos;ll help
          you onboard.
        </div>
      )}

      <div className={styles.cycleToggle}>
        <button
          type="button"
          className={billingCycle === "monthly" ? styles.cycleActive : ""}
          onClick={() => setBillingCycle("monthly")}
        >
          Monthly
        </button>
        <button
          type="button"
          className={billingCycle === "annual" ? styles.cycleActive : ""}
          onClick={() => setBillingCycle("annual")}
        >
          Annual
          <span className={styles.saveBadge}>Save {discount}%</span>
        </button>
      </div>

      <div className={styles.plans}>
        <article className={styles.planCard}>
          <h2>Starter</h2>
          <p className={styles.priceRow}>
            <span className={styles.price}>${starterDisplay}</span>
            <span className={styles.interval}>
              / month{billingCycle === "annual" ? ", billed annually" : ""}
            </span>
          </p>
          <p className={styles.planBlurb}>
            Solo developers and small repos — full AST generation without the team workflow.
          </p>
          <ul className={styles.highlights}>
            <li>Unlimited scans</li>
            <li>OpenAPI, tests, diagrams</li>
            <li>Watch mode</li>
          </ul>
          <button
            type="button"
            className={styles.secondaryCta}
            disabled={checkout.isPending || currentPlan === "starter" || isLoading}
            onClick={() => checkout.mutate("starter")}
          >
            {currentPlan === "starter" ? "Current plan" : "Choose Starter"}
          </button>
        </article>

        <article className={`${styles.planCard} ${styles.planPro}`}>
          <span className={styles.badge}>Recommended</span>
          <h2>Pro</h2>
          <p className={styles.priceRow}>
            <span className={styles.price}>${proDisplay}</span>
            <span className={styles.interval}>
              / month{billingCycle === "annual" ? ", billed annually" : ""}
            </span>
          </p>
          {catalog && catalog.pro_trial_days > 0 && currentPlan !== "pro" && (
            <p className={styles.trial}>
              {catalog.pro_trial_days}-day free trial · cancel anytime
            </p>
          )}
          <p className={styles.planBlurb}>
            The plan most teams pick — AI polish and GitHub PR comments where reviewers
            already work.
          </p>
          <ul className={styles.highlights}>
            <li>Everything in Starter</li>
            <li>AI markdown polish</li>
            <li>GitHub PR automation</li>
            <li>Priority support</li>
          </ul>
          <button
            type="button"
            className={styles.primaryCta}
            disabled={checkout.isPending || currentPlan === "pro" || isLoading}
            onClick={() => checkout.mutate("pro")}
          >
            {checkout.isPending ? (
              <>
                <Loader2 size={16} className={styles.spin} /> Redirecting…
              </>
            ) : currentPlan === "pro" ? (
              "Current plan"
            ) : (
              <>
                Start Pro — ${proDisplay}/mo <ArrowRight size={16} />
              </>
            )}
          </button>
          <p className={styles.secure}>
            <Lock size={12} />
            Secure checkout powered by Stripe
          </p>
        </article>

        <article className={styles.planCard}>
          <h2>Enterprise</h2>
          <p className={styles.priceRow}>
            <span className={styles.priceCustom}>Custom</span>
          </p>
          <p className={styles.planBlurb}>
            SSO, audit logs, SLAs, and dedicated onboarding for regulated or large orgs.
          </p>
          <ul className={styles.highlights}>
            <li>Everything in Pro</li>
            <li>SSO / SAML</li>
            <li>Custom SLA</li>
            <li>Dedicated success manager</li>
          </ul>
          <a href="mailto:sales@specwright.dev" className={styles.secondaryCta}>
            <Building2 size={16} /> Contact sales
          </a>
        </article>
      </div>

      <section className={styles.compare}>
        <h3>Full comparison</h3>
        <div className={styles.tableWrap}>
          <table>
            <thead>
              <tr>
                <th>Feature</th>
                <th>Starter</th>
                <th>Pro</th>
                <th>Enterprise</th>
              </tr>
            </thead>
            <tbody>
              {(catalog?.feature_matrix ?? []).map((row) => (
                <tr key={row.name}>
                  <td>{row.name}</td>
                  <td>
                    {row.starter ? (
                      <Check size={16} className={styles.yes} aria-label="Yes" />
                    ) : (
                      <X size={16} className={styles.no} aria-label="No" />
                    )}
                  </td>
                  <td>
                    {row.pro ? (
                      <Check size={16} className={styles.yes} aria-label="Yes" />
                    ) : (
                      <X size={16} className={styles.no} aria-label="No" />
                    )}
                  </td>
                  <td>
                    {row.enterprise ? (
                      <Check size={16} className={styles.yes} aria-label="Yes" />
                    ) : (
                      <X size={16} className={styles.no} aria-label="No" />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className={styles.trust}>
        <div>
          <Shield size={20} />
          <strong>Cancel anytime</strong>
          <p>Manage billing in the Stripe customer portal. No surprise renewals.</p>
        </div>
        <div>
          <Sparkles size={20} />
          <strong>AI stays factual</strong>
          <p>Polish improves prose — it won&apos;t invent endpoints or models.</p>
        </div>
        <div>
          <Github size={20} />
          <strong>PR-native</strong>
          <p>Docs land in the PR thread, not a forgotten wiki page.</p>
        </div>
        <div>
          <Zap size={20} />
          <strong>AST-first</strong>
          <p>OpenAPI and tests from static analysis, not LLM guesswork.</p>
        </div>
      </section>

      <section className={styles.faq}>
        <h3>FAQ</h3>
        <details>
          <summary>Why is Pro $79/month?</summary>
          <p>
            Pro replaces hours of tech-writer and reviewer time per release. Teams typically
            recover that in the first PR that ships with generated OpenAPI and tests.
          </p>
        </details>
        <details>
          <summary>Can I try before paying?</summary>
          <p>
            Run unlimited scans from the home page at no cost. Pro adds a{" "}
            {catalog?.pro_trial_days ?? 14}-day trial when you upgrade — card required,
            cancel before day {catalog?.pro_trial_days ?? 14} and you won&apos;t be charged.
          </p>
        </details>
        <details>
          <summary>Starter vs Pro?</summary>
          <p>
            Starter is full code generation. Pro adds AI polish and GitHub — the workflow
            pieces teams pay for when docs must ship with every merge.
          </p>
        </details>
      </section>
    </main>
  );
}
