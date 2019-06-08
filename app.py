# coding: UTF-8
from bottle import route, run, template, request, redirect, static_file
from contextlib import contextmanager
from psycopg2 import pool, extras
import os

# 接続プール
conn_pool = pool.SimpleConnectionPool(minconn=1, maxconn=10, dsn=os.environ.get("DATABASE_URL"))

# BBS-ID
bbs_id = "1"

@route("/")
def index():
    with get_cursor() as cur:
        bbs = get_bbs(cur, bbs_id)
        thread_list = get_thread_list(cur, bbs_id)
    return template("index", title=bbs["title"], thread_list=thread_list)

@route("/add", method="POST")
def add():
    with get_cursor() as cur:
        add_thread(cur, bbs_id, request.forms.getunicode("txt_title"), request.forms.getunicode("txt_author"))
    return redirect("/")

@route("/delete")
def delete():
    with get_cursor() as cur:
        bbs = get_bbs(cur, bbs_id)
        if bbs["key"] == request.query.getunicode("key"):
            delete_thread(cur, bbs_id, request.query.getunicode("id"))
            return redirect(".")
        else:
            return template("error", title=bbs["title"], message="削除できませんでした。")

@route("/thread/<thread_id>/")
def thread(thread_id):
    with get_cursor() as cur:
        bbs = get_bbs(cur, bbs_id)
        thread = get_thread(cur, bbs_id, thread_id)
        message_list = get_message_list(cur, bbs_id, thread_id)
    return template("thread", title=bbs["title"], thread_id=thread_id, thread_title=thread["title"], message_list=message_list)

@route("/thread/<thread_id>/add", method="POST")
def thread_add(thread_id):
    with get_cursor() as cur:
        add_message(cur, bbs_id, thread_id, request.forms.getunicode("txt_subject"), request.forms.getunicode("txt_message"), request.forms.getunicode("txt_name"))
    return redirect(".")

@route("/thread/<thread_id>/delete")
def thread_delete(thread_id):
    with get_cursor() as cur:
        bbs = get_bbs(cur, bbs_id)
        if bbs["key"] == request.query.getunicode("key"):
            delete_message(cur, bbs_id, thread_id, request.query.getunicode("id"))
            return redirect(".")
        else:
            return template("error", title=bbs["title"], message="削除できませんでした。")

@route("/<filename:path>")
def static(filename):
    return static_file(filename, root="./static")

@contextmanager
def get_cursor():
    conn = conn_pool.getconn()
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=extras.DictCursor)
    try:
        yield cur
    finally:
        cur.close()
        conn_pool.putconn(conn)

# BBS情報取得
def get_bbs(cur, bbs_id):
    cur.execute("select title, admin, key, to_char(date, 'yyyy/mm/dd hh24:mi') date from t_bbs where bbs_id = %s and del_flg = false", (bbs_id,))
    return cur.fetchone()

# スレッド一覧取得
def get_thread_list(cur, bbs_id):
    cur.execute("select thread_id, title, author, to_char(date, 'yyyy/mm/dd hh24:mi') date from t_thread where bbs_id = %s and del_flg = false order by thread_id", (bbs_id,))
    return cur.fetchall()

# スレッド情報取得
def get_thread(cur, bbs_id, thread_id):
    cur.execute("select thread_id, title, author, to_char(date, 'yyyy/mm/dd hh24:mi') date from t_thread where bbs_id = %s and thread_id = %s and del_flg = false", (bbs_id, thread_id,))
    return cur.fetchone()

# メッセージ一覧取得
def get_message_list(cur, bbs_id, thread_id):
    cur.execute("select message_id, subject, message, name, to_char(date, 'yyyy/mm/dd hh24:mi') date from t_message where bbs_id = %s and thread_id = %s and del_flg = false order by message_id", (bbs_id, thread_id,))
    return cur.fetchall()

# スレッド情報追加
def add_thread(cur, bbs_id, title, author):
    cur.execute("insert into t_thread (bbs_id, title, author) values (%s, %s, %s)", (bbs_id, title, author,))
    return

# メッセージ情報追加
def add_message(cur, bbs_id, thread_id, subject, message, name):
    cur.execute("insert into t_message (bbs_id, thread_id, subject, message, name) values (%s, %s, %s, %s, %s)", (bbs_id, thread_id, subject, message, name,))
    return

# スレッド情報削除
def delete_thread(cur, bbs_id, thread_id):
    cur.execute("update t_thread set del_flg = true where bbs_id = %s and thread_id = %s", (bbs_id, thread_id,))
    return

# メッセージ情報削除
def delete_message(cur, bbs_id, thread_id, message_id):
    cur.execute("update t_message set del_flg = true where bbs_id = %s and thread_id = %s and message_id = %s", (bbs_id, thread_id, message_id))
    return

if __name__ == "__main__":
    run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
