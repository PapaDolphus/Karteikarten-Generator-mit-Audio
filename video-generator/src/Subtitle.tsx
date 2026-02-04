import { useCurrentFrame, useVideoConfig } from 'remotion';

interface Word {
    word: string;
    start: number;
    end: number;
}

const WORDS_PER_PAGE = 4; // Smaller chunks for mobile readability

export const Subtitles: React.FC<{ subtitles: Word[] }> = ({ subtitles }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const currentTime = frame / fps;

    if (!subtitles || subtitles.length === 0) return null;

    // Find active word and page logic
    let activeWordIndex = subtitles.findIndex(w => currentTime >= w.start && currentTime <= w.end);

    if (activeWordIndex === -1) {
        // Look back to see if we just passed a word
        activeWordIndex = subtitles.findLastIndex(w => w.end <= currentTime);
        // If totally before
        if (activeWordIndex === -1 && currentTime < subtitles[0].start) {
            activeWordIndex = 0;
        }
        // If totally after
        if (currentTime > subtitles[subtitles.length - 1].end) {
            activeWordIndex = subtitles.length - 1;
        }
    }

    const pageIndex = Math.floor(activeWordIndex / WORDS_PER_PAGE);
    const pageStartWord = pageIndex * WORDS_PER_PAGE;
    // Limit to subtitles length
    const pageEndWord = Math.min((pageIndex + 1) * WORDS_PER_PAGE, subtitles.length);

    const currentWords = subtitles.slice(pageStartWord, pageEndWord);

    // Calculate strict active index for highlighting
    const strictlyActiveIndex = subtitles.findIndex(w => currentTime >= w.start && currentTime <= (w.end + 0.1));

    return (
        <div style={{
            position: 'absolute',
            bottom: 250, // Higher up
            left: 0,
            width: '100%',
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 24, // More space
            padding: '0 80px',
        }}>
            {currentWords.map((w, i) => {
                const globalIndex = pageStartWord + i;
                const isActive = globalIndex === strictlyActiveIndex;

                return (
                    <span
                        key={globalIndex}
                        style={{
                            fontFamily: "'Montserrat', sans-serif",
                            fontSize: isActive ? 70 : 60,
                            fontWeight: 900,
                            textTransform: 'uppercase',
                            color: isActive ? '#FF3B30' : 'white',
                            textShadow: '0 4px 20px rgba(0,0,0,0.8)',
                            transform: isActive ? 'scale(1.1)' : 'scale(1)',
                            transition: 'all 0.1s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                            display: 'inline-block',
                            zIndex: isActive ? 10 : 1
                        }}
                    >
                        {w.word}
                    </span>
                );
            })}
        </div>
    );
};
