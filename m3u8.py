# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import requests
import urllib.parse
import urllib.request
import os,json,shutil
import time


class Downloader:
    def __init__(self, pool_size, retry=3):
        self.session = self._get_http_session(pool_size, pool_size, retry)
        self.retry = retry
        self.dir = ''
        self.succed = {}
        self.failed = []
        self.ts_total = 0

    def _get_http_session(self, pool_connections, pool_maxsize, max_retries):
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(pool_connections=pool_connections, pool_maxsize=pool_maxsize, max_retries=max_retries)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            return session

    def run(self, m3u8_url, dir='tmp'):
        self.dir = dir
        if self.dir and not os.path.isdir(self.dir):
            os.makedirs(self.dir)

        r = self.session.get(m3u8_url, timeout=10)
        if r.ok:
            body = r.content.decode("utf-8")
            if body:
                ts_list = [urllib.parse.urljoin(m3u8_url, n.strip()) for n in body.split('\n') if n and not n.startswith("#")]
                if ts_list:
                    for k in ts_list:
                        self.download(k, self.dir)
        else:
            print(r.status_code)

    def download(self, url, path):
        base_url, origin_name = os.path.split(url)
        save_path = os.path.join(path, origin_name)
        response = urllib.request.urlretrieve(url=url)
        contents = open(response[0], "br").read()

        # save path
        f = open(save_path, "wb")
        f.write(contents)
        f.close()


class Parser:
    def __init__(self, dir='tmp'):
        self.dir = dir
        self.retry = 1
        if self.dir and not os.path.isdir(self.dir):
            os.makedirs(self.dir)

    def prase(self, http_url, type):
        response = requests.get(url=http_url, verify=False)
        if response.status_code == 200:
            jsondata = json.loads(response.content.decode('utf-8'))

            if type == "VIDEO":
                playlist = jsondata["playlist"]
                for k in playlist["videos"]:
                    self.download(k["uri"])
                    self.download(k["thumbnail"])
                    self.download(k["download_uri"])
            elif type == "PHOTO":
                playlist = jsondata["album"]
                for k in playlist["photos"]:
                    self.download(k["uri"])
                    self.download(k["thumbnail"])
            # if os.path.exists(self.dir):
            #     shutil.rmtree(self.dir)  # delete local files
            # print("end")
        else:
            print("http error %d" % response.status_code)
            self.prase(http_url, type)

    def download(self, http_link):
        self.retry = 1
        ext = os.path.splitext(http_link)[1]
        if ext == ".m3u8":
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=3)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            r = session.get(http_link, timeout=10)
            if r.ok:
                body = r.content.decode("utf-8")
                if body:
                    ts_list = [urllib.parse.urljoin(http_link, n.strip()) for n in body.split('\n') if
                               n and not n.startswith("#")]
                    if ts_list:
                        for k in ts_list:
                            self._download(k, self.dir)
            else:
                print(r.status_code)
        else:
            self._download(http_link, self.dir)

    def _download(self, http_link, dst):
        print(http_link)
        origin_name = os.path.split(http_link)[1]
        save_path = os.path.join(dst, origin_name)
        if os.path.exists(save_path):
            print(save_path + " exist.")
            return
        try:
            _http_link = http_link
            response = urllib.request.urlretrieve(url=_http_link)
            contents = open(response[0], "br").read()
            with open(save_path, 'wb') as f:
                f.write(contents)
                f.close()
        except Exception as e:
            print('Network(%s) conditions is not good.Reloading.' % str(e))
            if self.retry < 4:
                self.retry += 1
                self._download(http_link, dst)
            else:
                print("Retry %d times faild" % self.retry)
                return

if __name__ == '__main__':
    parse = Parser()
    parse.prase(http_url="https://api.kandaovr.com/video/v1/playlist?codec=4&container=H&language=ZH-CN&name=KANDAO_APP_MAIN&vbr=8&warping=C", type="VIDEO")
    parse.prase(http_url="https://api.kandaovr.com/photo/v1/album?language=EN-US&name=KANDAO_APP_MAIN", type="PHOTO")
    #downloader = Downloader(50)
    #downloader.run('http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_16x9/gear5/prog_index.m3u8', '/home/wuminlai/Work/media/offset_hls/bipbop_16x9/gear5')
