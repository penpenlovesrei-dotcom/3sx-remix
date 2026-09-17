# MESURER LA PERF : CPU / GPU / RAM pendant une partie, pour le fork ou pour la build officielle.
# Se lance par C:\Temp3sx\MESURER LA PERF.cmd, en double-clic par Frederic :
# le jeu ecrit dans %APPDATA%, donc jamais lance par l'agent (REPRISE.md, regle 12).
# Fichier volontairement sans accents : PowerShell 5.1 lit les .ps1 sans BOM en ANSI.
#
# Pour ne pas fausser la mesure sur un CPU a 2 coeurs, typeperf ne lit que des compteurs
# legers (coeurs, memoire, GPU). Les fils du jeu sont lus directement sur son processus,
# et les autres programmes par deux instantanes, au debut et a la fin.
#
# Ce que le fork ajoute a la mesure de C:\3sx-officiel :
#   -RenderScale N  pose render-scale = N le temps de la mesure, puis remet le config d'origine
#   -SansObjets     SF3_DECOR_OBJETS=0 : aucun objet anime ne nait, le decor reste
#   la comparaison avec le dernier rapport de la build officielle, et un historique des mesures
param(
    [ValidateSet('fork', 'officielle')][string]$Build = 'fork',
    [ValidateSet('vulkan', 'opengl')][string]$Rendu = 'vulkan',
    [int]$RenderScale = 0,
    [switch]$SansObjets,
    [string]$Exe = '',
    [string]$ArgsJeu = '',
    [int]$AttenteDemarrage = 5,
    [string]$DossierMesures = '',
    [string]$Prefs = '',
    [switch]$Essai   # essai du pipeline avec un faux jeu et un faux %APPDATA% : ne touche a rien
)

$ErrorActionPreference = 'Stop'
$inv = [Globalization.CultureInfo]::InvariantCulture
$ea = [char]0xE9   # e accent aigu, pour les noms francais des compteurs Windows

$depot = Split-Path -Parent $PSScriptRoot
$officielle = 'C:\3sx-officiel'
if (-not $Exe) {
    $Exe = if ($Build -eq 'fork') { Join-Path $depot 'build\application\bin\3sx.exe' } else { Join-Path $officielle 'jeu\bin\3sx.exe' }
}
if (-not $DossierMesures) { $DossierMesures = Join-Path $depot 'essais\perf' }
if (-not $Prefs) { $Prefs = Join-Path $env:APPDATA 'CrowdedStreet\3SX' }
$nomProc = [IO.Path]::GetFileNameWithoutExtension($Exe)
$dossierExe = Split-Path $Exe
$cfgPath = Join-Path $Prefs 'config'
$cfgGarde = "$cfgPath.avant-mesure"

$stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$etiquette = "$Build-$Rendu" + $(if ($RenderScale -gt 0) { "-rs$RenderScale" } else { '' }) + $(if ($SansObjets) { '-sans-objets' } else { '' })
New-Item -ItemType Directory -Force $DossierMesures | Out-Null
$csvPath = Join-Path $DossierMesures "$stamp-$etiquette.csv"
$rapportPath = Join-Path $DossierMesures "$stamp-$etiquette-RAPPORT.txt"
$historiquePath = Join-Path $DossierMesures 'historique.csv'
$R = New-Object System.Collections.Generic.List[string]

function Titre([string]$t) {
    $barre = '=' * 72
    foreach ($l in @('', $barre, "  $t", $barre)) { $R.Add($l) }
    Write-Host ''
    Write-Host $barre -ForegroundColor DarkGray
    Write-Host "  $t" -ForegroundColor Cyan
    Write-Host $barre -ForegroundColor DarkGray
}
function Ligne([string]$t, [string]$couleur = 'Gray') { $R.Add($t); Write-Host $t -ForegroundColor $couleur }
function Alerte([string]$t) { Ligne "  ATTENTION : $t" 'Yellow' }
function Enregistrer { $R | Set-Content $rapportPath -Encoding UTF8 }

