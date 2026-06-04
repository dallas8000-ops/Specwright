import { Navigate, Route, Routes } from "react-router-dom";
import ErrorBoundary from "@/components/ErrorBoundary";
import Shell from "@/components/shell/Shell";
import HomePage from "@/pages/HomePage";
import ProjectPage from "@/pages/ProjectPage";
import BillingPage from "@/pages/BillingPage";
import ApiPage from "@/pages/ApiPage";

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route element={<Shell />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<Navigate to="/" replace />} />
          <Route path="/project/:id" element={<ProjectPage />} />
          <Route path="/billing" element={<BillingPage />} />
          <Route path="/api" element={<ApiPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}
