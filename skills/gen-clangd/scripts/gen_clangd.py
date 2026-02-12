#!/usr/bin/env python3
"""
gen_clangd.py: C 프로젝트의 .clangd 파일을 자동으로 생성/수정하는 유틸리티
소스 코드의 #include를 분석하여 필요한 라이브러리 경로를 자동으로 감지합니다.
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from collections import defaultdict

try:
    import yaml
except ImportError:
    # yaml 모듈이 없으면 간단한 구현 사용
    yaml = None

class ClangdGenerator:
    """C 프로젝트 분석 및 .clangd 파일 생성"""

    def __init__(self, project_root):
        self.project_root = Path(project_root).resolve()
        self.found_includes = defaultdict(set)
        self.include_dirs = set()
        self.lib_paths = {}

    def find_c_files(self):
        """프로젝트에서 C 소스 파일 찾기"""
        c_files = []
        for ext in ['*.c', '*.h']:
            c_files.extend(self.project_root.rglob(ext))
        return c_files

    def extract_includes(self, file_path):
        """C 파일에서 #include 문 추출"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # #include <...> 형식 추출 (시스템 헤더)
                system_includes = re.findall(r'#include\s+<([^>]+)>', content)
                # #include "..." 형식 추출 (로컬 헤더)
                local_includes = re.findall(r'#include\s+"([^"]+)"', content)
                return system_includes, local_includes
        except Exception as e:
            print(f"⚠ Warning: Could not read {file_path}: {e}", file=sys.stderr)
            return [], []

    def get_pkg_config_cflags(self, package):
        """pkg-config에서 패키지의 CFLAGS 가져오기"""
        try:
            result = subprocess.run(
                ['pkg-config', '--cflags', package],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                flags = result.stdout.strip().split()
                return [f for f in flags if f.startswith('-I')]
        except Exception:
            pass
        return []

    def find_library_paths(self, header_name):
        """헤더 파일의 위치 찾기 (다양한 방법 시도)"""
        # 1. 프로젝트 내 로컬 헤더 먼저 확인
        local_path = self.project_root / header_name
        if local_path.exists():
            return [str(local_path.parent)]

        # 2. 라이브러리 이름 추출 (예: GL/gl.h -> GL)
        parts = header_name.split('/')
        if len(parts) > 1:
            lib_name = parts[0]

            # 3. pkg-config로 찾기
            pkg_flags = self.get_pkg_config_cflags(lib_name)
            if pkg_flags:
                return pkg_flags

            # 4. 일반적인 설치 위치 확인 (macOS Homebrew)
            homebrew_paths = [
                f"/opt/homebrew/opt/{lib_name}/include",
                f"/usr/local/opt/{lib_name}/include",
            ]
            found = [p for p in homebrew_paths if Path(p).exists()]
            if found:
                return [f"-I{p}" for p in found]

        # 5. 표준 시스템 경로 확인
        standard_paths = [
            "/usr/include",
            "/usr/local/include",
            "/opt/homebrew/include",
        ]

        for std_path in standard_paths:
            header_path = Path(std_path) / header_name
            if header_path.exists():
                return [f"-I{std_path}"]

        return []

    def analyze_project(self):
        """전체 프로젝트 분석"""
        print(f"📁 Analyzing project: {self.project_root}", file=sys.stderr)

        # C 파일 찾기
        c_files = self.find_c_files()
        if not c_files:
            print("⚠ No C files found", file=sys.stderr)
            return set()

        print(f"📄 Found {len(c_files)} C files", file=sys.stderr)

        # 각 파일에서 include 추출
        all_headers = set()
        for c_file in c_files:
            system_incs, local_incs = self.extract_includes(c_file)
            all_headers.update(system_incs)
            all_headers.update(local_incs)

        if all_headers:
            print(f"🔍 Found {len(all_headers)} unique includes", file=sys.stderr)

        # Include 디렉토리 결정
        needed_flags = set()

        for header in sorted(all_headers):
            flags = self.find_library_paths(header)
            if flags:
                needed_flags.update(flags)

        return sorted(needed_flags)

    def simple_yaml_dump(self, data, file_obj):
        """간단한 YAML 덤프 (PyYAML 없이도 작동)"""
        file_obj.write("CompileFlags:\n")

        if 'Add' in data:
            file_obj.write("  Add:\n")
            for flag in data['Add']:
                file_obj.write(f"    - \"{flag}\"\n")

        if 'Remove' in data:
            file_obj.write("  Remove:\n")
            for flag in data['Remove']:
                file_obj.write(f"    - \"{flag}\"\n")

    def parse_existing_clangd(self, clangd_path):
        """기존 .clangd 파일 파싱"""
        try:
            with open(clangd_path, 'r') as f:
                content = f.read()

            # 간단한 파싱: Remove 섹션 추출
            remove_flags = []
            in_remove = False

            for line in content.split('\n'):
                if 'Remove:' in line:
                    in_remove = True
                elif in_remove:
                    if line.startswith('    - '):
                        flag = line.replace('    - ', '').strip('\'"')
                        remove_flags.append(flag)
                    elif line and not line.startswith('    '):
                        in_remove = False

            return {'Remove': remove_flags}
        except Exception:
            return {}

    def generate_clangd(self):
        """`.clangd` 파일 생성"""
        add_flags = self.analyze_project()

        clangd_path = self.project_root / '.clangd'

        # 기존 설정 로드
        existing_remove_flags = []
        if clangd_path.exists():
            existing = self.parse_existing_clangd(clangd_path)
            existing_remove_flags = existing.get('Remove', [])
            print(f"📝 Found existing .clangd, preserving {len(existing_remove_flags)} Remove flags", file=sys.stderr)

        # 최종 설정
        compile_flags = {}

        if add_flags:
            compile_flags['Add'] = add_flags

        if existing_remove_flags:
            compile_flags['Remove'] = existing_remove_flags

        config = {'CompileFlags': compile_flags}

        # 파일 작성
        with open(clangd_path, 'w') as f:
            if yaml:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            else:
                f.write("CompileFlags:\n")
                if add_flags:
                    f.write("  Add:\n")
                    for flag in add_flags:
                        f.write(f"    - \"{flag}\"\n")
                if existing_remove_flags:
                    f.write("  Remove:\n")
                    for flag in existing_remove_flags:
                        f.write(f"    - \"{flag}\"\n")

        # 결과 출력
        print(f"\n✅ Generated: {clangd_path}", file=sys.stderr)

        if add_flags:
            print(f"\n📌 Include paths added ({len(add_flags)}):", file=sys.stderr)
            for i, flag in enumerate(add_flags, 1):
                print(f"  {i}. {flag}", file=sys.stderr)
        else:
            print("\n⚠ No include paths found. Manual configuration may be needed.", file=sys.stderr)

        if existing_remove_flags:
            print(f"\n⚙️ Preserved Remove flags ({len(existing_remove_flags)}):", file=sys.stderr)
            for flag in existing_remove_flags:
                print(f"  - {flag}", file=sys.stderr)

        # 사용자에게 출력
        print(f"\n✨ .clangd 파일이 생성되었습니다: {clangd_path}")

        if add_flags:
            print(f"\n추가된 Include 경로:")
            for flag in add_flags:
                print(f"  • {flag}")

        return clangd_path

def main():
    project_root = sys.argv[1] if len(sys.argv) > 1 else '.'

    try:
        generator = ClangdGenerator(project_root)
        generator.generate_clangd()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
