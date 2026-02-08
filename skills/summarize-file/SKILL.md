---
name: summarize-file
description: migrate project source code
argument-hint: [filename] [programming language]
model: haiku
---

- 한글 사용.
- $1 Use Programming Lanaguage Context.
- $0 파일에 대해 각 줄별로 소스코드 분석하여 $0 파일 내에 한글로 주석처리.
- 외부 라이브러리, 헤더파일을 참조하는 경우라면 어디서 참조하고 있는지 경로또한 주석처리.
