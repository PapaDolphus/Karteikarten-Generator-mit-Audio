import { Composition } from 'remotion';
import { FlashcardVideo } from './Composition';
import data from './video-data.json';
import './style.css';

export const SingleFlashcardComposition: React.FC = () => {
    const duration = data.durationInFrames || 300;
    return (
        <Composition
            id="FlashcardVideo"
            component={FlashcardVideo}
            durationInFrames={duration}
            fps={30}
            width={1080}
            height={1920}
            defaultProps={{
                audioUrl: data.audioUrl,
                subtitles: (data.subtitles as any),
                content: (data.content as any),
            }}
        />
    );
};
