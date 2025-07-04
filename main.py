from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel,ConfigDict
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, or_
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session,relationship
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update
import google.generativeai as genai
from telegram.ext import  CommandHandler, CallbackContext
import requests
from telegram import Bot,Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
from fastapi.security import OAuth2PasswordRequestForm
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    oauth2_scheme,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from jose import JWTError, jwt
from auth import SECRET_KEY, ALGORITHM
import json
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from contextlib import asynccontextmanager
import httpx
import urllib.parse

load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
TOKEN = os.getenv('TOKEN').strip()
print(TOKEN)

bot_application = Application.builder().token(TOKEN).build()

if not os.getenv('GEMINI_API_KEY'):
    raise ValueError('GEMINI_API_KEY не найден в env файле')

DATABASE_URL = 'postgresql://postgres:1337@localhost/tododb'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit = False, autoflush=False, bind=engine, class_ =Session)
Base = declarative_base()


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
class UserResponce(BaseModel):
    id:int
    username:str
    email: str
    class Config:
        orm_mode = True
class Token(BaseModel):
    access_token:str
    token_type: str
class TokenData(BaseModel):
    username: str

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer,primary_key=True,index=True)
    username = Column(String(50),unique=True,nullable=False)
    email = Column(String(100),unique=True,nullable=False)
    password_hash = Column(String(128), nullable=False)
    telegram_chat_id = Column(String(50),unique=True)

    tasks = relationship('Task',back_populates='owner', cascade='all, delete-orphan')
class Task(Base): 
    __tablename__= 'tasks'
    id = Column(Integer, primary_key = True, index=True)
    user_id = Column(Integer,ForeignKey('users.id'))
    title = Column(String(255),nullable=False)
    description = Column(String)
    priority = Column(Integer, default=3)
    due_date = Column(TIMESTAMP)
    is_completed = Column(Boolean, default=False)
    ai_comment = Column(String)
    parent_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=True, index = True)
    owner = relationship('User', back_populates='tasks')
Base.metadata.create_all(bind=engine)

(AWAITING_TASK_TITLE, AWAITING_SUBTASK_DATA, AWAITING_DELETE_TITLE) = range(3)


