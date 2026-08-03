import streamlit as st
import datetime
import json
import re
import requests
from collections import defaultdict
import os

# ------------------ НАСТРОЙКИ СТРАНИЦЫ ------------------
st.set_page_config(
    page_title="Марина: Планер жизни",
    page_icon="🌿",
    layout="wide"
)

# ------------------ ФАЙЛ ДЛЯ СОХРАНЕНИЯ ДАННЫХ ------------------
DATA_FILE = "marina_data.json"

def load_data():
    """Загружает данные из файла"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_data(entries):
    """Сохраняет данные в файл"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2, default=str)

# ------------------ СТИЛИ ------------------
st.markdown("""
<style>
    .stApp {
        background: #F7F3E8;
    }
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
    .green-button {
        background-color: #7BAF8A;
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 30px;
        font-weight: bold;
        cursor: pointer;
        width: 100%;
    }
    .green-button:hover {
        background-color: #5E8F6E;
    }
    .footer {
        text-align: center;
        color: #8BA89A;
        font-size: 0.8rem;
        margin-top: 3rem;
        border-top: 1px solid #DDE8E0;
        padding-top: 1rem;
    }
    .win-entry {
        background: #F0F7F2;
        padding: 0.8rem;
        border-radius: 12px;
        margin-bottom: 0.5rem;
        border-left: 4px solid #7BAF8A;
    }
</style>
""", unsafe_allow_html=True)

# ------------------ ПРОФИЛЬ (ТВОЙ) ------------------
PROFILE = {
    "name": "Марина",
    "family": {
        "husband": "Султан",
        "children": [
            {"name": "София", "age": 13},
            {"name": "Лена", "age": 8},
            {"name": "Алекс", "age": 2}
        ]
    },
    "goals_5_years": [
        "Сместить фокус с окружающих на себя — стать главным героем своей жизни",
        "Восстановить здоровье и физическую форму",
        "Найти/создать вдохновляющие проекты, от которых кайфовать",
        "Выстроить вдохновляющие отношения с детьми и семьёй"
    ],
    "goals_this_year": "Те же цели, но в мелком масштабе — начать двигаться",
    "work_days": ["вторник", "среда", "четверг"],
    "work_hours": 2,
    "best_time": "первая половина дня",
    "needs_before_work": "прогулка 30-60 мин + настройка",
    "unavailable_time": "17:00-21:00",
    "habits": [
        "ежедневный спорт (от 5 мин до 1-2 ч)",
        "утренняя настройка на себя",
        "вечерний ритуал подведения итогов",
        "жизнь по расписанию"
    ],
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
    ],
    "main_pain": "Нет вечернего ритуала и обесценивание своих действий"
}

# ------------------ ИНИЦИАЛИЗАЦИЯ ------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "entries" not in st.session_state:
    st.session_state.entries = load_data()
if "current_page" not in st.session_state:
    st.session_state.current_page = "Главная"
if "profile" not in st.session_state:
    st.session_state.profile = PROFILE.copy()
if "temp_text" not in st.session_state:
    st.session_state.temp_text = ""

# ------------------ ФУНКЦИИ ------------------
def call_deepseek(prompt, api_key):
    """Вызов DeepSeek через Polza.ai"""
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

def analyze_entries(entries, profile, api_key):
    """Анализ записей с помощью ИИ"""
    if not entries:
        return "Нет записей для анализа."
    
    text = "\n".join([f"- {e['text']}" for e in entries[-30:]])
    prompt = f"""
    Ты — поддерживающий коуч для Марины.
    Её цели: {', '.join(profile['goals_5_years'])}
    Её привычки: {', '.join(profile['habits'])}
    
    Вот её записи за последнее время:
    {text}
    
    Проанализируй:
    1. Какие категории чаще всего встречаются (спорт, семья, работа, забота о себе)?
    2. Какие успехи она уже достигла?
    3. Что можно улучшить?
    4. Какой у неё прогресс к целям?
    5. Дай 2-3 тёплые рекомендации на следующую неделю.
    
    Отвечай на русском, коротко, поддерживающим тоном.
    """
    return call_deepseek(prompt, api_key)

