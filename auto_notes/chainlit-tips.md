# Chainlit Tips

## cl.Image 렌더링 (Mickey 31)
- Chainlit 2.10.0 기준
- `content=bytes` 파라미터로 바이너리 직접 전달 가능
- `display="inline"` 시 content에 `![name](name)` 불필요, 메시지 아래 자동 표시
- Docker 환경에서 `path=/tmp/xxx.png`보다 `content=bytes`가 안정적
- `size` 파라미터: "small", "medium"(기본), "large" (inline에서만 동작)
