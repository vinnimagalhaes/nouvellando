<#
Gera os arquivos do logotipo usados no site a partir de assets/marca/logo-nouvellando-original.jpg.

Uso (PowerShell, na pasta do projeto):
  powershell -ExecutionPolicy Bypass -File ferramentas\logo.ps1

Saída em assets/marca/ (PNG com fundo transparente):
  logo-horizontal.png        novelo + "Nouvellando" lado a lado, marrom (cabeçalho claro)
  logo-horizontal-claro.png  o mesmo em creme (cabeçalho escuro da página Videoaulas)
  logo-completo-claro.png    logotipo completo, com "by Claudia Gerth", em creme (rodapé escuro)
  logo-completo.png          logotipo completo em marrom (uso geral, Google)
  logo-nome.png / -claro     só a palavra "Nouvellando" (sem o símbolo)
  logo-simbolo.png / -claro  só o símbolo redondo (novelo com o gato)
  favicon.png                ícone da aba do navegador (64x64)
  apple-touch-icon.png       ícone ao salvar o site na tela inicial do celular (180x180)
#>
Add-Type -AssemblyName System.Drawing
$ErrorActionPreference = 'Stop'
$raiz = Split-Path (Split-Path $MyInvocation.MyCommand.Path -Parent) -Parent
$dir = Join-Path $raiz 'assets\marca'
$orig = [Drawing.Bitmap]::FromFile((Join-Path $dir 'logo-nouvellando-original.jpg'))
$W = $orig.Width; $H = $orig.Height

# Tinta = quanto o pixel é mais escuro que o branco do fundo (0 = fundo, 1 = marrom cheio)
$tinta = New-Object 'double[,]' $W, $H
$linhaTem = New-Object 'int[]' $H
$dados = $orig.LockBits((New-Object Drawing.Rectangle 0, 0, $W, $H), 'ReadOnly', 'Format24bppRgb')
$bytes = New-Object byte[] ($dados.Stride * $H)
[Runtime.InteropServices.Marshal]::Copy($dados.Scan0, $bytes, 0, $bytes.Length)
$orig.UnlockBits($dados)
for ($y = 0; $y -lt $H; $y++) {
  $base = $y * $dados.Stride
  for ($x = 0; $x -lt $W; $x++) {
    $i = $base + 3 * $x
    $l = (0.299 * $bytes[$i + 2] + 0.587 * $bytes[$i + 1] + 0.114 * $bytes[$i]) / 255.0
    $t = [Math]::Min(1.0, [Math]::Max(0.0, (0.96 - $l) / (0.96 - 0.33)))
    $tinta[$x, $y] = $t
    if ($t -gt 0.15) { $linhaTem[$y]++ }
  }
}

