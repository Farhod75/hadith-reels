/** @type {import('next').NextConfig} */
const nextConfig = {
  // P054/P055: Externalize Remotion native binaries from Next.js build
  // Next.js 15+: use serverExternalPackages (not experimental.serverComponentsExternalPackages)
  // Next.js 16+: uses Turbopack by default — no webpack config needed
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

  // Silence Turbopack warning — we have no webpack customizations
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
              "connect-src 'self' https://api.anthropic.com https://api.elevenlabs.io https://xeirfeqnbjfyszykiraa.supabase.co",
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
