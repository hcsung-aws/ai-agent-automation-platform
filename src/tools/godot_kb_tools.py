"""Godot KB Tools - 로컬 파일 기반 지식 검색."""
import os
from strands import tool

# KB 루트 디렉토리들
PONG_PROJECT_ROOT = "/mnt/c/Users/hcsung/work/q/ai-developer-mickey/pong"
GODOT_ANALYSIS_ROOT = "/mnt/c/Users/hcsung/work/q/ai-developer-mickey/godot-analysis"

@tool
def search_godot_kb(query: str, file_extension: str = ".gd") -> str:
    """Godot 프로젝트에서 관련 파일을 검색합니다.
    
    Args:
        query: 검색할 키워드
        file_extension: 파일 확장자 (기본: .gd, .md도 가능)
    
    Returns:
        검색 결과
    """
    results = []
    search_roots = [PONG_PROJECT_ROOT, GODOT_ANALYSIS_ROOT]
    
    for root_dir in search_roots:
        if not os.path.exists(root_dir):
            continue
            
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith(file_extension):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if query.lower() in content.lower():
                            rel_path = os.path.relpath(file_path, root_dir)
                            # 매칭된 라인 찾기
                            lines = content.split('\n')
                            matched_lines = [f"  {i+1}: {line.strip()}" for i, line in enumerate(lines) 
                                           if query.lower() in line.lower()][:3]  # 최대 3줄
                            
                            results.append(f"📁 {os.path.basename(root_dir)}/{rel_path}\n" + 
                                         "\n".join(matched_lines))
                    except Exception:
                        continue
    
    if not results:
        return f"'{query}' 관련 파일을 찾지 못했습니다."
    
    return f"=== '{query}' 검색 결과 ===\n\n" + "\n\n".join(results[:5])  # 최대 5개 결과

@tool
def get_godot_reference(file_path: str) -> str:
    """특정 파일의 내용을 가져옵니다.
    
    Args:
        file_path: 파일 경로 (상대 경로 또는 절대 경로)
    
    Returns:
        파일 내용
    """
    # 상대 경로면 KB 루트에서 찾기
    if not file_path.startswith('/'):
        for root_dir in [PONG_PROJECT_ROOT, GODOT_ANALYSIS_ROOT]:
            full_path = os.path.join(root_dir, file_path)
            if os.path.exists(full_path):
                file_path = full_path
                break
    
    if not os.path.exists(file_path):
        return f"파일을 찾을 수 없습니다: {file_path}"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"📄 {file_path}\n\n{content}"
    except Exception as e:
        return f"파일 읽기 오류: {str(e)}"