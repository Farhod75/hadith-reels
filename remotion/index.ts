// remotion/index.ts
// Composition registry — registers all reel compositions with Remotion

import { Composition } from 'remotion'
import { HadithReel, type HadithReelProps } from './compositions/HadithReel'
import { KidsReel, type KidsReelProps } from './compositions/KidsReel'

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Adults composition — dark elegant */}
      <Composition
        id="HadithReel"
        component={HadithReel}
        durationInFrames={1800}  // 60 seconds at 30fps
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          hadithArabic:  'الصِّيَامُ جُنَّةٌ',
          hadithText:    'Fasting is a shield.',
          narrator:      'Abu Hurairah',
          collection:    'Sahih al-Bukhari',
          hadithNumber:  '1894',
          story:         'One day the Prophet ﷺ saw his companions struggling with their desires...',
          moral:         'Protect yourself with fasting — it shields you from harm.',
          seerahContext: 'During the blessed month of Ramadan in Madinah...',
          attribution:   '📖 Source: Ar-Raheeq Al-Makhtum',
          lang:          'en',
          audioUrl:      undefined,
        } as HadithReelProps}
      />

      {/* Kids composition — bright colorful */}
      <Composition
        id="KidsReel"
        component={KidsReel}
        durationInFrames={1800}  // 60 seconds at 30fps
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          hadithArabic: 'تَبَسُّمُكَ فِي وَجْهِ أَخِيكَ لَكَ صَدَقَةٌ',
          hadithText:   'Your smile for your brother is charity!',
          narrator:     'Abu Dharr',
          collection:   'Jami at-Tirmidhi',
          story:        'One day a young boy came to the Prophet ﷺ feeling sad...',
          moral:        'A simple smile can make someone\'s whole day better!',
          lang:         'en',
          audioUrl:     undefined,
        } as KidsReelProps}
      />
    </>
  )
}
