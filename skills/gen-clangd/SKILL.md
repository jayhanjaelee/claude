---
name: gen-clangd
description: C 프로젝트의 소스 코드를 분석하여 필요한 라이브러리를 자동으로 감지하고 .clangd 파일을 생성/수정합니다
allowed-tools: Bash, Read, Grep, Glob, Write
argument-hint: "[project-root]"
---

# gen-clangd - .clangd 자동 생성 도구

C 프로젝트의 소스 코드를 분석하여 필요한 라이브러리를 자동으로 감지하고 `.clangd` 파일을 생성 또는 수정합니다.

## 기능

- **헤더 파일 분석**: C 소스 코드에서 `#include` 문 추출
- **라이브러리 자동 감지**: 각 라이브러리의 설치 경로를 자동으로 찾기 (pkg-config 활용)
- **컴파일 플래그 추가**: 필요한 `-I` 플래그를 `.clangd`에 추가
- **기존 설정 보존**: 이미 있는 `.clangd` 파일의 기존 설정을 유지하면서 업데이트

## 사용 방법

현재 디렉토리에서 분석:
```
/gen-clangd
```

특정 경로에서 분석:
```
/gen-clangd /path/to/project
```

## 실행 절차

1. 프로젝트에서 C 소스 파일 (`.c`, `.h`) 검색
2. 모든 C 파일에서 `#include` 문 분석
3. `pkg-config` 또는 시스템 패키지 관리자로 라이브러리 경로 찾기
4. 필요한 `-I` 컴파일 플래그 수집
5. 기존 `.clangd` 파일 업데이트 또는 새 파일 생성

## 지원하는 라이브러리

- **GLFW**: `-I/usr/include` (Linux, macOS)
- **OpenGL**: 시스템 표준 경로에서 자동 감지
- **pkg-config**: 설치된 모든 라이브러리 감지

## 예상 결과

실행 후 프로젝트 루트에 `.clangd` 파일이 생성됩니다:

```yaml
CompileFlags:
  Add:
    - "-I/usr/local/include"
  Remove:
    - "-fno-PIC"
```

## 주의사항

- 비표준 위치의 라이브러리는 수동으로 추가할 수 있습니다
- `.clangd` 파일이 이미 있으면 기존 설정을 보존합니다
- `pkg-config`가 설치되어 있어야 최적의 감지 성능을 발휘합니다

---

실제 분석을 시작합니다...

!`python ~/.claude/skills/gen-clangd/scripts/gen_clangd.py ${1:-.}`
