import { useState, useCallback } from 'react';
import { PostInput } from './components/PostInput';
import { ExplanationDisplay } from './components/ExplanationDisplay';
import { ComparisonDisplay } from './components/ComparisonDisplay';
import { ExamplePosts } from './components/ExamplePosts';
import { ErrorDisplay } from './components/ErrorDisplay';
import { LoadingSkeleton } from './components/LoadingSkeleton';
import { explainPostStream, compareProviders, Source, CompareResponse } from './api/client';

type AppState = 'idle' | 'loading' | 'streaming' | 'complete' | 'comparing' | 'compared' | 'error';

function App() {
  const [state, setState] = useState<AppState>('idle');
  const [postText, setPostText] = useState('');
  const [bullets, setBullets] = useState<string[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [streamedText, setStreamedText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [comparisonData, setComparisonData] = useState<CompareResponse | null>(null);

  const handleExplain = useCallback((text: string, imageUrl?: string, compare?: boolean) => {
    setPostText(text);
    setBullets([]);
    setSources([]);
    setStreamedText('');
    setError(null);
    setComparisonData(null);

    if (compare) {
      // Use comparison mode
      setState('comparing');
      compareProviders(text, imageUrl)
        .then((data) => {
          setComparisonData(data);
          setState('compared');
        })
        .catch((err) => {
          setError(err.message);
          setState('error');
        });
      return;
    }

    // Use streaming mode
    setState('loading');

    const cancel = explainPostStream(text, {
      onSources: (newSources) => {
        setSources(newSources);
        setState('streaming');
      },
      onChunk: (chunk) => {
        setStreamedText((prev) => prev + chunk);
      },
      onComplete: () => {
        setState('complete');
        // Parse bullets from streamed text
        setStreamedText((prev) => {
          const parsedBullets = parseBullets(prev);
          setBullets(parsedBullets);
          return prev;
        });
      },
      onError: (err) => {
        setError(err.message);
        setState('error');
      },
    });

    return cancel;
  }, []);

  const handleExampleSelect = useCallback((text: string) => {
    handleExplain(text);
  }, [handleExplain]);

  const handleReset = useCallback(() => {
    setState('idle');
    setPostText('');
    setBullets([]);
    setSources([]);
    setStreamedText('');
    setError(null);
  }, []);

  const isLoading = state === 'loading' || state === 'streaming' || state === 'comparing';

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-midnight-800/50 backdrop-blur-sm sticky top-0 z-10 bg-midnight-950/80">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-coral-500 to-coral-600 flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-100">Post Explainer</h1>
                <p className="text-xs text-gray-500">Understand any social media post</p>
              </div>
            </div>

            {(state === 'complete' || state === 'compared') && (
              <button
                onClick={handleReset}
                className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors"
              >
                ← New post
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="space-y-8">
          {/* Hero text - only show on idle */}
          {state === 'idle' && (
            <div className="text-center py-8 animate-fade-in">
              <h2 className="text-3xl font-bold text-gray-100 mb-3">
                What does this post <span className="text-coral-500">mean</span>?
              </h2>
              <p className="text-gray-400 max-w-xl mx-auto">
                Paste any confusing social media post and get a clear explanation with context and sources.
              </p>
            </div>
          )}

          {/* Input section */}
          <div className={(state === 'complete' || state === 'compared') ? 'opacity-50' : ''}>
            <PostInput onSubmit={handleExplain} isLoading={isLoading} />
          </div>

          {/* Examples - only show on idle */}
          {state === 'idle' && (
            <ExamplePosts onSelect={handleExampleSelect} disabled={isLoading} />
          )}

          {/* Loading state */}
          {(state === 'loading' || state === 'comparing') && (
            <div className="py-8">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-2 h-2 rounded-full bg-coral-500 animate-pulse" />
                <span className="text-gray-400">
                  {state === 'comparing' ? 'Comparing providers...' : 'Searching for context...'}
                </span>
              </div>
              <LoadingSkeleton />
            </div>
          )}

          {/* Explanation display */}
          {(state === 'streaming' || state === 'complete') && (
            <div className="py-4">
              <ExplanationDisplay
                bullets={bullets}
                sources={sources}
                isStreaming={state === 'streaming'}
                streamedText={streamedText}
              />
            </div>
          )}

          {/* Comparison display */}
          {state === 'compared' && comparisonData && (
            <div className="py-4">
              <ComparisonDisplay data={comparisonData} />
            </div>
          )}

          {/* Error state */}
          {state === 'error' && error && (
            <ErrorDisplay
              message={error}
              onRetry={() => handleExplain(postText)}
            />
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-midnight-800/50 mt-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <p className="text-center text-xs text-gray-600">
            Powered by AI • Sources are searched in real-time • Results may not always be accurate
          </p>
        </div>
      </footer>
    </div>
  );
}

/**
 * Parse bullet points from the streamed LLM response.
 */
function parseBullets(text: string): string[] {
  const bullets: string[] = [];
  const lines = text.trim().split('\n');

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    // Remove bullet markers
    const cleaned = trimmed
      .replace(/^[•\-\*]\s*/, '')
      .replace(/^\d+[\.\)]\s*/, '');

    if (cleaned && cleaned.length > 10) {
      bullets.push(cleaned);
    }
  }

  return bullets.slice(0, 5);
}

export default App;