function Num($v) {
    $d = 0.0
    if ([double]::TryParse(("$v").Trim(), [Globalization.NumberStyles]::Float, $inv, [ref]$d)) { return $d }
    return $null
}
function Stats($valeurs) {
    $v = @($valeurs | Where-Object { $null -ne $_ } | Sort-Object)
    if ($v.Count -eq 0) { return $null }
    [pscustomobject]@{
        Moy = ($v | Measure-Object -Average).Average
        P90 = $v[[math]::Min($v.Count - 1, [int][math]::Floor($v.Count * 0.9))]
        Min = $v[0]
        Max = $v[-1]
        N   = $v.Count
    }
}
function F($x, [int]$dec = 0) { if ($null -eq $x) { return 'n/a' }; return ([math]::Round([double]$x, $dec)).ToString($inv) }

function Lire-Config {
    $h = @{}
    if (Test-Path -LiteralPath $cfgPath) {
        foreach ($l in Get-Content -LiteralPath $cfgPath) {
            $m = [regex]::Match($l, '^\s*([\w-]+)\s*=\s*(.*?)\s*$')
            if ($m.Success) { $h[$m.Groups[1].Value] = $m.Groups[2].Value }
        }
    }
    $h
}

# Le config d'origine est garde en `config.avant-mesure` et remis tel quel, octet pour octet.
function Remettre-Config {
    if (Test-Path -LiteralPath $cfgGarde) { Move-Item -Force -LiteralPath $cfgGarde -Destination $cfgPath; return $true }
    return $false
}

function Instantane-Cpu {
    $t = @{}
    foreach ($p in Get-Process) { try { if ($null -ne $p.CPU) { $t[$p.Id] = [pscustomobject]@{ Nom = $p.ProcessName; Cpu = [double]$p.CPU } } } catch { } }
    $t
}

function Journal-Du-Jeu {
    if ($Essai) { return @() }
    $dossier = Join-Path $Prefs 'logs'
    $f = Get-ChildItem $dossier -Filter *.log -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -ge $debut.AddSeconds(-2) } |
        Sort-Object LastWriteTime | Select-Object -Last 1
    if (-not $f) { return @("  (aucun journal du jeu trouve dans $dossier)") }
    $l = @(Get-Content $f.FullName | Where-Object { $_ -match 'Trying|backend|GPU|Vulkan|OpenGL|driver|renderer|canvas|render-scale|fail|error|unsupported|missing' } | Select-Object -First 15)
    return @("  journal : $($f.FullName)") + @($l | ForEach-Object { "    $_" })
}

# Le dernier rapport Vulkan de C:\3sx-officiel assez long pour servir de reference.
function Reference-Officielle {
    $d = Join-Path $officielle 'mesures'
    foreach ($f in @(Get-ChildItem $d -Filter '*vulkan*RAPPORT.txt' -ErrorAction SilentlyContinue | Sort-Object Name -Descending)) {
        $t = Get-Content $f.FullName -Raw -Encoding UTF8
        if ($t -notmatch '3SX OFFICIEL') { continue }
        $n = [regex]::Match($t, '(\d+) releves')
        if (-not $n.Success -or [int]$n.Groups[1].Value -lt 40) { continue }
        $v = { param($motif) $x = [regex]::Match($t, $motif); if ($x.Success) { [double]::Parse($x.Groups[1].Value, $inv) } else { $null } }
        return [pscustomobject]@{
            Fichier = $f.Name
            Date    = [regex]::Match($t, 'Date : (.+)').Groups[1].Value.Trim()
            Alim    = [regex]::Match($t, 'Alim : (.+)').Groups[1].Value.Trim()
            Releves = [int]$n.Groups[1].Value
            Fil     = & $v 'fil principal du jeu\s*:\s*moy (\d+(?:\.\d+)?)'
            Jeu     = & $v 'exe entier\s*:\s*moy (\d+(?:\.\d+)?)'
            Machine = & $v 'machine entiere\s*:\s*moy (\d+(?:\.\d+)?)'
            Gpu     = & $v 'moteur 3D, total\s*:\s*moy (\d+(?:\.\d+)?)'
            Ram     = & $v 'le jeu occupe\s*:\s*(\d+(?:\.\d+)?) Mo'
        }
    }
    return $null
}

# ---------------------------------------------------------------------------
$nomBuild = if ($Build -eq 'fork') { 'FORK' } else { 'OFFICIELLE' }
Titre "3SX $nomBuild - MESURE CPU / GPU / RAM - rendu $($Rendu.ToUpper())"

