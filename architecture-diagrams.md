# HV + HR Architecture Diagrams

Source-of-truth diagrams for the Hadith Verifier + Hadith Reels ecosystem.

All diagrams in Mermaid format — text, version-controlled, renders in GitHub/VS Code/Claude.ai natively.

---

## Diagram 1 — HV Full Agent Workflow (currently live)

```mermaid
graph TD
    %% User inputs
    A1[Web app<br/>hadithverifier.com]
    A2[Telegram bot<br/>Railway · Python]
    A3[Screenshot upload<br/>Claude Vision API]
    
    %% Agent 1: Claude Analyze
    B[🤖 Claude Analyze Agent<br/>app/api/analyze/route.ts<br/>Sonnet · verdict + severity + seerah_context + comment]
    
    A1 --> B
    A2 --> B
    A3 --> B
    
    %% Verdict outputs
    B --> C1[🔴 CRITICAL / HIGH<br/>fabricated · triggers alerts]
    B --> C2[🟡 MEDIUM<br/>weak · saved to queue]
    B --> C3[🟢 LOW<br/>authentic · no action]
    
    %% Agents 2 · 3 · 4
    C1 --> D1[🤖 Telegram alert<br/>Railway Python bot]
    C1 --> D2[🤖 Slack alert<br/>Webhook from analyze route]
    C2 --> D3[🤖 Queue agent<br/>Supabase flagged_posts]
    
    %% Shared data layer
    D3 --> E[(Supabase shared DB<br/>flagged_posts · hadith_library · hadith_reels · quran_library)]
    
    %% Agents 5 · 6
    E --> F1[🤖 Dua corrector agent<br/>app/api/dua · Claude Vision + Sonnet]
    E --> F2[🤖 Search agent<br/>app/api/search · hadith_library query]
    
    F1 --> G1[Admin queue UI<br/>Human review · approve/dismiss]
    F2 --> G2[TTS player<br/>ElevenLabs + browser fallback]
    
    style B fill:#d4f4dd
    style D1 fill:#e6d4ff
    style D2 fill:#e6d4ff
    style D3 fill:#d4f4dd
    style F1 fill:#d4f4dd
    style F2 fill:#d4f4dd
```

**Pending HV features (not yet built):**
- ShareCard (P-pending)
- User History
- PWA mode
- Bookmarklet
- Email digest
- ElevenLabs CSP fix on production

---

## Diagram 2 — HR Planned Agent Workflow (post-Hajj 06/06+)

```mermaid
graph TD
    %% Data source (shared with HV)
    A[(hadith_library<br/>70 sahih hadiths · 134 tags<br/>shared Supabase)]
    
    %% Planned agent 1: Daily cron
    A --> B[⏰ Daily cron agent<br/>Picks 1 sahih hadith<br/>Triggers Claude story generation<br/>Runs at 06:00 UTC daily]
    
    %% Planned agents 2 · 3
    B --> C1[📝 Claude story agent<br/>Sonnet · story + moral + seerah_context<br/>Adults + Kids variants]
    B --> C2[🎤 TTS agent<br/>gpt-4o-mini-tts + ElevenLabs<br/>Hijazi · Abrar · Nova · Onyx · James · Danielle<br/>AR/UZ/RU/EN/TJ narration]
    
    %% Planned agent 4: Render
    C1 --> D[🎬 Remotion render agent<br/>HadithReel.tsx Adults dark<br/>KidsReel.tsx colorful<br/>Exports MP4 · 1 of each per day]
    C2 --> D
    
    %% Planned agent 5: DB save
    D --> E[💾 hadith_reels DB agent<br/>Saves reel record to Supabase<br/>HV Search tab shows Watch Reel button per hadith]
    
    %% Validation agents (also planned)
    C2 -.validation.-> V1[🔍 TTS-validating agent<br/>SKILL.md exists]
    D -.validation.-> V2[🔍 STT-validating agent]
    C1 -.validation.-> V3[🔍 A/B-comparing agent<br/>Claude + ChatGPT + Kimi]
    
    %% Final distribution
    E --> F[Telegram · Instagram · TikTok · YouTube · hadithreels.com]
    
    style B fill:#ffe6c4
    style C1 fill:#ffe6c4
    style C2 fill:#ffe6c4
    style D fill:#ffe6c4
    style E fill:#ffe6c4
    style V1 fill:#cce5ff
    style V2 fill:#cce5ff
    style V3 fill:#cce5ff
```

---

## Diagram 3 — HR Content Studio Model

```mermaid
graph TD
    Cron[⏰ Daily cron · 06:00 UTC<br/>Picks 1 sahih hadith]
    
    Cron --> Adults[📖 Adults reel<br/>Dark elegant · scholarly tone<br/>Arabic + EN/UZ/RU/TJ narration]
    Cron --> Kids[🌟 Kids reel<br/>Bright colorful · simple words<br/>Age 6-14 · fun facts]
    
    Adults --> Claude[Claude generates<br/>Story · Ar-Raheeq Seerah · Moral · Caption + hashtags]
    Kids --> Claude
    
    Claude --> TTS[TTS narrates<br/>Hijazi AR · Abrar RU · UZ/TJ via OpenAI<br/>EN voices · MP3 audio]
    
    TTS --> Render[Remotion or ffmpeg renders MP4<br/>60 seconds · 1080×1920 vertical<br/>Calligraphy · subtitles · branding]
    
    Render --> Post[Manual or automated post<br/>Instagram Reels · TikTok · YouTube Shorts · Telegram · Facebook]
    
    Post --> Revenue[Revenue streams<br/>YouTube Partner · TikTok Creator Fund · Sponsors · Reel packs]
    
    Revenue --> Funds[Revenue covers infra<br/>Vercel · Railway · Supabase · ElevenLabs · Claude API<br/>HadithVerifier.com stays FREE forever for users]
    
    style Cron fill:#e6d4ff
    style Adults fill:#d4e6ff
    style Kids fill:#d4ffd4
    style Claude fill:#d4f4dd
    style TTS fill:#d4f4dd
    style Render fill:#fff4dd
    style Funds fill:#d4e0ff
```