async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    keyboard = [
    [InlineKeyboardButton('Добавить задачу', callback_data='add_task')],
    [InlineKeyboardButton('Удалить задачу', callback_data='delete_task')],
    [InlineKeyboardButton("Добавить подзадачу", callback_data='add_subtask')],
    [InlineKeyboardButton("Показать задачи", callback_data='show_tasks')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! 👋\n\nЯ твой бот-помощник для управления задачами.", reply_markup=reply_markup
    )
async def button_handler(update:Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    command = query.data
    if command == 'add_task':
        await query.message.reply_text('Пожалуйста, введите название новой задачи:')
        return AWAITING_TASK_TITLE
    elif command == 'delete_task':
        await query.message.reply_text('Пожалуйста, введите название задачи, которую хотите удалить:')
        return AWAITING_DELETE_TITLE
    elif command == 'add_subtask':
        await query.message.reply_text('Введите название родительской задачи, а затем, через пробел, название подзадачи:')
        return AWAITING_SUBTASK_DATA
    elif command == 'show_tasks':
        await show_tasks(query,context)
        return ConversationHandler.END

async def add_task(update:Update, context:CallbackContext):
    task_title = update.message.text
    if not task_title:
        await update.message.reply_text('Пожалуйста, укажите название задачи. Пример: Купить молоко')
        return
    fastapi_url = 'http://localhost:8000/tasks'
    payload = {
        "title": task_title,
        "description": 'Добавлено через Telegram',
        "due_date": None,
        "parent_id": None
    }

    try: 
        async with httpx.AsyncClient() as client:
            response = await client.post(fastapi_url, json=payload)
        if response.status_code == 200:
            response_data = response.json()
            ai_advice = response_data.get('ai_advice', 'Совет от ИИ не получен')
            await update.message.reply_text(
                f"✅ Задача '{task_title}' успешно добавлена!\n"
                f"🧠 Совет от ИИ: {ai_advice}"
            )
        else: 
            await update.message.reply_text(
                f"❌ Не удалось добавить задачу. Ошибка: {response.status_code} - {response.text}"
            )
    except httpx.RequestError as e:
        await update.message.reply_text(
            f"❌ Ошибка соединения с сервером FastAPI: {e}"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Произошла непредвиденная ошибка: {e}"
        )
    return ConversationHandler.END
async def add_subtask(update: Update, context: CallbackContext):
    full_command_text = update.message.text
    parent_task_obj = None
    subtask_title = None
    parent_task_name = None
    with SessionLocal() as db:
        all_parent_tasks = db.query(Task).filter(Task.parent_id == None).all()
        sorted_parent_tasks = sorted(all_parent_tasks, key=lambda x: len(x.title),reverse=True)
        for task in sorted_parent_tasks:
            if full_command_text.lower().startswith(task.title.lower()):
               if len(full_command_text) == len(task.title) or full_command_text[len(task.title)]== ' ':
                   parent_task_obj = task
                   parent_task_name = task.title
                   subtask_title = full_command_text[len(parent_task_name):].strip()
                   break
        if not parent_task_obj:
            await update.message.reply_text(f"❌ Родительская задача не найдена. Пожалуйста, убедитесь, что вы ввели полное и точное название родительской задачи.")
            return AWAITING_SUBTASK_DATA
        if not subtask_title:
             await update.message.reply_text("Пожалуйста, укажите название подзадачи.")
             return AWAITING_SUBTASK_DATA
        fastapi_url = 'http://localhost:8000/tasks'
        payload = {
            "title": subtask_title,
            "description": f'Добавлено как подзадача для "{parent_task_name}" через Telegram',
            "due_date": None,
            "parent_id": parent_task_obj.id
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(fastapi_url, json=payload)
            if response.status_code == 200:
                response_data = response.json()
                ai_advice = response_data.get('ai_advice', 'Совет от ИИ не получен')
                await update.message.reply_text(
                    f"✅ Подзадача '{subtask_title}' для задачи '{parent_task_name}' успешно добавлена!\n"
                    f"🧠 Совет от ИИ: {ai_advice}"
                )
            else:
                await update.message.reply_text(
                    f"❌ Не удалось добавить подзадачу. Ошибка: {response.status_code} - {response.text}"
                )
        except httpx.RequestError as e:
            await update.message.reply_text(
                f"❌ Ошибка соединения с сервером FastAPI: {e}"
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Произошла непредвиденная ошибка: {e}"
            )
        return ConversationHandler.END
async def delete_task_command(update: Update, context: CallbackContext):
    task_delete = update.message.text
    if not task_delete:
        await update.message.reply_text(
            "Пожалуйста, укажите название задачи для удаления. Пример: Купить молоко"
        )
        return
    
    encoded_task_delete = urllib.parse.quote(task_delete)
    fastapi_url = f"http://localhost:8000/tasks/task-title/{encoded_task_delete}"


    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(fastapi_url)

        if response.status_code == 200:
            await update.message.reply_text(f"🗑️ Задача с названием {task_delete} успешно удалена.")
        elif response.status_code == 404:
            await update.message.reply_text(f"❌ Задача с названием {task_delete} не найдена.")
        else:
            await update.message.reply_text(
                f"❌ Не удалось удалить задачу. Ошибка: {response.status_code} - {response.text}"
            )
    except httpx.RequestError as e:
        await update.message.reply_text(
            f"❌ Ошибка соединения с сервером FastAPI: {e}"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Произошла непредвиденная ошибка: {e}"
        )
    return ConversationHandler.END
async def show_tasks(update: Update, context: CallbackContext):
    message_text = "<b> Ваш список задач:</b>\n\n"
    with SessionLocal() as db: 
        parent_tasks = db.query(Task).filter(Task.parent_id==None).order_by(Task.is_completed,Task.id).all()
    if not parent_tasks:
        message_text = "У вас пока нет задач. Самое время добавить первую!"
    else: 
        task_lines = []
        for task in parent_tasks:
                status_icon = '✅' if task.is_completed else ""
                task_lines.append(f'{status_icon} {task.title}')
                if task.description:
                    task_lines.append(f'  <i>{task.description}</i>')
                if task.ai_comment:
                    task_lines.append(f'  🧠: {task.ai_comment}')
                sub_tasks = db.query(Task).filter(Task.parent_id==task.id).order_by(Task.is_completed,Task.id).all()
                if sub_tasks:
                    for sub_task in sub_tasks:
                        sub_status_icon = '✅' if sub_task.is_completed else ""
                        task_lines.append(f'  <code>{sub_status_icon} └─ {sub_task.title}</code>')
                        if sub_task.description:
                            task_lines.append(f'    <code>  <i>{sub_task.description}</i></code>')
                        if sub_task.ai_comment:
                            task_lines.append(f'    <code>  🧠: {sub_task.ai_comment}</code>')
                task_lines.append("")
        message_text +='\n'.join(task_lines)
    await update.message.reply_html(message_text)
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text('Действие отменено.')
    return ConversationHandler.END
@asynccontextmanager
async def lifespan(app):
 
    print("Приложение запускается, настраиваем бота...")

    conv_handler = ConversationHandler(entry_points=[CallbackQueryHandler(button_handler)],
                                       states={AWAITING_TASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task)],
                                               
                                               AWAITING_SUBTASK_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_subtask)],
                                            AWAITING_DELETE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_task_command)],
                                               },
                                               fallbacks=[CommandHandler('cancel',cancel)]
                                       )


    bot_application.add_handler(CommandHandler("start", start))
    bot_application.add_handler(conv_handler)
    bot_application.add_handler(CommandHandler("tasks", show_tasks))

    await bot_application.initialize()

    await bot_application.start()

    await bot_application.updater.start_polling()
    print("Бот успешно запущен в режиме polling и интегрирован в FastAPI.")

    yield

  
    print("Приложение останавливается, выключаем бота...")

    await bot_application.updater.stop()

    await bot_application.stop()

    await bot_application.shutdown()
    print("Бот успешно остановлен.")