def generate_morning_plan(profile, api_key):
    """Генерация плана на день"""
    today = datetime.datetime.now().strftime("%A, %d %B")
    prompt = f"""
    Ты — личный коуч Марины.
    Сегодня {today}.
    Её идеальный день: {', '.join(profile['ideal_day'])}.
    Рабочие дни: {', '.join(profile['work_days'])}.
    
    Составь для неё мягкий план на сегодня с учётом:
    - прогулки с Алексом
    - рабочего блока (если сегодня рабочий день)
    - времени на себя
    - подготовки ко сну
    
    Напиши в поддерживающем, тёплом тоне. Добавь одну цитату или вдохновляющую фразу.
    """
    return call_deepseek(prompt, api_key)

def generate_weekly_summary(entries, profile, api_key):
    """Еженедельный итог"""
    week_entries = [e for e in entries if (datetime.datetime.now() - datetime.datetime.strptime(e['date'], "%Y-%m-%d %H:%M:%S.%f")).days < 7]
    if not week_entries:
        return "За эту неделю нет записей."
    
    text = "\n".join([f"- {e['text']}" for e in week_entries])
    prompt = f"""
    Ты — коуч Марины.
    Вот её записи за эту неделю:
    {text}
    
    Составь итог недели:
    1. Что получилось лучше всего?
    2. Что можно улучшить?
    3. 3 главные победы.
    4. План на следующую неделю (3 задачи).
    
    Отвечай тёпло, поддерживающе.
    """
    return call_deepseek(prompt, api_key)

def generate_monthly_summary(entries, profile, api_key):
    """Ежемесячный итог"""
    month_entries = [e for e in entries if datetime.datetime.strptime(e['date'], "%Y-%m-%d %H:%M:%S.%f").month == datetime.datetime.now().month]
    if not month_entries:
        return "За этот месяц нет записей."
    
    text = "\n".join([f"- {e['text']}" for e in month_entries])
    prompt = f"""
    Ты — коуч Марины.
    Вот её записи за этот месяц:
    {text}
    
    Составь глубокий итог месяца:
    1. Категории и частотность (спорт, семья, работа, забота о себе).
    2. Прогресс по целям Марины: {', '.join(profile['goals_5_years'])}
    3. Что сработало, что дало ресурс?
    4. Что можно скорректировать?
    5. План на следующий месяц (3-5 целей).
    
    Ответ должен быть развёрнутым, вдохновляющим.
    """
    return call_deepseek(prompt, api_key)

# ------------------ АВТОРИЗАЦИЯ ------------------
if not st.session_state.authenticated:
    st.markdown("<h1 class='main-header'>🌿 Марина: Планер жизни</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Войди, чтобы продолжить</p>", unsafe_allow_html=True)
    
    password = st.text_input("Введите пароль", type="password")
    api_key_input = st.text_input("Введите API-ключ Polza.ai", type="password")
    
    if st.button("Войти"):
        if password == "botiamhappy":
            if api_key_input.startswith("pza_"):
                st.session_state.authenticated = True
                st.session_state.api_key = api_key_input
                st.rerun()
            else:
                st.error("❌ Неверный API-ключ. Он должен начинаться с 'pza_'.")
        else:
            st.error("❌ Неверный пароль.")
    st.stop()

# ------------------ ОСНОВНОЕ ПРИЛОЖЕНИЕ ------------------
st.markdown(f"<h1 class='main-header'>🌿 Здравствуй, {st.session_state.profile['name']}!</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Ты — главный герой своей жизни ✨</p>", unsafe_allow_html=True)

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
    if st.button("🎯 Цели", use_container_width=True):
        st.session_state.current_page = "Цели"

st.divider()

# ------------------ СТРАНИЦЫ ------------------
page = st.session_state.current_page

