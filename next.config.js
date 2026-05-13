/** @type {import('next').NextConfig} */
const nextConfig = {
  serverExternalPackages: [
    '@remotion/renderer',
    '@remotion/bundler',
    '@remotion/compositor-win32-x64-msvc',
    '@remotion/compositor-linux-x64-gnu',
    '@remotion/compositor-linux-x64-musl',
    '@remotion/compositor-darwin-x64',
    '@remotion/compositor-darwin-arm64',
    'remotion',
  ],

  turbopack: {},

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
              "media-src 'self' blob: https://api.elevenlabs.io",
              "connect-src 'self' https://api.anthropic.com https://api.elevenlabs.io https://xeirfeqnbjfyszykiraa.supabase.co https://queue.fal.run https://v3b.fal.media",
              "font-src 'self' https://fonts.gstatic.com",
              "frame-src 'none'",
            ].join('; '),
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(self), geolocation=()',
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig