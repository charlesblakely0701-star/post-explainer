import { useState, useCallback } from 'react';

interface PostInputProps {
  onSubmit: (text: string, imageUrl?: string, compare?: boolean) => void;
  isLoading: boolean;
}

export function PostInput({ onSubmit, isLoading }: PostInputProps) {
  const [text, setText] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [showImageInput, setShowImageInput] = useState(false);

  const handleSubmit = useCallback(
    (e: React.FormEvent, compare: boolean = false) => {
      e.preventDefault();
      if (text.trim() && !isLoading) {
        onSubmit(text.trim(), imageUrl.trim() || undefined, compare);
      }
    },
    [text, imageUrl, isLoading, onSubmit]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        handleSubmit(e);
      }
    },
    [handleSubmit]
  );

  const charCount = text.length;
  const maxChars = 2000;
  const isOverLimit = charCount > maxChars;

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Paste a social media post here... What needs explaining?"
          className={`
            w-full min-h-[140px] p-5 rounded-xl
            bg-midnight-900/60 backdrop-blur-sm
            border-2 transition-all duration-300
            text-gray-100 placeholder:text-gray-500
            font-sans text-base leading-relaxed
            resize-none
            ${isOverLimit 
              ? 'border-red-500/50 focus:border-red-500' 
              : 'border-midnight-700/50 focus:border-coral-500/50'
            }
          `}
          disabled={isLoading}
        />
        
        {/* Character count */}
        <div className={`
          absolute bottom-3 right-3 text-xs font-mono
          ${isOverLimit ? 'text-red-400' : 'text-gray-500'}
        `}>
          {charCount} / {maxChars}
        </div>
      </div>

      {/* Image URL input (collapsible) */}
      <div className="mt-3">
        <button
          type="button"
          onClick={() => setShowImageInput(!showImageInput)}
          className="text-xs text-gray-400 hover:text-coral-400 transition-colors flex items-center gap-1"
        >
          <ImageIcon />
          {showImageInput ? 'Hide image URL' : 'Add image URL (optional)'}
        </button>
        
        {showImageInput && (
          <input
            type="url"
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            placeholder="https://example.com/image.jpg"
            className="
              mt-2 w-full px-4 py-2 rounded-lg
              bg-midnight-900/40 border border-midnight-700/30
              text-gray-300 placeholder:text-gray-600
              text-sm focus:border-coral-500/50
            "
            disabled={isLoading}
          />
        )}
      </div>

      {/* Submit buttons */}
      <div className="mt-4 flex items-center justify-between">
        <span className="text-xs text-gray-500">
          Press <kbd className="px-1.5 py-0.5 rounded bg-midnight-800 text-gray-400 font-mono">Ctrl</kbd> + <kbd className="px-1.5 py-0.5 rounded bg-midnight-800 text-gray-400 font-mono">Enter</kbd> to submit
        </span>
        
        <div className="flex gap-2">
          {/* Compare button */}
          <button
            type="button"
            onClick={(e) => handleSubmit(e, true)}
            disabled={isLoading || !text.trim() || isOverLimit}
            className={`
              px-4 py-3 rounded-lg font-medium text-sm
              transition-all duration-300
              flex items-center gap-2
              ${isLoading || !text.trim() || isOverLimit
                ? 'bg-midnight-800 text-gray-500 cursor-not-allowed'
                : 'bg-midnight-700 text-gray-300 hover:bg-midnight-600 hover:text-white border border-midnight-600'
              }
            `}
            title="Compare GPT-4 vs Claude"
          >
            <CompareIcon />
            Compare
          </button>

          {/* Main submit button */}
          <button
            type="submit"
            disabled={isLoading || !text.trim() || isOverLimit}
            className={`
              px-6 py-3 rounded-lg font-medium
              transition-all duration-300
              flex items-center gap-2
              ${isLoading || !text.trim() || isOverLimit
                ? 'bg-midnight-800 text-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-coral-500 to-coral-600 text-white hover:from-coral-400 hover:to-coral-500 hover:shadow-lg hover:shadow-coral-500/25'
              }
            `}
          >
            {isLoading ? (
              <>
                <LoadingSpinner />
                Analyzing...
              </>
            ) : (
              <>
                <ExplainIcon />
                Explain This
              </>
            )}
          </button>
        </div>
      </div>
    </form>
  );
}

function LoadingSpinner() {
  return (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
        fill="none"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

function ExplainIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
      />
    </svg>
  );
}

function ImageIcon() {
  return (
    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  );
}

function CompareIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  );
}

