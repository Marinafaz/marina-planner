import streamlit as st
import datetime
import json
import requests
import os
import re
import time
from collections import defaultdict
import base64
from datetime import datetime as dt
import plotly.express as px
import pandas as pd

# ------------------ НАСТРОЙКИ СТРАНИЦЫ ------------------
st.set_page_config(
    page_title="Марина: Планер жизни",
    page_icon="🌿",
    layout="wide"
)

# ------------------ ФАЙЛ ДЛЯ СОХРАНЕНИЯ ДАННЫХ ------------------
DATA_FILE = "marina_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"entries": [], "weekly_plan": None, "monthly_plan": None, "daily_plan": None}
    return {"entries": [], "weekly_plan": None, "monthly_plan": None, "daily_plan": None}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

# ------------------ СТИЛИ ------------------
st.markdown("""
<style>
    .stApp { background: #F7F3E8; }
    .main-header {
        color: #2D4A3E;
        font-family: 'Georgia', serif;
        font-size: 2.5rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #4A6B5A;
        font-family: 'Georgia', serif;
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 2rem;
        font-style: italic;
    }
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
        border-left: 5px solid #7BAF8A;
    }
    .day-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2D4A3E;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
        border-bottom: 2px solid #DDE8E0;
        padding-bottom: 0.3rem;
    }
    .win-entry {
        padding: 0.3rem 0 0.3rem 1.5rem;
        margin-bottom: 0.2rem;
        color: #3A5A4A;
    }
    .focus-text {
        font-size: 1.3rem;
        color: #2D4A3E;
        background: #E8F0EA;
        padding: 0.8rem 1.5rem;
        border-radius: 30px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .footer {
        text-align: center;
        color: #8BA89A;
        font-size: 0.8rem;
        margin-top: 3rem;
        border-top: 1px solid #DDE8E0;
        padding-top: 1rem;
    }
    .chat-message {
        background: white;
        padding: 1rem;
        border-radius: 15px;
        margin-bottom: 0.8rem;
        border-left: 4px solid #7BAF8A;
    }
    .chat-message-user {
        background: #E8F0EA;
        border-left: 4px solid #4A6B5A;
    }
    .voice-btn {
        background: #7BAF8A;
        color: white;
        border: none;
        padding: 0.3rem 1rem;
        border-radius: 30px;
        font-size: 1.2rem;
        cursor: pointer;
        margin-left: 0.5rem;
    }
    .voice-btn:hover {
        background: #5E8F6E;
    }
    .backup-card {
        background: #E8F0EA;
        padding: 1rem;
        border-radius: 15px;
        border: 1px dashed #7BAF8A;
        margin-top: 1rem;
    }
    .thought-input {
        background: #FFF8F0;
        border-radius: 15px;
        padding: 1rem;
        border-left: 5px solid #D4A373;
    }
    .checklist-item {
        background: white;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        margin-bottom: 0.3rem;
        border-left: 3px solid #7BAF8A;
    }
</style>
""", unsafe_allow_html=True)

# ------------------ ПРОФИЛЬ ------------------
PROFILE = {
    "name": "Марина",
    "goals_5_years": [
        "Сместить фокус с окружающих на себя — стать главным героем своей жизни",
        "Восстановить здоровье и физическую форму",
        "Найти/создать вдохновляющие проекты, от которых кайфовать",
        "Выстроить вдохновляющие отношения с детьми и семьёй"
    ],
    "habits": [
        "ежедневный спорт (от 5 мин до 1-2 ч)",
        "утренняя настройка на себя",
        "вечерний ритуал подведения итогов",
        "жизнь по расписанию"
    ],
    "work_days": ["вторник", "среда", "четверг"],
    "ideal_day": [
        "ранний подъём",
        "прогулка/зарядка/пробежка",
        "настройка дня + маятник (30-40 мин)",
        "завтрак с семьёй",
        "проводить детей",
        "активная прогулка с Алексом",
        "обед",
        "дневной сон Алекса → рабочий блок 2 часа",
        "домашние дела с Алексом",
        "спорт/уход за собой",
        "вечерний семейный ужин",
        "20:30-21:00 — подготовка ко сну"
    ]
}

# ------------------ ИНИЦИАЛИЗАЦИЯ ------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "api_key_verified" not in st.session_state:
    st.session_state.api_key_verified = False
if "data" not in st.session_state:
    st.session_state.data = load_data()
