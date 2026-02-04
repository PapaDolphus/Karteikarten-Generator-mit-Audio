import { Series } from 'remotion';
import { FlashcardScene, FlashcardVideoProps } from './Composition';

interface CardData extends FlashcardVideoProps {
    id: number;
    durationInFrames: number;
}

interface CompilationProps {
    cards: CardData[];
}

export const Compilation: React.FC<CompilationProps> = ({ cards }) => {
    return (
        <Series>
            {cards.map((card, i) => (
                <Series.Sequence key={card.id} durationInFrames={card.durationInFrames}>
                    <FlashcardScene
                        audioUrl={card.audioUrl}
                        subtitles={card.subtitles}
                        content={card.content}
                    />
                </Series.Sequence>
            ))}
        </Series>
    );
};
