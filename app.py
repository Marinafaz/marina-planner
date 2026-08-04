import streamlit as st
import datetime
import json
import requests
import os
import re
from collections import defaultdict
import base64
from datetime import datetime as dt

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
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "planning_mode" not in st.session_state:
    st.session_state.planning_mode = None
if "daily_plan_dialog" not in st.session_state:
    st.session_state.daily_plan_dialog = []
if "editing_entry" not in st.session_state:
    st.session_state.editing_entry = None

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

# ------------------ АВТОРИЗАЦИЯ ------------------
st.markdown("""
<script>
    function loadPassword() {
        const pwd = localStorage.getItem('marina_password');
        if (pwd) {
            const input = window.parent.document.querySelector('input[type="password"]');
            if (input) {
                input.value = pwd;
                const btn = window.parent.document.querySelector('button:has(> div:contains("Войти"))');
                if (btn) btn.click();
            }
        }
    }
    setTimeout(loadPassword, 1000);
</script>
""", unsafe_allow_html=True)

if not st.session_state.authenticated:
    st.markdown("<h1 class='main-header'>🌿 Марина: Планер жизни</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Войди, чтобы продолжить</p>", unsafe_allow_html=True)
    
    password = st.text_input("Введите пароль", type="password", key="login_password")
    remember = st.checkbox("Запомнить меня (пароль сохранится в браузере)")
    
    if st.button("Войти"):
        if password == "botiamhappy":
            st.session_state.authenticated = True
            # НОВЫЙ КЛЮЧ
            st.session_state.api_key = "pza_X3mIB8n6SdL35mn-ZI3QiRLMRwJ_ES1i"
            if remember:
                st.markdown(f"""
                <script>
                    localStorage.setItem('marina_password', '{password}');
                </script>
                """, unsafe_allow_html=True)
            st.rerun()
        else:
            st.error("❌ Неверный пароль.")
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
    st.markdown("### ☀️ План на сегодня")
    
    if st.button("✨ Создать план на сегодня"):
        with st.spinner("Генерирую план для тебя..."):
            weekly_plan = st.session_state.data.get("weekly_plan")
            if not weekly_plan:
                st.warning("Сначала создай план на неделю в разделе «Планы»!")
                st.stop()
            prompt = f"""
            Ты — личный коуч Марины.
            Сегодня {datetime.datetime.now().strftime('%A, %d %B')}.
            План на неделю: {weekly_plan}
            Составь план на сегодня в виде списка задач.
            После плана спроси, что она хочет добавить или скорректировать.
            """
            plan = call_deepseek(prompt, st.session_state.api_key)
            st.session_state.daily_plan_dialog = [{"role": "assistant", "content": plan}]
    
    if st.session_state.daily_plan_dialog:
        for msg in st.session_state.daily_plan_dialog:
            if msg["role"] == "user":
                st.markdown(f"<div class='chat-message chat-message-user'>👤 {msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-message'>🌿 {msg['content']}</div>", unsafe_allow_html=True)
        
        user_response = st.text_input("Ваш ответ:", key="daily_plan_input")
        col_voice, col_send = st.columns([1, 4])
        with col_voice:
            st.markdown("""
            <button class="voice-btn" onclick="startVoiceInput('daily_plan_input')">🎤</button>
            <script>
                function startVoiceInput(fieldId) {
                    const input = window.parent.document.querySelector(`input[key="${fieldId}"]`);
                    if (!input) return;
                    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                    recognition.lang = 'ru-RU';
                    recognition.onresult = function(event) {
                        const transcript = event.results[0][0].transcript;
                        input.value = transcript;
                        const event = new Event('input', { bubbles: true });
                        input.dispatchEvent(event);
                    };
                    recognition.start();
                }
            </script>
            """, unsafe_allow_html=True)
        with col_send:
            if st.button("Отправить", key="daily_send"):
                if user_response.strip():
                    st.session_state.daily_plan_dialog.append({"role": "user", "content": user_response})
                    prompt = f"""
                    Ты — коуч Марины.
                    План: {st.session_state.daily_plan_dialog[0]['content']}
                    Марина ответила: {user_response}
                    Отреагируй и предложи обновлённый план или скажи сохранить.
                    """
                    response = call_deepseek(prompt, st.session_state.api_key)
                    st.session_state.daily_plan_dialog.append({"role": "assistant", "content": response})
                    st.rerun()
        
        if st.button("💾 Сохранить план дня"):
            st.session_state.data["daily_plan"] = st.session_state.daily_plan_dialog[0]["content"]
            save_data(st.session_state.data)
            st.success("✅ План на сегодня сохранён!")
    
    if st.session_state.data.get("daily_plan"):
        st.markdown("### 📋 Текущий план на сегодня")
        plan_text = st.session_state.data["daily_plan"]
        lines = plan_text.split("\n")
        for line in lines:
            if line.strip():
                if line.strip().startswith(("-", "•", "—")):
                    st.markdown(f"<div class='win-entry'>{line.strip()}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='win-entry'>• {line.strip()}</div>", unsafe_allow_html=True)
    
    # БЛОК БЭКАПА
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
            week_entries = []
            for e in st.session_state.data["entries"]:
                date_obj = datetime.datetime.strptime(e['date'], "%Y-%m-%d %H:%M:%S.%f")
                if week_start_selected <= date_obj < week_start_selected + datetime.timedelta(days=7):
                    week_entries.append(e)
            if not week_entries:
                st.info("Нет записей за эту неделю.")
            else:
                text = "\n".join([f"- {e['text']}" for e in week_entries])
                prompt = f"""
                Сгруппируй победы по целям (спорт, семья, работа, забота о себе).
                Записи: {text}
                Дай итог и 2-3 мягкие рекомендации.
                """
                analysis = call_deepseek(prompt, st.session_state.api_key)
                st.markdown(f"<div class='card'>{analysis}</div>", unsafe_allow_html=True)

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
