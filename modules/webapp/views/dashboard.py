# modules/web_application/views/dashboard.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from ..models.models import User, db, ScrapedData, PromptLog
from ..service.scraper import WebScraper
from ..service.prompt_handler import PromptHandler
from ..views.auth import login_required

dashboard_bp = Blueprint('dashboard', __name__)
scraper = WebScraper()
prompt_handler = PromptHandler()


def get_current_user():
    """Helper function to get the current user from session"""
    user = session.get('user_info')
    if user:
        return user;
    return None

@dashboard_bp.route('/dashboard')
@login_required
def index():
    # user = get_current_user()
    # if not user:
    #     flash('Please log in to access this page', 'error')
    #     print("NOT LOGGED IN AT Dashboard")
    #     return redirect(url_for('auth.login'))
    user = session.get('user_info')
    if not user:
        flash('Please log in to access this page', 'error')
        return redirect(url_for('auth.login'))

    print("CURRENT_USER: ", user["id"])
    scraped_data = ScrapedData.query.filter_by(created_by_user_id=user["id"]).all()
    prompt_logs = PromptLog.query.filter_by(created_by_user_id=user["id"]).all()
    
    # Serialize metadata for JSON rendering
    serialized_data = []
    for data in scraped_data:
        metadata_serialized = data.page_metadata if isinstance(data.page_metadata, dict) else None
        serialized_data.append({
            "id": data.id,
            "url": data.url,
            "content": data.content,
            "metadata": metadata_serialized,
            "created_at": data.created_at
        })
    return render_template('dashboard/index.html',
                         scraped_data=serialized_data, 
                         prompt_logs=prompt_logs)
    # return render_template('dashboard/index.html')

@dashboard_bp.route('/scrape', methods=['GET', 'POST'])
@login_required
def scrape_url():
    user = get_current_user()
    if not user:
        flash('Please log in to access this page', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        url = request.form.get('url')
        if not url:
            flash('Please provide a URL', 'error')
            return redirect(url_for('dashboard.index'))

        result = scraper.scrape_url(url)
        
        if result['status'] == 'success':
            # Analyze scraped data using LangChain
            analysis, tokens = prompt_handler.process_scraped_data(result)
            
            # Save to database
            scraped_data = ScrapedData(
                url=url,
                content=result['content'],
                page_metadata=result['metadata'],
                created_by_user_id=user["id"]
            )
            db.session.add(scraped_data)
            
            # Log the analysis as a prompt
            prompt_log = PromptLog(
                prompt_text=f"Analyze scraped data from: {url}",
                generated_output=analysis,
                tokens_used=tokens,
                created_by_user_id=user["id"]
            )
            db.session.add(prompt_log)
            
            db.session.commit()
            flash('URL successfully scraped and analyzed!', 'success')
        else:
            flash(f'Error scraping URL: {result["error"]}', 'error')
            
        return redirect(url_for('dashboard.index'))
        
    return render_template('dashboard/scraper.html')

@dashboard_bp.route('/prompt', methods=['GET', 'POST'])
@login_required
def create_prompt():
    user = get_current_user()
    if not user:
        flash('Please log in to access this page', 'error')
        print("Not logged in")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        prompt_text = request.form.get('prompt')
        context = request.form.get('context')
        
        if not prompt_text:
            flash('Please provide a prompt', 'error')
            return redirect(url_for('dashboard.create_prompt'))
            
        response, tokens = prompt_handler.process_custom_prompt(prompt_text, context)
        
        prompt_log = PromptLog(
            prompt_text=prompt_text,
            generated_output=response,
            tokens_used=tokens,
            created_by_user_id=user["id"]
        )
        db.session.add(prompt_log)
        db.session.commit()
        
        flash('Prompt processed successfully!', 'success')
        return redirect(url_for('dashboard.index'))
    prompt_logs = PromptLog.query.filter_by(created_by_user_id=user["id"]).all()
        
    return render_template('dashboard/prompt.html', prompt_logs=prompt_logs)

@dashboard_bp.route('/delete/scraped/<int:id>', methods=['POST'])
@login_required
def delete_scraped(id):
    user = get_current_user()
    if not user:
        flash('Please log in to access this page', 'error')
        return redirect(url_for('auth.login'))

    data = ScrapedData.query.get_or_404(id)
    if data.created_by_user_id != user["id"]:
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
    if not user:
        flash('Please log in to access this page', 'error')
        return redirect(url_for('auth.login'))

    prompt = PromptLog.query.get_or_404(id)
    if prompt.created_by_user_id != user["id"]:
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
