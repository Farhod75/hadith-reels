<#
  make-kids-reel.ps1 — one command from narration MP3s to finished kids reel.

  Assumes /api/tts has already written story + moral into the work tree
  (P106). Chains: concat -> duration check -> split if needed -> fal Fabric
  lip-sync per chunk -> render-mascot-reel.ps1.

  USAGE
    .\make-kids-reel.ps1 -Lang en -Slug bukhari-1417
    .\make-kids-reel.ps1 -Lang uz -Slug bukhari-1417 -Mascot boy -Auto
    .\make-kids-reel.ps1 -Lang ru -Slug bukhari-1417 -Nasheed ramadan-2-bg.mp3

  PARAMS
    -Lang      (required) en|ru|uz|tj|ar
    -Slug      (required) e.g. bukhari-1417
    -Mascot    (optional) boy|girl — default boy. Picks the still.
    -Nasheed   (optional) file in out\backgrounds\; else render script picks
    -Auto      (optional) skip the pre-Fabric confirmation pause
    -ForceRegen (optional) re-generate talking clips even if the mp4 exists (costs money)
    -ValidateOnly (optional) run step 0 and exit — smoke test for the pre-push hook
    -MaxLen    (optional) chunk cap in seconds, default 28
#>

param(
  [Parameter(Mandatory)][ValidateSet('en','ru','uz','tj','ar')][string]$Lang,
  [Parameter(Mandatory)][string]$Slug,
  [ValidateSet('boy','girl')][string]$Mascot = 'boy',
  [string]$Nasheed,
  [switch]$Auto,
  [switch]$ValidateOnly,
  [switch]$ForceRegen,
  [double]$MaxLen = 28
)

Set-Location $PSScriptRoot
$ErrorActionPreference = 'Stop'

function Say ($m){ Write-Host $m -ForegroundColor Cyan }
function Ok  ($m){ Write-Host "  OK  $m" -ForegroundColor Green }
function Die ($m){ Write-Host "`nFAILED: $m" -ForegroundColor Red; exit 1 }

$base    = "kids-$Lang-$Slug"
$workDir = "out\work\kids\$Slug\$Lang"
$story   = "$workDir\$base-story.mp3"
$moral   = "$workDir\$base-moral.mp3"
$narr    = "$workDir\$base-narration.mp3"

$stillMap = @{
  boy  = 'assets\mascot\lamb-boy-mosque-night-v3.png'
  girl = 'assets\mascot\lamb-girl-garden-day-v2.png'
}
$still = $stillMap[$Mascot]

Say "================================================================"
Say " Kids reel: $base   (mascot: $Mascot)"
Say "================================================================"

# --- STEP 0: validate before spending anything ------------------------------
Say "`n[0/4] Validating..."
$problems = @()
if (-not (Test-Path $story)) { $problems += "missing story mp3: $story" }
if (-not (Test-Path $moral)) { $problems += "missing moral mp3: $moral" }
if (-not (Test-Path $still)) { $problems += "missing mascot still: $still" }
if (-not $env:FAL_KEY)       { $problems += "FAL_KEY not set - fal Fabric will fail" }
if ($env:FAL_KEY -and $env:FAL_KEY.Length -lt 40) {
  $problems += "FAL_KEY looks wrong ($($env:FAL_KEY.Length) chars; expected ~69)"
}
foreach ($e in @('ffmpeg','ffprobe','python')) {
  if (-not (Get-Command $e -ErrorAction SilentlyContinue)) { $problems += "$e not on PATH" }
}
if ($problems) { $problems | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }; Die "fix the above first" }
Ok "inputs present; mascot: $(Split-Path $still -Leaf); ffmpeg/python ready"
if ($ValidateOnly) { Ok "validate-only: parsed and executed to step 0"; exit 0 }

# --- STEP 1: concat story + 1s gap + moral -----------------------------------
Say "`n[1/4] Concatenating narration..."
# P135: 1s here plus ElevenLabs' own trailing silence read as ~2s.
ffmpeg -hide_banner -loglevel error -y -i $story `
  -f lavfi -t 0.5 -i anullsrc=r=44100:cl=mono -i $moral `
  -filter_complex "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]" -map "[out]" $narr
if ($LASTEXITCODE -ne 0) { Die "ffmpeg concat failed" }

