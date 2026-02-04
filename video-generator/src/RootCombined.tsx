import { registerRoot, Composition } from 'remotion';
import { SingleFlashcardComposition } from './Root';
import { Compilation } from './Compilation';
import compilationData from './compilation.json';
import './style.css';

// We need a separate Root or just register both compositions here?
// 'registerRoot' can only be called once? 
// No, the standard way is to export a RemotionRoot component that has multiple compositions.

export const RemotionRoot: React.FC = () => {
    // Calculate total duration for compilation
    // Default to empty array if json not found (compilationData might be missing in some envs) OR handled via require
    const cards = (compilationData as any).cards || [];
    const totalFrames = cards.reduce((acc: number, c: any) => acc + c.durationInFrames, 0) || 300;

    return (
        <>
            {/* Single Video Mode (Keep as Default or Secondary) */}
            <SingleFlashcardComposition />

            {/* Compilation Mode */}
            <Composition
                id="CompilationVideo"
                component={Compilation}
                durationInFrames={totalFrames}
                fps={30}
                width={1080}
                height={1920}
                defaultProps={{
                    cards: cards
                }}
            />
        </>
    );
};

// We need to verify if SingleRoot also calls registerRoot? 
// The previous index.ts registered Root.tsx
// I should make THIS file the new Root and update index.ts to register IT.
