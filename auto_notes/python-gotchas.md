# Python Gotchas

## 이중 임포트 문제 (Mickey 31)
- PYTHONPATH에 `pkg/` 디렉토리가 있을 때, `from module import X`와 `from pkg.module import X`는 별개 모듈 인스턴스
- 모듈 레벨 변수 (리스트, 딕셔너리 등)가 공유되지 않음
- 해결: 한 프로젝트 내에서 동일 모듈은 반드시 동일 임포트 경로 사용
