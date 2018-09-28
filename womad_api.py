#!/usr/bin/python3
import requests
import time
import json
from urllib.parse import quote
from requests.adapters import HTTPAdapter
import lxml.html

'''
import logging
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 1
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
'''


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Mobile Safari/537.36",
    }
XHR_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Pragma": "no-cache",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/69.0.3497.81 Chrome/69.0.3497.81 Safari/537.36",
    }

def raw_parse(text, start, end, offset=0):
    s = text.find(start, offset)
    if s == -1: return None, 0
    s += len(start)
    e = text.find(end, s)
    if e == -1: return None, 0
    return text[s:e], e

import cfscrape

def gen_session():
    #sess = requests.Session()
    #sess = cfscrape.create_scraper(sess=sess)
    sess = cfscrpae.create_scraper(delay=5)
    sess.mount('http://', HTTPAdapter(max_retries=100))
    sess.headers.update(DEFAULT_HEADERS)
    #sess.head('http://dcinside.com')
    return sess
default_sess = gen_session()


def board(board_id, num=-1, start_page=1, include_contents=False, sess=default_sess):
    page = start_page
    while num:
        url = "https://m.womad.life/r/%s/%s"%(board_id, page)
        res = sess.get(url)
        parsed = lxml.html.fromstring(res.text)
        maybe_remaining_docs = False
        for doc_header in parsed.xpath("//ul[@class='listview']/li/a"):
            doc_id = doc_header.get("href").split('?')[0][1:]
            title = doc_header.text
            author, time, view_num = tuple(i.strip() for i in doc_header[0].text.split('|')[:2])
            view_num = int(view_num[3:])
            vote_num = int(doc_header[0][0].text)
            comment_num = int(doc_header[0][1].text)
            #doc = document(board_id, doc_id, sess) if include_contents else None
            doc = None
            yield {
                "id": doc_id,
                "doc_id": doc_id,
                "no": doc_id,
                "doc_no":doc_id,
                "page": page,
                "title": title,
                "comment_num": comment_num,
                "name": author,
                "nickname": author,
                "author": author,
                "time": time,
                "date": time,
                "view_num": view_num,
                "vote_num": vote_num,
                "recommend": vote_num,
                "contents": doc and doc["contents"],
                "images": doc and doc["images"],
                "comments": doc and doc["comments"],
                "vote_up": doc and doc["vote_up"],
                "vote_down": doc and doc["vote_down"],
                 }
            maybe_remaining_docs = True
            num -= 1
            if num==0: break
        if not maybe_remaining_docs:
            break
        page += 1

print(next(board("자유게시판")))


def document(board_id, doc_id, sess=default_sess):
    url = "http://gall.dcinside.com/board/view/?id=%s&no=%s&page=1"%(board_id, doc_id)
    res = sess.get(url)
    parsed = lxml.html.fromstring(res.text)
    doc_content = parsed.xpath("//div[@class='writing_view_box']")[0]
    recomm_btn = parsed.xpath("//div[@class='btn_recommend_box clear']")[0]
    # remove jikbang ad
    doc_content.remove(doc_content[0])
    contents = '\n'.join(i.strip() for i in doc_content.itertext() if i.strip())
    imgs = [i.get("src").replace("dcimg1.dcinside.com/viewimage.php?", "image.dcinside.com/viewimagePop.php?") for i in doc_content[1].xpath(".//img")]
    comments = _comments(board_id, doc_id, sess, e_s_n_o=parsed.xpath("//input[@id='e_s_n_o']")[0].get("value"))
    return {"contents": contents, "images": imgs, "comments": comments,
            "vote_up": recomm_btn[1][0][0].text, "vote_down": recomm_btn[2][1][0].text}

INF = 99999
def _comments(board_id, doc_id, sess, e_s_n_o='3eabc219ebdd65f53e'):
    # must call after doc contents read
    url = "http://gall.dcinside.com/board/comment/"
    page = 1
    total_cmt, read_cmt = INF, 0
    while read_cmt < total_cmt:
        payload = "ci_t=%s&id=%s&no=%s&e_s_n_o=%s&comment_page=%s&sort="%(sess.cookies.get('ci_c'), board_id, doc_id, e_s_n_o, page)
        res = sess.post(url, data=payload, headers=XHR_HEADERS)
        comments_json = json.loads(res.text)
        total_cmt = int(comments_json["total_cnt"])
        if not comments_json["comments"]: break
        for com in comments_json["comments"]:
            com.update({
                "page": page,
                "id": com["no"],
                "comment_id": com["no"],
                "comment_no": com["no"],
                })
            yield(com)
            read_cmt += 1
        page += 1

def writeDoc(board_id, title, contents, name='봇', password=1234, mgallery=False, sess=default_sess):
    url = "http://gall.dcinside.com/%sboard/lists?id=%s&page=%s"%("mgallery/" if mgallery else "/", board_id, 1)
    res = sess.get(url)
    time.sleep(1)
    url = "http://gall.dcinside.com/%sboard/write/?id=%s" % ("mgallery/" if mgallery else "/", board_id)
    sess.headers.update({
        "Referer": url,
        "Host": "gall.dcinside.com",
        "Origin": "http://gall.dcinside.com",
        })
    res = sess.get(url)
    time.sleep(1)
    parsed = lxml.html.fromstring(res.text)
    inputs = parsed.xpath("//form[@action='http://gall.dcinside.com/index.php/board/forms/article_submit']/input")
    payload = '&'.join(i.get('name')+'='+(i.get('value') or '') for i in inputs)
    name, password, title, contents = quote(name), quote(password), quote(title), quote(contents, safe='')
    payload += '&name=%s&password=%s&subject=%s&ci_t=%s&mode=W'%(name, password, title, inputs[0].get("value"))
    url = "http://gall.dcinside.com/block/block/"
    sess.cookies.update({"ck_lately_gall": "1iA"})
    res = sess.post(url, data=payload, headers=XHR_HEADERS)
    block_key = res.text
    url = "http://gall.dcinside.com/board/forms/article_submit"
    payload += "&block_key=%s&memo=%s&code=undefined&bgm=0"%(block_key, contents)
    print(payload)
    #sess.cookies.update({"ck_lately_gall": "1iA", "alarm_new": "1", "alarm_popup": "1", "last_notice_no": "24068", "last_alarm": "1537587596"})
    print(sess.cookies)

    res = sess.post(url, data=payload, headers=XHR_HEADERS, cookies=sess.cookies)
    print(res.text)

writeDoc("alphago", "ㄹㄹㄹㄹㄹ?", "<p>ㄹㄹ</p>", "ff", "1234", mgallery=True)
#for i in board_page('programming', 1, include_contents=True): print(i)
#for i in board("programming", include_contents=True):
#    print([com for com in i["comments"]])

