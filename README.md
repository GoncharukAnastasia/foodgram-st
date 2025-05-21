# FoodGram

## Простой кулинарный сервис для публикации и обмена рецептами.

## Технологии

* Python 3.11

* Django REST Framework

* Djoser

* PostgreSQL

* Docker & Docker Compose

* Gunicorn


## Эти шаги помогут запустить проект локально с помощью Docker.
### Склонируйте реозиторий
```bash
    git clone https://github.com/GoncharukAnastasia/foodgram-st
```

### Перейдите в директорию с docker-compose.yml и запускайте оттуда
```bash
    cd foogggram-st/infra
    docker-compose up --build
    docker compose exec backend python manage.py load_ingredients
```



### _________________________________________________________

* Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

* По адресу [Frontend](http://localhost) изучите фронтенд веб-приложения, а по адресу [API](http://localhost/api/docs/) — спецификацию API.




## Дополнение:
1. Гончарук Анастасия Александровна - [Telegram](https://t.me/GoncharukNastya)
2. Команды развертывания(Команда миграции автоматически применяется). А также команды импорта json-фикстур.:
```bash
    docker compose up -d --build
    docker compose exec backend python manage.py load_ingredients
```
