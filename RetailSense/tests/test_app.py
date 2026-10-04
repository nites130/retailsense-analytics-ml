import io
import pandas as pd
import pytest
from app import create_app
from analytics import clean_data, demo_data, customer_features
from ml import snapshot
H={'X-RetailSense':'local-app'}
@pytest.fixture
def client(tmp_path):
    c=create_app(tmp_path/'test.db').test_client()
    assert c.post('/api/auth/signup',headers=H,json={'name':'Test User','email':'test@example.com','password':'password123'}).status_code==200
    return c
def test_full_workflow(client):
    assert client.get('/').status_code==200
    assert client.get('/api/status').json['dataset'] is None
    assert client.get('/api/dashboard').status_code==400
    assert client.post('/api/demo').status_code==403
    assert client.post('/api/demo',headers=H).status_code==200
    d=client.get('/api/dashboard').json
    assert d['orders']>0 and d['customers']>30
    assert abs(sum(x['value'] for x in d['monthly'])-d['revenue'])<.1
    assert client.get('/api/dashboard?country=Germany').json['revenue']<d['revenue']
    response=client.post('/api/train',headers=H)
    assert response.status_code==200,response.json
    r=response.json
    assert r['train_cutoff']<r['validation_cutoff']<r['test_cutoff']<r['as_of']
    assert 0<=r['test']['f1']<=1
    rows=client.get('/api/customers').json['rows']
    assert len(rows)==25 and all(0<=x['probability']<=1 for x in rows)
    assert client.get('/api/customers?q=DOESNOTEXIST').json['total']==0
    assert client.get('/api/export').status_code==200
    client.post('/api/demo',headers=H)
    assert client.get('/api/status').json['model'] is None

def test_import_and_preserve_on_failure(client):
    raw=demo_data().head(200)
    r=client.post('/api/import',headers=H,data={'file':(io.BytesIO(raw.to_csv(index=False).encode()),'data.csv')})
    assert r.status_code==200,r.json
    old=client.get('/api/dashboard').json['revenue']
    bad=client.post('/api/import',headers=H,data={'file':(io.BytesIO(b'foo\nbar'),'bad.csv')})
    assert bad.status_code==400
    assert client.get('/api/dashboard').json['revenue']==old
    assert client.post('/api/train',headers=H).status_code==400

def test_cleaning_and_no_future_leakage():
    raw=demo_data().head(50)
    invalid=raw.iloc[[0]].copy();invalid['Quantity']=-1
    clean,r=clean_data(pd.concat([raw,raw.iloc[[0]],invalid],ignore_index=True))
    assert r['duplicate_rows']==1 and r['excluded_rows']==1
    cutoff=clean.InvoiceDate.sort_values().iloc[20]
    before=customer_features(clean,cutoff)
    changed=clean.copy();changed.loc[changed.InvoiceDate>=cutoff,'Revenue']=999999
    pd.testing.assert_frame_equal(before,customer_features(changed,cutoff))
    x,y=snapshot(clean,cutoff)
    future=clean[(clean.InvoiceDate>=cutoff)&(clean.InvoiceDate<cutoff+pd.Timedelta(days=30))]
    assert set(y[y==1].index)==set(x.index)&set(future.CustomerID)

def test_persistent_database(tmp_path):
    path=tmp_path/'persist.db'
    c=create_app(path).test_client()
    c.post('/api/auth/signup',headers=H,json={'name':'Test User','email':'test@example.com','password':'password123'})
    c.post('/api/demo',headers=H)
    new=create_app(path).test_client()
    assert new.post('/api/auth/login',headers=H,json={'email':'test@example.com','password':'password123'}).status_code==200
    assert new.get('/api/dashboard').json['orders']>0

def test_date_filter_and_customer_profile(client):
    client.post('/api/demo',headers=H)
    all_data=client.get('/api/dashboard').json
    selected=client.get('/api/dashboard?start=2025-04-01&end=2025-04-30')
    assert selected.status_code==200
    assert selected.json['start']>='2025-04-01'
    assert selected.json['end']<='2025-04-30'
    assert selected.json['revenue']<all_data['revenue']
    assert client.get('/api/dashboard?start=invalid').status_code==400
    assert client.get('/api/dashboard?start=2030-01-01').status_code==400
    customer=client.get('/api/customers').json['rows'][0]
    profile=client.get('/api/customer/'+customer['CustomerID'])
    assert profile.status_code==200
    assert len(profile.json['orders'])>0
    assert abs(profile.json['profile']['monetary']-customer['monetary'])<.01
    assert client.get('/api/customer/missing').status_code==404


def test_auth_and_user_isolation(tmp_path):
    app=create_app(tmp_path/'accounts-test.db')
    a=app.test_client();b=app.test_client()
    assert a.get('/').status_code==200
    assert a.get('/login').status_code==200
    assert a.get('/signup').status_code==200
    assert a.get('/dashboard').status_code==302
    assert a.get('/api/status').status_code==401
    assert a.post('/api/auth/signup',headers=H,json={'name':'Alice','email':'alice@example.com','password':'secret123'}).status_code==200
    assert a.get('/dashboard').status_code==200
    a.post('/api/demo',headers=H)
    assert b.post('/api/auth/signup',headers=H,json={'name':'Bob','email':'bob@example.com','password':'secret456'}).status_code==200
    assert b.get('/api/status').json['dataset'] is None
    assert b.get('/api/dashboard').status_code==400
    assert a.get('/api/dashboard').status_code==200
    a.post('/api/auth/logout',headers=H)
    assert a.get('/api/status').status_code==401
    assert a.post('/api/auth/login',headers=H,json={'email':'alice@example.com','password':'wrongpass'}).status_code==401
    assert a.post('/api/auth/login',headers=H,json={'email':'alice@example.com','password':'secret123'}).status_code==200
    assert a.get('/api/dashboard').status_code==200
