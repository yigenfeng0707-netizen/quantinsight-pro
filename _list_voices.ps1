Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
Write-Host "Installed voices:"
$synth.GetInstalledVoices() | ForEach-Object {
    $v = $_.VoiceInfo
    Write-Host ("  {0} | {1} | {2}" -f $v.Name, $v.Culture, $v.Gender)
}
$synth.Dispose()
