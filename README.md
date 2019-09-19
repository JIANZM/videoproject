# videoproject
基于nginx-uWSGI-django-mysql的视频播放网站


#docker部署

#django部署
docker run -it --name django-jzm -p 8083:8000 -v /home/python01/Learn/videoproject/videoproject:/videoproject --privileged=true ubuntu-utf8:django /bin/bash
uwsgi --ini videoproject/videoproject_uwsgi.ini

#nginx部署
docker run -d -p 80:80 --name nginx-jzm -v /home/python01/Learn/dockerLearn/nginx/www:/usr/share/nginx/html -v /home/python01/Learn/videoproject/videoproject/videoproject_nginx.conf:/etc/nginx/nginx.conf -v /home/python01/Learn/dockerLearn/nginx/logs:/var/log/nginx -v /home/python01/Learn/videoproject/videoproject/upload:/usr/share/nginx/upload -v /home/python01/Learn/videoproject/videoproject/static:/usr/share/nginx/static --privileged=true nginx

#mysql部署
