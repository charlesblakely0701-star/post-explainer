/**
 * API client for the Post Explainer backend.
 */

export interface Source {
  id: number;
  title: string;
  url: string;
  snippet?: string;
}

export interface ExplainResponse {
  bullets: string[];
  sources: Source[];
  cached: boolean;
}

export interface ProviderResult {
  bullets: string[];
  sources: Source[];
  error?: string;
}

export interface CompareResponse {
  providers: Record<string, ProviderResult>;
  available_providers: string[];
}

export interface StreamCallbacks {
  onSources: (sources: Source[]) => void;
  onChunk: (text: string) => void;
  onComplete: () => void;
  onError: (error: Error) => void;
}

const API_BASE = '/api';

/**
 * Explain a post (non-streaming).
 */
export async function explainPost(text: string, imageUrl?: string): Promise<ExplainResponse> {
  const response = await fetch(`${API_BASE}/explain`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text, image_url: imageUrl }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to explain post');
  }

  return response.json();
}

/**
 * Compare explanations from multiple providers.
 */
export async function compareProviders(text: string, imageUrl?: string): Promise<CompareResponse> {
  const response = await fetch(`${API_BASE}/explain/compare`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text, image_url: imageUrl }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to compare providers');
  }

  return response.json();
}

/**
 * Explain a post with streaming response.
 */
export function explainPostStream(
  text: string,
  callbacks: StreamCallbacks
): () => void {
  const abortController = new AbortController();

  (async () => {
    try {
      const response = await fetch(`${API_BASE}/explain/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        throw new Error('Failed to start stream');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let currentEvent = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          callbacks.onComplete();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          // Track event type
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim();
            continue;
          }
          
          if (line.startsWith('data:')) {
            const data = line.slice(5).trim();
            if (!data) continue;
            
            try {
              const parsed = JSON.parse(data);
              
              // Handle based on event type
              if (currentEvent === 'sources') {
                callbacks.onSources(parsed);
              } else if (currentEvent === 'chunk') {
                if (parsed.text) {
                  callbacks.onChunk(parsed.text);
                }
              } else if (currentEvent === 'done') {
                callbacks.onComplete();
              } else if (currentEvent === 'error') {
                callbacks.onError(new Error(parsed.error || 'Unknown error'));
              } else if (parsed.text) {
                // Fallback for chunk data
                callbacks.onChunk(parsed.text);
              } else if (parsed.status === 'complete') {
                callbacks.onComplete();
              }
            } catch {
              // Not JSON, skip
            }
            
            // Reset event after processing data
            currentEvent = '';
          }
        }
      }
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
        callbacks.onError(error as Error);
      }
    }
  })();

  return () => abortController.abort();
}

/**
 * Health check.
 */
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

