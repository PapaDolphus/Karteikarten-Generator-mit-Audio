import { AbsoluteFill, Audio, staticFile, useVideoConfig, useCurrentFrame, interpolate } from 'remotion';
import { Subtitles } from './Subtitle';
import { VisualModel } from './VisualModel';

interface Word {
    word: string;
    start: number;
    end: number;
}

interface ContentItem {
    text: string;
    startFrame: number;
}

interface Content {
    question: string;
    items: ContentItem[];
    intro: string;
}

export interface FlashcardVideoProps {
    audioUrl: string;
    subtitles: Word[];
    content: Content;
}

// Reusable Scene Component
export const FlashcardScene: React.FC<FlashcardVideoProps> = ({ audioUrl, subtitles, content }) => {
    const { fps, durationInFrames } = useVideoConfig(); // Inherits from Sequence or Composition
    const frame = useCurrentFrame();
    const audioSrc = staticFile(audioUrl);

    // Animated Gradient Background
    const shift = interpolate(frame, [0, durationInFrames], [0, 360]);

    const backgroundStyle: React.CSSProperties = {
        background: `linear-gradient(${shift}deg, #121212 0%, #2a2a2a 100%)`,
    };

    // ... rest of the render logic ...
    return (
        <AbsoluteFill style={{ ...backgroundStyle, color: 'white' }}>
            <AbsoluteFill style={{
                opacity: 0.05,
                backgroundImage: 'radial-gradient(circle at 50% 50%, white 1px, transparent 1px)',
                backgroundSize: '40px 40px'
            }} />

            <AbsoluteFill style={{ padding: '80px 40px', alignItems: 'center' }}>
                <h1 style={{
                    fontSize: 48,
                    textAlign: 'center',
                    marginBottom: 60,
                    color: '#4da6ff',
                    textTransform: 'uppercase',
                    letterSpacing: 2,
                    opacity: 0.9,
                    maxHeight: 200, // Limit height
                    overflow: 'hidden'
                }}>
                    {content.question}
                </h1>

                <div style={{ flex: 1, width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'flex-start', paddingTop: 40 }}>
                    <VisualModel content={content} />
                </div>

                <div style={{ height: 350 }} />
            </AbsoluteFill>

            <Subtitles subtitles={subtitles} />

            <Audio src={audioSrc} />
        </AbsoluteFill>
    );
};

// Wrapper for Single Video
export const FlashcardVideo: React.FC<FlashcardVideoProps> = (props) => {
    return <FlashcardScene {...props} />;
};