if "current_page" not in st.session_state:
    st.session_state.current_page = "Главная"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "planning_mode" not in st.session_state:
    st.session_state.planning_mode = None
if "daily_plan_dialog" not in st.session_state:
    st.session_state.daily_plan_dialog = []
if "editing_entry" not in st.session_state:
    st.session_state.editing_entry = None
if "thoughts" not in st.session_state:
    st.session_state.thoughts = ""
if "daily_plan_generated" not in st.session_state:
    if st.session_state.data.get("daily_plan"):
        st.session_state.daily_plan_generated = True
    else:
        st.session_state.daily_plan_generated = False
if "week_planning_active" not in st.session_state:
    st.session_state.week_planning_active = False
if "month_planning_active" not in st.session_state:
    st.session_state.month_planning_active = False
if "checklist_completed" not in st.session_state:
    st.session_state.checklist_completed = []
if "evening_checklist_active" not in st.session_state:
    st.session_state.evening_checklist_active = False

# ------------------ ФУНКЦИИ ДЛЯ РАБОТЫ С ИИ ------------------
def call_deepseek(prompt, api_key, retries=2):
    url = "https://api.polza.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    for attempt in range(retries + 1):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=120)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                if attempt < retries:
                    time.sleep(2)
                    continue
                return f"Ошибка: {response.status_code}"
        except requests.exceptions.Timeout:
            if attempt < retries:
                time.sleep(3)
                continue
            return "Ошибка: Сервер не отвечает (таймаут 120 сек). Попробуй позже."
        except Exception as e:
            if attempt < retries:
                time.sleep(2)
                continue
            return f"Ошибка: {str(e)}"
    return "Ошибка: Не удалось получить ответ после нескольких попыток."

def generate_daily_plan_from_thoughts(thoughts, profile, api_key):
    weekly_plan = st.session_state.data.get("weekly_plan")
    weekly_context = f"План на неделю: {weekly_plan}" if weekly_plan else "План на неделю не создан."
    
    prompt = f"""
    Ты — личный коуч Марины.
    Вот её профиль:
    - Цели на 5 лет: {', '.join(profile['goals_5_years'])}
    - Привычки: {', '.join(profile['habits'])}
    - Идеальный день: {', '.join(profile['ideal_day'])}
    
    {weekly_context}
    
    Марина написала свои мысли на сегодня:
    "{thoughts}"
    
    Задача:
    1. Проанализируй её мысли.
    2. Сопоставь с её целями и привычками.
    3. Составь структурированный план на сегодня в виде списка (используй маркеры • или -).
    4. После плана задай вопрос: "Марина, я составила такой план. Что хочешь добавить, убрать или изменить?"
    
    Отвечай на русском, тёпло, поддерживающе.
    """
    return call_deepseek(prompt, api_key)

def refine_daily_plan(plan, user_feedback, profile, api_key):
    prompt = f"""
    Ты — личный коуч Марины.
    Вот её профиль:
    - Цели: {', '.join(profile['goals_5_years'])}
    - Привычки: {', '.join(profile['habits'])}
    
    Ты составила такой план:
    {plan}
    
    Марина ответила:
    "{user_feedback}"
    
    Задача:
    1. Учти её замечания.
    2. Обнови план в виде списка.
    3. Спроси, всё ли теперь устраивает.
    
    Отвечай на русском, тёпло, поддерживающе.
    """
    return call_deepseek(prompt, api_key)

def get_ai_response_for_planning(chat_history, profile, api_key, planning_type):
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history])
    
    if planning_type == "week":
        prompt = f"""
        Ты — личный коуч Марины.
        Вот её профиль:
        - Цели на 5 лет: {', '.join(profile['goals_5_years'])}
        - Привычки: {', '.join(profile['habits'])}
        
        Вот диалог:
        {history_text}
        
        Ответь Марине:
        - Если она пишет задачи — помоги структурировать их по дням недели.
        - Если она говорит о неудаче — сначала спроси, что помешало, почему не получилось.
        - Если она согласна с планом — предложи сохранить его.
        - Отвечай на русском, тёпло, поддерживающе.
        """
    else:
        prompt = f"""
        Ты — личный коуч Марины.
        Вот её профиль:
        - Цели на 5 лет: {', '.join(profile['goals_5_years'])}
        - Привычки: {', '.join(profile['habits'])}
        
        Вот диалог:
        {history_text}
        
        Ответь Марине:
        - Помоги структурировать цели по неделям месяца.
        - Если она говорит о неудаче — сначала спроси, что помешало.
        - Отвечай на русском, тёпло, поддерживающе.
        """
    return call_deepseek(prompt, api_key)