# Faixas horizontais com desenho (novelo, "Nouvellando", "by Claudia Gerth")
$faixas = @(); $ini = -1
for ($y = 0; $y -lt $H; $y++) {
  if ($linhaTem[$y] -gt 0 -and $ini -lt 0) { $ini = $y }
  if ($linhaTem[$y] -eq 0 -and $ini -ge 0) { if ($y - $ini -gt 8) { $fim = $y - 1; $faixas += ,@($ini, $fim) }; $ini = -1 }
}
function Caixa($y0, $y1) {
  $x0 = $W; $x1 = 0
  for ($y = $y0; $y -le $y1; $y++) { for ($x = 0; $x -lt $W; $x++) { if ($tinta[$x, $y] -gt 0.15) { if ($x -lt $x0) { $x0 = $x }; if ($x -gt $x1) { $x1 = $x } } } }
  return @($x0, $y0, $x1, $y1)
}
# Agrupa faixas próximas (o novelo tem frestas brancas entre as listras)
$grupos = @(); $atual = $faixas[0]
for ($k = 1; $k -lt $faixas.Count; $k++) {
  if ($faixas[$k][0] - $atual[1] -lt 15) { $atual = @($atual[0], $faixas[$k][1]) } else { $grupos += ,$atual; $atual = $faixas[$k] }
}
$grupos += ,$atual
"Partes encontradas: $($grupos.Count) -> " + (($grupos | ForEach-Object { "$($_[0])-$($_[1])" }) -join ', ')
$novelo = Caixa $grupos[0][0] $grupos[0][1]
# "Nouvellando" e "by Claudia Gerth" se encostam: corta na linha com menos tinta da
# parte de baixo do bloco de texto (entre 70% e 92% da altura dele)
$t0 = $grupos[1][0]; $t1 = $grupos[1][1]; $corte = $t1; $menor = [int]::MaxValue
for ($y = [int]($t0 + 0.70 * ($t1 - $t0)); $y -le [int]($t0 + 0.92 * ($t1 - $t0)); $y++) {
  if ($linhaTem[$y] -lt $menor) { $menor = $linhaTem[$y]; $corte = $y }
}
"Corte entre o nome e o 'by Claudia Gerth' na linha $corte (tinta: $menor px)"
$nome = Caixa $t0 $corte
$tudo = Caixa $grupos[0][0] $grupos[$grupos.Count - 1][1]

