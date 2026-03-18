import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ExternalLink, AlertCircle } from 'lucide-react';
import { api } from '../../utils/api';
import LoadingSpinner from '../shared/LoadingSpinner';

export default function AnalyseView() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleAnalyse = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const result = await api.analyseCompany(url.trim());
      navigate(`/analyse/${encodeURIComponent(result.company_name)}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickNav = async (name) => {
    navigate(`/analyse/${encodeURIComponent(name)}`);
  };

  const [recentCompanies, setRecentCompanies] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const handleSearch = async (q) => {
    setSearchQuery(q);
    if (q.length < 2) { setSearchResults([]); return; }
    setSearching(true);
    try {
      const companies = await api.getCompanies({ search: q, include_excluded: false });
      setSearchResults(companies.slice(0, 8));
    } catch { setSearchResults([]); }
    finally { setSearching(false); }
  };

  return (
    <>
      <div className="page-header">
        <h1>Company Analyser</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
          Analyse a company from URL or search existing profiles
        </p>
      </div>
      <div className="page-body">
        {/* AI Analysis */}
        <div className="card mb-4">
          <div className="card-header">
            <span className="card-title">AI Company Analysis</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: 12 }}>
            Paste a company website or profile URL to generate an AI-powered analysis with scores, sustainability data, and strategic fit assessment.
          </p>
          <form onSubmit={handleAnalyse} className="flex gap-3">
            <div className="relative flex-1">
              <ExternalLink size={16} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--text-muted)' }} />
              <input
                type="url"
                placeholder="https://company-website.com"
                value={url}
                onChange={e => setUrl(e.target.value)}
                style={{ paddingLeft: 32, width: '100%' }}
                disabled={loading}
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading || !url.trim()}>
              {loading ? 'Analysing...' : 'Analyse'}
            </button>
          </form>
          {loading && (
            <div style={{ marginTop: 16 }}>
              <LoadingSpinner text="AI is analysing the company... This may take 30-60 seconds." />
            </div>
          )}
          {error && (
            <div className="flex items-center gap-2" style={{ marginTop: 12, color: 'var(--danger)' }}>
              <AlertCircle size={16} />
              <span style={{ fontSize: '0.85rem' }}>{error}</span>
            </div>
          )}
        </div>

        {/* Search existing */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Search Existing Companies</span>
          </div>
          <div className="relative">
            <Search size={16} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--text-muted)' }} />
            <input
              type="search"
              placeholder="Search by company name, country, or crop..."
              value={searchQuery}
              onChange={e => handleSearch(e.target.value)}
              style={{ paddingLeft: 32, width: '100%' }}
            />
          </div>
          {searchResults.length > 0 && (
            <div style={{ marginTop: 12 }}>
              {searchResults.map(c => (
                <div
                  key={c.company_name}
                  onClick={() => handleQuickNav(c.company_name)}
                  className="flex items-center justify-between cursor-pointer"
                  style={{
                    padding: '10px 12px', borderRadius: 6, marginBottom: 2,
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-raised)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <div>
                    <span style={{ fontWeight: 600 }}>{c.company_name}</span>
                    <span style={{ color: 'var(--text-muted)', marginLeft: 8, fontSize: '0.8rem' }}>
                      {c.hq_country} | {c.region}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      Score: {c.weighted_score.toFixed(2)}
                    </span>
                    <span className={`stage-badge stage-${c.pipeline_stage}`}>{c.pipeline_stage}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
          {searchQuery.length >= 2 && searchResults.length === 0 && !searching && (
            <p style={{ color: 'var(--text-muted)', marginTop: 12, fontSize: '0.85rem' }}>
              No companies found matching "{searchQuery}"
            </p>
          )}
        </div>
      </div>
    </>
  );
}
