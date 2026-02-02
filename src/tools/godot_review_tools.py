"""Godot Review Tools - GDScript 코드 리뷰 및 분석."""
import os
import re
from strands import tool

@tool
def read_gdscript_file(file_path: str) -> str:
    """GDScript 파일을 읽어서 내용을 반환합니다.
    
    Args:
        file_path: 읽을 .gd 파일의 경로
    
    Returns:
        파일 내용 또는 오류 메시지
    """
    try:
        if not file_path.endswith('.gd'):
            return f"오류: {file_path}는 GDScript 파일(.gd)이 아닙니다."
        
        if not os.path.exists(file_path):
            return f"오류: 파일 {file_path}를 찾을 수 없습니다."
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return f"파일: {file_path}\n\n{content}"
    except Exception as e:
        return f"파일 읽기 오류: {str(e)}"

@tool
def analyze_gdscript_structure(gdscript_code: str) -> str:
    """GDScript 코드의 구조를 분석합니다.
    
    Args:
        gdscript_code: 분석할 GDScript 코드
    
    Returns:
        코드 구조 분석 결과
    """
    lines = gdscript_code.split('\n')
    
    # 기본 정보 수집
    extends_class = None
    class_name = None
    signals = []
    exports = []
    onready_vars = []
    functions = []
    process_functions = []
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('extends '):
            extends_class = line.replace('extends ', '')
        elif line.startswith('class_name '):
            class_name = line.replace('class_name ', '')
        elif line.startswith('signal '):
            signals.append(line.replace('signal ', ''))
        elif line.startswith('@export '):
            exports.append(line)
        elif line.startswith('@onready '):
            onready_vars.append(line)
        elif line.startswith('func '):
            func_name = line.split('(')[0].replace('func ', '')
            functions.append(func_name)
            if func_name in ['_process', '_physics_process', '_input', '_unhandled_input']:
                process_functions.append(func_name)
    
    result = f"""
=== GDScript 구조 분석 ===

상속: {extends_class or '없음'}
클래스명: {class_name or '없음'}

시그널 ({len(signals)}개):
{chr(10).join(f"- {s}" for s in signals) if signals else "- 없음"}

Export 변수 ({len(exports)}개):
{chr(10).join(f"- {e}" for e in exports) if exports else "- 없음"}

@onready 변수 ({len(onready_vars)}개):
{chr(10).join(f"- {v}" for v in onready_vars) if onready_vars else "- 없음"}

함수 ({len(functions)}개):
{chr(10).join(f"- {f}" for f in functions) if functions else "- 없음"}

프로세스 함수:
{chr(10).join(f"- {f}" for f in process_functions) if process_functions else "- 없음"}
"""
    
    return result