if (-not (Test-Path $Exe)) { Ligne "  Introuvable : $Exe" 'Red'; Enregistrer; exit 1 }

$cpu = (Get-CimInstance Win32_Processor | Select-Object -First 1).Name.Trim()
$gpu = Get-CimInstance Win32_VideoController | Select-Object -First 1
$ramTotale = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
$vitesseRam = (Get-CimInstance Win32_PhysicalMemory | Select-Object -First 1).ConfiguredClockSpeed
$bat = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Select-Object -First 1
$surBatterie = [bool]($bat -and $bat.BatteryStatus -eq 1)   # 1 = se decharge

$exeInfo = Get-Item $Exe
$commit = ''
if ($Build -eq 'fork') {
    try { $commit = (git -C $depot log -1 --format='%h %ad' --date=format:'%d/%m/%Y' 2>$null) } catch { }
}
Ligne "  Date : $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')"
Ligne "  Exe  : $Exe  (du $($exeInfo.LastWriteTime.ToString('dd/MM/yyyy HH:mm')))"
if ($commit) { Ligne "  Git  : $(git -C $depot branch --show-current 2>$null) $commit" }
Ligne "  CPU  : $cpu"
Ligne "  GPU  : $($gpu.Name) (pilote $($gpu.DriverVersion))"
Ligne "  RAM  : $ramTotale Go a $vitesseRam MHz"
Ligne "  Alim : $(if ($surBatterie) { "BATTERIE ($($bat.EstimatedChargeRemaining) %)" } else { 'secteur' })"
if ($surBatterie) { Alerte "le PC est sur batterie : Windows bride le processeur. Branchez le chargeur pour une mesure juste." }
$claude = @(Get-Process claude -ErrorAction SilentlyContinue)
if ($claude.Count -gt 0) {
    $moClaude = [math]::Round(($claude | Measure-Object WorkingSet64 -Sum).Sum / 1MB)
    Alerte "l'application Claude est ouverte ($($claude.Count) processus, $moClaude Mo). Elle prend du CPU au jeu : fermez-la pendant le test. Le rapport est enregistre dans un fichier, rien ne se perd."
}

if (Remettre-Config) { Alerte "une mesure precedente avait ete interrompue : le config d'origine vient d'etre remis." }

if (-not $Essai) {
    $afs = Join-Path $Prefs 'resources\SF33RD.AFS'
    if (Test-Path $afs) { Ligne "  OK   donnees du jeu : $afs" 'Green' }
    else { Alerte "$afs absent : le jeu va reclamer l'ISO. Lancez d'abord C:\Temp3sx\VERIFIER LES ASSETS.cmd." }
}
$sauv = Join-Path $DossierMesures "sauvegarde-config\$stamp"
New-Item -ItemType Directory -Force $sauv | Out-Null
foreach ($f in 'config', 'keymap') {
    $src = Join-Path $Prefs $f
    if (Test-Path $src) { Copy-Item $src $sauv }
}
Ligne "  OK   config et keymap copies dans $sauv" 'Green'

