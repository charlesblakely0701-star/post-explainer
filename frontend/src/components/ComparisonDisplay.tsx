import { CompareResponse, Source } from '../api/client';

interface ComparisonDisplayProps {
  data: CompareResponse;
}

export function ComparisonDisplay({ data }: ComparisonDisplayProps) {
  const providers = Object.entries(data.providers);

  return (
    <div className="space-y-6 animate-fade-in">
      <h3 className="text-lg font-semibold text-gray-200 flex items-center gap-2">
        <CompareIcon />
        Provider Comparison
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {providers.map(([name, result]) => (
          <div
            key={name}
            className="bg-midnight-900/40 rounded-xl p-5 border border-midnight-700/30"
          >
            {/* Provider header */}
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-midnight-700/30">
              <ProviderIcon name={name} />
              <span className="font-medium text-gray-200 capitalize">
                {name === 'openai' ? 'GPT-4o' : name === 'anthropic' ? 'Claude' : name}
              </span>
            </div>

            {/* Error state */}
            {result.error && (
              <div className="text-red-400 text-sm">
                {result.error}
              </div>
            )}

            {/* Bullets */}
            {!result.error && result.bullets.length > 0 && (
              <div className="space-y-2">
                {result.bullets.map((bullet, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <span className="text-coral-500 mt-0.5 text-sm">•</span>
                    <p className="text-gray-300 text-sm leading-relaxed">
                      {formatBulletWithCitations(bullet)}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {/* Sources */}
            {!result.error && result.sources.length > 0 && (
              <div className="mt-4 pt-3 border-t border-midnight-700/30">
                <p className="text-xs text-gray-500 mb-2">Sources:</p>
                <div className="space-y-1">
                  {result.sources.slice(0, 3).map((source) => (
                    <a
                      key={source.id}
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-xs text-gray-400 hover:text-coral-400 truncate"
                    >
                      [{source.id}] {source.title}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Available providers note */}
      <p className="text-xs text-gray-500 text-center">
        Available providers: {data.available_providers.join(', ')}
      </p>
    </div>
  );
}

function formatBulletWithCitations(text: string): React.ReactNode {
  const parts = text.split(/(\[\d+\])/g);
  
  return parts.map((part, index) => {
    if (/^\[\d+\]$/.test(part)) {
      return (
        <span key={index} className="text-coral-400 font-mono text-xs">
          {part}
        </span>
      );
    }
    return part;
  });
}

function CompareIcon() {
  return (
    <svg className="h-5 w-5 text-coral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  );
}

function ProviderIcon({ name }: { name: string }) {
  if (name === 'openai') {
    return (
      <div className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
        <span className="text-emerald-400 text-xs font-bold">O</span>
      </div>
    );
  }
  if (name === 'anthropic') {
    return (
      <div className="w-6 h-6 rounded-full bg-orange-500/20 flex items-center justify-center">
        <span className="text-orange-400 text-xs font-bold">A</span>
      </div>
    );
  }
  return (
    <div className="w-6 h-6 rounded-full bg-gray-500/20 flex items-center justify-center">
      <span className="text-gray-400 text-xs font-bold">?</span>
    </div>
  );
}