if page == "Главная":
    with st.container():
        st.markdown("### ☀️ Утренний план")
        if st.button("✨ Создать план на сегодня"):
            with st.spinner("Генерирую план для тебя..."):
                plan = generate_morning_plan(st.session_state.profile, st.session_state.api_key)
                st.session_state.temp_text = plan
        if st.session_state.temp_text:
            st.markdown(f"<div class='card'>{st.session_state.temp_text}</div>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("### 📖 Книга успехов")
        if st.session_state.entries:
            # Группировка по месяцам
            sorted_entries = sorted(st.session_state.entries, key=lambda x: datetime.datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S.%f"), reverse=True)
            months = {}
            for e in sorted_entries:
                date_obj = datetime.datetime.strptime(e['date'], "%Y-%m-%d %H:%M:%S.%f")
                key = date_obj.strftime("%B %Y")
                if key not in months:
                    months[key] = []
                months[key].append(e)
            
            for month, entries in list(months.items())[:3]:
                st.markdown(f"#### {month}")
                for entry in entries[:5]:
                    st.markdown(f"<div class='win-entry'>📌 {entry['text']}</div>", unsafe_allow_html=True)
                if len(entries) > 5:
                    st.caption(f"и ещё {len(entries) - 5} записей...")
        else:
            st.info("Пока нет записей. Напиши свои победы в разделе «Победы»!")

elif page == "Победы":
    st.markdown("### 🌙 Вечерние победы")
    st.markdown("Запиши всё, за что ты благодарна себе сегодня:")
    
    victory_text = st.text_area("Мои победы сегодня:", height=150)
    
    if st.button("💾 Сохранить победы"):
        if victory_text.strip():
            new_entry = {
                "date": str(datetime.datetime.now()),
                "text": victory_text.strip()
            }
            st.session_state.entries.append(new_entry)
            save_data(st.session_state.entries)
            st.success("✅ Запись сохранена! Ты большая молодец 🌿")
            st.rerun()
        else:
            st.warning("Напиши хотя бы одну победу!")
    
    st.divider()
    st.markdown("### 📜 Мои победы (все записи)")
    if st.session_state.entries:
        sorted_entries = sorted(st.session_state.entries, key=lambda x: datetime.datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S.%f"), reverse=True)
        for entry in sorted_entries[:20]:
            date_obj = datetime.datetime.strptime(entry['date'], "%Y-%m-%d %H:%M:%S.%f")
            st.markdown(f"<div class='win-entry'>📌 {date_obj.strftime('%d.%m')}: {entry['text']}</div>", unsafe_allow_html=True)
    else:
        st.info("Пока нет записей. Начни прямо сейчас!")

elif page == "Итоги":
    tab1, tab2 = st.tabs(["📊 Неделя", "📆 Месяц"])
    
    with tab1:
        st.markdown("### Итоги недели")
        if st.button("📋 Сгенерировать итог недели"):
            with st.spinner("Анализирую твою неделю..."):
                summary = generate_weekly_summary(st.session_state.entries, st.session_state.profile, st.session_state.api_key)
                st.markdown(f"<div class='card'>{summary}</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Итоги месяца")
        if st.button("📋 Сгенерировать итог месяца"):
            with st.spinner("Анализирую твой месяц..."):
                summary = generate_monthly_summary(st.session_state.entries, st.session_state.profile, st.session_state.api_key)
                st.markdown(f"<div class='card'>{summary}</div>", unsafe_allow_html=True)

elif page == "Цели":
    st.markdown("### 🎯 Мои цели")
    
    with st.container():
        st.markdown("#### 📌 Цели на 5 лет")
        for goal in st.session_state.profile['goals_5_years']:
            st.markdown(f"- {goal}")
        
        st.markdown("#### 📌 Цели на этот год")
        st.markdown(f"- {st.session_state.profile['goals_this_year']}")
    
    with st.container():
        st.markdown("#### 🧠 ИИ-анализ целей")
        if st.button("🔍 Попросить ИИ-коуча проанализировать мои цели"):
            with st.spinner("Анализирую..."):
                entries_text = "\n".join([f"- {e['text']}" for e in st.session_state.entries[-30:]])
                prompt = f"""
                Ты — коуч Марины.
                Её цели: {', '.join(st.session_state.profile['goals_5_years'])}
                Её текущие привычки: {', '.join(st.session_state.profile['habits'])}
                Её записи: {entries_text}
                
                Проанализируй, насколько её ежедневные действия соответствуют её целям.
                Дай конкретные рекомендации, как ей лучше двигаться к целям.
                Будь поддерживающим, но честным.
                """
                analysis = call_deepseek(prompt, st.session_state.api_key)
                st.markdown(f"<div class='card'>{analysis}</div>", unsafe_allow_html=True)

# ------------------ ФУТЕР ------------------
st.markdown(f"""
<div class='footer'>
    🌿 Марина: Планер жизни — создано с любовью для тебя<br>
    <small>Все данные хранятся в файле на сервере.</small>
</div>
""", unsafe_allow_html=True)
