#!/bin/sh
set -e

echo "==> Применяем миграции..."
python manage.py migrate --settings=config.settings_docker

echo "==> Загружаем демо-данные (если есть фикстура)..."
if [ -f shop/fixtures/demo_data.json ]; then
    python manage.py loaddata shop/fixtures/demo_data.json --settings=config.settings_docker || true
fi

echo "==> Создаём admin/admin123 (если не существует)..."
python manage.py shell --settings=config.settings_docker -c "
from django.contrib.auth import get_user_model
U = get_user_model()
if not U.objects.filter(username='admin').exists():
    U.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('admin создан')
else:
    print('admin уже есть')
" || true

echo "==> Запускаем сервер..."
exec python manage.py runserver 0.0.0.0:8000 --settings=config.settings_docker
