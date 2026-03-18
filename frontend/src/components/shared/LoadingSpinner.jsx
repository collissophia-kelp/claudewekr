import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ text = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <Loader2 size={32} className="animate-spin" style={{ color: 'var(--interactive)' }} />
      <span style={{ color: 'var(--text-muted)' }}>{text}</span>
    </div>
  );
}
