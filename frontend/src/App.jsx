import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import LandingPage from "./pages/LandingPage";
import Dashboard from "./pages/Dashboard";
import AnalyzePage from "./pages/AnalyzePage";
import BatchPage from "./pages/BatchPage";
import TransactionHistoryPage from "./pages/TransactionHistoryPage";
import ModelPerformancePage from "./pages/ModelPerformancePage";
import AboutPage from "./pages/AboutPage";
import LoginPage from "./pages/LoginPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route element={<Layout />}>
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="analyze" element={<AnalyzePage />} />
          <Route path="batch" element={<BatchPage />} />
          <Route path="history" element={<TransactionHistoryPage />} />
          <Route path="model" element={<ModelPerformancePage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="login" element={<LoginPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
