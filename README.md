# Habr parcer
**для старта выполните:**
~~~
git clone git@github.com:mikhailkv/habr_parcer.git
docker-compose -f docker-compose.yml up 
~~~

в env контейнера `app` вы можете передать следующие параметры:

<li> CRON - строка в формате "* * * * *" для установки расписания запуска </li> 
<li> URL_PATTERN - regex для валидации url </li> 
<li> CHUNK_SIZE - количество url для обработки </li> 
<li> FILE_PATH - путь к файлу (должен быть *.json, внутри массив строк) если параметр не указан будет использоваться фикстура post.json</li> 

