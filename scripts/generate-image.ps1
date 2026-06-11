<#
================================================================================
 generate-image.ps1  —  text-to-image (image-first workflow, step A)
================================================================================
 Generates 1-5 still images from a prompt via fal.ai FLUX, downloads them to
 out\refs\ for REVIEW. You pick the good one(s), then animate with
 generate-scene.ps1 -Image (image-to-video).

 WHY image-first: a still is cheaper and far easier to control/review than a
 video. Approve the frame, THEN animate it. Best for anonymous atmospheric
 scenes (pilgrim, desert, light, paths, Quran, lantern). For hands / the Kaaba,
 still prefer your OWN photos/footage -- generators fumble those.

 Reads FAL_KEY from .env.local -- you never type the key.

 USAGE (run from repo root):
   .\scripts\generate-image.ps1 -Name "b1520-path" -Count 3 -Prompt "Cinematic vertical 9:16 photoreal, a winding sunlit path through desert dunes leading toward a glowing dawn horizon, footprints in the sand, warm light, no people, reverent and uplifting."

 PARAMS:
   -Name    base filename -> out\refs\<Name>-1.jpg, -2.jpg, ...
   -Prompt  the image prompt (apply the scene-prompt spec guardrails: MODE B,
            themes not figures, era-accurate)
   -Count   how many variants to generate (1-5, default 3) -- review, keep best
   -Model   fal model id (default FLUX.1.1 pro -- good photoreal/value)

 COST: ~$0.03/megapixel. A few 9:16 stills per call is a few cents.
================================================================================
#>

param(
  [Parameter(Mandatory)][string]$Name,
  [Parameter(Mandatory)][string]$Prompt,
  [ValidateRange(1,5)][int]$Count = 3,
  [string]$Model = 'fal-ai/flux-pro/v1.1'
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo

function Say($m){ Write-Host $m -ForegroundColor Cyan }
function Ok ($m){ Write-Host "  OK  $m" -ForegroundColor Green }
function Die($m){ Write-Host "`nFAILED: $m" -ForegroundColor Red; exit 1 }

# --- read FAL_KEY from .env.local --------------------------------------------
if (-not (Test-Path ".env.local")) { Die ".env.local not found in repo root" }
$keyLine = Select-String -Path ".env.local" -Pattern '^\s*FAL_KEY\s*=' | Select-Object -First 1
if (-not $keyLine) { Die "FAL_KEY not found in .env.local" }
$FAL_KEY = ($keyLine.Line -replace '^\s*FAL_KEY\s*=\s*','').Trim().Trim('"').Trim("'")
if ([string]::IsNullOrWhiteSpace($FAL_KEY)) { Die "FAL_KEY in .env.local is empty" }

$refDir = "out\refs"
if (-not (Test-Path $refDir)) { New-Item -ItemType Directory -Path $refDir | Out-Null }

$headers = @{ "Authorization" = "Key $FAL_KEY"; "Content-Type" = "application/json" }
$body = @{
  prompt          = $Prompt
  image_size      = "portrait_16_9"   # vertical 9:16 for reels
  num_images      = $Count
  num_inference_steps = 28
  safety_tolerance = "2"
} | ConvertTo-Json -Depth 5

Say "================================================================"
Say " FLUX images -> $refDir\$Name-*.jpg   ($Count variant(s), 9:16)"
Say " model: $Model"
Say "================================================================"
Write-Host "  prompt: $Prompt" -ForegroundColor DarkGray

# --- submit ------------------------------------------------------------------
Say "`n[1/3] Submitting to fal.ai..."
try {
  $submit = Invoke-RestMethod -Method Post -Uri "https://queue.fal.run/$Model" -Headers $headers -Body $body
} catch {
  Die "submit failed: $($_.Exception.Message) -- check FAL_KEY / credits"
}
$statusUrl = $submit.status_url; $resultUrl = $submit.response_url
if (-not $submit.request_id) { Die "no request_id (resp: $($submit | ConvertTo-Json -Compress))" }
Ok "queued: $($submit.request_id)"

# --- poll (images are fast, usually < 30s) -----------------------------------
Say "`n[2/3] Generating..."
$deadline = (Get-Date).AddMinutes(4)
do {
  Start-Sleep -Seconds 4
  try { $st = Invoke-RestMethod -Method Get -Uri $statusUrl -Headers $headers }
  catch { Die "status check failed: $($_.Exception.Message)" }
  Write-Host "        status: $($st.status)" -ForegroundColor DarkGray
  if ((Get-Date) -gt $deadline) { Die "timed out after 4 min" }
} while ($st.status -ne 'COMPLETED')
Ok "done"

# --- fetch + download all variants -------------------------------------------
Say "`n[3/3] Downloading $Count image(s)..."
try { $res = Invoke-RestMethod -Method Get -Uri $resultUrl -Headers $headers }
catch { Die "result fetch failed: $($_.Exception.Message)" }
if (-not $res.images) { Die "no images in result: $($res | ConvertTo-Json -Compress -Depth 5)" }

$i = 0
foreach ($img in $res.images) {
  $i++
  $dest = Join-Path $refDir "$Name-$i.jpg"
  Invoke-WebRequest -Uri $img.url -OutFile $dest
  if (Test-Path $dest) { Ok "$dest" } else { Write-Host "  (failed: variant $i)" -ForegroundColor Yellow }
}

Write-Host "`nNEXT: review $refDir\$Name-*.jpg -- pick the best (MODE B, era-accurate, no forbidden figure)," -ForegroundColor Cyan
Write-Host "      then animate it:  .\scripts\generate-scene.ps1 -Name `"$Name`" -Image `"$refDir\$Name-1.jpg`" -Prompt `"gentle subtle motion, ...`"" -ForegroundColor Cyan
# open the folder so you can review the variants
Start-Process (Resolve-Path $refDir)