def analyze_week_with_plots(entries, week_start, api_key):
    """Анализ недели с графиками"""
    week_entries = []
    for e in entries:
        date_obj = datetime.datetime.strptime(e['date'], "%Y-%m-%d %H:%M:%S.%f")
        if week_start <= date_obj < week_start + datetime.timedelta(days=7):
            week_entries.append(e)
    
    if not week_entries:
        return None, None, "Нет записей за эту неделю."
    
    # Подготовка данных для графиков
    df = pd.DataFrame([{
        'date': datetime.datetime.strptime(e['date'], "%Y-%m-%d %H:%M:%S.%f").date(),
        'text': e['text']
    } for e in week_entries])
    
    # График по дням
    daily_counts = df.groupby('date').size().reset_index(name='count')
    fig1 = px.bar(daily_counts, x='date', y='count', title='Количество побед по дням')
    
    # Категории
    categories = {'спорт': 0, 'семья': 0, 'работа': 0, 'забота о себе': 0}
    for e in week_entries:
        text_lower = e['text'].lower()
        for cat in categories:
            if cat in text_lower:
                categories[cat] += 1
    
    df_cat = pd.DataFrame([{'Категория': k, 'Количество': v} for k, v in categories.items() if v > 0])
    fig2 = px.pie(df_cat, values='Количество', names='Категория', title='Распределение побед по категориям')
    
    # Анализ от ИИ
    text = "\n".join([f"- {e['text']}" for e in week_entries])
    prompt = f"""
    Сгруппируй победы по целям (спорт, семья, работа, забота о себе).
    Записи: {text}
    Дай итог и 2-3 мягкие рекомендации.
    """
    analysis = call_deepseek(prompt, api_key)
    
    return fig1, fig2, analysis

# ------------------ АВТОРИЗАЦИЯ (с запоминанием ключа) ------------------
st.markdown("""
<script>
    function loadCredentials() {
        const pwd = localStorage.getItem('marina_password');
        const key = localStorage.getItem('marina_api_key');
        if (pwd) {
            const input = window.parent.document.querySelector('input[type="password"]');
            if (input) input.value = pwd;
        }
        if (key) {
            const input = window.parent.document.querySelector('input[type="password"][key="api_key_input"]');
            if (input) input.value = key;
        }
    }
    setTimeout(loadCredentials, 1000);
</script>
""", unsafe_allow_html=True)

if not st.session_state.authenticated:
    st.markdown("<h1 class='main-header'>🌿 Марина: Планер жизни</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Войди, чтобы продолжить</p>", unsafe_allow_html=True)
    
    password = st.text_input("Введите пароль", type="password", key="login_password")
    remember_pass = st.checkbox("Запомнить пароль", key="remember_pass")
    
    if st.button("Войти"):
        if password == "botiamhappy":
            st.session_state.authenticated = True
            if remember_pass:
                st.markdown(f"""
                <script>
                    localStorage.setItem('marina_password', '{password}');
                </script>
                """, unsafe_allow_html=True)
            st.rerun()
        else:
            st.error("❌ Неверный пароль.")
    st.stop()

