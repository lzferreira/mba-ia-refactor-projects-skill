import logging

from database import db
from models.category import Category
from models.task import Task

logger = logging.getLogger(__name__)


class CategoryController:

    @staticmethod
    def list_categories():
        categories = Category.query.all()
        result = []
        for c in categories:
            data = c.to_dict()
            data['task_count'] = Task.query.filter_by(category_id=c.id).count()
            result.append(data)
        return result, 200

    @staticmethod
    def create_category(data):
        if not data:
            return {'error': 'Dados inválidos'}, 400

        name = data.get('name')
        if not name:
            return {'error': 'Nome é obrigatório'}, 400

        category = Category()
        category.name = name
        category.description = data.get('description', '')
        category.color = data.get('color', '#000000')

        try:
            db.session.add(category)
            db.session.commit()
            return category.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            logger.error("Erro ao criar categoria: %s", e)
            return {'error': 'Erro ao criar categoria'}, 500

    @staticmethod
    def update_category(cat_id, data):
        cat = Category.query.get(cat_id)
        if not cat:
            return {'error': 'Categoria não encontrada'}, 404

        if not data:
            return {'error': 'Dados inválidos'}, 400

        if 'name' in data:
            cat.name = data['name']
        if 'description' in data:
            cat.description = data['description']
        if 'color' in data:
            cat.color = data['color']

        try:
            db.session.commit()
            return cat.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            logger.error("Erro ao atualizar categoria: %s", e)
            return {'error': 'Erro ao atualizar'}, 500

    @staticmethod
    def delete_category(cat_id):
        cat = Category.query.get(cat_id)
        if not cat:
            return {'error': 'Categoria não encontrada'}, 404
        try:
            db.session.delete(cat)
            db.session.commit()
            return {'message': 'Categoria deletada'}, 200
        except Exception as e:
            db.session.rollback()
            logger.error("Erro ao deletar categoria: %s", e)
            return {'error': 'Erro ao deletar'}, 500
