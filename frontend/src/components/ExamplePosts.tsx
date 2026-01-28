import { EXAMPLE_POSTS } from '../data/examples';

interface ExamplePostsProps {
  onSelect: (text: string) => void;
  disabled: boolean;
}

export function ExamplePosts({ onSelect, disabled }: ExamplePostsProps) {
  return (
    <div>
      <h3 className="text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">
        Try an example
      </h3>
      
      <div className="flex flex-wrap gap-2">
        {EXAMPLE_POSTS.map((post) => (
          <button
            key={post.id}
            onClick={() => onSelect(post.text)}
            disabled={disabled}
            className={`
              px-3 py-2 rounded-lg text-sm
              bg-midnight-800/60 border border-midnight-700/40
              transition-all duration-200
              ${disabled
                ? 'opacity-50 cursor-not-allowed'
                : 'hover:bg-midnight-700/60 hover:border-coral-500/30 hover:text-coral-400'
              }
            `}
          >
            <span className="text-gray-500 mr-1.5">{post.category}:</span>
            <span className="text-gray-300">
              {post.text.length > 50 ? post.text.slice(0, 50) + '...' : post.text}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

