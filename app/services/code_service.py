"""
Code Execution Service - Piston API integration
"""
import requests
from app.config.constants import PISTON_API_URL, PISTON_LANGUAGES, CODE_FILE_EXTENSIONS


def execute_code(language, code, stdin=''):
    """Execute code using Piston API"""
    language = language.lower()

    if not code:
        return {'success': False, 'error': 'No code provided'}

    if language not in PISTON_LANGUAGES:
        return {
            'success': False,
            'error': f'Unsupported language: {language}. Supported: Python, JavaScript, Java, C++, C, Go, Rust, Ruby, PHP'
        }

    lang_config = PISTON_LANGUAGES[language]
    file_ext = CODE_FILE_EXTENSIONS.get(lang_config['language'], 'txt')

    payload = {
        'language': lang_config['language'],
        'version': lang_config['version'],
        'files': [
            {
                'name': f'main.{file_ext}',
                'content': code
            }
        ],
        'stdin': stdin,
        'args': [],
        'compile_timeout': 10000,
        'run_timeout': 5000,
        'compile_memory_limit': -1,
        'run_memory_limit': -1
    }

    try:
        response = requests.post(PISTON_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        output = result.get('run', {}).get('stdout', '')
        stderr = result.get('run', {}).get('stderr', '')
        compile_output = result.get('compile', {}).get('output', '') if result.get('compile') else ''

        if stderr:
            output = f"{output}\n[STDERR]\n{stderr}" if output else f"[STDERR]\n{stderr}"
        if compile_output and result.get('compile', {}).get('code', 0) != 0:
            output = f"[COMPILE ERROR]\n{compile_output}\n{output}" if output else f"[COMPILE ERROR]\n{compile_output}"

        return {
            'success': True,
            'output': output.strip() or 'Program executed successfully with no output.',
            'language': lang_config['language'],
            'version': lang_config['version']
        }

    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Code execution timed out. Please check for infinite loops.'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'Failed to connect to code execution service: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'An error occurred: {str(e)}'}
