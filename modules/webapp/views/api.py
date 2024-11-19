from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from ..models.models import db, ScrapedData, PromptLog
from ..service.scraper import WebScraper
from ..service.prompt_handler import PromptHandler

api_bp = Blueprint('api', __name__, url_prefix='/api')
scraper = WebScraper()
prompt_handler = PromptHandler()

@api_bp.route('/scraped-data', methods=['GET'])
@login_required
def get_scraped_data():
    data = ScrapedData.query.filter_by(created_by_user_id=current_user.id).all()
    print("From api, get_scraped_data:", data)
    for d in data:
        print("From api, in loop:", d)
    return jsonify([{
        'id': item.id,
        'url': item.url,
        'content': item.content,
        'metadata': item.page_metadata,
        'created_at': item.created_at.isoformat()
    } for item in data])

@api_bp.route('/scraped-data', methods=['POST'])
@login_required
def create_scraped_data():
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
        
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
        
    result = scraper.scrape_url(url)
    print("From api, result:", result)
    
    if result['status'] == 'error':
        return jsonify({'error': result['error']}), 400
        
    scraped_data = ScrapedData(
        url=url,
        content=result['content'],
        page_metadata=result['metadata'],
        created_by_user_id=current_user.id
    )
    
    db.session.add(scraped_data)
    db.session.commit()
    
    return jsonify({
        'id': scraped_data.id,
        'url': scraped_data.url,
        'content': scraped_data.content,
        'metadata': scraped_data.metadata,
        'created_at': scraped_data.created_at.isoformat()
    }), 201

@api_bp.route('/scraped-data/<string:id>', methods=['GET'])
@login_required
def get_scraped_data_by_id(id):
    data = ScrapedData.query.get_or_404(id)
    if data.created_by_user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    print("From api, get_scraped_data:", data)
    for d in data:
        print("From api, in loop:", d)
        
    return jsonify({
        'id': data.id,
        'url': data.url,
        'content': data.content,
        'metadata': data.metadata,
        'created_at': data.created_at.isoformat()
    })

@api_bp.route('/scraped-data/<string:id>', methods=['DELETE'])
@login_required
def delete_scraped_data(id):
    data = ScrapedData.query.get_or_404(id)
    if data.created_by_user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    db.session.delete(data)
    db.session.commit()
    
    return jsonify({'message': 'Data deleted successfully'})

@api_bp.route('/prompts', methods=['GET'])
@login_required
def get_prompts():
    prompts = PromptLog.query.filter_by(created_by_user_id=current_user.id).all()
    return jsonify([{
        'id': prompt.id,
        'prompt_text': prompt.prompt_text,
        'generated_output': prompt.generated_output,
        'tokens_used': prompt.tokens_used,
        'created_at': prompt.created_at.isoformat()
    } for prompt in prompts])

@api_bp.route('/prompts', methods=['POST'])
@login_required
def create_prompt():
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
        
    prompt_text = request.json.get('prompt')
    context = request.json.get('context')
    
    if not prompt_text:
        return jsonify({'error': 'Prompt text is required'}), 400
        
    response, tokens = prompt_handler.process_custom_prompt(prompt_text, context)
    
    prompt_log = PromptLog(
        prompt_text=prompt_text,
        generated_output=response,
        tokens_used=tokens,
        created_by_user_id=current_user.id
    )
    
    db.session.add(prompt_log)
    db.session.commit()
    
    return jsonify({
        'id': prompt_log.id,
        'prompt_text': prompt_log.prompt_text,
        'generated_output': prompt_log.generated_output,
        'tokens_used': prompt_log.tokens_used,
        'created_at': prompt_log.created_at.isoformat()
    }), 201

@api_bp.route('/prompts/<string:id>', methods=['DELETE'])
@login_required
def delete_prompt(id):
    prompt = PromptLog.query.get_or_404(id)
    if prompt.created_by_user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    db.session.delete(prompt)
    db.session.commit()
    
    return jsonify({'message': 'Prompt deleted successfully'})
