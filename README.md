# FastAPI + Starlette-Admin demo project


> ⚠️ **Важно для использования из РФ:**
> Starlette-Admin загружает стили из зарубежных источников, для корректной работы из РФ требуется VPN / прокси

 
## ⚡️ Быстрый старт
0. **Подготовка конфигураций:**
   
   Переименовать .env.example в .env или заменить на свой .env
2.  **Запуск приложения и базы данных:**
    ```bash
    docker compose up --build -d
    ```
3.  **Проведение миграций:**
    ```bash
    docker-compose exec app alembic upgrade head
    ```
4.  **Доступ к админ-панели:**
    [http://localhost:9000/admin](http://localhost:9000/admin)
