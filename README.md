# FastAPI с авторизацией по почте

Вероятно, что проект дальше не будет развиваться. Скорее всего, я просто перенесу наработки отсюда в свой основной
проект [learn_many_things](https://github.com/Marat22/learn_many_things).

# TODO

- [x] регистрация по почте
- [x] авторизация
- [x] аутентификация
- [ ] в функции `send_confirmation_email` ссылка на подтверждение почты захадкодена. Нужно просто как-то получать
  текущий адрес.
- [ ] проверять expire time (время экспирации можно достать, например, в `decode_token`)
  - возможно oauth сам делает эти проверки
- [ ] удаление пользователей
- [ ] восстановление пароля
- [ ] изменение пароля
- [ ] возможно разные роли
- [ ] добавить async!! (особенно для бд)
- [ ] тестирование
- [ ] добавить на сайт ссылку на репозиторий в github
- [ ] обновить README и больше рассказать о проекте
- [ ] продумать безопасноть
  - [ ] возможно стоит проверить, есть ли какие-то линтеры, которые проверяют, что почта, токены и всё в этом роде не попали в коммит.
  - [ ] почитать статьи на эту тему
  - [ ] сделать базовую защиту от DoS атак
- [ ] добавить дедлайны для задач
  - [ ] добавить напоминания о дедлайнах по почте