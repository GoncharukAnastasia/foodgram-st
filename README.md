# FoodGram

## Простой кулинарный сервис для публикации и обмена рецептами.

## Использованные технологии.

- Python 3.11

- Django REST Framework

- Djoser (авторизация)

- PostgreSQL

- Docker & Docker Compose

- Gunicorn

- Быстрый старт

## Эти шаги помогут запустить проект локально с помощью Docker.

### Перейдите в директорию с docker-compose.yml и запускайте оттуда

```bash
    cd foogggram-st/infra
    docker-compose up --build
    docker-compose up
```

### ****************************\_****************************

- Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

- По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.
