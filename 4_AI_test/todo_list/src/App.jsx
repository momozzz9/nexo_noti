import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [todos, setTodos] = useState(() => {
    const saved = localStorage.getItem('antigravity_todos');
    return saved ? JSON.parse(saved) : [];
  });
  const [inputValue, setInputValue] = useState('');

  useEffect(() => {
    localStorage.setItem('antigravity_todos', JSON.stringify(todos));
  }, [todos]);

  const addTodo = () => {
    if (inputValue.trim() === '') return;
    const newTodo = {
      id: Date.now(),
      text: inputValue,
      completed: false
    };
    setTodos([newTodo, ...todos]);
    setInputValue('');
  };

  const deleteTodo = (id) => {
    setTodos(todos.filter(todo => todo.id !== id));
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      addTodo();
    }
  };

  return (
    <div className="todo-container">
      <h1>Task Master</h1>
      
      <div className="input-group">
        <input
          id="todo-input"
          type="text"
          placeholder="오늘 할 일을 입력하세요..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
        />
        <button id="add-button" className="add-btn" onClick={addTodo}>추가</button>
      </div>

      <ul>
        {todos.length > 0 ? (
          todos.map(todo => (
            <li key={todo.id} className="todo-item">
              <span className="todo-text">{todo.text}</span>
              <button 
                className="delete-btn" 
                onClick={() => deleteTodo(todo.id)}
                id={`delete-${todo.id}`}
              >
                삭제
              </button>
            </li>
          ))
        ) : (
          <p className="empty-state">할 일이 없습니다. 새로운 할 일을 추가해보세요!</p>
        )}
      </ul>
    </div>
  )
}

export default App
