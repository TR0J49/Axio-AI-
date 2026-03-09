"""
Search routes - Web search and speech endpoints
"""
from flask import Blueprint, request, jsonify

from app.services.search_service import web_search
from app.services.ai_service import generate_ai_response

search_bp = Blueprint('search', __name__)


@search_bp.route('/search', methods=['POST'])
def search():
    """Perform web search and optionally get AI summary"""
    data = request.json
    query = data.get('query', '')
    summarize = data.get('summarize', False)

    if not query:
        return jsonify({'error': 'No query provided'}), 400

    # Perform web search
    results = web_search(query)

    if not results:
        return jsonify({
            'results': [],
            'summary': 'No search results found.',
            'query': query
        })

    # If summarize is requested, use AI to summarize results
    summary = None
    if summarize:
        search_context = f"Web search results for '{query}':\n\n"
        for i, r in enumerate(results, 1):
            search_context += f"{i}. **{r['title']}**\n"
            if r['snippet']:
                search_context += f"   {r['snippet']}\n"
            if r['link']:
                search_context += f"   Link: {r['link']}\n"
            search_context += "\n"

        # Get AI summary
        summary_conversation = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Summarize the following search results concisely and provide key insights. Include relevant links when appropriate."
            },
            {
                "role": "user",
                "content": search_context + "\n\nPlease summarize these search results and provide the most relevant information."
            }
        ]
        summary = generate_ai_response(summary_conversation)

    return jsonify({
        'results': results,
        'summary': summary,
        'query': query
    })

