import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import AppShell from "@/layouts/AppShell";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Dashboard from "@/pages/Dashboard";
import Infrastructure from "@/pages/Infrastructure";
import Kubernetes from "@/pages/Kubernetes";
import Metrics from "@/pages/Metrics";
import Alerts from "@/pages/Alerts";
import Jenkins from "@/pages/Jenkins";
import Incidents from "@/pages/Incidents";
import Logs from "@/pages/Logs";
import AIChat from "@/pages/AIChat";
import Settings from "@/pages/Settings";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            <Route element={<ProtectedRoute />}>
              <Route element={<AppShell />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/infrastructure" element={<Infrastructure />} />
                <Route path="/kubernetes" element={<Kubernetes />} />
                <Route path="/metrics" element={<Metrics />} />
                <Route path="/alerts" element={<Alerts />} />
                <Route path="/jenkins" element={<Jenkins />} />
                <Route path="/incidents" element={<Incidents />} />
                <Route path="/logs" element={<Logs />} />
                <Route path="/chat" element={<AIChat />} />
                <Route path="/settings" element={<Settings />} />
              </Route>
            </Route>

            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
