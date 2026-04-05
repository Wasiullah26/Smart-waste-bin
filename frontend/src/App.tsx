import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AllBinsPage } from "./pages/AllBinsPage";
import { BinDetailPage } from "./pages/BinDetailPage";
import { CriticalPage } from "./pages/CriticalPage";
import { ZoneHubPage } from "./pages/ZoneHubPage";
import { ZonePage } from "./pages/ZonePage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<AllBinsPage />} />
          <Route path="/critical" element={<CriticalPage />} />
          <Route path="/zones" element={<ZoneHubPage />} />
          <Route path="/zones/:zone" element={<ZonePage />} />
          <Route path="/bins/:binId" element={<BinDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