@tool
def check_godot_best_practices(gdscript_code: str) -> str:
    """Godot 베스트 프랙티스 준수 여부를 검사합니다.
    
    Args:
        gdscript_code: 검사할 GDScript 코드
    
    Returns:
        베스트 프랙티스 검사 결과
    """
    issues = []
    suggestions = []
    
    lines = gdscript_code.split('\n')
    
    # 네이밍 컨벤션 검사
    for i, line in enumerate(lines, 1):
        line = line.strip()
        
        # 변수명 검사 (snake_case)
        if line.startswith('var '):
            var_match = re.search(r'var\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
            if var_match:
                var_name = var_match.group(1)
                if not var_name.islower() and '_' not in var_name:
                    if var_name != var_name.lower():
                        issues.append(f"라인 {i}: 변수명 '{var_name}'은 snake_case를 사용해야 합니다")
        
        # 함수명 검사
        if line.startswith('func '):
            func_match = re.search(r'func\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
            if func_match:
                func_name = func_match.group(1)
                if not func_name.startswith('_') and not func_name.islower():
                    issues.append(f"라인 {i}: 함수명 '{func_name}'은 snake_case를 사용해야 합니다")
    
    # 성능 이슈 검사
    has_process = '_process' in gdscript_code
    has_physics_process = '_physics_process' in gdscript_code
    
    if has_process and has_physics_process:
        issues.append("_process와 _physics_process를 동시에 사용하면 성능에 영향을 줄 수 있습니다")
    
    # get_node 사용 패턴 검사
    get_node_count = gdscript_code.count('get_node(')
    dollar_count = gdscript_code.count('$')
    
    if get_node_count > 3:
        suggestions.append(f"get_node() 호출이 {get_node_count}회 발견됨. @onready var로 캐싱을 고려하세요")
    
    # 시그널 연결 패턴 검사
    if '.connect(' in gdscript_code:
        suggestions.append("코드에서 시그널을 연결하는 대신 에디터에서 연결하는 것을 고려하세요")
    
    # 타입 힌트 검사
    untyped_vars = []
    for line in lines:
        if line.strip().startswith('var ') and ':' not in line and '=' in line:
            var_name = line.split('=')[0].replace('var ', '').strip()
            untyped_vars.append(var_name)
    
    if untyped_vars:
        suggestions.append(f"타입 힌트가 없는 변수들: {', '.join(untyped_vars)}")
    
    result = "=== Godot 베스트 프랙티스 검사 ===\n\n"
    
    if issues:
        result += "🚨 문제점:\n"
        for issue in issues:
            result += f"- {issue}\n"
        result += "\n"
    
    if suggestions:
        result += "💡 개선 제안:\n"
        for suggestion in suggestions:
            result += f"- {suggestion}\n"
        result += "\n"
    
    if not issues and not suggestions:
        result += "✅ 베스트 프랙티스를 잘 준수하고 있습니다!\n"
    
    return result

@tool
def analyze_performance_issues(gdscript_code: str) -> str:
    """GDScript 코드의 성능 이슈를 분석합니다.
    
    Args:
        gdscript_code: 분석할 GDScript 코드
    
    Returns:
        성능 이슈 분석 결과
    """
    performance_issues = []
    
    lines = gdscript_code.split('\n')
    
    # _process 함수 내용 분석
    in_process_func = False
    process_content = []
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith('func _process(') or stripped.startswith('func _physics_process('):
            in_process_func = True
            continue
        elif stripped.startswith('func ') and in_process_func:
            in_process_func = False
        
        if in_process_func:
            process_content.append(stripped)
    
    # _process 내 성능 이슈 검사
    if process_content:
        process_text = '\n'.join(process_content)
        
        if 'get_node(' in process_text:
            performance_issues.append("_process 함수에서 get_node() 호출 발견. @onready로 미리 캐싱하세요")
        
        if 'find_child(' in process_text:
            performance_issues.append("_process 함수에서 find_child() 호출 발견. 매우 느린 함수입니다")
        
        if 'get_children()' in process_text:
            performance_issues.append("_process 함수에서 get_children() 호출 발견. 캐싱을 고려하세요")
        
        if process_text.count('new()') > 0:
            performance_issues.append("_process 함수에서 객체 생성 발견. 메모리 누수 위험이 있습니다")
    
    # 전역 성능 이슈
    if gdscript_code.count('print(') > 5:
        performance_issues.append(f"print() 호출이 많음 ({gdscript_code.count('print(')}회). 릴리즈 시 제거하세요")
    
    if 'queue_free()' not in gdscript_code and 'new()' in gdscript_code:
        performance_issues.append("객체 생성은 있지만 queue_free() 호출이 없음. 메모리 누수 확인 필요")
    
    result = "=== 성능 이슈 분석 ===\n\n"
    
    if performance_issues:
        result += "⚠️ 성능 이슈:\n"
        for issue in performance_issues:
            result += f"- {issue}\n"
    else:
        result += "✅ 명백한 성능 이슈가 발견되지 않았습니다.\n"
    
    return result

@tool
def list_gdscript_files(directory_path: str) -> str:
    """디렉토리에서 GDScript 파일들을 찾습니다.
    
    Args:
        directory_path: 검색할 디렉토리 경로
    
    Returns:
        발견된 .gd 파일 목록
    """
    try:
        if not os.path.exists(directory_path):
            return f"오류: 디렉토리 {directory_path}를 찾을 수 없습니다."
        
        gd_files = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.gd'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, directory_path)
                    gd_files.append(rel_path)
        
        if not gd_files:
            return f"디렉토리 {directory_path}에서 GDScript 파일을 찾을 수 없습니다."
        
        result = f"=== {directory_path}의 GDScript 파일들 ===\n\n"
        for i, file_path in enumerate(sorted(gd_files), 1):
            result += f"{i}. {file_path}\n"
        
        return result
    except Exception as e:
        return f"디렉토리 검색 오류: {str(e)}"