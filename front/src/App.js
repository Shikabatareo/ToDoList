
import { useEffect, useState } from 'react';
import './App.css';
import icoTrash from '../src/img/trash.svg';
import icoInfo from '../src/img/sangU.svg'
import icoEdit from '../src/img/edit.svg'



function App() {

  const API_URL = 'http://localhost:8000'
  const [newTaskTitle,setNewTaskTitle]=useState('')
  const [newTaskPriority,setnewTaskPriority]=useState(3)
  const [newTaskDescription,setNewTaskDescription]=useState('')
  const [newDateTask, setNewDateTask]= useState('')
  const [loading, setLoading] = useState(false)
  const [tasks, setTasks]=useState([])
  const [error,setError] = useState(null)
  const [isOpenForm,setIsOpenForm] = useState(false)
  const [isOpenDetailForm, setIsOpenDetailForm]=useState(false)
  const [selectedTask, setSelectedTask]= useState(null)
  const [parentTaskId, setParentTaskId] = useState(null)

  const [isEditing, setIsEditing] = useState(false);
  const [currentTaskToEdit, setCurrentTaskToEdit] = useState(null);
  const [editTaskTitle, setEditTaskTitle] = useState('');
  const [editTaskDescription, setEditTaskDescription] = useState('');
  const [editTaskPriority, setEditTaskPriority] = useState(3);
  const [editTaskDueDate, setEditTaskDueDate] = useState('');


  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [isSearchFormOpen, setIsSearchFormOpen] = useState(false);
  const [searchFilters, setSearchFilters] = useState({
    includeCompleted: true,
    priorityFilter: null,
  })
  useEffect(()=> {
    fetchTasks()
    const intervalId = setInterval(fetchTasks,10000)
    return () => clearInterval(intervalId)
  },[])


   const openSearchForm = () => {
    setIsSearchFormOpen(true);
  }
const closeSearchForm = () => {
    setIsSearchFormOpen(false);
    setSearchQuery('');
    setIsSearchMode(false);
    setSearchResults([]);
  }

  const clearSearch = () => {
    setSearchQuery('');
    setIsSearchMode(false);
    setSearchResults([]);
    setSearchFilters({
      priorityFilter: null,
    });
  }
  const openForm = (parentTaskId=null)=> {
    setParentTaskId(parentTaskId)
    setIsOpenForm(true)
  }
  const closeaForm = ()=> {
    setParentTaskId(null)
    setIsOpenForm(false)
  }
  const openDetailForm = (task) => {
    setSelectedTask(task);
    setIsOpenDetailForm(true)
  }
  const closeDetailForm = (task) => {
    setIsOpenDetailForm(false)
  }
  const openEditForm = (task) => {
    setIsEditing(true)
    setCurrentTaskToEdit(task)
    setEditTaskTitle(task.title)
    setEditTaskDescription(task.description || '');
    setEditTaskPriority(task.priority || 3);
    setEditTaskDueDate(task.due_date?new Date(task.due_date).toLocaleDateString(): '')
    setIsOpenForm(true)
  }

  const closeEditForm = () => {
    setIsEditing(false);
    setCurrentTaskToEdit(null);
    setIsOpenForm(false);
  }


  const fetchTasks = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/tasks`)
       if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json()
      setTasks(data)
    }
    catch(e) {
       setError('Не удалось загрузить задачи')

    }
    finally {
      setLoading(false)
    }
  }

const deleteTask = async (task_id)=> {
  setLoading(true)
  setError(null)

  try {
    const responce = await fetch(`${API_URL}/tasks/${task_id}`, {
      method: 'DELETE',
    })
    await fetchTasks()

  }
  
  catch(e) {
    setError('Ошибка при удалении задачи')
  }
  finally{ 
    setLoading(false)
  }

}

const handleSearch = async (e)=> {
  e.preventDefault()
  if (!searchQuery.trim()) {
      setError('Введите поисковый запрос');
      return;
    }

    setLoading(true);
    setError(null);
    try {
    const params = new URLSearchParams({
      query: searchQuery,
    })
    if(searchFilters.priorityFilter !==null) {
      params.append('priority_filter',searchFilters.priorityFilter)
    }
    const responce = await fetch(`${API_URL}/tasks/search?${params}`)
    if (!responce.ok) {
        throw new Error(`HTTP error! status: ${responce.status}`);
      }
      const results = await responce.json()
      console.log(results)
      setSearchResults(results)
      setIsSearchMode(true)
      

  }catch (e) {
      setError(`Ошибка при поиске: ${e.message}`);
    } finally {
      setLoading(false);
    }



}

  const handleCreateTask = async (e)=> {
    e.preventDefault()
    setLoading(true)
    setError(null)

    if(!newTaskTitle.trim()) {
      setError('Название задачи не может быть пустым')
      setLoading(false)
      return
    }
    try {
      const responce = await fetch(`${API_URL}/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: newTaskTitle,
          description: newTaskDescription,
          priority: parseInt(newTaskPriority) || null,
          due_date: newDateTask || null,
          parent_id: parentTaskId || null
        })
      })
      await fetchTasks()
      setNewTaskTitle('')
      setNewTaskDescription('')
      setNewDateTask('')
    }
    catch(e) {
      setError(`Ошибка при создании задачи: ${e.message}`)
    }finally {
      setLoading(false)
    }
  }

  const handleCompleteTask = async(task_id)=> {
    setLoading(true)
    setError(null)
    try {
      const responce = await fetch(`${API_URL}/tasks/${task_id}/complete`, {
        method: 'PUT',
      })
      if(responce.ok){await fetchTasks()

        if (isSearchMode) {
          setSearchResults(prev=> prev.map(task=> task.id === task_id ? {...task,is_completed: true}: task))
        }
        
      } else {
        console.error('Failed to complete task:', responce.status, responce.statusText);
      }


     
    }
    catch(e) {
      console.log('Complete taskn error');
      
    }
    finally {
      setLoading(false)
    }
  }

  const handleUnCompleteTask = async(task_id)=> {
    setLoading(true)
    setError(null)
    try {
      const responce = await fetch(`${API_URL}/tasks/${task_id}/uncomplete`, {
        method: 'PUT',
      })
       if(responce.ok){await fetchTasks()} else {
        console.error('Failed to complete task:', responce.status, responce.statusText);
      }
       if (isSearchMode) {
          setSearchResults(prev=> prev.map(task=> task.id === task_id ? {...task,is_completed: false}: task))
        }
    }
    catch(e) {
      console.log('Complete taskn error');
      
    }
    finally {
      setLoading(false)
    }
  }
  const handleUpdateTask = async (e)=> {
    e.preventDefault()
    setLoading(true)
    setError(null)
    if(!editTaskTitle.trim()) {
      setError('Название задачи не может быть пустым')
      setLoading(false)
      return
    }
    try {
      const response = await fetch(`${API_URL}/tasks/${currentTaskToEdit.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: editTaskTitle,
          description: editTaskDescription,
          priority: parseInt(editTaskPriority) || null,
          due_date: editTaskDueDate || null,
          parent_id: currentTaskToEdit.parent_id || null
        })
      })
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      await fetchTasks();
      closeEditForm();  
    }
    catch (e) {
      setError(`Ошибка при обновлении задачи: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }


  const sortTasks = (taskToSort)=> {
    return [...taskToSort].sort((a,b)=> {
      if (a.priority !==b.priority) {
        return a.priority - b.priority
      }
      return a.id - b.id
    })
  }
const renderTasks = (tasksToRender, showSubtasks = true) => {
    const parentTasks = tasksToRender.filter(task => task.parent_id === null);
    const subTasksAll = tasksToRender.filter(task => task.parent_id !== null);
    
    return parentTasks.map((task) => {
      const subTasksParent = showSubtasks ? subTasksAll.filter(sub => sub.parent_id === task.id) : [];
      
      return (
        <div key={task.id} className='task'>
          <div className='container-task'>
            <div className='checkbox-task'>
              <input 
                type='checkbox' 
                id={task.id} 
                checked={task.is_completed} 
                onChange={() => task.is_completed ? handleUnCompleteTask(task.id) : handleCompleteTask(task.id)} 
                disabled={loading}
              />
              <label htmlFor={task.id}>
                <strong>{task.title}</strong>
                {task.priority && <span className='priority-badge'>Приоритет: {task.priority}</span>}
              </label>
            </div>
            {task.due_date && <p>Срок выполнения: {new Date(task.due_date).toLocaleDateString()}</p>}
            <div>
              <img onClick={() => openEditForm(task)} src={icoEdit} width={'30px'} alt="Редактировать" />
              <img onClick={() => openDetailForm(task)} src={icoInfo} width={'30px'} className='ico-img' alt="Подробности" />
              <img onClick={() => deleteTask(task.id)} src={icoTrash} width={'30px'} className='ico-img' alt="Удалить" />
            </div>
          </div>
          
          {subTasksParent.map((subTask) => (
            <div key={subTask.id} className='task'>
              <div className='container-task'>
                <div className='sub-task'>
                  <div className='checkbox-task'>
                    <input 
                      type='checkbox' 
                      id={subTask.id} 
                      checked={subTask.is_completed} 
                      onChange={() => subTask.is_completed ? handleUnCompleteTask(subTask.id) : handleCompleteTask(subTask.id)} 
                      disabled={loading}
                    />
                    <label htmlFor={subTask.id}>
                      <strong>{subTask.title}</strong>
                      {subTask.priority && <span className='priority-badge'>Приоритет: {subTask.priority}</span>}
                    </label>
                  </div>
                  {subTask.due_date && <p>Срок выполнения: {new Date(subTask.due_date).toLocaleDateString()}</p>}
                  <div>
                    <img onClick={() => openEditForm(subTask)} src={icoEdit} width={'30px'} alt="Редактировать" />
                    <img onClick={() => openDetailForm(subTask)} src={icoInfo} width={'30px'} className='ico-img' alt="Подробности" />
                    <img onClick={() => deleteTask(subTask.id)} src={icoTrash} width={'30px'} className='ico-img' alt="Удалить" />
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {!task.is_completed && !isSearchMode && (
            <button onClick={() => openForm(task.id)}>+</button>
          )}
          <hr className='hr'/>
        </div>
      );
    });
  };

  const activeTasks = sortTasks(tasks.filter(task=> !task.is_completed && task.parent_id === null))
  const completedTasks = sortTasks(tasks.filter(task=>task.is_completed && task.parent_id === null))
  const subTasks = sortTasks(tasks.filter(task=> task.parent_id !== null))
  





  return (
    <>
   <header>
    <h1 className='h1'>Мой список задач</h1>
    <button onClick={openSearchForm} className='search-button'>
            🔍 Поиск
          </button>
     </header>
      {isSearchFormOpen && (
        <div className='container-form search-form'>
          <form onSubmit={handleSearch} className='form'>
            <input
              type='text'
              placeholder='Поиск по названию или описанию...'
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              required
            />

          <div className='filter-options'>
              <label>
                Приоритет:
                <select
                  value={searchFilters.priorityFilter || ''}
                  onChange={(e) => setSearchFilters({ ...searchFilters, priorityFilter: e.target.value ? parseInt(e.target.value) : null })}
                >
                  <option value=''>Все</option>
                  <option value='1'>1</option>
                  <option value='2'>2</option>
                  <option value='3'>3</option>
                  <option value='4'>4</option>
                  <option value='5'>5</option>
                </select>
              </label>

              </div>




            <div className='form-buttons'>
              <button type='submit' disabled={loading}>
                {loading ? 'Поиск...' : 'Найти'}
              </button>
              <button type='button' onClick={clearSearch}>
                Очистить
              </button>
              <button type='button' className='button-close' onClick={closeSearchForm}>
                X
              </button>
            </div>
            {error && <p className='error'>{error}</p>}
          </form>
        </div>
      )}
    <div className='container-form'>
      {isOpenForm&&
        <form onSubmit={isEditing ? handleUpdateTask : handleCreateTask} className='form'>
          <input
          
          type='text'
          placeholder='Название задачи'
          value={isEditing ? editTaskTitle : newTaskTitle}
          onChange={(e)=>isEditing ? setEditTaskTitle(e.target.value) : setNewTaskTitle(e.target.value)}
          required          
          />
           <input
          type='number'
          placeholder='Приоритетность задачи'
          value={isEditing ? editTaskPriority: newTaskPriority}
          onChange={(e)=>isEditing ? setEditTaskPriority(e.target.value): setnewTaskPriority(e.target.value)}
          required
          min='1'
          max='5'        
          />
          <textarea
          placeholder='Описание задачи'
          value={isEditing ? editTaskDescription: newTaskDescription}
          onChange={(e)=>isEditing ? setEditTaskDescription(e.target.value) : setNewTaskDescription(e.target.value)}
          />
          <input
          type='date'
          placeholder='Срок выполнения'
          value={isEditing ? editTaskDueDate : newDateTask}
          onChange={(e)=> isEditing ? setEditTaskDueDate(e.target.value): setNewDateTask(e.target.value)}
          required          
          />
          <button type='submit' disabled={loading}>
            {loading? 'Добавляем...': isEditing ? 'Обноваить задачу':'Добавить задачу' }
          </button>
        <button className='button-close' onClick={closeaForm}>X</button>
           {error && <p>{error}</p>}
        </form>
}
</div>

    <main className='container'>
        {isSearchMode && (
          <section className='section-tasks search-results'>
            <div className='list-task'>
              <h2>Результаты поиска ({searchResults.length})</h2>
              <button onClick={clearSearch} className='clear-search-btn'>
                ← Вернуться к полному списку
              </button>
              {searchResults.length === 0 ? (
                <p className='p-task'>По вашему запросу ничего не найдено</p>
              ) : (
                renderTasks(searchResults, true)
              )}
            </div>
          </section>
        )}


{!isSearchMode && (
      <div className='container-tasks'>
      <section className='section-tasks'>
        <div className='list-task'>
          <h2>Задачи:</h2>
              {!loading && activeTasks.length == 0 && <p className='p-task'>Пока нет задач. Добавьте первую</p>}
              {activeTasks.map((task)=> {
              const subTasksParent = subTasks.filter(sub=> sub.parent_id === task.id)
              console.log(subTasks)
             return (
              <div key={task.id} className='task'>
                <div className='container-task'>
            <div className='checkbox-task'>
                <input type='checkbox' id={task.id} checked={task.is_completed} onChange={(e)=> task.is_completed ? handleUnCompleteTask(task.id): handleCompleteTask(task.id)} disabled={loading}/>
                <label for={task.id}><strong>{task.title}</strong></label>
            </div>
            {task.due_date && <p>Срок выполнения: {new Date(task.due_date).toLocaleDateString()}</p>}
            <div>
            <img onClick={()=> openEditForm(task)} src={icoEdit}  width={'30px'} ></img>
            <img onClick={()=>openDetailForm(task)} src={icoInfo} width={'30px'} className='ico-img' ></img>
            <img onClick={()=>deleteTask(task.id)} src={icoTrash} width={'30px'} className='ico-img' ></img>
            </div>
            </div>
            
            {subTasksParent.map((subTask) => {
              return (
              <div key={subTask.id} className='task'>
                <div className='container-task'>
                  <div className='sub-task'>
            <div className='checkbox-task'>
                <input type='checkbox' id={subTask.id} checked={subTask.is_completed} onChange={(e)=> subTask.is_completed ? handleUnCompleteTask(subTask.id): handleCompleteTask(subTask.id)} disabled={loading}/>
                <label for={subTask.id}><strong>{subTask.title}</strong></label>
            </div>
            {subTask.due_date && <p>Срок выполнения: {new Date(subTask.due_date).toLocaleDateString()}</p>}
            <div>
            <img onClick={()=> openEditForm(subTask)} src={icoEdit}  width={'30px'} ></img>
            <img onClick={()=>openDetailForm(subTask)} src={icoInfo} width={'30px'} className='ico-img' ></img>
            <img onClick={()=>deleteTask(subTask.id)} src={icoTrash} width={'30px'} className='ico-img' ></img>
            </div>
            </div>
            </div>
              </div>
          
              // {/* {task.description && <p><strong>Описание:</strong> {task.description}</p>}
              //  <p><strong>Приоритет:</strong> {task.priority}</p>
              //  <p><strong>Выполнена:</strong> {task.is_completed ? 'Да' : 'Нет'}</p>
              //   {task.ai_comment && <p><strong>Совет от ИИ:</strong> {task.ai_comment}</p>} */}
             )})}
             {!task.is_completed && (
              <button onClick={()=>openForm(task.id)}>+</button>
            )}
              <hr className='hr'/>
            
        </div>
             )
            })}
            </div>
      </section>
      <section className='section-tasks completed-tasks'>
        <div className='list-task'> 
          <h2>Выполненные задачи:</h2>
          {!loading && completedTasks.length == 0 && <p className='p-task'>Пока нет выполненных задач</p>}
          {completedTasks.map((task)=> {
             const subTasksParent = subTasks.filter(sub=> sub.parent_id === task.id)
             return (
              <div key={task.id} className='task'>
                <div className='container-task'>
            <div className='checkbox-task'>
                <input type='checkbox' id={task.id} checked={task.is_completed} onChange={(e)=> task.is_completed ? handleUnCompleteTask(task.id): handleCompleteTask(task.id)} disabled={loading}/>
                <label for={task.id} ><strong>{task.title}</strong></label>
            </div>
            <img onClick={()=>deleteTask(task.id)} src={icoTrash} width={'30px'} className='ico-img' ></img>
            </div>
            {subTasksParent.map((subTask) => (
              <div key={subTask.id} className='task'>
                <div className='container-task'>
                  <div className='sub-task'>
            <div className='checkbox-task'>
                <input type='checkbox' id={subTask.id} checked={true} onChange={(e)=> subTask.is_completed ? handleUnCompleteTask(subTask.id): handleCompleteTask(subTask.id)} disabled={loading}/>
                <label htmlFor={subTask.id}><strong>{subTask.title}</strong></label>
            </div>
            {subTask.due_date && <p>Срок выполнения: {new Date(subTask.due_date).toLocaleDateString()}</p>}
            <div>
            <img onClick={()=>openDetailForm(subTask)} src={icoInfo} width={'30px'} className='ico-img' ></img>
            <img onClick={()=>deleteTask(subTask.id)} src={icoTrash} width={'30px'} className='ico-img' ></img>
            </div>
            </div>
            </div>
            </div>
          
              // {/* {task.description && <p><strong>Описание:</strong> {task.description}</p>}
              //  <p><strong>Приоритет:</strong> {task.priority}</p>}
              //  <p><strong>Выполнена:</strong> {task.is_completed ? 'Да' : 'Нет'} </p>
              //   {task.ai_comment && <p><strong>Совет от ИИ:</strong> {task.ai_comment}</p>} */}
          ))}
          
              <hr className='hr'/>
              {/* {task.description && <p><strong>Описание:</strong> {task.description}</p>}
               <p><strong>Приоритет:</strong> {task.priority}</p>
               <p><strong>Выполнена:</strong> {task.is_completed ? 'Да' : 'Нет'}</p>
                {task.ai_comment && <p><strong>Совет от ИИ:</strong> {task.ai_comment}</p>} */}
            </div>
          )})}
        </div>
      </section>
      </div>
)}
      {isOpenDetailForm && selectedTask && (
        <div className='detail-form'>
        <h2>{selectedTask.title}</h2>
         {selectedTask.description && <p><strong>Описание: </strong> {selectedTask.description}</p>}
         {selectedTask.ai_comment && <p><strong>Совет: </strong>{selectedTask.ai_comment}</p>}
        <button onClick={()=> closeDetailForm()}>X</button>
      </div>
    ) }
      <button onClick={()=> openForm(null)} className='add-task'>+</button>
    </main>
    
  </>
  );
}

export default App;
