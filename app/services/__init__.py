"""
Services package - Business logic layer
"""
from app.services.ai_service import (
    get_system_prompt,
    get_current_model,
    set_current_model,
    generate_ai_response,
    generate_gpt_response,
    generate_lite_response,
    generate_coder_response,
    generate_max_response
)

from app.services.chat_service import (
    get_conversation,
    save_conversation,
    clear_conversation,
    chat_with_ai,
    edit_message,
    get_debug_info
)

from app.services.search_service import (
    should_search_web,
    web_search
)

from app.services.speech_service import generate_speech

from app.services.code_service import execute_code

from app.services.dociq_service import (
    get_dociq_session_id,
    get_dociq_documents,
    generate_dociq_response,
    process_document_upload,
    delete_document,
    clear_all_documents,
    save_chat_message,
    generate_summary
)

from app.services.viziq_service import (
    generate_kpis,
    generate_chart_configs,
    generate_insights,
    generate_dashboard_name,
    process_data_file,
    generate_full_analysis
)

from app.services.productivity_service import (
    get_all_notes,
    create_note,
    delete_note,
    get_all_tasks,
    create_task,
    update_task,
    delete_task,
    get_all_reminders,
    create_reminder,
    delete_reminder,
    get_stats
)

from app.services.apigee_service import (
    extract_proxy_details,
    validate_proxy_details,
    generate_apigee_bundle,
    process_apigee_request
)
