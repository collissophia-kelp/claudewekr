import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { api } from '../../utils/api';
import LoadingSpinner from '../shared/LoadingSpinner';
import TierBadge from '../shared/TierBadge';
import StageBadge from '../shared/StageBadge';
import ScorePanel from './ScorePanel';
import CompanyOverview from './CompanyOverview';
import BusinessCaseView from '../business-case/BusinessCaseView';
import FarmerROICard from '../farmer-roi/FarmerROICard';

export default function CompanyProfilePage() {
  const { companyName } = useParams();
  const navigate = useNavigate();
  const [company, setCompany] = useState(null);
  const [weights, setWeights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.getCompany(decodeURIComponent(companyName)),
      api.getScoringConfig(),
    ])
      .then(([c, cfg]) => {
        setCompany(c);
        setWeights(cfg.scoring_weights);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [companyName]);

  const handleScoreSave = async (scores) => {
    try {
      const updated = await api.updateScores(company.company_name, scores);
      setCompany(updated);
    } catch (err) {
      alert('Failed to save scores: ' + err.message);
    }
  };

  if (loading) return <LoadingSpinner text="Loading company..." />;
  if (error) return (
    <div className="page-body">
      <p style={{ color: 'var(--danger)' }}>Error: {error}</p>
      <button className="btn" onClick={() => navigate(-1)}>Go Back</button>
    </div>
  );
  if (!company) return (
    <div className="page-body">
      <p>Company not found.</p>
      <button className="btn" onClick={() => navigate('/directory')}>Back to Directory</button>
    </div>
  );

  return (
    <>
      <div className="page-header">
        <div className="flex items-center gap-3">
          <button className="btn btn-sm" onClick={() => navigate(-1)} title="Back">
            <ArrowLeft size={16} />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 style={{ margin: 0 }}>{company.company_name}</h1>
              <TierBadge tier={company.tier} label={company.tier_label} />
              <StageBadge stage={company.pipeline_stage} />
            </div>
            <p style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
              {company.hq_country} | {company.region} | {company.pipeline_owner || 'Unassigned'}
            </p>
          </div>
        </div>
      </div>
      <div className="page-body">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <ScorePanel company={company} weights={weights} onSave={handleScoreSave} />
          <CompanyOverview company={company} />
        </div>

        <BusinessCaseView companyName={company.company_name} hectares={company.hectares_controlled} />

        {company.main_crops.length > 0 && (
          <div className="mt-4">
            <FarmerROICard
              defaultCrop={company.main_crops[0]}
              defaultCountry={company.hq_country}
            />
          </div>
        )}
      </div>
    </>
  );
}
