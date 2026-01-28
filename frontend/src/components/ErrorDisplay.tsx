interface ErrorDisplayProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorDisplay({ message, onRetry }: ErrorDisplayProps) {
  return (
    <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6 animate-fade-in">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          <svg className="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        
        <div className="flex-1">
          <h3 className="text-red-400 font-medium">Something went wrong</h3>
          <p className="text-red-300/80 text-sm mt-1">{message}</p>
          
          {onRetry && (
            <button
              onClick={onRetry}
              className="
                mt-3 px-4 py-2 text-sm
                bg-red-500/20 hover:bg-red-500/30
                text-red-300 rounded-lg
                transition-colors duration-200
              "
            >
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

