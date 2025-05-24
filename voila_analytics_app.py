import ipywidgets as widgets
from IPython.display import display, clear_output
import openai
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

# Загружаем ключи
load_dotenv()

# Настройки OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# UI
question_input = widgets.Textarea(
    value='',
    placeholder='Например: Покажи продажи шоколада по месяцам за 2023 год',
    description='Вопрос:',
    layout=widgets.Layout(width='100%', height='100px'),
)
submit_button = widgets.Button(description='Анализировать', button_style='primary')
output = widgets.Output()

display(question_input, submit_button, output)

# Генерация SQL-запроса с GPT
def question_to_sql(question: str) -> str:
    prompt = (
        "Ты аналитик. Преобразуй вопрос на русском языке в SQL-запрос для PostgreSQL 17.\n"
        "Структура таблиц:\n"
        "- Products(product_id, product_name)\n"
        "- Product_materials(product_id, component_id)\n"
        "- Customers(customer_id, customer_name, product_id, purchase_date, price, quantity)\n"
        "- Components(component_id, product_id, component_name, material_id)\n"
        "- Materials(material_id, material_name)\n\n"
        f"Вопрос: {question}\nSQL:"
    )
    response = openai.ChatCompletion.create(
        model="openai/gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response['choices'][0]['message']['content'].strip()

# Выполнение SQL на PostgreSQL
def execute_sql(query: str) -> pd.DataFrame:
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
        database=os.getenv("PG_DBNAME"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD")
    )
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Визуализация: таблица + график
def visualize(df: pd.DataFrame):
    display(df)

    time_cols = [col for col in df.columns if col.lower() in ['purchase_date', 'month', 'date']]
    value_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]

    if time_cols and value_cols:
        time_col = time_cols[0]
        value_col = value_cols[0]

        df[time_col] = pd.to_datetime(df[time_col])
        df.sort_values(by=time_col, inplace=True)
        df.set_index(time_col, inplace=True)

        df[value_col].plot(kind='line', marker='o', title=f"{value_col} по дате")
        plt.grid(True)
        plt.ylabel(value_col)
        plt.show()

# Кнопка
def on_submit_clicked(b):
    with output:
        clear_output()
        question = question_input.value.strip()
        if not question:
            print("Введите вопрос.")
            return

        print("🧠 Вопрос:", question)
        sql = question_to_sql(question)
        print("\n📄 SQL:")
        print(sql)

        try:
            df = execute_sql(sql)
            print("\n📊 Результат:")
            visualize(df)
        except Exception as e:
            print("⚠️ Ошибка:", e)

submit_button.on_click(on_submit_clicked)