function Dur ($p){ [double](ffprobe -v error -show_entries format=duration -of csv=p=0 $p) }
$storyDur = Dur $story
$totalDur = Dur $narr
Ok ("narration {0:N1}s  (story {1:N1}s + 0.5s gap + moral {2:N1}s)" -f $totalDur, $storyDur, (Dur $moral))

# --- STEP 2: split only if over the cap --------------------------------------
Say "`n[2/4] Chunking..."
$clips = @()
if ($totalDur -le $MaxLen) {
  Ok ("under {0}s cap - single clip, no split" -f $MaxLen)
  $clips = @("$base-clip01")
  Copy-Item $narr "$workDir\$base-clip01.mp3" -Force
} else {
  # P106: cut at the story/moral silence rather than greedy max-length.
  # split-narration.py maximises chunk length, which cuts mid-sentence.
  # P135: was +0.5 to land mid-gap when the gap was 1s. Now half of 0.5.
  $cut = $storyDur + 0.25
  if ($cut -gt $MaxLen -or ($totalDur - $cut) -gt $MaxLen) {
    Die ("story/moral seam at {0:N1}s doesn't fit the {1}s cap - shorten the text or split by hand" -f $cut, $MaxLen)
  }
  ffmpeg -hide_banner -loglevel error -y -i $narr -t $cut -c copy "$workDir\$base-clip01.mp3"
  ffmpeg -hide_banner -loglevel error -y -i $narr -ss $cut -c copy "$workDir\$base-clip02.mp3"
  $clips = @("$base-clip01", "$base-clip02")
  Ok ("split at story/moral seam {0:N1}s -> {1:N1}s + {2:N1}s" -f $cut, (Dur "$workDir\$base-clip01.mp3"), (Dur "$workDir\$base-clip02.mp3"))
}

# --- STEP 3: confirm before spending fal credits -----------------------------
# P138: count what will ACTUALLY be generated. Warning about a cost that is not
# about to be incurred trains the operator to click through the one gate that
# guards real money.
$pending = @($clips | Where-Object { $ForceRegen -or -not (Test-Path "$workDir\$_.mp4") })
if ($pending.Count -eq 0) {
  Ok "all $($clips.Count) clip(s) already generated - nothing to submit, nothing to pay"
} elseif (-not $Auto) {
  Write-Host "`n  About to submit $($pending.Count) of $($clips.Count) clip(s) to fal Fabric at 720p (paid)." -ForegroundColor Yellow
  if ($pending.Count -lt $clips.Count) {
    Write-Host "  Reusing: $(($clips | Where-Object { $_ -notin $pending }) -join ', ')" -ForegroundColor DarkGray
  }
  Write-Host "  Listen to the narration first: $narr" -ForegroundColor Yellow
  $ans = Read-Host "  Continue? (y/N)"
  if ($ans -ne 'y') { Say "`nStopped before Fabric. Nothing spent."; exit 0 }
}

# --- STEP 4: lip-sync each chunk, then render --------------------------------
Say "`n[3/4] Lip-syncing $($clips.Count) clip(s) via fal Fabric (720p)..."
# P138: Fabric is the paid step. A mid-set failure used to re-pay for every
# clip that had already succeeded — R057 lost a 720p generation that way when
# clip02's upload hit a TLS timeout and the re-run regenerated clip01 too.
$made = 0; $kept = 0
foreach ($c in $clips) {
  $clipMp4 = "$workDir\$c.mp4"
  if ((Test-Path $clipMp4) -and -not $ForceRegen) {
    $kb = [math]::Round((Get-Item $clipMp4).Length/1KB)
    Ok "$c.mp4 already exists (${kb} KB) - skipping, not re-paying. -ForceRegen to override."
    $kept++
    continue
  }
  python generate-talking-clip.py --image $still `
    --audio "$workDir\$c.mp3" --out "$workDir\$c.mp4" --resolution 720p
  if ($LASTEXITCODE -ne 0) { Die "Fabric failed on $c" }
  $made++
}
Ok "$($clips.Count) talking clip(s) ready ($made generated, $kept reused)"

Say "`n[4/4] Rendering..."
$clipFiles = $clips | ForEach-Object { "$_.mp4" }
$renderParams = @{
  Lang  = $Lang
  Slug  = $Slug
  Clips = $clipFiles
}
if ($Nasheed) { $renderParams['Nasheed'] = $Nasheed }
& "$PSScriptRoot\render-mascot-reel.ps1" @renderParams