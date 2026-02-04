import { useCurrentFrame, useVideoConfig, spring } from 'remotion';

interface ContentItem {
    text: string;
    startFrame: number;
}

interface Content {
    intro: string;
    items: ContentItem[];
}

export const VisualModel: React.FC<{ content: Content }> = ({ content }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const hasItems = content.items.length > 0;

    if (!hasItems) {
        return (
            <div style={{
                fontSize: 40,
                lineHeight: 1.5,
                textAlign: 'center',
                whiteSpace: 'pre-wrap',
                fontWeight: 700,
                textShadow: '0 4px 20px rgba(0,0,0,0.5)'
            }}>
                {content.intro || "..."}
            </div>
        );
    }

    // Auto-Scroll Logic
    const ITEM_HEIGHT_ESTIMATE = 220; // Approx height of box + gap
    const SCROLL_THRESHOLD_INDEX = 2; // Keep top 2 items visible, then scroll

    let currentScroll = 0;

    content.items.forEach((item, index) => {
        // If an item beyond threshold has started appearing
        if (index > SCROLL_THRESHOLD_INDEX) {
            const scrollStartFrame = item.startFrame;
            // Animate the scroll contribution of this item
            const scrollProgress = spring({
                frame: frame - scrollStartFrame,
                fps,
                config: { damping: 15, stiffness: 80 }
            });
            currentScroll += scrollProgress * ITEM_HEIGHT_ESTIMATE;
        }
    });

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 40,
            width: '100%',
            padding: '0 40px',
            transform: `translateY(-${currentScroll}px)`, // Apply the calculated scroll
            willChange: 'transform' // Optim
        }}>
            {content.items.map((item, index) => {
                const itemStart = item.startFrame;

                // Spring animation for Pop-In
                const spr = spring({
                    frame: frame - itemStart,
                    fps,
                    config: {
                        damping: 12,
                        stiffness: 100,
                    }
                });

                // Determine Active State
                const nextItemStart = content.items[index + 1]?.startFrame || Infinity;
                const isFuture = frame < itemStart;
                const isCurrent = frame >= itemStart && frame < nextItemStart;

                const opacity = isFuture ? 0 : 1;
                const scale = isFuture ? 0 : spr;

                // Styles for Active vs Inactive
                const activeColor = '#ffffff';
                const inactiveColor = 'rgba(255,255,255,0.4)'; // Dimmed more

                const activeBg = 'rgba(255,255,255,0.15)';
                const inactiveBg = 'rgba(255,255,255,0.02)'; // Nearly invisible

                return (
                    <div
                        key={index}
                        style={{
                            opacity,
                            transform: `scale(${scale})`,
                            backgroundColor: isCurrent ? activeBg : inactiveBg,
                            padding: '30px 40px',
                            borderRadius: 24,
                            fontSize: isCurrent ? 50 : 40,
                            fontWeight: isCurrent ? 900 : 700,
                            color: isCurrent ? activeColor : inactiveColor,
                            border: isCurrent ? '4px solid rgba(255,255,255,0.3)' : '4px solid transparent',
                            boxShadow: isCurrent ? '0 10px 40px rgba(0,0,0,0.3)' : 'none',
                            transition: 'all 0.5s ease'
                        }}
                    >
                        {item.text}
                    </div>
                );
            })}
        </div>
    );
};
