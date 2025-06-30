from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
import google.generativeai as genai
from telegram.ext import  CommandHandler, CallbackContext
import requests
from telegram import Bot,Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
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
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer,primary_key=True,index=True)
    username = Column(String(50),unique=True,nullable=False)
    email = Column(String(100),unique=True,nullable=False)
    password_hash = Column(String(128), nullable=False)
    telegram_chat_id = Column(String(50),unique=True)
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

Base.metadata.create_all(bind=engine)


async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! 👋\n\nЯ твой бот-помощник для управления задачами."
    )

async def add_task(update:Update, context:CallbackContext):
    task_title = ' '.join(context.args)
    if not task_title:
        await update.message.reply_text('Пожалуйста, укажите название задачи. Пример: /addtask Купить молоко')
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
async def add_subtask(update: Update, context: CallbackContext):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('Пожалуйста, укажите название родительской задачи и название подзадачи. Пример: /add_subtask Купить молоко Взять деньги')
        return
    subtask_title = args[-1]
    parent_task_name = ' '.join(args[:-1])
    if not parent_task_name or not subtask_title:
        await update.message.reply_text('Неверный формат команды. Пожалуйста, укажите название родительской задачи и название подзадачи. Пример: /add_subtask Купить молоко Взять деньги')
        return
    with SessionLocal() as db:
        parent_task = db.query(Task).filter(Task.title.ilike(parent_task_name)).first()
        if not parent_task:
            await update.message.reply_text(f'❌ Родительская задача с названием "{parent_task_name}" не найдена.')
            return
        fastapi_url = 'http://localhost:8000/tasks'
        payload = {
            "title": subtask_title,
            "description": f'Добавлено как подзадача для "{parent_task_name}" через Telegram',
            "due_date": None,
            "parent_id": parent_task.id
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
async def delete_task_command(update: Update, context: CallbackContext):
    task_delete = " ".join(context.args)
    if not task_delete:
        await update.message.reply_text(
            "Пожалуйста, укажите название задачи для удаления. Пример: /deletetask Купить молоко"
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
@asynccontextmanager
async def lifespan(app):
 
    print("Приложение запускается, настраиваем бота...")

    bot_application.add_handler(CommandHandler("start", start))
    bot_application.add_handler(CommandHandler("tasks", show_tasks))
    bot_application.add_handler(CommandHandler("add_task", add_task))
    bot_application.add_handler(CommandHandler("delete_task", delete_task_command))
    bot_application.add_handler(CommandHandler("add_subtask", add_subtask))

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


@app.post('/tasks')
def create_task(task:TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(**task.dict())
    db_task.ai_comment = get_ai_comment(task.title)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return {'message': 'Task created', 'ai_advice':db_task.ai_comment, 'task': db_task}

@app.get('/tasks')
def get_tasks(db: Session = Depends(get_db)):
    return db.query(Task).all()

@app.delete('/tasks/{task_id}')
def delete_task(task_id, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
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
      print('tasks not found')
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
def update_task(task_id, task: TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail='Task not found')
    for field, value in task.dict().items():
        setattr(db_task, field, value)
    if task.title is not None and task.title !=db_task.title:
        db_task.ai_comment = get_ai_comment(task.title)
    db.commit()
    db.refresh(db_task)
    return {'message': f'Task updated {task_id}', 'task': db_task}
