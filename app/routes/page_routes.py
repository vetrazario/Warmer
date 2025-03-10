from flask import Blueprint, render_template

bp = Blueprint('pages', __name__)

@bp.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@bp.route('/smtp-test')
def smtp_test():
    """Страница управления SMTP-серверами"""
    return render_template('smtp.html')

@bp.route('/campaigns')
def campaigns():
    """Страница управления кампаниями"""
    return render_template('campaigns.html')

@bp.route('/campaign-stats/<int:campaign_id>')
def campaign_stats(campaign_id):
    """Страница статистики кампании"""
    return render_template('campaign_stats.html', campaign_id=campaign_id)

@bp.route('/dashboard')
def dashboard():
    """Страница дашборда"""
    return render_template('dashboard.html')

@bp.route('/logs')
def logs():
    """Страница логов отправки писем"""
    return render_template('logs.html') 