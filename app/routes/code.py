"""
Code routes - Code execution endpoints
"""
import time
from flask import Blueprint, request, jsonify
import requests

from app.config.constants import PISTON_LANGUAGES, PISTON_API_URL, CODE_FILE_EXTENSIONS

code_bp = Blueprint('code', __name__)


@code_bp.route('/execute', methods=['POST'])
def execute_code():
    """Execute code using Piston API"""
    data = request.json
    language = data.get('language', '').lower()
    code = data.get('code', '')
    stdin = data.get('stdin', '')

    if not code:
        return jsonify({'success': False, 'error': 'No code provided'})

    if language not in PISTON_LANGUAGES:
        return jsonify({
            'success': False,
            'error': f'Unsupported language: {language}. Supported: Python, JavaScript, Java, C++, C, Go, Rust, Ruby, PHP'
        })

    lang_config = PISTON_LANGUAGES[language]
    file_ext = CODE_FILE_EXTENSIONS.get(lang_config['language'], 'txt')

    # Prepare request for Piston API
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
        start_time = time.time()

        response = requests.post(
            PISTON_API_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        execution_time = int((time.time() - start_time) * 1000)

        if response.status_code == 200:
            result = response.json()

            # Extract output and errors
            run_result = result.get('run', {})
            compile_result = result.get('compile', {})

            output = run_result.get('stdout', '')
            error = run_result.get('stderr', '')

            # Check for compilation errors
            if compile_result.get('stderr'):
                error = compile_result.get('stderr', '') + '\n' + error

            # Check exit code
            exit_code = run_result.get('code', 0)

            return jsonify({
                'success': True,
                'output': output,
                'error': error,
                'exit_code': exit_code,
                'execution_time': execution_time
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Execution service error: {response.status_code}'
            })

    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Code execution timed out (max 30 seconds)'
        })
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Connection error: {str(e)}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Execution failed: {str(e)}'
        })
