#!/bin/bash

#django项目数据库初始化脚本
#需要先创建数据库

# 首先导入auth表
python manage.py migrate auth

# 制作users
python manage.py makemigrations users
 
# 导入users
python manage.py migrate users

# 导入admin
python manage.py migrate --fake admin

# 导入其他
python manage.py migrate

# 导入video
python manage.py makemigrations video
python manage.py migrate video

# 导入comment
python manage.py makemigrations comment
python manage.py migrate comment

# 导入myadmin
python manage.py makemigrations myadmin
python manage.py migrate myadmin
