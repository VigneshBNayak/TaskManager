from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Task
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    return render_template('landing.html')

@app.route('/dashboard')
@login_required
def index():
    now = datetime.now()
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_at.desc()).all()

    for task in tasks:
        if task.status == "pending" and task.deadline and task.deadline < now:
            task.status = "failed"
    db.session.commit()

    pending = [t for t in tasks if t.status == "pending"]
    completed = [t for t in tasks if t.status == "completed"]
    failed = [t for t in tasks if t.status == "failed"]

    categorized_pending = {
        "High": [t for t in pending if t.priority == "High"],
        "Medium": [t for t in pending if t.priority == "Medium"],
        "Low": [t for t in pending if t.priority == "Low"],
    }

    categorized_completed = {
        "High": [t for t in completed if t.priority == "High"],
        "Medium": [t for t in completed if t.priority == "Medium"],
        "Low": [t for t in completed if t.priority == "Low"],
    }

    categorized_failed = {
        "High": [t for t in failed if t.priority == "High"],
        "Medium": [t for t in failed if t.priority == "Medium"],
        "Low": [t for t in failed if t.priority == "Low"],
    }

    pending_serialized = [
        {
            "id": t.id,
            "deadline": t.deadline.isoformat()
        }
        for t in pending
    ]

    total = len(tasks)
    def pct(n): return int((n / total) * 100) if total else 0

    stats = {
        "total": total,
        "pending": len(pending),
        "completed": len(completed),
        "failed": len(failed),
        "completed_pct": pct(len(completed)),
        "failed_pct": pct(len(failed))
    }

    return render_template(
        "index.html",
        tasks=tasks,
        categorized_pending=categorized_pending,
        categorized_completed=categorized_completed,
        categorized_failed=categorized_failed,
        stats=stats,
        now=now,
        pending_serialized=pending_serialized 
    )

@app.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return "Unauthorized", 403

    task.content = request.form['content']
    task.priority = request.form['priority']
    deadline_str = request.form['deadline']
    deadline_time = request.form['deadline_time']
    task.deadline = datetime.strptime(deadline_str + " " + deadline_time, "%Y-%m-%d %H:%M")
    
    db.session.commit()
    return redirect('/')

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return "Unauthorized", 403
    db.session.delete(task)
    db.session.commit()
    return redirect('/')

@app.route('/add', methods=['POST'])
@login_required
def add():
    content = request.form['task']
    deadline_str = request.form['deadline']
    deadline_time = request.form['deadline_time']
    priority = request.form['priority']
    deadline = datetime.strptime(deadline_str + " " + deadline_time, "%Y-%m-%d %H:%M")
    task = Task(content=content, deadline=deadline, priority=priority, user_id=current_user.id, status="pending")
    db.session.add(task)
    db.session.commit()
    return redirect('/')

@app.route('/complete/<int:id>')
@login_required
def complete(id):
    task = Task.query.get_or_404(id)
    if task.user_id == current_user.id:
        task.status = "completed"
        db.session.commit()
    return '', 204 

@app.route('/fail/<int:id>')
@login_required
def fail(id):
    task = Task.query.get_or_404(id)
    if task.status == "pending":
        task.status = "failed"
        db.session.commit()
    return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if not user:
            error = "No user matched that username. Register Now!"
        elif not check_password_hash(user.password, password):
            error = "Incorrect password. Try again."
        else:
            login_user(user)
            return redirect('/')

    return render_template('login.html', error=error)

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    Task.query.filter_by(user_id=current_user.id).delete()

    user = User.query.get(current_user.id)
    db.session.delete(user)
    db.session.commit()

    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        new_user = User(username=request.form['username'], password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)