# connect.ps1 - News Agent SSM 포트포워딩 접속 스크립트 (Windows PowerShell)
# 사용법: .\connect.ps1 [-LocalPort 8080] [-Region us-west-2]
param(
    [int]$LocalPort = 8080,
    [string]$Region = "us-west-2",
    [string]$StackName = "NewsAgentStack"
)

$ErrorActionPreference = "Stop"

Write-Host "`n🔍 스택 정보 조회 중..." -ForegroundColor Cyan

$AlbUrl = aws cloudformation describe-stacks --stack-name $StackName `
    --query "Stacks[0].Outputs[?OutputKey=='InternalURL'].OutputValue" `
    --output text --region $Region
$AlbDns = $AlbUrl -replace "http://", ""

$Cluster = aws ecs list-clusters `
    --query "clusterArns[?contains(@,'NewsAgent')]|[0]" `
    --output text --region $Region

$TaskArn = aws ecs list-tasks --cluster $Cluster `
    --query "taskArns[0]" --output text --region $Region

$ClusterName = ($Cluster -split "/")[-1]
$TaskId = ($TaskArn -split "/")[-1]

$RuntimeId = aws ecs describe-tasks --cluster $Cluster --tasks $TaskArn `
    --query "tasks[0].containers[0].runtimeId" `
    --output text --region $Region

$Target = "ecs:${ClusterName}_${TaskId}_${RuntimeId}"

Write-Host ""
Write-Host "✅ 접속 정보:" -ForegroundColor Green
Write-Host "   ALB:    $AlbDns"
Write-Host "   Target: $Target"
Write-Host ""
Write-Host "🔗 포트포워딩 시작: http://localhost:$LocalPort" -ForegroundColor Yellow
Write-Host "   종료: Ctrl+C"
Write-Host ""

$params = "{`"host`":[`"$AlbDns`"],`"portNumber`":[`"80`"],`"localPortNumber`":[`"$LocalPort`"]}"

aws ssm start-session `
    --target $Target `
    --document-name AWS-StartPortForwardingSessionToRemoteHost `
    --parameters $params `
    --region $Region
