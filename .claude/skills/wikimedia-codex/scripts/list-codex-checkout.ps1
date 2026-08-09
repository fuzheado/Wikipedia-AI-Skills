# Lists Codex components, demos, and token categories from a local design-codex checkout.
# Usage: .\list-codex-checkout.ps1 [-CodexSource <path>]
# Default path: ..\..\..\..\codex-source relative to this script (i.e. <workspace>/codex-source).

param(
	[Parameter(Mandatory = $false)]
	[string]$CodexSource
)

if (-not $CodexSource) {
	$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
	$CodexSource = Join-Path (Join-Path $scriptDir '..\..\..\..') 'codex-source'
}

if (-not (Test-Path $CodexSource)) {
	Write-Error "Codex checkout not found at: $CodexSource. Pass -CodexSource <path>."
	exit 1
}

$componentsDir = Join-Path $CodexSource 'packages\codex\src\components'
$demosDir      = Join-Path $CodexSource 'packages\codex-docs\component-demos'
$tokensDir     = Join-Path $CodexSource 'packages\codex-docs\docs\design-tokens'

Write-Host "Codex checkout: $CodexSource"
Write-Host ""

if (Test-Path $componentsDir) {
	Write-Host "=== Vue components (packages/codex/src/components) ==="
	(Get-ChildItem $componentsDir -Directory | Select-Object -ExpandProperty Name) | Sort-Object
	Write-Host ""
}

if (Test-Path $demosDir) {
	Write-Host "=== Components with docs demos (packages/codex-docs/component-demos) ==="
	Get-ChildItem $demosDir -Directory | ForEach-Object {
		$examples = ''
		if (Test-Path (Join-Path $_.FullName 'examples')) {
			$examples = ' (examples/)'
		}
		Write-Host ("{0}{1}" -f $_.Name, $examples)
	}
	Write-Host ""
}

if (Test-Path $tokensDir) {
	Write-Host "=== Design token categories (docs/design-tokens) ==="
	(Get-ChildItem $tokensDir -Filter *.md | Select-Object -ExpandProperty BaseName) | Sort-Object
}