app = FastAPI(lifespan=lifespan)


origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=['*'], allow_headers=['*'])

class TaskResponce(BaseModel):
    id: int
    title: str
    description: str | None = None
    priority: int
    due_date: datetime | None = None
    is_completed: bool
    ai_comment: str | None = None
    parent_id: int | None = None
    user_id: int
    model_config = ConfigDict(from_attributes=True)
class TaskCreate(BaseModel):
    title: str
    description: str | None=None
    priority: int | None=3
    due_date: datetime | None = None
    parent_id: int | None=None
class TaskUpdate(BaseModel):
    title:str | None=None
    description: str | None=None
    priority: int | None=None
    due_date: datetime | None = None
    is_completed: bool | None = None 
    parent_id: int | None = None
class TaskSearch(BaseModel):
    query: str
    priority_filter: int | None=None
def get_db(): 
    db = SessionLocal()
    try:
        yield db
    finally: 
        db.close()
        
        

def get_ai_comment(task_title:str)-> str:
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Дай короткий, мотивирующий или полезный совет по задаче: '{task_title}'."
        response = model.generate_content(prompt)
        if response.text:
            return response.text.strip()
        else:
            return 'Нет овтета от ИИ'
    except Exception as e:
        print(f"Ошибка при получении AI-комментария от Gemini: {e}")
        return "Произошла ошибка при обращении к ИИ."



async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username = payload.get('sub')
        if username is None:
            print('Username not found')
        token_data = TokenData(username=username)
    except JWTError:
        print('Token error')
    user = db.query(User).filter(User.username==token_data.username).first()
    if user is None:
        print('User not found')
    return user

