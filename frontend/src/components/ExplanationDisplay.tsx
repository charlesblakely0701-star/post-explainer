import { Source } from '../api/client';

interface ExplanationDisplayProps {
  bullets: string[];
  sources: Source[];
  isStreaming: boolean;
  streamedText: string;
}

export function ExplanationDisplay({
  bullets,
  sources,
  isStreaming,
  streamedText,
}: ExplanationDisplayProps) {
  // If streaming, show the streamed text
  if (isStreaming || (!bullets.length && streamedText)) {
    return (
      <div className="animate-fade-in">
        <h3 className="text-lg font-semibold text-gray-200 mb-4 flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-coral-500 animate-pulse" />
          Generating explanation...
        </h3>
        
        <div className="bg-midnight-900/40 rounded-xl p-6 border border-midnight-700/30">
          <div className="prose prose-invert max-w-none">
            <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">
              {streamedText}
              <span className="inline-block w-2 h-5 bg-coral-500 animate-pulse ml-0.5" />
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Show completed explanation with bullets
  if (bullets.length > 0) {
    return (
      <div className="space-y-6 animate-fade-in">
        {/* Explanation bullets */}
        <div>
          <h3 className="text-lg font-semibold text-gray-200 mb-4 flex items-center gap-2">
            <CheckIcon />
            Explanation
          </h3>
          
          <div className="space-y-3">
            {bullets.map((bullet, index) => (
              <div
                key={index}
                className="flex items-start gap-3 animate-slide-up"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <span className="text-coral-500 mt-1 text-lg leading-none">•</span>
                <p className="text-gray-300 leading-relaxed flex-1">
                  {formatBulletWithCitations(bullet)}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Sources */}
        {sources.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">
              Sources
            </h3>
            
            <div className="space-y-2">
              {sources.map((source) => (
                <a
                  key={source.id}
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="
                    flex items-start gap-3 p-3 rounded-lg
                    bg-midnight-900/30 border border-midnight-700/20
                    hover:bg-midnight-800/40 hover:border-midnight-600/30
                    transition-all duration-200 group
                  "
                >
                  <span className="
                    flex-shrink-0 w-6 h-6 rounded-full
                    bg-midnight-700 text-gray-400
                    flex items-center justify-center
                    text-xs font-mono
                  ">
                    {source.id}
                  </span>
                  
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-300 font-medium truncate group-hover:text-coral-400 transition-colors">
                      {source.title}
                    </p>
                    <p className="text-xs text-gray-500 truncate mt-0.5">
                      {source.url}
                    </p>
                  </div>
                  
                  <ExternalLinkIcon />
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return null;
}

/**
 * Format bullet text, highlighting citation numbers.
 */
function formatBulletWithCitations(text: string): React.ReactNode {
  const parts = text.split(/(\[\d+\])/g);
  
  return parts.map((part, index) => {
    if (/^\[\d+\]$/.test(part)) {
      return (
        <span
          key={index}
          className="text-coral-400 font-mono text-sm"
        >
          {part}
        </span>
      );
    }
    return part;
  });
}

function CheckIcon() {
  return (
    <svg className="h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  );
}

function ExternalLinkIcon() {
  return (
    <svg className="h-4 w-4 text-gray-500 group-hover:text-gray-400 transition-colors flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
    </svg>
  );
}

