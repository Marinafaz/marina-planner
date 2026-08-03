import streamlit as st
import datetime
import json
import requests
import os
from collections import defaultdict

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
if "data" not in st.session_state:
    st.session_state.data = load_data()
if "current_page" not in st.session_state:
    st.session_state.current_page = "Главная"
if "temp_text" not in st.session_state:
    st.session_state.temp_text = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "planning_mode" not in st.session_state:
    st.session_state.planning_mode = None  # "week" or "month"
if "daily_plan_dialog" not in st.session_state:
    st.session_state.daily_plan_dialog = []

# ------------------ ФУНКЦИИ ДЛЯ РАБОТЫ С ИИ ------------------
def call_deepseek(prompt, api_key):
    try:
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
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Ошибка: {response.status_code}"
    except Exception as e:
        return f"Ошибка: {str(e)}"

def generate_daily_plan_with_dialog(profile, weekly_plan, api_key):
    """Генерация плана на день с диалогом"""
    today = datetime.datetime.now().strftime("%A")
    prompt = f"""
    Ты — личный коуч Марины.
    Сегодня {today}.
    
    Вот её профиль:
    - Цели: {', '.join(profile['goals_5_years'])}
    - Привычки: {', '.join(profile['habits'])}
    - Идеальный день: {', '.join(profile['ideal_day'])}
    
    Вот план на неделю (если есть):
    {weekly_plan if weekly_plan else "План на неделю ещё не создан."}
    
    Составь план на сегодня:
    1. Учти задачи из плана недели на этот день.
    2. Добавь что-то из привычек (например, 5 минут зарядки).
    3. Напиши план в виде списка.
    
    После плана задай вопрос Марине:
    "Вот план на сегодня. Хочешь что-то добавить или скорректировать? Может, добавим 5 минут зарядки утром или разгрузку вечером? Что скажешь?"
    
    Отвечай на русском, тёпло, поддерживающе.
    """
    return call_deepseek(prompt, api_key)

def analyze_week_entries(entries, week_start, api_key):
    """Анализ записей за неделю с группировкой по целям"""
    if not entries:
        return "Нет записей за эту неделю."
    
    week_entries = []
    for e in entries:
        date_obj = datetime.datetime.strptime(e['date'], "%Y-%m-%d %H:%M:%S.%f")
        if week_start <= date_obj < week_start + datetime.timedelta(days=7):
            week_entries.append(e)
    
    if not week_entries:
        return "Нет записей за эту неделю."
    
    text = "\n".join([f"- {e['text']}" for e in week_entries])
    prompt = f"""
    Ты — коуч Марины.
    Вот её записи за неделю (с {week_start.strftime('%d.%m')} по {(week_start + datetime.timedelta(days=6)).strftime('%d.%m')}):
    {text}
    
    Сгруппируй их по категориям (спорт, семья, работа, забота о себе).
    Для каждой категории укажи, сколько записей и что именно она делала.
    Дай общую оценку прогресса.
    Напиши 2-3 мягкие рекомендации на следующую неделю.
    Отвечай на русском, тёпло, поддерживающе.
    """
    return call_deepseek(prompt, api_key)

# ------------------ АВТОРИЗАЦИЯ ------------------
if not st.session_state.authenticated:
    st.markdown("<h1 class='main-header'>🌿 Марина: Планер жизни</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Войди, чтобы продолжить</p>", unsafe_allow_html=True)
    
    password = st.text_input("Введите пароль", type="password")
    
    if st.button("Войти"):
        if password == st.secrets["PASSWORD"]:
            st.session_state.authenticated = True
            st.session_state.api_key = st.secrets["API_KEY"]
            st.rerun()
        else:
            st.error("❌ Неверный пароль.")
    st.stop()

# ------------------ ОСНОВНОЕ ПРИЛОЖЕНИЕ ------------------
st.markdown(f"<h1 class='main-header'>🌿 Здравствуй, {PROFILE['name']}!</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Ты — главный герой своей жизни ✨</p>", unsafe_allow_html=True)

# ----- ФОКУСЫ (на главной) -----
if st.session_state.data.get("weekly_plan"):
    # Извлекаем фокус из плана недели (первая строка)
    focus_week = st.session_state.data["weekly_plan"].split("\n")[0] if st.session_state.data["weekly_plan"] else "Спланируйте неделю"
else:
    focus_week = "❓ Спланируйте неделю, чтобы задать фокус"

if st.session_state.data.get("monthly_plan"):
    focus_month = st.session_state.data["monthly_plan"].split("\n")[0] if st.session_state.data["monthly_plan"] else "Спланируйте месяц"
