---
name: summarize-git
description: summarize a change from git log.
argument-hint: [hash]
model: haiku
---

## 제외파일 목록
- *.min.js

## 지시사항

- 한글 사용.
- 해시값이 존재한다면 $0 해시값에 대해 `!git log` 실행.
- **해시값이 없는 경우** `!git log --author="Hanjae Lee" --stat --oneline -p` 명령어 실행.
- 작성자가 **Hanjae Lee** 인 경우에 대해서만 조회
- 소스코드 변경점도 첨부.
- 작업 내용 프로젝트 루트 디렉토리에 **task_notes\현재날짜.md** 파일로 생성 EX) 2026-01-01
- 날짜는 **YYYY-MM-DD** 형식으로 설정.
- 가장 첫 문단에 **Table of Contents** 추가, 이미 있다면 업데이트.
- 같은 이름의 파일이 존재한다면 기존 파일에 내용 추가.