@app.post('/tasks',response_model=TaskResponce)
def create_task(task:TaskCreate, db: Session = Depends(get_db), current_user:User = Depends(get_current_user)):
    db_task = Task(**task.dict(),user_id=current_user.id)
    db_task.ai_comment = get_ai_comment(task.title)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return {'message': 'Task created', 'ai_advice':db_task.ai_comment, 'task': db_task}

@app.get('/tasks', response_model=list[TaskResponce])
def get_tasks(db: Session = Depends(get_db), current_user: User= Depends(get_current_user)):
    return db.query(Task).filter(Task.user_id == current_user.id).all()
@app.get('/tasks/search')
def search_tasks(
    query = Query(...,description='Поисковый запрос'),
    priority_filter = Query(None, description ="Фильтр по приоритету"),
    db: Session = Depends(get_db)

):
    base_query = db.query(Task)
    if query:
        search_filter = or_(Task.title.ilike(f'%{query}%'), Task.description.ilike(f'%{query}%'))
        base_query = base_query.filter(search_filter)
    if priority_filter is not None:
        base_query = base_query.filter(Task.priority == priority_filter)
    matching_tasks = base_query.all()
    results_dict = {task.id: task for task in matching_tasks}
    parent_ids_to_fetch = {
        task.parent_id for task in matching_tasks if task.parent_id is not None and task.parent_id not in results_dict
    }
    if parent_ids_to_fetch:
        parent_tasks = db.query(Task).filter(Task.id.in_(parent_ids_to_fetch)).all()
        for parent in parent_tasks:
            results_dict[parent.id]=parent
    return list(results_dict.values())

@app.delete('/tasks/{task_id}')
def delete_task(task_id, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_task = db.query(Task).filter(Task.id == task_id, Task.user_id==current_user.id).first()
    if db_task is None: 
        raise HTTPException(status_code=404,detail='Task not found')
    db.delete(db_task)
    db.commit()
    return {'message:' f'Task delete {task_id}'}
@app.delete('/tasks/task-title/{task_title}')
def delete_tasks_title(task_title, db:Session = Depends(get_db)):
    task_to_delete = db.query(Task).filter(Task.title.ilike(task_title)).all()
    tasks_to_delete_sort = sorted([task.id for task in task_to_delete],reverse=True)
    if not task_to_delete:
      raise HTTPException(status_code=404,detail='Task not found')
    for task_id in tasks_to_delete_sort:
        found_task = db.query(Task).filter(Task.id==task_id).first()
        if found_task:
            sub_tasks = db.query(Task).filter(Task.parent_id == found_task.id).all()
            for sub_task in sub_tasks:
                db.delete(sub_task)
                
            db.delete(found_task)
    db.commit()
    return{'message': 'delete task'}


@app.put('/tasks/{task_id}/complete')
def complete_task(task_id,db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None: 
        raise HTTPException(status_code=404,detail='Task not found')
    db_task.is_completed = True
    db.commit()
    db.refresh(db_task)
    return {"message: f'Task copmleted with id {task_id}'"}
@app.put('/tasks/{task_id}/uncomplete')
def uncomplete_task(task_id,db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None: 
        raise HTTPException(status_code=404,detail='Task not found')
    db_task.is_completed = False
    db.commit()
    db.refresh(db_task)
    return {"message: f'Task copmleted with id {task_id}'"}

@app.put('/tasks/{task_id}')
def update_task(task_id, task: TaskUpdate, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail='Task not found')
    if db_task.user_id !=current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
    for field, value in task.dict().items():
        setattr(db_task, field, value)
    if task.title is not None and task.title !=db_task.title:
        db_task.ai_comment = get_ai_comment(task.title)
    db.commit()
    db.refresh(db_task)
    return {'message': f'Task updated {task_id}', 'task': db_task}






@app.post('/register',response_model=UserResponce)
def register_user(user:UserCreate, db: Session= Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username,email=user.email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
@app.post('/token', response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),db:Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        print('Login user failed')
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    acces_token= create_access_token(data={'sub': user.username}, expires_delta=access_token_expires)
    return {'access_token': acces_token, 'token_type': 'bearer'}