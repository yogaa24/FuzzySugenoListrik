from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

# Sample data
todos = [
    {"id": 1, "task": "Belajar Flask", "completed": False},
    {"id": 2, "task": "Deploy ke Railway", "completed": False},
    {"id": 3, "task": "Buat dokumentasi", "completed": False}
]

@app.route('/')
def home():
    return render_template('index.html', todos=todos)

@app.route('/api/todos', methods=['GET'])
def get_todos():
    return jsonify(todos)

@app.route('/api/todos', methods=['POST'])
def add_todo():
    data = request.get_json()
    if 'task' in data:
        new_id = max([todo['id'] for todo in todos]) + 1 if todos else 1
        new_todo = {
            "id": new_id,
            "task": data['task'],
            "completed": False
        }
        todos.append(new_todo)
        return jsonify(new_todo), 201
    return jsonify({"error": "Task is required"}), 400

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    global todos
    for i, todo in enumerate(todos):
        if todo['id'] == todo_id:
            deleted = todos.pop(i)
            return jsonify(deleted), 200
    return jsonify({"error": "Todo not found"}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)