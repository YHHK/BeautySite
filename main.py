#!/usr/bin/env python

from urllib import urlretrieve
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
from bs4 import BeautifulSoup
from multiprocessing import Pool
import requests
import base64
import click
import time
import os
import re

mysql_scheme = ""
mysql_cookie = ""

engine = create_engine(mysql_scheme, encoding='utf-8')
Base = declarative_base()
Sess = sessionmaker(bind=engine)
session = Sess()


class Article(Base):
    __tablename__ = "tutu_article"
    id = Column(Integer, primary_key=True)
    cid = Column(Integer)
    title = Column(String)
    tag = Column(String)
    content = Column(String)
    remark = Column(String, default='')
    cover = Column(String, default='')


class Attach(Base):
    __tablename__ = "tutu_attach"
    id = Column(Integer, primary_key=True)
    remark = Column(String, default='')
    name = Column(String, default='')
    ext = Column(String, default='jpg')
    file = Column(String, default='')
    article_id = Column(Integer)
    uid = Column(Integer, default=1)
    type = Column(Integer, default=1)


h = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "referer": "http://www.mzitu.com"
}


def request_image_url(image_path, article):
    data = requests.get(image_path)
    image_url = 'http://picupload.service.weibo.com/interface/pic_upload.php?mime=image%2Fjpeg&data=base64&url=0&markpos=1&logo=&nick=0&marks=1&app=miniblog'
    b = base64.b64encode(data.content)
    resp = requests.post(image_url, data={'b64_data': b}, headers={
        "cookie": weibo_cookie,
    })

    ret = re.findall(r'''"pid":"([^"]+)"''', resp.content)
    for image_id in ret:
        target = 'http://ww3.sinaimg.cn/large/%s' % image_id
        a = Attach(name=image_id, file=target, article_id=article.id)
        session.add(a)
        if not article.cover:
            article.cover = target
            session.add(article)
    session.commit()


def main(post_id):
    print post_id
    if not os.path.exists(post_id):
        os.mkdir(post_id)
    base = "http://www.mzitu.com/{id}/{p}"

    cur, article = 1, None

    while True:
        url = base.format(id=post_id, p=cur)
        resp = requests.get(url, headers=h)
        if not resp.ok:
            break
        if resp.url != url and cur > 1:
            break
        if cur == 1:
            dom = BeautifulSoup(resp.content)
            title = dom.find('h2', class_='main-title').text
            tag = ",".join(list(set([k.text for k in dom.find_all('a', rel='tag')])))
            cid = 1
            article = Article(title=title, tag=tag, cid=cid, remark='', content="<p data-src='{url}'>".format(
                url=url
            ))
            session.add(article)
            session.commit()
        open('{id}/{p}.html'.format(id=post_id, p=cur), "w").write(resp.content)
        one = re.findall(r'http://i.meizitu.net/\d+/\d+/[\w\-]+.jpg', resp.content)
        for p in one:
            request_image_url(p, article)

        cur += 1


p = Pool(3)
articles = open('articles').read().splitlines()
p.map(main, articles)