if st.session_state.authenticated and not st.session_state.api_key_verified:
    st.markdown("<h1 class='main-header'>🌿 Марина: Планер жизни</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Введите API-ключ Polza.ai</p>", unsafe_allow_html=True)
    
    api_key_input = st.text_input("Введите API-ключ:", type="password", key="api_key_input")
    remember_key = st.checkbox("Запомнить ключ в браузере", key="remember_key")
    
    if st.button("Подтвердить ключ"):
        if api_key_input.startswith("pza_"):
            try:
                url = "https://api.polza.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key_input}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": "deepseek-v4-pro",
                    "messages": [{"role": "user", "content": "Привет"}],
                    "temperature": 0.7
                }
                response = requests.post(url, headers=headers, json=data, timeout=30)
                if response.status_code == 200:
                    st.session_state.api_key = api_key_input
                    st.session_state.api_key_verified = True
                    if remember_key:
                        st.markdown(f"""
                        <script>
                            localStorage.setItem('marina_api_key', '{api_key_input}');
                        </script>
                        """, unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.error(f"❌ API-ключ неверный. Статус: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Ошибка: {str(e)}")
        else:
            st.error("❌ Неверный формат ключа. Он должен начинаться с 'pza_'.")
    st.stop()

# ------------------ ОСНОВНОЕ ПРИЛОЖЕНИЕ ------------------
st.markdown(f"<h1 class='main-header'>🌿 Здравствуй, {PROFILE['name']}!</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Ты — главный герой своей жизни ✨</p>", unsafe_allow_html=True)

# Фокусы
focus_week = "❓ Спланируйте неделю, чтобы задать фокус"
focus_month = "❓ Спланируйте месяц, чтобы задать фокус"
if st.session_state.data.get("weekly_plan"):
    focus_week = st.session_state.data["weekly_plan"].split("\n")[0][:60] + "..." if len(st.session_state.data["weekly_plan"]) > 60 else st.session_state.data["weekly_plan"].split("\n")[0]
if st.session_state.data.get("monthly_plan"):
    focus_month = st.session_state.data["monthly_plan"].split("\n")[0][:60] + "..." if len(st.session_state.data["monthly_plan"]) > 60 else st.session_state.data["monthly_plan"].split("\n")[0]

st.markdown(f"<div class='focus-text'>🎯 Фокус недели: {focus_week}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='focus-text'>🎯 Фокус месяца: {focus_month}</div>", unsafe_allow_html=True)
st.divider()

# Меню
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("🏠 Главная", use_container_width=True):
        st.session_state.current_page = "Главная"
        st.session_state.daily_plan_generated = False
with col2:
    if st.button("📝 Победы", use_container_width=True):
        st.session_state.current_page = "Победы"
with col3:
    if st.button("📊 Итоги", use_container_width=True):
        st.session_state.current_page = "Итоги"
with col4:
    if st.button("📋 Планы", use_container_width=True):
        st.session_state.current_page = "Планы"
        st.session_state.week_planning_active = False
        st.session_state.month_planning_active = False
with col5:
    if st.button("🎯 Цели", use_container_width=True):
        st.session_state.current_page = "Цели"

st.divider()

# ------------------ СТРАНИЦЫ ------------------
page = st.session_state.current_page

if page == "Главная":
    st.markdown("### ☀️ Мой план на сегодня")
    
    # Показываем сохранённый план, если есть
    if st.session_state.data.get("daily_plan") and not st.session_state.daily_plan_generated:
        st.markdown("### 📋 Сохранённый план на сегодня")
        plan_text = st.session_state.data["daily_plan"]
        lines = plan_text.split("\n")
        for line in lines:
            if line.strip():
                if line.strip().startswith(("-", "•", "—")):
                    st.markdown(f"<div class='win-entry'>{line.strip()}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='win-entry'>• {line.strip()}</div>", unsafe_allow_html=True)
        
        # Кнопка для вечернего чек-листа
        if st.button("🌙 Вечерний чек-лист (отметить, что сделано)"):
            st.session_state.evening_checklist_active = True
            st.session_state.checklist_completed = []
            st.rerun()
    
    # Чек-лист выполнения плана
    if st.session_state.evening_checklist_active and st.session_state.data.get("daily_plan"):
        st.markdown("### 📋 Что ты сделала из плана?")
        plan_text = st.session_state.data["daily_plan"]
        lines = [line.strip() for line in plan_text.split("\n") if line.strip() and not line.strip().startswith(("Марина", "Что хочешь"))]
        
        for idx, line in enumerate(lines[:10]):
            if line.startswith(("-", "•", "—")):
                line = line[1:].strip()
            if line:
                checked = st.checkbox(line, key=f"check_{idx}")
                if checked and line not in st.session_state.checklist_completed:
                    st.session_state.checklist_completed.append(line)
        
        if st.button("✅ Сохранить выполненные задачи как победы"):
            if st.session_state.checklist_completed:
                for task in st.session_state.checklist_completed:
                    st.session_state.data["entries"].append({
                        "date": str(datetime.datetime.now()),
                        "text": f"✅ {task}"
                    })
                save_data(st.session_state.data)
                st.success(f"✅ Добавлено {len(st.session_state.checklist_completed)} побед!")
                st.session_state.evening_checklist_active = False
                st.session_state.checklist_completed = []
                st.rerun()
            else:
                st.warning("Отметь хотя бы одну выполненную задачу.")
    
    # Генерация плана из мыслей
    if not st.session_state.daily_plan_generated:
        st.markdown("<div class='thought-input'>", unsafe_allow_html=True)
        st.markdown("#### 📌 Что сегодня важно?")
        st.markdown("*Напиши самое главное, что нужно сделать. Я помогу разложить это по времени и добавить заботу о себе.*")
        
        thoughts = st.text_area("Мои задачи на сегодня:", height=150, key="thoughts_input")
        st.session_state.thoughts = thoughts
        
        if st.button("🧠 Собрать план из моих мыслей"):
            if st.session_state.thoughts.strip():
                with st.spinner("Анализирую твои мысли, Марина... (может занять до 2 минут)"):
                    plan = generate_daily_plan_from_thoughts(
                        st.session_state.thoughts,
                        PROFILE,
                        st.session_state.api_key
                    )
                    st.session_state.daily_plan_dialog = [{"role": "assistant", "content": plan}]
                    st.session_state.daily_plan_generated = True
                    st.rerun()
            else:
                st.warning("Напиши свои задачи, чтобы я могла составить план.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Диалог с правками плана
    if st.session_state.daily_plan_generated and st.session_state.daily_plan_dialog:
        st.markdown("### 📋 Предлагаемый план")
        
        for msg in st.session_state.daily_plan_dialog:
            if msg["role"] == "user":
                st.markdown(f"<div class='chat-message chat-message-user'>👤 {msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-message'>🌿 {msg['content']}</div>", unsafe_allow_html=True)
        
        user_feedback = st.text_input("Твой ответ (добавить/убрать/изменить):", key="daily_feedback")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📩 Отправить правки"):
                if user_feedback.strip():
                    with st.spinner("Обновляю план..."):
                        plan_text = st.session_state.daily_plan_dialog[0]["content"]
                        refined = refine_daily_plan(
                            plan_text,
                            user_feedback,
                            PROFILE,
                            st.session_state.api_key
                        )
                        st.session_state.daily_plan_dialog.append({"role": "user", "content": user_feedback})
                        st.session_state.daily_plan_dialog.append({"role": "assistant", "content": refined})
                        st.rerun()
                else:
                    st.warning("Напиши, что хочешь изменить.")
        with col2:
            if st.button("💾 Сохранить план дня"):
                if st.session_state.daily_plan_dialog:
                    for msg in reversed(st.session_state.daily_plan_dialog):
                        if msg["role"] == "assistant" and ("план" in msg["content"].lower() or "составила" in msg["content"].lower()):
                            st.session_state.data["daily_plan"] = msg["content"]
                            save_data(st.session_state.data)
                            st.success("✅ План на сегодня сохранён!")
                            break
    
    st.divider()
    st.markdown("### 📦 Управление данными")
    with st.container():
        st.markdown("<div class='backup-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Скачать резервную копию", use_container_width=True):
                json_str = json.dumps(st.session_state.data, ensure_ascii=False, indent=2, default=str)
                b64 = base64.b64encode(json_str.encode()).decode()
                filename = f"marina_backup_{dt.now().strftime('%Y-%m-%d')}.json"
                href = f'<a href="data:application/json;base64,{b64}" download="{filename}" style="text-decoration:none;background:#7BAF8A;color:white;padding:0.5rem 1rem;border-radius:30px;display:inline-block;">📥 Скачать</a>'
                st.markdown(href, unsafe_allow_html=True)
        with col2:
            uploaded_file = st.file_uploader("📂 Восстановить из бэкапа", type=["json"], label_visibility="collapsed")
            if uploaded_file is not None:
                try:
                    backup_data = json.load(uploaded_file)
                    if st.button("⚠️ Восстановить данные (заменит текущие)"):
                        st.session_state.data = backup_data
                        save_data(st.session_state.data)
                        st.success("✅ Данные восстановлены!")
                        st.rerun()
                except:
                    st.error("❌ Неверный формат файла")
        st.markdown("</div>", unsafe_allow_html=True)

elif page == "Победы":
    st.markdown("### 🌙 Мои победы")
    
    victory_text = st.text_area("Напиши победу (каждую с новой строки):", height=120, key="victory_input")
    
    col_voice2, col_save = st.columns([1, 4])
    with col_voice2:
        st.markdown("""
        <button class="voice-btn" onclick="startVoiceInput('victory_input')">🎤</button>
        <script>
            function startVoiceInput(fieldId) {
                const input = window.parent.document.querySelector(`textarea[key="${fieldId}"]`);
                if (!input) return;
                const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                recognition.lang = 'ru-RU';
                recognition.continuous = true;
                recognition.onresult = function(event) {
                    let final = '';
                    for (let i = event.resultIndex; i < event.results.length; i++) {
                        if (event.results[i].isFinal) {
                            final += event.results[i][0].transcript + '\\n';
                        }
                    }
                    if (final) {
                        input.value += final;
                        const event = new Event('input', { bubbles: true });
                        input.dispatchEvent(event);
                    }
                };
                recognition.start();
            }
        </script>
        """, unsafe_allow_html=True)
    with col_save:
        if st.button("➕ Добавить победы", use_container_width=True):
            if victory_text.strip():
                lines = victory_text.strip().split("\n")
                for line in lines:
                    if line.strip():
                        new_entry = {
                            "date": str(datetime.datetime.now()),
                            "text": line.strip()
                        }
                        st.session_state.data["entries"].append(new_entry)
                save_data(st.session_state.data)
                st.success(f"✅ Добавлено {len(lines)} побед!")
                st.rerun()
            else:
                st.warning("Напиши хотя бы одну победу!")
    
    st.divider()
    
    if st.session_state.data["entries"]:
        st.markdown("### 📖 Книга успехов")
        entries_by_day = defaultdict(list)
        for entry in st.session_state.data["entries"]:
            date_obj = datetime.datetime.strptime(entry['date'], "%Y-%m-%d %H:%M:%S.%f")
            day_key = date_obj.strftime("%Y-%m-%d")
            entries_by_day[day_key].append(entry)
        
        for day_key in sorted(entries_by_day.keys(), reverse=True):
            date_obj = datetime.datetime.strptime(day_key, "%Y-%m-%d")
            day_name = date_obj.strftime("%A, %d %B")
            st.markdown(f"<div class='day-header'>📅 {day_name}</div>", unsafe_allow_html=True)
            for idx, entry in enumerate(entries_by_day[day_key]):
                col1, col2, col3, col4 = st.columns([6, 1, 1, 1])
                with col1:
                    st.markdown(f"<div class='win-entry'>• {entry['text']}</div>", unsafe_allow_html=True)
                with col2:
                    if st.button("✏️", key=f"edit_{entry['date']}_{idx}"):
                        st.session_state.editing_entry = entry
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"del_{entry['date']}_{idx}"):
                        st.session_state.data["entries"].remove(entry)
                        save_data(st.session_state.data)
                        st.rerun()
                with col4:
                    if st.session_state.editing_entry and st.session_state.editing_entry['date'] == entry['date']:
                        new_text = st.text_input("Новый текст:", entry['text'], key=f"edit_text_{idx}")
                        if st.button("Сохранить", key=f"save_edit_{idx}"):
                            entry['text'] = new_text
                            save_data(st.session_state.data)
                            st.session_state.editing_entry = None
                            st.rerun()
    else:
        st.info("Пока нет побед. Начни записывать свои достижения!")

elif page == "Итоги":
    st.markdown("### 📊 Анализ побед")
    
    today = datetime.datetime.now()
    week_start = today - datetime.timedelta(days=today.weekday())
    
    weeks = []
    for i in range(4):
        week_start_i = week_start - datetime.timedelta(days=i*7)
        weeks.append((week_start_i, f"{week_start_i.strftime('%d.%m')} - {(week_start_i + datetime.timedelta(days=6)).strftime('%d.%m')}"))
    
    selected_week = st.selectbox("Выберите неделю:", [label for _, label in weeks])
    
    week_start_selected = None
    for ws, label in weeks:
        if label == selected_week:
            week_start_selected = ws
            break
    
    if week_start_selected and st.button("📊 Анализ недели"):
        with st.spinner("Анализирую..."):
            fig1, fig2, analysis = analyze_week_with_plots(
                st.session_state.data["entries"],
                week_start_selected,
                st.session_state.api_key
            )
            if analysis.startswith("Нет записей"):
                st.info(analysis)
            else:
                st.plotly_chart(fig1, use_container_width=True)
                st.plotly_chart(fig2, use_container_width=True)
                st.markdown(f"<div class='card'>{analysis}</div>", unsafe_allow_html=True)

elif page == "Планы":
    st.markdown("### 📋 Планирование")
    
    tab1, tab2 = st.tabs(["📅 Неделя", "📆 Месяц"])
    
    with tab1:
        st.markdown("#### План на неделю")
        
        if not st.session_state.week_planning_active:
            if st.button("🗓️ Начать планирование недели"):
                st.session_state.week_planning_active = True
                st.session_state.chat_history = [
                    {"role": "assistant", "content": "Привет, Марина! Давай спланируем твою неделю. Расскажи, какие у тебя ключевые задачи, встречи или события на этой неделе? Также скажи, что ты хочешь попробовать новое (например, добавить зарядку, выделить время для себя)."}
                ]
                st.rerun()
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f"<div class='chat-message chat-message-user'>👤 {msg['content']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='chat-message'>🌿 {msg['content']}</div>", unsafe_allow_html=True)
            
            user_input = st.text_input("Ваше сообщение:", key="week_chat_input")
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("📩 Отправить", key="week_send"):
                    if user_input.strip():
                        st.session_state.chat_history.append({"role": "user", "content": user_input})
                        with st.spinner("Думаю..."):
                            response = get_ai_response_for_planning(
                                st.session_state.chat_history,
                                PROFILE,
                                st.session_state.api_key,
                                "week"
                            )
                            st.session_state.chat_history.append({"role": "assistant", "content": response})
                            st.rerun()
                    else:
                        st.warning("Напиши сообщение!")
            with col2:
                if st.button("💾 Сохранить план недели"):
                    plan = "\n".join([m["content"] for m in st.session_state.chat_history if m["role"] == "assistant"])
                    st.session_state.data["weekly_plan"] = plan
                    save_data(st.session_state.data)
                    st.success("✅ План недели сохранён!")
                    st.session_state.week_planning_active = False
                    st.rerun()
    
    with tab2:
        st.markdown("#### План на месяц")
        
        if not st.session_state.month_planning_active:
            if st.button("🗓️ Начать планирование месяца"):
                st.session_state.month_planning_active = True
                st.session_state.chat_history = [
                    {"role": "assistant", "content": "Привет, Марина! Давай спланируем твой месяц. Расскажи, какие у тебя ключевые события, поездки или цели на этот месяц? Что ты хочешь успеть?"}
                ]
                st.rerun()
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f"<div class='chat-message chat-message-user'>👤 {msg['content']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='chat-message'>🌿 {msg['content']}</div>", unsafe_allow_html=True)
            
            user_input = st.text_input("Ваше сообщение:", key="month_chat_input")
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("📩 Отправить", key="month_send"):
                    if user_input.strip():
                        st.session_state.chat_history.append({"role": "user", "content": user_input})
                        with st.spinner("Думаю..."):
                            response = get_ai_response_for_planning(
                                st.session_state.chat_history,
                                PROFILE,
                                st.session_state.api_key,
                                "month"
                            )
                            st.session_state.chat_history.append({"role": "assistant", "content": response})
                            st.rerun()
                    else:
                        st.warning("Напиши сообщение!")
            with col2:
                if st.button("💾 Сохранить план месяца"):
                    plan = "\n".join([m["content"] for m in st.session_state.chat_history if m["role"] == "assistant"])
                    st.session_state.data["monthly_plan"] = plan
                    save_data(st.session_state.data)
                    st.success("✅ План месяца сохранён!")
                    st.session_state.month_planning_active = False
                    st.rerun()

elif page == "Цели":
    st.markdown("### 🎯 Мои цели")
    
    with st.container():
        st.markdown("#### 📌 Цели на 5 лет")
        for goal in PROFILE['goals_5_years']:
            st.markdown(f"- {goal}")
        
        st.markdown("#### 📌 Привычки")
        for habit in PROFILE['habits']:
            st.markdown(f"- {habit}")
        
        st.markdown("#### 📌 Рабочие дни")
        st.markdown(f"- {', '.join(PROFILE['work_days'])}")

# ------------------ ФУТЕР ------------------
st.markdown("""
<div class='footer'>
    🌿 Марина: Планер жизни — создано с любовью для тебя<br>
    <small>Все данные сохраняются на сервере. Регулярно скачивайте резервную копию.</small>
</div>
""", unsafe_allow_html=True)
