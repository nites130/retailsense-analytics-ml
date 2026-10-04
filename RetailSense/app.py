"""RetailSense local full-stack app. Run: python app.py"""
from pathlib import Path
from io import StringIO
import json
import sqlite3
import threading
import secrets
import re
import time
import os
from datetime import timedelta
from contextlib import contextmanager
import pandas as pd
from flask import Flask, jsonify, render_template, request, Response, session, redirect, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
from analytics import clean_data, demo_data, customers, summary
from ml import train

ROOT = Path(__file__).resolve().parent


def create_app(db_path=None):
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=50*1024*1024, DATABASE=str(db_path or ROOT/'data'/'retailsense.db'))
    Path(app.config['DATABASE']).parent.mkdir(parents=True,exist_ok=True)
    lock = threading.RLock()
    data_root=Path(app.config['DATABASE']).parent
    account_path=data_root/(Path(app.config['DATABASE']).stem+'-accounts.sqlite3')
    key_path=data_root/'.session-secret'
    if not key_path.exists():
        try:
            fd=os.open(key_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'w') as f:f.write(secrets.token_hex(32))
        except FileExistsError:
            pass
    app.config.update(SECRET_KEY=key_path.read_text().strip(),SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',PERMANENT_SESSION_LIFETIME=timedelta(hours=8))
    attempts={}

    @contextmanager
    def accounts():
        conn=sqlite3.connect(account_path)
        conn.row_factory=sqlite3.Row
        try:
            with conn:yield conn
        finally:conn.close()

    with accounts() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL)')


    @contextmanager
    def connect():
        uid=session['user_id']
        user_path=data_root/(Path(app.config['DATABASE']).stem+f'-user-{uid}.sqlite3')
        conn = sqlite3.connect(user_path)
        conn.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        conn.execute('CREATE TABLE IF NOT EXISTS transactions (InvoiceNo TEXT,StockCode TEXT,Description TEXT,Quantity REAL,InvoiceDate TEXT,UnitPrice REAL,CustomerID TEXT,Country TEXT,Revenue REAL)')
        conn.execute('CREATE TABLE IF NOT EXISTS predictions (CustomerID TEXT PRIMARY KEY,probability REAL)')
        conn.commit()
        try:
            with conn:yield conn
        finally:conn.close()

    def setmeta(conn,key,value):
        conn.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)',(key,json.dumps(value)))

    def meta(conn,key,default=None):
        row=conn.execute('SELECT value FROM metadata WHERE key=?',(key,)).fetchone()
        return json.loads(row[0]) if row else default

    def save(df,quality,source):
        values=df.copy()
        values['InvoiceDate']=values.InvoiceDate.astype(str)
        with connect() as conn:
            conn.execute('DELETE FROM transactions')
            conn.executemany('INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?)',values.itertuples(index=False,name=None))
            conn.execute('DELETE FROM predictions')
            conn.execute("DELETE FROM metadata WHERE key='model'")
            setmeta(conn,'dataset',dict(source=source,quality=quality))

    def load():
        with connect() as conn:
            df=pd.read_sql_query('SELECT * FROM transactions',conn)
        if df.empty:
            raise ValueError('Load the demo or import a CSV first.')
        df['InvoiceDate']=pd.to_datetime(df.InvoiceDate)
        return df

    @app.before_request
    def protect_write():
        if request.method == 'POST' and request.headers.get('X-RetailSense') != 'local-app':
            return jsonify(error='Missing application request header.'),403
        g.user=None
        if session.get('user_id'):
            with accounts() as conn:
                row=conn.execute('SELECT id,name,email FROM users WHERE id=?',(session['user_id'],)).fetchone()
            if row:g.user=dict(row)
            else:session.clear()
        if request.path.startswith('/api/') and not request.path.startswith('/api/auth/') and not g.user:
            return jsonify(error='Please sign in to your workspace.'),401

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'"
        response.headers['Cache-Control']='no-store'
        return response

    @app.errorhandler(ValueError)
    def invalid(exc):
        return jsonify(error=str(exc)),400

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return jsonify(error='File exceeds 50 MB.' if exc.code==413 else exc.description),exc.code

    @app.errorhandler(Exception)
    def unexpected(exc):
        app.logger.exception('Request failed')
        return jsonify(error='Unexpected server error. Check the terminal for details.'),500

    @app.get('/')
    def home():
        return render_template('home.html',user=g.user)

    @app.get('/login')
    @app.get('/signup')
    def auth_page():
        if g.user:return redirect('/dashboard')
        return render_template('auth.html',signup=request.path=='/signup')

    @app.get('/dashboard')
    def workspace():
        if not g.user:return redirect('/login')
        return render_template('index.html',user=g.user)

    @app.post('/api/auth/signup')
    @app.post('/api/auth/login')
    def authenticate():
        payload=request.get_json(silent=True) or {}
        if not isinstance(payload,dict):raise ValueError('Invalid form data.')
        email=str(payload.get('email','')).strip().lower()
        password=str(payload.get('password',''))
        key=request.remote_addr or 'local'
        now=time.monotonic()
        with lock:
            attempts[key]=[t for t in attempts.get(key,[]) if now-t<60]
            if len(attempts[key])>=10:return jsonify(error='Too many attempts. Wait one minute and retry.'),429
            attempts[key].append(now)
        if len(email)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):
            raise ValueError('Enter a valid email address.')
        if len(password)<8 or len(password)>128:
            raise ValueError('Use a password between 8 and 128 characters.')
        if request.path.endswith('signup'):
            name=str(payload.get('name','')).strip()
            if not 2<=len(name)<=60:raise ValueError('Name must contain 2–60 characters.')
            try:
                with accounts() as conn:
                    cursor=conn.execute('INSERT INTO users (name,email,password) VALUES (?,?,?)',(name,email,generate_password_hash(password)))
                    uid=cursor.lastrowid
            except sqlite3.IntegrityError:
                return jsonify(error='An account with this email already exists. Sign in instead.'),409
        else:
            with accounts() as conn:
                row=conn.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
            if not row or not check_password_hash(row['password'],password):
                return jsonify(error='Email or password is incorrect.'),401
            uid=row['id']
        session.clear()
        session['user_id']=uid
        session.permanent=True
        return jsonify(ok=True,redirect='/dashboard')

    @app.post('/api/auth/logout')
    def logout():
        session.clear()
        return jsonify(ok=True)


    @app.get('/api/status')
    def status():
        with lock,connect() as conn:
            return jsonify(dataset=meta(conn,'dataset'),model=meta(conn,'model'))

    @app.post('/api/demo')
    def demo():
        with lock:
            df,quality=clean_data(demo_data())
            save(df,quality,'Synthetic demo • generated with seed 42 • GBP')
        return jsonify(ok=True,quality=quality)

    @app.post('/api/import')
    def upload():
        file=request.files.get('file')
        if not file or not file.filename.lower().endswith('.csv'):
            raise ValueError('Choose a .csv file with the required columns.')
        try:
            raw=pd.read_csv(file,dtype={'CustomerID':str,'InvoiceNo':str,'StockCode':str},encoding='utf-8-sig')
        except (UnicodeDecodeError,pd.errors.ParserError,pd.errors.EmptyDataError):
            raise ValueError('Cannot read this CSV. Export as CSV UTF-8 (comma-delimited).')
        df,quality=clean_data(raw)
        with lock:
            save(df,quality,'Imported CSV • prices treated as GBP')
        return jsonify(ok=True,quality=quality)

    @app.get('/api/dashboard')
    def dashboard():
        with lock:
            df=load()
            countries=sorted(df.Country.unique().tolist())
            country=request.args.get('country','')
            if country:
                df=df[df.Country==country]
            for key,op in [('start','ge'),('end','le')]:
                value=request.args.get(key,'')
                if value:
                    try:
                        date=pd.Timestamp(value).normalize()
                    except Exception:
                        raise ValueError('Enter a valid date.')
                    if op=='ge':
                        df=df[df.InvoiceDate>=date]
                    else:
                        df=df[df.InvoiceDate<date+pd.Timedelta(days=1)]
            if df.empty:
                raise ValueError('No transactions match the selected dates and country.')
            return jsonify(**summary(df),available_countries=countries)

    @app.get('/api/customers')
    def customer_list():
        with lock:
            out=customers(load())
            with connect() as conn:
                scores=pd.read_sql_query('SELECT * FROM predictions',conn)
            out=out.merge(scores,on='CustomerID',how='left')
            query=request.args.get('q','').strip()
            segment=request.args.get('segment','')
            if query:
                out=out[out.CustomerID.str.contains(query,regex=False)]
            if segment:
                out=out[out.segment==segment]
            out=out.sort_values('monetary',ascending=False)
            total=len(out)
            page=max(1,int(request.args.get('page','1')))
            out=out.iloc[(page-1)*25:page*25].round(4)
            return jsonify(total=total,page=page,rows=json.loads(out.to_json(orient='records')))

    @app.get('/api/customer/<customer_id>')
    def customer_detail(customer_id):
        with lock:
            df=load()
            selected=df[df.CustomerID==customer_id]
            if selected.empty:
                return jsonify(error='Customer not found.'),404
            profile=customers(df).set_index('CustomerID').loc[customer_id].to_dict()
            profile={k:float(v) if not isinstance(v,str) else v for k,v in profile.items()}
            recent=selected.groupby('InvoiceNo').agg(date=('InvoiceDate','max'),revenue=('Revenue','sum')).sort_values('date',ascending=False).head(10).reset_index()
            recent['date']=recent.date.dt.strftime('%Y-%m-%d')
            with connect() as conn:
                row=conn.execute('SELECT probability FROM predictions WHERE CustomerID=?',(customer_id,)).fetchone()
            return jsonify(customer_id=customer_id,profile=profile,probability=row[0] if row else None,orders=json.loads(recent.to_json(orient='records')),country=str(selected.Country.iloc[-1]))

    @app.post('/api/train')
    def train_model():
        with lock:
            report,scores=train(load())
            with connect() as conn:
                conn.execute('DELETE FROM predictions')
                conn.executemany('INSERT INTO predictions VALUES (?,?)',scores.itertuples(index=False,name=None))
                setmeta(conn,'model',report)
        return jsonify(report)

    @app.get('/api/export')
    def export():
        with lock:
            out=customers(load())
            with connect() as conn:
                out=out.merge(pd.read_sql_query('SELECT * FROM predictions',conn),on='CustomerID',how='left')
            # Protect spreadsheet consumers from formula injection in imported IDs.
            for col in out.select_dtypes(include=['object']).columns:
                out[col]=out[col].map(lambda v:"'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v)
            return Response(out.to_csv(index=False),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=retailsense_customers.csv'})

    @app.get('/api/template')
    def template():
        return Response(demo_data().head(10).to_csv(index=False),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=retailsense_template.csv'})

    return app


if __name__=='__main__':
    create_app().run(host='127.0.0.1',port=5000,debug=False)
