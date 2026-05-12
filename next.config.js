/** @type {import('next').NextConfig} */
const nextConfig = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline' https://www.googletagmanager.com",
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data: blob: https:",
              // ElevenLabs TTS audio + blob URLs for audio playback
              "media-src 'self' blob: https://api.elevenlabs.io",
              "connect-src 'self' https://api.anthropic.com https://api.elevenlabs.io https://xeirfeqnbjfyszykiraa.supabase.co",
              "font-src 'self' https://fonts.gstatic.com",
              "frame-src 'none'",
            ].join('; '),
          },
          {
            key: 'Permissions-Policy',
            // microphone=(self) — needed for voice search
            value: 'camera=(), microphone=(self), geolocation=()',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig
