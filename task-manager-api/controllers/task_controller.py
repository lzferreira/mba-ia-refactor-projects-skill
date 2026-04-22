import logging
from datetime import datetime, timezone

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)


class TaskController:

    @staticmethod
    def list_tasks():
        tasks = (
            Task.query
            .options(joinedload(Task.user), joinedload(Task.category))
            .all()
        )
        result = []
        for t in tasks:
            data = t.to_dict()
            data['user_name'] = t.user.name if t.user else None
            data['category_name'] = t.category.name if t.category else None
            result.append(data)
        return result, 200

    @staticmethod
    def get_task(task_id):
        task = Task.query.get(task_id)
        if not task:
            return {'error': 'Task não encontrada'}, 404
        return task.to_dict(), 200

    @staticmethod
    def create_task(data):
        if not data:
            return {'error': 'Dados inválidos'}, 400

        title = data.get('title')
        if not title:
            return {'error': 'Título é obrigatório'}, 400
        title = title.strip()
        if len(title) < 3:
            return {'error': 'Título muito curto'}, 400
        if len(title) > 200:
            return {'error': 'Título muito longo'}, 400

        status = data.get('status', 'pending')
        if status not in Task.VALID_STATUSES:
            return {'error': 'Status inválido'}, 400

        priority = data.get('priority', 3)
        try:
            priority = int(priority)
        except (TypeError, ValueError):
            return {'error': 'Prioridade inválida'}, 400
        if priority not in Task.VALID_PRIORITY_RANGE:
            return {'error': 'Prioridade deve ser entre 1 e 5'}, 400

        user_id = data.get('user_id')
        if user_id:
            if not User.query.get(user_id):
                return {'error': 'Usuário não encontrado'}, 404

        category_id = data.get('category_id')
        if category_id:
            if not Category.query.get(category_id):
                return {'error': 'Categoria não encontrada'}, 404

        task = Task()
        task.title = title
        task.description = data.get('description', '')
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id

        due_date = data.get('due_date')
        if due_date:
            try:
                task.due_date = datetime.strptime(due_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                return {'error': 'Formato de data inválido. Use YYYY-MM-DD'}, 400

        tags = data.get('tags')
        if tags:
            if isinstance(tags, list):
                task.tags = ','.join(tags)
            else:
                task.tags = tags

        try:
            db.session.add(task)
            db.session.commit()
            logger.info("Task criada: %s - %s", task.id, task.title)
            return task.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            logger.error("Erro ao criar task: %s", e)
            return {'error': 'Erro ao criar task'}, 500

    @staticmethod
    def update_task(task_id, data):
        task = Task.query.get(task_id)
        if not task:
            return {'error': 'Task não encontrada'}, 404
        if not data:
            return {'error': 'Dados inválidos'}, 400

        if 'title' in data:
            title = data['title'].strip() if data['title'] else ''
            if len(title) < 3:
                return {'error': 'Título muito curto'}, 400
            if len(title) > 200:
                return {'error': 'Título muito longo'}, 400
            task.title = title

        if 'description' in data:
            task.description = data['description']

        if 'status' in data:
            if data['status'] not in Task.VALID_STATUSES:
                return {'error': 'Status inválido'}, 400
            task.status = data['status']

        if 'priority' in data:
            try:
                p = int(data['priority'])
            except (TypeError, ValueError):
                return {'error': 'Prioridade inválida'}, 400
            if p not in Task.VALID_PRIORITY_RANGE:
                return {'error': 'Prioridade deve ser entre 1 e 5'}, 400
            task.priority = p

        if 'user_id' in data:
            if data['user_id'] and not User.query.get(data['user_id']):
                return {'error': 'Usuário não encontrado'}, 404
            task.user_id = data['user_id']

        if 'category_id' in data:
            if data['category_id'] and not Category.query.get(data['category_id']):
                return {'error': 'Categoria não encontrada'}, 404
            task.category_id = data['category_id']

        if 'due_date' in data:
            if data['due_date']:
                try:
                    task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    return {'error': 'Formato de data inválido'}, 400
            else:
                task.due_date = None

        if 'tags' in data:
            if isinstance(data['tags'], list):
                task.tags = ','.join(data['tags'])
            else:
                task.tags = data['tags']

        try:
            db.session.commit()
            logger.info("Task atualizada: %s", task.id)
            return task.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            logger.error("Erro ao atualizar task: %s", e)
            return {'error': 'Erro ao atualizar'}, 500

    @staticmethod
    def delete_task(task_id):
        task = Task.query.get(task_id)
        if not task:
            return {'error': 'Task não encontrada'}, 404
        try:
            db.session.delete(task)
            db.session.commit()
            logger.info("Task deletada: %s", task_id)
            return {'message': 'Task deletada com sucesso'}, 200
        except Exception as e:
            db.session.rollback()
            logger.error("Erro ao deletar task: %s", e)
            return {'error': 'Erro ao deletar'}, 500

    @staticmethod
    def search_tasks(query, status, priority, user_id):
        qs = Task.query

        if query:
            qs = qs.filter(
                db.or_(
                    Task.title.contains(query),
                    Task.description.contains(query),
                )
            )
        if status:
            qs = qs.filter(Task.status == status)
        if priority:
            try:
                qs = qs.filter(Task.priority == int(priority))
            except (ValueError, TypeError):
                return {'error': 'Prioridade inválida'}, 400
        if user_id:
            try:
                qs = qs.filter(Task.user_id == int(user_id))
            except (ValueError, TypeError):
                return {'error': 'user_id inválido'}, 400

        tasks = qs.all()
        return [t.to_dict() for t in tasks], 200

    @staticmethod
    def get_stats():
        total = Task.query.count()
        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()

        overdue_count = (
            Task.query
            .filter(Task.due_date < datetime.now(timezone.utc))
            .filter(Task.status.notin_(['done', 'cancelled']))
            .count()
        )

        stats = {
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
            'overdue': overdue_count,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        }
        return stats, 200
