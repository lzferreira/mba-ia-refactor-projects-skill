import logging
from datetime import datetime, timedelta, timezone

from database import db
from models.task import Task
from models.user import User
from models.category import Category

logger = logging.getLogger(__name__)


class ReportController:

    @staticmethod
    def summary_report():
        total_tasks = Task.query.count()
        total_users = User.query.count()
        total_categories = Category.query.count()

        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()

        p1 = Task.query.filter_by(priority=1).count()
        p2 = Task.query.filter_by(priority=2).count()
        p3 = Task.query.filter_by(priority=3).count()
        p4 = Task.query.filter_by(priority=4).count()
        p5 = Task.query.filter_by(priority=5).count()

        now = datetime.now(timezone.utc)

        overdue_tasks = (
            Task.query
            .filter(Task.due_date < now)
            .filter(Task.status.notin_(['done', 'cancelled']))
            .all()
        )
        overdue_list = []
        for t in overdue_tasks:
            due = t.due_date if t.due_date.tzinfo else t.due_date.replace(tzinfo=timezone.utc)
            overdue_list.append({
                'id': t.id,
                'title': t.title,
                'due_date': str(t.due_date),
                'days_overdue': (now - due).days,
            })

        seven_days_ago = now - timedelta(days=7)
        recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
        recent_done = Task.query.filter(
            Task.status == 'done',
            Task.updated_at >= seven_days_ago,
        ).count()

        users = User.query.all()
        user_stats = []
        for u in users:
            total = u.tasks.count()
            completed = u.tasks.filter_by(status='done').count()
            user_stats.append({
                'user_id': u.id,
                'user_name': u.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0,
            })

        report = {
            'generated_at': str(now),
            'overview': {
                'total_tasks': total_tasks,
                'total_users': total_users,
                'total_categories': total_categories,
            },
            'tasks_by_status': {
                'pending': pending,
                'in_progress': in_progress,
                'done': done,
                'cancelled': cancelled,
            },
            'tasks_by_priority': {
                'critical': p1,
                'high': p2,
                'medium': p3,
                'low': p4,
                'minimal': p5,
            },
            'overdue': {
                'count': len(overdue_list),
                'tasks': overdue_list,
            },
            'recent_activity': {
                'tasks_created_last_7_days': recent_tasks,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_stats,
        }
        return report, 200

    @staticmethod
    def user_report(user_id):
        user = User.query.get(user_id)
        if not user:
            return {'error': 'Usuário não encontrado'}, 404

        tasks = user.tasks.all()
        total = len(tasks)
        done = sum(1 for t in tasks if t.status == 'done')
        pending = sum(1 for t in tasks if t.status == 'pending')
        in_progress = sum(1 for t in tasks if t.status == 'in_progress')
        cancelled = sum(1 for t in tasks if t.status == 'cancelled')
        overdue = sum(1 for t in tasks if t.is_overdue())
        high_priority = sum(1 for t in tasks if t.priority <= 2)

        report = {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            },
            'statistics': {
                'total_tasks': total,
                'done': done,
                'pending': pending,
                'in_progress': in_progress,
                'cancelled': cancelled,
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
            },
        }
        return report, 200
