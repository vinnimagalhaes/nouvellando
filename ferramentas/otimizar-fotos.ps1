<#
Gera as fotos otimizadas do site em wp-content/uploads/ (mesmo caminho do WordPress).

Uso (PowerShell, na pasta do projeto):
  powershell -ExecutionPolicy Bypass -File ferramentas\otimizar-fotos.ps1 -Lista _fotos-conferencia\correspondencia.tsv

A lista é um TSV com duas colunas: endereco_no_site <TAB> arquivo_original.
Regras (um arquivo por foto; tamanho pensado para onde ela aparece no site, com
folga para telas de alta resolução, sem ficar borrada):
  - Fotos comuns (novelos): lado maior com no máximo -Lado pixels (padrão 1000).
  - Fotos em pé (altura > 1,25x a largura: xales, videoaulas): largura máxima
    -LarguraRetrato (padrão 900), para não ficarem estreitas demais.
  - Banners (largura >= 2x a altura) e artes em PNG de até 1200 px que não são
    fotos em pé (têm texto): só
    diminuem se passarem de -LarguraMax (padrão 1920) de largura, com qualidade
    -QualidadeArte (92), para o texto continuar nítido.
  - Fotos listadas em -Grandes (fundo do topo de Videoaulas, ocupa a tela toda):
    largura máxima -LarguraGrandes (padrão 1440).
  - Demais fotos: JPEG com qualidade -Qualidade (padrão 80). Logos ficam PNG
    (transparência) e WebP é copiado como está (já é leve).
  - Nunca aumenta a foto. Corrige a rotação (EXIF) e remove os metadados.
  - Grava conteudo/fotos.json: endereço antigo -> endereço da foto otimizada
    (muda só quando um PNG vira JPG). O gerar.py usa esse arquivo.
#>
param(
  [Parameter(Mandatory)] [string]$Lista,
  [string]$Raiz = '',
  [string]$Saida = 'wp-content\uploads',
  [int]$Lado = 1000,
  [int]$LarguraRetrato = 900,
  [int]$LarguraMax = 1920,
  [int]$LarguraGrandes = 1440,
  [int]$Qualidade = 80,
  [int]$QualidadeArte = 92,
  [string]$Grandes = 'conteudo\fotos-grandes.txt',
  [int]$Limite = 0,
  [string]$Filtro = '',  # regex: gera só os endereços que batem (a lista continua completa)
  [string]$Manifesto = 'conteudo\fotos.json',
  [int]$Parte = 0,     # para rodar em paralelo: -Partes 4 e -Parte 0..3 em 4 janelas
  [int]$Partes = 1,
  [switch]$Refazer
)
Add-Type -AssemblyName System.Drawing
$ErrorActionPreference = 'Stop'
if (-not $Raiz) { $Raiz = Split-Path (Split-Path $MyInvocation.MyCommand.Path -Parent) -Parent }

