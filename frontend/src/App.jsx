import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';
import DashboardView from './components/dashboard/DashboardView';
import DirectoryView from './components/directory/DirectoryView';
import AnalyseView from './components/company/AnalyseView';
import CompanyProfilePage from './components/company/CompanyProfilePage';
import SettingsView from './components/settings/SettingsView';

export default function App() {
  return (
    <BrowserRouter>
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<DashboardView />} />
          <Route path="/analyse" element={<AnalyseView />} />
          <Route path="/analyse/:companyName" element={<CompanyProfilePage />} />
          <Route path="/directory" element={<DirectoryView />} />
          <Route path="/settings" element={<SettingsView />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
