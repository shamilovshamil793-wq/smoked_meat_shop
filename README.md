# 🥩 Smoked Meat Shop

Интернет-магазин копчёного мяса на Django. Учебный/пет-проект с полным циклом: каталог, корзина, оформление заказа, админка, тесты, Docker.

## 🛠 Стек

- **Backend:** Python 3, Django
- **БД:** SQLite (в Docker-контейнере)
- **Контейнеризация:** Docker, docker-compose
- **Frontend:** HTML, CSS, JavaScript (шаблоны Django)
- **Тесты:** Django TestCase (19 тестов)

## ✨ Функционал

- Каталог товаров с категориями
- Карточка товара, детальная страница
- Корзина и оформление заказа (с адресом доставки)
- Кастомные страницы 404 и 500 в стиле сайта
- Адаптивная вёрстка (мобильная версия)
- Админка Django с inline-редактированием заказов и товаров
- Production-настройки: безопасность, логирование, `check --deploy` без предупреждений

## 🚀 Быстрый запуск (локально)

```bash
# 1. Клонировать репозиторий
git clone git@github.com:shamilovshamil793-wq/smoked_meat_shop.git
cd smoked_meat_shop

# 2. Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Скопировать пример env и заполнить
cp .env.example .env
# отредактируй .env: SECRET_KEY, DEBUG, параметры БД

# 5. Применить миграции
python manage.py migrate

# 6. Запустить
python manage.py runserver