# --- Les reglages qui pesent, tels que le jeu va les lire ---
$cfgAvant = Lire-Config
if ($RenderScale -gt 0) {
    Copy-Item -LiteralPath $cfgPath -Destination $cfgGarde
    $texte = [IO.File]::ReadAllText($cfgPath)
    if ($texte -match '(?m)^[ \t]*render-scale[ \t]*=') {
        $texte = [regex]::Replace($texte, '(?m)^[ \t]*render-scale[ \t]*=[^\r\n]*', "render-scale = $RenderScale")
    } else {
        $texte = $texte.TrimEnd() + "`nrender-scale = $RenderScale`n"
    }
    [IO.File]::WriteAllText($cfgPath, $texte)
}
$cfg = Lire-Config
$rsEffectif = if ($cfg.ContainsKey('render-scale')) { $cfg['render-scale'] } else { '1 (defaut)' }
Titre 'REGLAGES DE CETTE MESURE'
Ligne "  render-scale   = $rsEffectif$(if ($RenderScale -gt 0) { "   (pose pour la mesure, config d'origine : $(if ($cfgAvant.ContainsKey('render-scale')) { $cfgAvant['render-scale'] } else { 'absent' }))" })"
foreach ($k in 'window-width', 'window-height', 'fullscreen', 'scale-mode', 'tex-remix-dump') {
    if ($cfg.ContainsKey($k)) { Ligne ("  {0,-14} = {1}" -f $k, $cfg[$k]) }
}
Ligne "  objets animes  = $(if ($SansObjets) { 'COUPES (SF3_DECOR_OBJETS=0)' } else { 'actifs' })"
Ligne "  rendu          = $Rendu"
if ($cfg['tex-remix-dump'] -eq 'true') { Alerte "tex-remix-dump = true : chaque page de texture inedite est ecrite sur disque (a-coups a l'entree d'un decor)." }
if ($Build -eq 'fork' -and (Test-Path (Join-Path $dossierExe 'jalons.on'))) { Alerte "jalons.on est present a cote de l'exe : l'instrumentation des jalons tourne et ecrit ses journaux." }

if ($Rendu -eq 'opengl') {
    # Pilote SDL GPU inconnu : SDL_CreateGPUDevice echoue, et le jeu retombe sur OpenGL.
    [Environment]::SetEnvironmentVariable('SDL_GPU_DRIVER', 'aucun', 'Process')
} else {
    [Environment]::SetEnvironmentVariable('SDL_GPU_DRIVER', $null, 'Process')
}
[Environment]::SetEnvironmentVariable('SF3_DECOR_OBJETS', $(if ($SansObjets) { '0' } else { $null }), 'Process')

try {
    Titre 'LE JEU SE LANCE'
    Write-Host '  1. Faites un VRAI combat (Versus ou Arcade), 1 a 2 minutes, la ou ca rame.'
    Write-Host '  2. FERMEZ le jeu : le verdict s''affiche dans cette fenetre.'
    Write-Host '  Optionnel : Win+G, widget "Performances", pour voir les FPS en direct.'
    Write-Host ''

    $debut = Get-Date
    $lancement = @{ FilePath = $Exe; WorkingDirectory = $dossierExe; PassThru = $true }
    if ($ArgsJeu) { $lancement.ArgumentList = $ArgsJeu }
    $jeu = Start-Process @lancement
    Start-Sleep -Seconds $AttenteDemarrage
    if ($jeu.HasExited) {
        Ligne "  Le jeu s'est ferme tout de suite (code $($jeu.ExitCode)). Rien a mesurer." 'Red'
        Journal-Du-Jeu | ForEach-Object { Ligne $_ }
        Enregistrer
        exit 1
    }

    # Les jokers de typeperf se resolvent a son demarrage : il demarre donc apres le jeu.
    $pidJeu = $jeu.Id
    $compteurs = @(
        '\Processeur(*)\% temps processeur',
        "\M${ea}moire\M${ea}gaoctets disponibles",
        "\M${ea}moire\Pages en entr${ea}e/s",
        '\GPU Engine(*engtype_3D)\Utilization Percentage',
        "\GPU Process Memory(pid_${pidJeu}_*)\Dedicated Usage",
        "\GPU Process Memory(pid_${pidJeu}_*)\Shared Usage"
    )
    $argsTp = (($compteurs | ForEach-Object { '"' + $_ + '"' }) -join ' ') + " -si 1 -f CSV -y -o `"$csvPath`""
    $tp = Start-Process typeperf -ArgumentList $argsTp -WindowStyle Hidden -PassThru
    $cpuDebut = Instantane-Cpu
    $chrono = [Diagnostics.Stopwatch]::StartNew()
    Write-Host '  Mesure en cours, un releve par seconde... fermez le jeu quand vous avez fini.' -ForegroundColor Cyan

    # Fils du jeu : temps CPU de chaque fil, releve toutes les secondes.
    $filsSeries = @{}
    $filsAvant = @{}
    $echJeu = New-Object System.Collections.Generic.List[double]
    $echRamJeu = New-Object System.Collections.Generic.List[double]
    $tAvant = $null; $cpuJeuAvant = $null
    while (-not $jeu.HasExited) {
        try {
            $gp = Get-Process -Id $pidJeu -ErrorAction Stop
            $t = $chrono.Elapsed.TotalMilliseconds
            $cpuJeu = $gp.TotalProcessorTime.TotalMilliseconds
            $filsMaintenant = @{}
            foreach ($th in $gp.Threads) {
                try { $filsMaintenant[$th.Id] = $th.TotalProcessorTime.TotalMilliseconds } catch { }
            }
            if ($null -ne $tAvant) {
                $dt = $t - $tAvant
                $echJeu.Add(($cpuJeu - $cpuJeuAvant) / $dt * 100)
                $echRamJeu.Add($gp.WorkingSet64 / 1MB)
                foreach ($id in $filsMaintenant.Keys) {
                    if (-not $filsAvant.ContainsKey($id)) { continue }
                    if (-not $filsSeries.ContainsKey($id)) { $filsSeries[$id] = New-Object System.Collections.Generic.List[double] }
                    $filsSeries[$id].Add(($filsMaintenant[$id] - $filsAvant[$id]) / $dt * 100)
                }
            }
            $tAvant = $t; $cpuJeuAvant = $cpuJeu; $filsAvant = $filsMaintenant
        } catch { }
        Start-Sleep -Milliseconds 1000
    }
    $secondesMesure = $chrono.Elapsed.TotalSeconds
    $cpuFin = Instantane-Cpu
    $duree = (Get-Date) - $debut
    Start-Sleep -Seconds 1
    if (-not $tp.HasExited) { Stop-Process -Id $tp.Id -Force }
    Start-Sleep -Milliseconds 500
} finally {
    if (Remettre-Config) { Ligne "  OK   config d'origine remis (render-scale = $(if ($cfgAvant.ContainsKey('render-scale')) { $cfgAvant['render-scale'] } else { 'absent' }))" 'Green' }
}

# ---------------------------------------------------------------------------
Titre 'MESURES'
if (-not (Test-Path $csvPath)) { Ligne '  typeperf n''a rien enregistre.' 'Red'; Enregistrer; exit 1 }
$tout = @(Get-Content $csvPath -Encoding Default | ConvertFrom-Csv)
# Le premier releve est vide pour les debits ; le dernier peut etre coupe par l'arret de typeperf.
$releves = @($tout | Select-Object -Skip 2 | Select-Object -SkipLast 1)
Ligne "  Duree de jeu : $([int][math]::Floor($duree.TotalMinutes)) min $($duree.Seconds) s - $($releves.Count) releves - rendu $($Rendu.ToUpper())"
if ($releves.Count -lt 10) { Ligne '  Moins de 10 releves : jouez au moins 30 secondes pour un verdict fiable.' 'Red'; if ($releves.Count -lt 2) { Enregistrer; exit 1 } }

$cols = $releves[0].PSObject.Properties.Name
function Colonnes([string]$motif) { @($cols | Where-Object { $_ -match $motif }) }
function Serie($colonne, [double]$diviseur = 1) {
    if (-not $colonne) { return $null }
    Stats ($releves | ForEach-Object { $x = Num $_.$colonne; if ($null -ne $x) { $x / $diviseur } })
}
function SerieSomme($colonnes, [double]$plafond = [double]::MaxValue, [double]$diviseur = 1) {
    if ($colonnes.Count -eq 0) { return $null }
    Stats ($releves | ForEach-Object {
        $ligne = $_; $s = 0.0; $n = 0
        foreach ($c in $colonnes) { $x = Num $ligne.$c; if ($null -ne $x) { $s += $x; $n++ } }
        if ($n) { [math]::Min($plafond, $s / $diviseur) }
    })
}
function SerieMaxi($colonnes) {
    if ($colonnes.Count -eq 0) { return $null }
    Stats ($releves | ForEach-Object {
        $ligne = $_; $m = $null
        foreach ($c in $colonnes) { $x = Num $ligne.$c; if ($null -ne $x -and ($null -eq $m -or $x -gt $m)) { $m = $x } }
        $m
    })
}

$cCoeurs = Colonnes '\\Processeur\(\d+\)\\'
$nbCoeurs = [math]::Max(1, $cCoeurs.Count)
$sTotal = Serie (Colonnes '\\Processeur\(_Total\)\\' | Select-Object -First 1)
$sCoeurMax = SerieMaxi $cCoeurs
$sRamLibre = Serie (Colonnes 'moire\\M.gaoctets disponibles' | Select-Object -First 1)
$sPagesIn = Serie (Colonnes 'moire\\Pages en entr.e/s' | Select-Object -First 1)
$sGpu = SerieSomme (Colonnes 'GPU Engine\(.*engtype_3D\)') 100
$sGpuJeu = SerieSomme (Colonnes "GPU Engine\(pid_${pidJeu}_.*engtype_3D\)") 100
$sVramDed = SerieSomme (Colonnes 'GPU Process Memory\(.*\)\\Dedicated Usage') ([double]::MaxValue) 1MB
$sVramPart = SerieSomme (Colonnes 'GPU Process Memory\(.*\)\\Shared Usage') ([double]::MaxValue) 1MB

$sProcJeu = Stats $echJeu
$sRamJeu = Stats $echRamJeu
# Le fil principal du jeu = le fil le plus charge en moyenne. A 100 %, il ne dort plus entre deux images.
$sFil = $null
foreach ($id in $filsSeries.Keys) {
    $s = Stats $filsSeries[$id]
    if ($s -and $s.N -ge 3 -and ($null -eq $sFil -or $s.Moy -gt $sFil.Moy)) { $sFil = $s }
}

# Autres programmes : temps CPU consomme entre les deux instantanes, en % de la machine.
# Les processus proteges (antivirus, System) ne livrent pas leur temps CPU : ils tombent dans "non attribue".
$autres = @{}
$mesure = 0.0
foreach ($id in $cpuFin.Keys) {
    if (-not $cpuDebut.ContainsKey($id) -or $id -eq $pidJeu -or $id -eq 0) { continue }
    $pct = ($cpuFin[$id].Cpu - $cpuDebut[$id].Cpu) / $secondesMesure * 100 / $nbCoeurs
    if ($id -eq $PID -or $id -eq $tp.Id) { $mesure += $pct; continue }
    $nom = $cpuFin[$id].Nom
    $autres[$nom] = [double]$autres[$nom] + $pct
}
$sommeAutres = [double](($autres.Values | Measure-Object -Sum).Sum)
$topAutres = @($autres.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 5 |
    ForEach-Object { "$($_.Key) $(F $_.Value) %" })
$nonAttribue = if ($sTotal -and $sProcJeu) { [math]::Max(0, $sTotal.Moy - $sProcJeu.Moy / $nbCoeurs - $sommeAutres - $mesure) } else { $null }

# --- Seuils ---
$filSature = [bool]($sFil -and $sFil.Moy -ge 85)
$cpuPlein = [bool]($sTotal -and $sTotal.Moy -ge 90)
$gpuPlein = [bool]($sGpu -and ($sGpu.Moy -ge 80 -or $sGpu.P90 -ge 95))
$ramPleine = [bool]($sRamLibre -and ($sRamLibre.Min -lt 300 -or ($sRamLibre.Min -lt 700 -and $sPagesIn -and $sPagesIn.Moy -gt 50)))

function Etat([bool]$b) { if ($b) { 'SATURE' } else { 'marge' } }
Ligne ''
Ligne "  CPU  [$(Etat ($filSature -or $cpuPlein))]"
Ligne "       machine entiere      : moy $(F $sTotal.Moy) %  (p90 $(F $sTotal.P90) %)   seuil 90 %"
Ligne "       coeur le plus charge : moy $(F $sCoeurMax.Moy) %  (p90 $(F $sCoeurMax.P90) %)"
Ligne "       fil principal du jeu : moy $(F $sFil.Moy) % d'un coeur  (p90 $(F $sFil.P90) %)   seuil 85 %"
Ligne "       $(("$nomProc.exe entier").PadRight(21)): moy $(F $sProcJeu.Moy) % d'un coeur"
Ligne "       autres programmes    : $(F $sommeAutres) % de la machine  ->  $($topAutres -join ', ')"
Ligne "       non attribue         : $(F $nonAttribue) % de la machine  (systeme, antivirus, programmes lances en cours de route)"
Ligne "       la mesure elle-meme  : $(F $mesure 1) % de la machine"
Ligne ''
Ligne "  GPU  [$(Etat $gpuPlein)]"
Ligne "       moteur 3D, total     : moy $(F $sGpu.Moy) %  (p90 $(F $sGpu.P90) %)   seuils 80 % moy / 95 % p90"
if ($sGpuJeu) { Ligne "       dont le jeu          : moy $(F $sGpuJeu.Moy) %  (p90 $(F $sGpuJeu.P90) %)" }
if ($sVramDed -or $sVramPart) { Ligne "       memoire video du jeu : $(F $sVramDed.Max) Mo dediee + $(F $sVramPart.Max) Mo partagee" }
Ligne ''
Ligne "  RAM  [$(Etat $ramPleine)]"
Ligne "       memoire libre        : min $(F $sRamLibre.Min) Mo, moy $(F $sRamLibre.Moy) Mo   seuil 300 Mo"
Ligne "       pages lues du disque : moy $(F $sPagesIn.Moy 1)/s  (p90 $(F $sPagesIn.P90 1)/s)   seuil 50/s"
Ligne "       le jeu occupe        : $(F $sRamJeu.Max) Mo"

# ---------------------------------------------------------------------------
Titre 'VERDICT'
$candidats = @()
if ($ramPleine) { $candidats += [pscustomobject]@{ Nom = 'RAM'; Score = 200 } }
if ($filSature -or $cpuPlein) { $candidats += [pscustomobject]@{ Nom = 'CPU'; Score = [math]::Max([double]$sFil.Moy, [double]$sTotal.Moy) } }
if ($gpuPlein) { $candidats += [pscustomobject]@{ Nom = 'GPU'; Score = [double]$sGpu.Moy } }
$principal = $candidats | Sort-Object Score -Descending | Select-Object -First 1
$verdict = if ($principal) { $principal.Nom } else { 'aucun' }

switch ($verdict) {
    'RAM' {
        Ligne '  FACTEUR LIMITANT : LA MEMOIRE VIVE.' 'Red'
        Ligne '  Windows manque de RAM et relit sur le disque pendant le combat.'
        Ligne '  Leviers : fermer les programmes ouverts (Claude, navigateur, Dropbox).'
    }
    'CPU' {
        if ($filSature) {
            Ligne '  FACTEUR LIMITANT : LE PROCESSEUR.' 'Red'
            Ligne "  Le fil principal du jeu tourne a fond ($(F $sFil.Moy) % d'un coeur) : il n'a plus le temps"
            Ligne '  de finir une image en 1/60 s, alors le jeu ralentit. Le GPU, lui, attend.'
        } else {
            Ligne '  FACTEUR LIMITANT : LE PROCESSEUR, PARTAGE AVEC D''AUTRES PROGRAMMES.' 'Red'
            Ligne "  La machine est a $(F $sTotal.Moy) % : le jeu n'a pas un coeur pour lui seul."
            Ligne "  Qui prend le CPU : $($topAutres -join ', ') ; non attribue $(F $nonAttribue) %."
        }
        Ligne '  Leviers : chargeur branche, mode d''alimentation "Performances optimales",'
        Ligne '  fermer Claude / navigateur / Dropbox pendant le jeu.'
    }
    'GPU' {
        Ligne '  FACTEUR LIMITANT : LA CARTE GRAPHIQUE (Radeon R5 integree).' 'Red'
        if ($Build -eq 'fork' -and $rsEffectif -notmatch '^1') {
            Ligne "  render-scale = $rsEffectif fait dessiner $([int]$rsEffectif * [int]$rsEffectif) fois les pixels d'origine : mesurez avec le choix 2 (render-scale 1)."
        }
        Ligne '  Leviers : render-scale 1, fenetre plus petite, comparer Vulkan et OpenGL, pilote AMD a jour.'
    }
    default {
        Ligne '  AUCUN COMPOSANT SATURE pendant cette mesure.' 'Green'
        Ligne '  Le jeu avait de la marge : il devait tenir ses 60 images/s.'
    }
}
if ($candidats.Count -gt 1) { Ligne "  A noter : aussi pres de la limite -> $(@($candidats | Where-Object Nom -ne $principal.Nom | ForEach-Object Nom) -join ', ')" 'Yellow' }
if ($surBatterie) { Ligne '  Mesure faite SUR BATTERIE : processeur bride, a refaire chargeur branche.' 'Yellow' }
if ($claude.Count -gt 0) { Ligne '  Claude etait ouvert pendant la mesure : sa part est dans "autres programmes".' 'Yellow' }

# ---------------------------------------------------------------------------
if ($Build -eq 'fork') {
    $ref = Reference-Officielle
    Titre 'COMPARAISON AVEC LA BUILD OFFICIELLE'
    if (-not $ref) {
        Ligne "  Pas de rapport officiel Vulkan d'au moins 40 releves dans $officielle\mesures."
        Ligne "  Lancez C:\3sx-officiel\1 - MESURER - rendu normal.cmd pour avoir une reference."
    } else {
        Ligne "  Reference : $($ref.Fichier) ($($ref.Releves) releves, $($ref.Alim))"
        Ligne ''
        Ligne ("  {0,-26}{1,12}{2,14}" -f '', 'officielle', 'ce fork')
        Ligne ("  {0,-26}{1,12}{2,14}" -f "fil principal (% coeur)", (F $ref.Fil), (F $sFil.Moy))
        Ligne ("  {0,-26}{1,12}{2,14}" -f "jeu entier (% coeur)", (F $ref.Jeu), (F $sProcJeu.Moy))
        Ligne ("  {0,-26}{1,12}{2,14}" -f "machine entiere (%)", (F $ref.Machine), (F $sTotal.Moy))
        Ligne ("  {0,-26}{1,12}{2,14}" -f "GPU 3D total (%)", (F $ref.Gpu), (F $sGpu.Moy))
        Ligne ("  {0,-26}{1,12}{2,14}" -f "RAM du jeu (Mo)", (F $ref.Ram), (F $sRamJeu.Max))
        if ($ref.Fil -and $sFil -and $ref.Fil -gt 0) {
            Ligne ''
            Ligne "  Le fil principal du fork travaille $(F ($sFil.Moy / $ref.Fil) 1) fois plus que celui de la build officielle."
        }
    }
    $nouveaux = @(Get-ChildItem $dossierExe -Filter *.log -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -ge $debut })
    if ($nouveaux.Count) {
        Ligne ''
        Ligne "  Journaux ecrits par le fork pendant la partie : $(@($nouveaux | ForEach-Object { "$($_.Name) $([math]::Round($_.Length / 1KB)) Ko" }) -join ', ')"
    }
}

$journal = @(Journal-Du-Jeu)
if ($journal.Count) { Titre 'RENDU CHOISI PAR LE JEU'; $journal | ForEach-Object { Ligne $_ } }

# Une ligne par mesure : c'est ce qui permet de comparer les variantes entre elles.
[pscustomobject]@{
    date           = Get-Date -Format 'yyyy-MM-dd HH:mm'
    build          = $Build
    rendu          = $Rendu
    render_scale   = $rsEffectif
    objets         = $(if ($SansObjets) { 'coupes' } else { 'actifs' })
    alim           = $(if ($surBatterie) { 'batterie' } else { 'secteur' })
    claude_ouvert  = [bool]($claude.Count -gt 0)
    releves        = $releves.Count
    fil_principal  = F $sFil.Moy
    jeu_entier     = F $sProcJeu.Moy
    machine        = F $sTotal.Moy
    gpu_3d         = F $sGpu.Moy
    ram_jeu_mo     = F $sRamJeu.Max
    verdict        = $verdict
    rapport        = Split-Path $rapportPath -Leaf
} | Export-Csv -LiteralPath $historiquePath -Append -NoTypeInformation -Delimiter ';' -Encoding UTF8

Titre 'HISTORIQUE DES MESURES (les 8 dernieres)'
$h = @(Import-Csv -LiteralPath $historiquePath -Delimiter ';' | Select-Object -Last 8)
($h | Format-Table date, build, rendu, render_scale, objets, alim, releves, fil_principal, jeu_entier, machine, gpu_3d, verdict -AutoSize | Out-String -Width 160).TrimEnd() -split "`r?`n" | ForEach-Object { Ligne $_ }

Ligne ''
Ligne "  Rapport    : $rapportPath"
Ligne "  Releves    : $csvPath"
Ligne "  Historique : $historiquePath"
Enregistrer