$jpegCodec = [Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
function Qualidade-Jpeg([int]$q) {
  $p = New-Object Drawing.Imaging.EncoderParameters 1
  $p.Param[0] = New-Object Drawing.Imaging.EncoderParameter ([Drawing.Imaging.Encoder]::Quality), ([long]$q)
  $p
}
$paramsFoto = Qualidade-Jpeg $Qualidade
$paramsArte = Qualidade-Jpeg $QualidadeArte
$listaGrandes = @{}
$arqGrandes = Join-Path $Raiz $Grandes
if ($Grandes -and (Test-Path -LiteralPath $arqGrandes)) {
  Get-Content $arqGrandes -Encoding UTF8 | Where-Object { $_ -match '^/' } | ForEach-Object { $listaGrandes[$_.Trim()] = $true }
}

$linhas = Get-Content (Join-Path $Raiz $Lista) -Encoding UTF8 | Select-Object -Skip 1
if ($Limite -gt 0) { $linhas = $linhas | Select-Object -First $Limite }
$ok = 0; $pulou = 0; $erros = @()
$mapa = [ordered]@{}
$n = -1
$todos = @{}
foreach ($l in $linhas) { $todos[($l -split "`t")[0]] = $true }

foreach ($l in $linhas) {
  $n++
  $endereco, $origem = $l -split "`t"
  $logo = $endereco -match '(?i)logo[^/]*\.png$'
  $copiar = $endereco -match '(?i)\.(webp|svg|gif)$'
  $novo = if ($logo -or $copiar) { $endereco } else { $endereco -replace '(?i)\.(png|jpe?g)$', '.jpg' }
  if ($endereco -match '(?i)\.jpeg$') { $novo = $endereco }   # .jpeg continua .jpeg (mesmo formato)
  # foto.png virando foto.jpg não pode ocupar o lugar de uma foto.jpg que já existe
  if ($novo -ne $endereco -and $todos.ContainsKey($novo)) { $novo = $endereco -replace '(?i)\.png$', '-png.jpg' }
  $mapa[$endereco] = $novo
  if ($n % $Partes -ne $Parte) { continue }
  if ($Filtro -and $endereco -notmatch $Filtro) { continue }
  $destino = Join-Path $Raiz ($Saida + ($novo -replace '^/wp-content/uploads', '' -replace '/', '\'))
  if ((Test-Path -LiteralPath $destino) -and -not $Refazer) { $pulou++; continue }
  $arqOrigem = Join-Path $Raiz $origem
  if ($copiar) {
    New-Item -ItemType Directory -Force (Split-Path $destino) | Out-Null
    Copy-Item -LiteralPath $arqOrigem -Destination $destino -Force
    $ok++; continue
  }
  try {
    $img = [Drawing.Image]::FromFile($arqOrigem)
    try {
      if ($img.PropertyIdList -contains 0x0112) {
        switch ([BitConverter]::ToUInt16($img.GetPropertyItem(0x0112).Value, 0)) {
          3 { $img.RotateFlip('Rotate180FlipNone') }
          6 { $img.RotateFlip('Rotate90FlipNone') }
          8 { $img.RotateFlip('Rotate270FlipNone') }
        }
      }
      $w = $img.Width; $h = $img.Height
      # PNG pequeno = arte com texto (ex.: banner de celular). PNG grande costuma ser foto salva em PNG.
      $arte = ($w -ge 2 * $h) -or (($endereco -match '(?i)\.png$') -and $w -le 1200 -and $h -le 1.5 * $w)
      if ($arte) { $escala = $LarguraMax / $w }                       # banner, arte com texto
      elseif ($listaGrandes.ContainsKey($endereco)) { $escala = $LarguraGrandes / $w }   # fundo de tela inteira
      elseif ($h -gt 1.25 * $w) { $escala = $LarguraRetrato / $w }    # foto em pé
      else { $escala = $Lado / [Math]::Max($w, $h) }                   # foto comum
      $escala = [Math]::Min(1.0, $escala)
      $nw = [int][Math]::Round($w * $escala); $nh = [int][Math]::Round($h * $escala)
      $png = $logo
      $fmt = if ($png) { [Drawing.Imaging.PixelFormat]::Format32bppArgb } else { [Drawing.Imaging.PixelFormat]::Format24bppRgb }
      $bmp = New-Object Drawing.Bitmap $nw, $nh, $fmt
      $g = [Drawing.Graphics]::FromImage($bmp)
      if (-not $png) { $g.Clear([Drawing.Color]::White) }
      $g.InterpolationMode = 'HighQualityBicubic'; $g.SmoothingMode = 'HighQuality'
      $g.PixelOffsetMode = 'HighQuality'; $g.CompositingQuality = 'HighQuality'
      $attr = New-Object Drawing.Imaging.ImageAttributes
      $attr.SetWrapMode('TileFlipXY')
      $g.DrawImage($img, (New-Object Drawing.Rectangle 0, 0, $nw, $nh), 0, 0, $w, $h, 'Pixel', $attr)
      $g.Dispose()
      New-Item -ItemType Directory -Force (Split-Path $destino) | Out-Null
      if ($png) { $bmp.Save($destino, [Drawing.Imaging.ImageFormat]::Png) }
      else { $bmp.Save($destino, $jpegCodec, $(if ($arte) { $paramsArte } else { $paramsFoto })) }
      $bmp.Dispose()
      $ok++
    } finally { $img.Dispose() }
  } catch { $erros += "$endereco  ($($_.Exception.Message))" }
}
if ($Manifesto) {
  $json = '{' + (($mapa.Keys | Sort-Object | ForEach-Object { "`n `"$_`": `"$($mapa[$_])`"" }) -join ',') + "`n}`n"
  [IO.File]::WriteAllText((Join-Path $Raiz $Manifesto), $json, (New-Object Text.UTF8Encoding $false))
}
"$ok geradas, $pulou ja existiam, $($erros.Count) com erro"
$erros