else:
    focus_month = "❓ Спланируйте месяц, чтобы задать фокус"

st.markdown(f"<div class='focus-text'>🎯 Фокус недели: {focus_week}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='focus-text'>🎯 Фокус месяца: {focus_month}</div>", unsafe_allow_html=True)
st.divider()

# Меню
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🏠 Главная", use_container_width=True):
        st.session_state.current_page = "Главная"
with col2:
    if st.button("📝 Победы", use_container_width=True):
        st.session_state.current_page = "Победы"
with col3:
    if st.button("📊 Итоги", use_container_width=True):
        st.session_state.current_page = "Итоги"
with col4:
    if st.button("📋 Планы", use_container_width=True):
        st.session_state.current_page = "Планы"

st.divider()

# ------------------ СТРАНИЦЫ ------------------
page = st.session_state.current_page

if page == "Главная":
    st.markdown("### ☀️ План на сегодня")
    
    if st.button("✨ Создать план на сегодня"):
        with st.spinner("Генерирую план для тебя..."):
            weekly_plan = st.session_state.data.get("weekly_plan")
            plan = generate_daily_plan_with_dialog(PROFILE, weekly_plan, st.session_state.api_key)
            st.session_state.temp_text = plan
            st.session_state.daily_plan_dialog = [{"role": "assistant", "content": plan}]
    
    if st.session_state.daily_plan_dialog:
        # Отображаем диалог
        for msg in st.session_state.daily_plan_dialog:
            if msg["role"] == "user":
                st.markdown(f"<div class='chat-message chat-message-user'>👤 {msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-message'>🌿 {msg['content']}</div>", unsafe_allow_html=True)
        
        # Поле для ответа
        user_response = st.text_input("Ваш ответ:", key="daily_plan_input")
        if st.button("Отправить"):
            if user_response.strip():
                st.session_state.daily_plan_dialog.append({"role": "user", "content": user_response})
                # Отправляем ответ в ИИ
                prompt = f"""
                Ты — коуч Марины.
                Вот план на сегодня: {st.session_state.daily_plan_dialog[0]['content']}
                Марина ответила: {user_response}
                
                Отреагируй на её ответ. Если она хочет что-то добавить или изменить — предложи обновлённый план.
                Если она согласна — скажи это и предложи сохранить план.
                Отвечай на русском, тёпло, поддерживающе.
                """
                response = call_deepseek(prompt, st.session_state.api_key)
                st.session_state.daily_plan_dialog.append({"role": "assistant", "content": response})
                st.rerun()
        
        if st.button("💾 Сохранить план дня"):
            st.session_state.data["daily_plan"] = st.session_state.daily_plan_dialog[0]["content"]
            save_data(st.session_state.data)
            st.success("✅ План на сегодня сохранён!")

elif page == "Победы":
    st.markdown("### 🌙 Мои победы")
    
    # Добавление победы
    victory_text = st.text_area("Напиши свои победы (каждую с новой строки):", height=120)
    
    if st.button("➕ Добавить победы"):
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
    
    # Группировка побед по дням
    if st.session_state.data["entries"]:
        st.markdown("### 📖 Книга успехов")
        entries_by_day = defaultdict(list)
        for entry in st.session_state.data["entries"]:
            date_obj = datetime.datetime.strptime(entry['date'], "%Y-%m-%d %H:%M:%S.%f")
            day_key = date_obj.strftime("%Y-%m-%d")
            entries_by_day[day_key].append(entry)
        
        # Сортируем дни по убыванию
        for day_key in sorted(entries_by_day.keys(), reverse=True):
            date_obj = datetime.datetime.strptime(day_key, "%Y-%m-%d")
            day_name = date_obj.strftime("%A, %d %B")
            st.markdown(f"<div class='day-header'>📅 {day_name}</div>", unsafe_allow_html=True)
            for entry in entries_by_day[day_key]:
                st.markdown(f"<div class='win-entry'>• {entry['text']}</div>", unsafe_allow_html=True)
    else:
        st.info("Пока нет побед. Начни записывать свои достижения!")