function Pinta($caixas, $posicoes, $largura, $altura, $cor) {
  # Desenha as partes (recortes do original) numa imagem transparente na cor pedida
  $bmp = New-Object Drawing.Bitmap $largura, $altura, ([Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $g = [Drawing.Graphics]::FromImage($bmp)
  $g.InterpolationMode = 'HighQualityBicubic'; $g.PixelOffsetMode = 'HighQuality'; $g.SmoothingMode = 'HighQuality'
  for ($k = 0; $k -lt $caixas.Count; $k++) {
    $c = $caixas[$k]; $w = $c[2] - $c[0] + 1; $h = $c[3] - $c[1] + 1
    $parte = New-Object Drawing.Bitmap $w, $h, ([Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $pd = $parte.LockBits((New-Object Drawing.Rectangle 0, 0, $w, $h), 'WriteOnly', 'Format32bppArgb')
    $pb = New-Object byte[] ($pd.Stride * $h)
    for ($y = 0; $y -lt $h; $y++) { for ($x = 0; $x -lt $w; $x++) {
      $i = $y * $pd.Stride + 4 * $x
      $pb[$i] = $cor.B; $pb[$i + 1] = $cor.G; $pb[$i + 2] = $cor.R
      $ox = $c[0] + $x; $oy = $c[1] + $y
      $a = $tinta[$ox, $oy]
      $pb[$i + 3] = [byte][Math]::Round(255 * $a)
    } }
    [Runtime.InteropServices.Marshal]::Copy($pb, 0, $pd.Scan0, $pb.Length)
    $parte.UnlockBits($pd)
    $p = $posicoes[$k]
    $g.DrawImage($parte, (New-Object Drawing.Rectangle $p[0], $p[1], $p[2], $p[3]))
    $parte.Dispose()
  }
  $g.Dispose()
  return $bmp
}

$marrom = [Drawing.Color]::FromArgb(92, 70, 44)
$creme = [Drawing.Color]::FromArgb(246, 238, 226)

# Horizontal: novelo com 120 px de altura e "Nouvellando" ao lado (3x a altura exibida no cabeçalho)
$hN = 120
$wN = [int][Math]::Round(($novelo[2] - $novelo[0] + 1) * $hN / ($novelo[3] - $novelo[1] + 1))
$hNome = [int]($hN * 0.50)
$wNome = [int][Math]::Round(($nome[2] - $nome[0] + 1) * $hNome / ($nome[3] - $nome[1] + 1))
$gap = [int]($hN * 0.18)
$larg = $wN + $gap + $wNome; $alt = $hN
$pos = @(@(0, 0, $wN, $hN), @(($wN + $gap), [int](($hN - $hNome) / 2 + $hN * 0.04), $wNome, $hNome))
foreach ($v in @(@('logo-horizontal.png', $marrom), @('logo-horizontal-claro.png', $creme))) {
  $b = Pinta @($novelo, $nome) $pos $larg $alt $v[1]
  $b.Save((Join-Path $dir $v[0]), [Drawing.Imaging.ImageFormat]::Png); $b.Dispose()
  "$($v[0]): ${larg}x$alt"
}

# Completo (como o original, sem o branco em volta), 600 px de largura
$wT = $tudo[2] - $tudo[0] + 1; $hT = $tudo[3] - $tudo[1] + 1
$lc = 600; $ac = [int][Math]::Round($hT * $lc / $wT)
foreach ($v in @(@('logo-completo.png', $marrom), @('logo-completo-claro.png', $creme))) {
  $b = Pinta @(,$tudo) @(,@(0, 0, $lc, $ac)) $lc $ac $v[1]
  $b.Save((Join-Path $dir $v[0]), [Drawing.Imaging.ImageFormat]::Png); $b.Dispose()
  "$($v[0]): ${lc}x$ac"
}

# Partes separadas: só a palavra "Nouvellando" (900 px de largura) e só o símbolo (400 px de altura)
$wP = $nome[2] - $nome[0] + 1; $hP = $nome[3] - $nome[1] + 1
$lp = 900; $ap = [int][Math]::Round($hP * $lp / $wP)
foreach ($v in @(@('logo-nome.png', $marrom), @('logo-nome-claro.png', $creme))) {
  $b = Pinta @(,$nome) @(,@(0, 0, $lp, $ap)) $lp $ap $v[1]
  $b.Save((Join-Path $dir $v[0]), [Drawing.Imaging.ImageFormat]::Png); $b.Dispose()
  "$($v[0]): ${lp}x$ap"
}
$wS = $novelo[2] - $novelo[0] + 1; $hS = $novelo[3] - $novelo[1] + 1
$as = 400; $ls = [int][Math]::Round($wS * $as / $hS)
foreach ($v in @(@('logo-simbolo.png', $marrom), @('logo-simbolo-claro.png', $creme))) {
  $b = Pinta @(,$novelo) @(,@(0, 0, $ls, $as)) $ls $as $v[1]
  $b.Save((Join-Path $dir $v[0]), [Drawing.Imaging.ImageFormat]::Png); $b.Dispose()
  "$($v[0]): ${ls}x$as"
}

# Ícones: aba do navegador (símbolo marrom, fundo transparente) e tela inicial do celular
# (símbolo marrom sobre o creme do site, porque o iPhone não aceita transparência)
$fundoCreme = [Drawing.Color]::FromArgb(251, 248, 244)
foreach ($v in @(@('favicon.png', 64, 0.04, $null), @('apple-touch-icon.png', 180, 0.14, $fundoCreme))) {
  $lado = $v[1]; $margem = [int]($lado * $v[2]); $util = $lado - 2 * $margem
  $esc = [Math]::Min($util / $wS, $util / $hS)
  $w = [int]($wS * $esc); $h = [int]($hS * $esc)
  $simb = Pinta @(,$novelo) @(,@(0, 0, $w, $h)) $w $h $marrom
  $ico = New-Object Drawing.Bitmap $lado, $lado, ([Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $g = [Drawing.Graphics]::FromImage($ico)
  if ($v[3]) { $g.Clear($v[3]) }
  $g.InterpolationMode = 'HighQualityBicubic'
  $g.DrawImage($simb, [int](($lado - $w) / 2), [int](($lado - $h) / 2), $w, $h)
  $g.Dispose(); $simb.Dispose()
  $ico.Save((Join-Path $dir $v[0]), [Drawing.Imaging.ImageFormat]::Png); $ico.Dispose()
  "$($v[0]): ${lado}x$lado"
}
$orig.Dispose()
