from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Formulario, Lead
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, URL

admin_formulario_bp = Blueprint('admin_formulario', __name__, template_folder='templates')

TIPOS_FORMULARIO = [
    ('avaliacao_fisica', 'Avaliação Física'),
    ('anamnese_nutricional', 'Anamnese Nutricional'),
    ('outro', 'Outro'),
]

class FormularioForm(FlaskForm):
    lead_id = SelectField('Lead (opcional)', coerce=int, choices=[], default=0)
    tipo = SelectField('Tipo', choices=TIPOS_FORMULARIO, validators=[DataRequired()])
    link = StringField('Link do Formulário', validators=[DataRequired(), URL()])
    submit = SubmitField('Salvar')

def admin_required(func):
    from functools import wraps
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            flash('Acesso restrito ao administrador.', 'danger')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_view

@admin_formulario_bp.route('/admin/formularios')
@login_required
@admin_required
def listar_formularios():
    formularios = Formulario.query.order_by(Formulario.id.desc()).all()
    return render_template('admin/listar_formularios.html', formularios=formularios)

@admin_formulario_bp.route('/admin/formularios/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_formulario():
    form = FormularioForm()
    leads = Lead.query.order_by(Lead.nome).all()
    form.lead_id.choices = [(0, 'Nenhum (modelo)')] + [(lead.id, lead.nome) for lead in leads]
    if form.validate_on_submit():
        lead_id = form.lead_id.data if form.lead_id.data != 0 else None
        novo_form = Formulario(
            lead_id=lead_id,
            tipo=form.tipo.data,
            link=form.link.data,
            status='pendente'
        )
        db.session.add(novo_form)
        db.session.commit()
        flash('Formulário cadastrado com sucesso!', 'success')
        return redirect(url_for('admin_formulario.listar_formularios'))
    return render_template('admin/novo_formulario.html', form=form, formulario=None)

@admin_formulario_bp.route('/admin/formularios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_formulario(id):
    formulario = Formulario.query.get_or_404(id)
    form = FormularioForm(obj=formulario)
    leads = Lead.query.order_by(Lead.nome).all()
    form.lead_id.choices = [(0, 'Nenhum (modelo)')] + [(lead.id, lead.nome) for lead in leads]
    if form.validate_on_submit():
        formulario.lead_id = form.lead_id.data if form.lead_id.data != 0 else None
        formulario.tipo = form.tipo.data
        formulario.link = form.link.data
        db.session.commit()
        flash('Formulário atualizado!', 'success')
        return redirect(url_for('admin_formulario.listar_formularios'))
    return render_template('admin/editar_formulario.html', form=form, formulario=formulario)

@admin_formulario_bp.route('/admin/formularios/<int:id>/deletar', methods=['POST'])
@login_required
@admin_required
def deletar_formulario(id):
    formulario = Formulario.query.get_or_404(id)
    db.session.delete(formulario)
    db.session.commit()
    flash('Formulário removido!', 'success')
    return redirect(url_for('admin_formulario.listar_formularios'))