elif page == "Итоги":
    st.markdown("### 📊 Анализ побед")
    
    # Выбор недели
    today = datetime.datetime.now()
    week_start = today - datetime.timedelta(days=today.weekday())
    
    # Список доступных недель
    weeks = []
    for i in range(4):
        week_start_i = week_start - datetime.timedelta(days=i*7)
        week_end_i = week_start_i + datetime.timedelta(days=6)
        weeks.append((week_start_i, f"{week_start_i.strftime('%d.%m')} - {week_end_i.strftime('%d.%m')}"))
    
    selected_week = st.selectbox("Выберите неделю:", [f"{w[0].strftime('%d.%m')} - {(w[0] + datetime.timedelta(days=6)).strftime('%d.%m')}" for w in weeks])
    
    # Находим выбранную неделю
    week_start_selected = None
    for ws, label in weeks:
        if label == selected_week:
            week_start_selected = ws
            break
    
    if week_start_selected and st.button("📊 Анализ недели"):
        with st.spinner("Анализирую..."):
            analysis = analyze_week_entries(
                st.session_state.data["entries"],
                week_start_selected,
                st.session_state.api_key
            )
            st.markdown(f"<div class='card'>{analysis}</div>", unsafe_allow_html=True)

elif page == "Планы":
    st.markdown("### 📋 Планирование")
    
    tab1, tab2 = st.tabs(["📅 Неделя", "📆 Месяц"])
    
    with tab1:
        st.markdown("#### План на неделю")
        
        if st.button("🗓️ Начать планирование недели"):
            st.session_state.planning_mode = "week"
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Привет, Марина! Давай спланируем твою неделю. Расскажи, какие у тебя ключевые задачи, встречи или события на этой неделе? Также скажи, что ты хочешь попробовать новое (например, добавить зарядку, выделить время для себя)."}
            ]
        
        if st.session_state.planning_mode == "week":
            # Отображение чата
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f"<div class='chat-message chat-message-user'>👤 {msg['content']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='chat-message'>🌿 {msg['content']}</div>", unsafe_allow_html=True)
            
            user_input = st.text_input("Ваше сообщение:", key="week_chat_input")
            if st.button("Отправить", key="week_send"):
                if user_input.strip():
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    
                    # Формируем запрос к ИИ
                    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history])
                    prompt = f"""
                    Ты — коуч Марины.
                    Вот диалог:
                    {history_text}
                    
                    Ответь Марине:
                    - Если она говорит о неудаче — сначала спроси, что помешало, почему не получилось.
                    - Если она говорит о планах — помоги структурировать их по дням недели.
                    - Если она согласна с планом — предложи сохранить его.
                    - Отвечай на русском, тёпло, поддерживающе.
                    """
                    response = call_deepseek(prompt, st.session_state.api_key)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    st.rerun()
            
            if st.button("💾 Сохранить план недели"):
                # Извлекаем план из последнего сообщения ассистента
                plan = "\n".join([m["content"] for m in st.session_state.chat_history if m["role"] == "assistant"])
                st.session_state.data["weekly_plan"] = plan
                save_data(st.session_state.data)
                st.success("✅ План недели сохранён!")
                st.session_state.planning_mode = None
    
    with tab2:
        st.markdown("#### План на месяц")
        
        if st.button("🗓️ Начать планирование месяца"):
            st.session_state.planning_mode = "month"
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Привет, Марина! Давай спланируем твой месяц. Расскажи, какие у тебя ключевые события, поездки или цели на этот месяц? Что ты хочешь успеть?"}
            ]
        
        if st.session_state.planning_mode == "month":
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f"<div class='chat-message chat-message-user'>👤 {msg['content']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='chat-message'>🌿 {msg['content']}</div>", unsafe_allow_html=True)
            
            user_input = st.text_input("Ваше сообщение:", key="month_chat_input")
            if st.button("Отправить", key="month_send"):
                if user_input.strip():
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    
                    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history])
                    prompt = f"""
                    Ты — коуч Марины.
                    Вот диалог:
                    {history_text}
                    
                    Ответь Марине:
                    - Помоги структурировать цели по неделям месяца.
                    - Если она говорит о неудаче — сначала спроси, что помешало.
                    - Отвечай на русском, тёпло, поддерживающе.
                    """
                    response = call_deepseek(prompt, st.session_state.api_key)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    st.rerun()
            
            if st.button("💾 Сохранить план месяца"):
                plan = "\n".join([m["content"] for m in st.session_state.chat_history if m["role"] == "assistant"])
                st.session_state.data["monthly_plan"] = plan
                save_data(st.session_state.data)
                st.success("✅ План месяца сохранён!")
                st.session_state.planning_mode = None

# ------------------ ФУТЕР ------------------
st.markdown(f"""
<div class='footer'>
    🌿 Марина: Планер жизни — создано с любовью для тебя<br>
    <small>Все данные хранятся в файле на сервере.</small>
</div>
""", unsafe_allow_html=True)
