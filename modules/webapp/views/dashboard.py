# modules/web_application/views/dashboard.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from ..models.models import User, db, ScrapedData, PromptLog
from ..service.scraper import WebScraper
from ..service.prompt_handler import PromptHandler
from ..views.auth import login_required
import logging
from sqlalchemy.exc import SQLAlchemyError
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)
scraper = WebScraper()
prompt_handler = PromptHandler()



def get_current_user():
    """Helper function to get the current user from session"""
    try:
        user = session.get('user_info')
        if not user:
            return None
        return user
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return None

@dashboard_bp.route('/dashboard')
@login_required
def index():
    try:
        user = get_current_user()
        if not user:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))

        user_id = user["id"]
        
        # Add debug logging
        logger.info(f"Fetching data for user_id: {user_id}")
        
        scraped_data = ScrapedData.query.filter_by(created_by_user_id=user_id).all()
        logger.info(f"Found {len(scraped_data)} scraped data records")
        
        prompt_logs = PromptLog.query.filter_by(created_by_user_id=user_id).all()
        logger.info(f"Found {len(prompt_logs)} prompt logs")
        
        # Try serializing one record at a time to identify issues
        serialized_data = []
        for data in scraped_data:
            try:
                serialized_data.append(data.to_dict())
                logger.info(f"Serialized data {data.id}")
            except Exception as e:
                logger.error(f"Error serializing scraped data {data.id}: {str(e)}")
                
        serialized_prompts = []
        for log in prompt_logs:
            try:
                # serialized_prompts.append(log.to_dict())
                serialized_prompts.append({
                    "id": str(log.id),  # Ensure UUID is a string
                    "prompt_text": log.prompt_text,
                    "created_at": log.created_at,
                    "tokens_used": log.tokens_used,
                    "generated_output": log.generated_output,
                })
                logger.info(f"Serialized prompt log {log.id}")
            except Exception as e:
                logger.error(f"Error serializing prompt log {log.id}: {str(e)}")
        
        return render_template('dashboard/index.html',
                             scraped_data=serialized_data, 
                             prompt_logs=serialized_prompts)
    
    except SQLAlchemyError as e:
        logger.error(f"Database error in dashboard: {str(e)}")
        flash('An error occurred while loading your data', 'error')
        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.error(f"Unexpected error in dashboard: {str(e)}")
        flash('An unexpected error occurred', 'error')
        return redirect(url_for('auth.login'))

@dashboard_bp.route('/scrape', methods=['GET', 'POST'])
@login_required
def scrape_url():
    try:
        user = get_current_user()
        if not user:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))

        user_id = user["id"]

        if request.method == 'POST':
            url = request.form.get('url')
            if not url:
                flash('Please provide a URL', 'error')
                return redirect(url_for('dashboard.index'))

            result = scraper.scrape_url(url)
            
            if result['status'] == 'success':
                try:
                    # Analyze scraped data using LangChain
                    analysis, tokens = prompt_handler.process_scraped_data(result)
                    
                    # Save to database within transaction
                    scraped_data = ScrapedData(
                        url=url,
                        content=result['content'],
                        page_metadata=result['metadata'],
                        created_by_user_id=user_id
                    )
                    db.session.add(scraped_data)
                    
                    prompt_log = PromptLog(
                        prompt_text=f"Analyze scraped data from: {url}",
                        generated_output=analysis,
                        tokens_used=tokens,
                        created_by_user_id=user_id
                    )
                    db.session.add(prompt_log)
                    
                    db.session.commit()
                    flash('URL successfully scraped and analyzed!', 'success')
                
                except SQLAlchemyError as e:
                    db.session.rollback()
                    logger.error(f"Database error while saving scraped data: {str(e)}")
                    flash('Error saving scraped data', 'error')
                
            else:
                flash(f'Error scraping URL: {result["error"]}', 'error')
            
            return redirect(url_for('dashboard.index'))
            
        return render_template('dashboard/scraper.html')
    
    except Exception as e:
        logger.error(f"Unexpected error in scrape_url: {str(e)}")
        flash('An unexpected error occurred', 'error')
        return redirect(url_for('dashboard.index'))


@dashboard_bp.route('/prompt', methods=['GET', 'POST'])
@login_required
def create_prompt():
    try:
        user = get_current_user()
        if not user:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))

        user_id = str(user["id"])

        if request.method == 'POST':
            prompt_text = request.form.get('prompt')
            context = request.form.get('context')
            
            if not prompt_text:
                flash('Please provide a prompt', 'error')
                return redirect(url_for('dashboard.create_prompt'))
                
            try:
                response, tokens = prompt_handler.process_custom_prompt(prompt_text, context)
                
                prompt_log = PromptLog(
                    prompt_text=prompt_text,
                    generated_output=response,
                    tokens_used=tokens,
                    created_by_user_id=user_id,
                    created_at=datetime.utcnow()  # Explicitly set the datetime
                )
                db.session.add(prompt_log)
                db.session.commit()
                
                flash('Prompt processed successfully!', 'success')
                return redirect(url_for('dashboard.index'))
                
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"Database error in create_prompt: {str(e)}")
                flash('Error saving prompt', 'error')
                return redirect(url_for('dashboard.index'))
                
        prompt_logs = PromptLog.query.filter_by(created_by_user_id=user_id).all()
        return render_template('dashboard/prompt.html', prompt_logs=prompt_logs)
        
    except Exception as e:
        logger.error(f"Unexpected error in create_prompt: {str(e)}")
        flash('An unexpected error occurred', 'error')
        return redirect(url_for('dashboard.index'))


@dashboard_bp.route('/delete/scraped/<int:id>', methods=['POST'])
@login_required
def delete_scraped(id):
    user = get_current_user()
    user_id = str(user["id"])
    if not user:
        flash('Please log in to access this page', 'error')
        return redirect(url_for('auth.login'))

    data = ScrapedData.query.get_or_404(id)
    if data.created_by_user_id != user_id:
        flash('Unauthorized', 'error')
        return redirect(url_for('dashboard.index'))
        
    db.session.delete(data)
    db.session.commit()
    flash('Data deleted successfully', 'success')
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/delete/prompt/<int:id>', methods=['POST'])
@login_required
def delete_prompt(id):
    user = get_current_user()
    user_id = str(user["id"])
    if not user:
        flash('Please log in to access this page', 'error')
        return redirect(url_for('auth.login'))

    prompt = PromptLog.query.get_or_404(id)
    if prompt.created_by_user_id != user_id:
        flash('Unauthorized', 'error')
        return redirect(url_for('dashboard.index'))
        
    db.session.delete(prompt)
    db.session.commit()
    flash('Prompt deleted successfully', 'success')
    return redirect(url_for('dashboard.index'))

# @dashboard_bp.route('/dashboard/gemi')
# @login_required
# def gemini_check():
#     from ..service.prompt_handler import PromptHandler
#     g = PromptHandler()
#     out = g.gemini_check()
#     return out
