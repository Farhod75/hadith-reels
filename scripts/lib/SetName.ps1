# scripts/lib/SetName.ps1
# P412 (from P403): a still or clip name carries the set's collection as a prefix -
# t1987-sand is Jami at-Tirmidhi #1987. The #1987 assets were generated as b1987-*
# (Bukhari's prefix) and every sidecar had to be rebuilt. Dot-source this file and
# call Assert-SetName before spending money on a generation.
#
#   Test-SetName  - PURE: the verdict for a name, given the library collections that
#                   hold its number ($null = the library could not be read).
#   Get-LibraryCollections - the collections in hadith_library holding a number.
#   Assert-SetName - both together; returns @{ Ok; Message }.

$script:SetPrefix = [ordered]@{
  ad = 'Sunan Abu Dawud'
  ij = 'Sunan Ibn Majah'
  ah = 'Musnad Ahmad'        # P412: no asset has used it yet
  b  = 'Sahih al-Bukhari'
  m  = 'Sahih Muslim'
  t  = 'Jami at-Tirmidhi'
  n  = 'Sunan an-Nasai'      # P412: no asset has used it yet
}

function Get-SetPrefixFor([string]$Collection) {
  foreach ($k in $script:SetPrefix.Keys) { if ($script:SetPrefix[$k] -eq $Collection) { return $k } }
  return $null
}

function Test-SetName {
  param([Parameter(Mandatory)][string]$Name, [AllowNull()][string[]]$Collections)
  if ($Name -notmatch '^([a-z]+)(\d+)-') {
    return @{ Ok = $true; Message = "'$Name' is not a set name (<prefix><number>-...), prefix not checked" }
  }
  $prefix = $Matches[1]; $number = $Matches[2]
  if (-not $script:SetPrefix.Contains($prefix)) {
    return @{ Ok = $false; Message = "'$Name': prefix '$prefix' is not a collection prefix (" +
      (($script:SetPrefix.Keys | ForEach-Object { "$_ $($script:SetPrefix[$_])" }) -join ', ') +
      "). Rename it, or add the collection to scripts\lib\SetName.ps1 (P412)." }
  }
  $want = $script:SetPrefix[$prefix]
  if ($null -eq $Collections) {
    return @{ Ok = $true; Message = "library could not be read - '$Name' NOT checked against it" }
  }
  if ($Collections -contains $want) { return @{ Ok = $true; Message = '' } }
  if ($Collections.Count -eq 0) {
    return @{ Ok = $false; Message = "'$Name': no hadith_library row has number $number. Stills and clips are made for a " +
      "library row; promote it first, or pass -SkipNameCheck if this is deliberate (P412)." }
  }
  $right = ($Collections | ForEach-Object {
    $p = Get-SetPrefixFor $_; if ($p) { "$p$number- ($_)" } else { "? ($_ has no prefix yet)" } }) -join ', '
  return @{ Ok = $false; Message = "'$Name' says $want #$number, but the library's #$number is: $right. " +
    "Use that prefix, or -SkipNameCheck if this really is a $want row not yet in the library (P412)." }
}

function Get-LibraryCollections {
  param([Parameter(Mandatory)][string]$Number, [string]$EnvFile = '.env.local')
  try {
    $kv = @{}
    Get-Content $EnvFile -ErrorAction Stop | ForEach-Object {
      if ($_ -match '^\s*([A-Z0-9_]+)\s*=\s*(.*)$') { $kv[$Matches[1]] = $Matches[2].Trim().Trim('"').Trim("'") }
    }
    $url = $kv['NEXT_PUBLIC_SUPABASE_URL']; $key = $kv['SUPABASE_SERVICE_ROLE_KEY']
    if (-not $url -or -not $key) { return $null }
    $rows = Invoke-RestMethod -TimeoutSec 15 -Headers @{ apikey = $key; Authorization = "Bearer $key" } `
      -Uri "$($url.TrimEnd('/'))/rest/v1/hadith_library?select=collection&hadith_number=eq.$Number"
    return [string[]]@($rows | ForEach-Object { $_.collection })
  } catch {
    return $null
  }
}

function Assert-SetName {
  param([Parameter(Mandatory)][string]$Name)
  $cols = $null
  if ($Name -match '^[a-z]+(\d+)-') { $cols = Get-LibraryCollections -Number $Matches[1] }
  return Test-SetName -Name $Name -Collections $cols
}