---

## Diagram 4 — HR Audiobook Feature (planned)

```mermaid
graph TD
    %% Content sources
    Src1[Ar-Raheeq Al-Makhtum<br/>AR · EN available]
    Src2[Усваи Ҳасана<br/>RU · UZ · TJ available]
    Src3[Quran + Tafsir<br/>quran_library table · all langs]
    
    %% Adaptation
    Src1 --> Adapt[Claude generates audio-optimized<br/>narration script<br/>Conversational tone · no visual references<br/>chapter summaries · 5 languages]
    Src2 --> Adapt
    Src3 --> Adapt
    
    %% Narration
    Adapt --> Narrate[ElevenLabs narrates full chapters<br/>Hijazi AR · Abrar RU/UZ/TJ · EN voice<br/>High quality MP3]
    
    %% Output formats
    Narrate --> Out1[📱 In-app player<br/>hadithreels.com/listen · free]
    Narrate --> Out2[💾 MP3 download<br/>offline listening]
    Narrate --> Out3[🎧 Podcast RSS feed<br/>Spotify · Apple Podcasts]
    
    %% Audience + monetization
    Out1 --> Why[Why this matters<br/>~39M vision-impaired Muslims globally<br/>No Islamic audio book app exists<br/>in Uzbek or Tajik · fills real gap]
    
    Out2 --> Mon[Monetization<br/>Podcast sponsorships<br/>Pro plan for offline MP3 downloads<br/>Spotify for Podcasters revenue<br/>~$0.10/chapter ElevenLabs cost]
    
    style Src1 fill:#fff4dd
    style Src2 fill:#fff4dd
    style Src3 fill:#d4e6ff
    style Adapt fill:#d4f4dd
    style Narrate fill:#e6d4ff
    style Out1 fill:#d4ffd4
    style Out2 fill:#d4ffd4
    style Out3 fill:#d4ffd4
```

---

## Diagram 5 — Six Claude Code Primitives (architectural framing)

```mermaid
graph TB
    subgraph Visible[Visible Layer]
        Skills[Skills · KNOWLEDGE<br/>.claude/skills/ · SKILL.md modules<br/>Loaded on-demand · progressive disclosure]
        MCP[MCP · ABILITY<br/>External system connectors<br/>GitHub · Slack · DB · APIs]
    end
    
    subgraph Hidden[Invisible Plumbing]
        Sub[Subagents · DELEGATION<br/>Isolated context · own model · own permissions<br/>Code Reviewer · Researcher · Deployer]
        Hook[Hooks · AUTOMATION<br/>PRE-TOOL · POST-TOOL · ON-EDIT<br/>Deterministic · not LLM-controlled]
        CMD[CLAUDE.md · ALWAYS-ON CONTEXT<br/>Project conventions · architecture · company info<br/>Loaded every session]
        Plug[Plugins · PACKAGING<br/>Skills + Hooks + Subagents + MCP<br/>Team-distributable unit]
    end
    
    Skills --> Sub
    Skills --> Hook
    Skills --> CMD
    MCP --> Sub
    MCP --> Hook
    
    Sub --> Plug
    Hook --> Plug
    CMD --> Plug
    
    style Skills fill:#d4f4dd
    style MCP fill:#d4f4dd
    style Sub fill:#fff4dd
    style Hook fill:#fff4dd
    style CMD fill:#fff4dd
    style Plug fill:#e6d4ff
```

**Our mapping (HV+HR project):**

| Primitive | What we have | What we need |
|---|---|---|
| Skills | `agents/tts-validating/SKILL.md` (HR) | Build 10 more skills per agent-fleet-roadmap |
| MCP | Claude Code MCP on Windows | Expose own agents as MCP tools post-Hajj |
| Subagents | None executable | Build orchestrator post-Hajj using Claude Code agent view |
| Hooks | `.githooks/pre-push` (smart pre-push v3) | Commit it; document enable command |
| CLAUDE.md | `CLAUDE.md` + `hr-CLAUDE.md` | Keep updated as architecture evolves |
| Plugins | None | Future · if open-sourcing toolchain |

---

## How to update these diagrams

1. Edit the Mermaid code blocks in this file
2. Preview in VS Code (install "Markdown Preview Mermaid Support" extension), or push to GitHub (renders natively)
3. Verify diagram renders correctly
4. Commit with message describing what changed in the architecture

Do NOT replace diagrams with screenshots — screenshots cannot be diffed, versioned, or edited.

---

## When to update which diagram

| Change | Update diagram |
|---|---|
| New agent added/removed | 1 (HV) or 2 (HR) |
| New data source/sink | 1 or 2 |
| Distribution channel added | 3 |
| New audiobook feature | 4 |
| Claude Code primitive adoption | 5 |
| Sonnet model migration | 1, 2 (update labels) |
