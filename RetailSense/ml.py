"""Out-of-time repeat-purchase evaluation with non-overlapping label windows."""
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss
from sklearn.base import clone
from analytics import customer_features

FEATURES = ['recency','frequency','monetary','tenure','average_order','orders_30d']


def snapshot(df, cutoff):
    x = customer_features(df, cutoff)
    future = df[(df.InvoiceDate >= cutoff) & (df.InvoiceDate < cutoff + pd.Timedelta(days=30))]
    y = pd.Series(x.index.isin(future.CustomerID.unique()).astype(int), index=x.index)
    return x, y


def metrics(model, x, y):
    p = model.predict_proba(x)[:, list(model.classes_).index(1)]
    pred = (p >= .5).astype(int)
    return dict(precision=round(float(precision_score(y,pred,zero_division=0)),4), recall=round(float(recall_score(y,pred,zero_division=0)),4), f1=round(float(f1_score(y,pred,zero_division=0)),4), roc_auc=round(float(roc_auc_score(y,p)),4), brier=round(float(brier_score_loss(y,p)),4))


def train(df):
    end = df.InvoiceDate.max().normalize() + pd.Timedelta(days=1)
    if (end - df.InvoiceDate.min()).days < 180:
        raise ValueError('Training needs at least 180 days of transaction history.')
    cutoffs = [end - pd.Timedelta(days=d) for d in [90,60,30]]
    splits = [snapshot(df,c) for c in cutoffs]
    for x,y in splits:
        if len(x) < 30 or y.nunique() != 2 or y.value_counts().min() < 5:
            raise ValueError('Each time window needs 30+ customers and at least 5 repeat and 5 non-repeat purchasers.')
    (xt,yt),(xv,yv),(xe,ye) = splits
    candidates = {'Logistic Regression': make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,random_state=42)), 'Random Forest': RandomForestClassifier(n_estimators=120,max_depth=6,min_samples_leaf=5,random_state=42,n_jobs=1)}
    validation = {}
    for name,model in candidates.items():
        model.fit(xt,yt)
        validation[name] = metrics(model,xv,yv)
    winner = max(validation,key=lambda n:validation[n]['f1'])
    # Select only on validation. Refit using observed labels before test cutoff.
    evaluated = clone(candidates[winner]).fit(pd.concat([xt,xv]),pd.concat([yt,yv]))
    baseline = DummyClassifier(strategy='prior').fit(xt,yt)
    report = dict(selected_model=winner, validation=validation, test=metrics(evaluated,xe,ye), baseline=metrics(baseline,xe,ye), threshold=.5, train_cutoff=str(cutoffs[0].date()), validation_cutoff=str(cutoffs[1].date()), test_cutoff=str(cutoffs[2].date()), as_of=str(end.date()), train_customers=len(xt), validation_customers=len(xv), test_customers=len(xe), test_positive_rate=round(float(ye.mean()),4), features=FEATURES, note='Historical out-of-time evaluation; not a guarantee of future performance. Final scoring model is refit on all three labelled windows. Probabilities are uncalibrated estimates.')
    final = clone(candidates[winner]).fit(pd.concat([x for x,y in splits]),pd.concat([y for x,y in splits]))
    current = customer_features(df,end)
    p = final.predict_proba(current)[:, list(final.classes_).index(1)]
    scores = pd.DataFrame({'CustomerID':current.index,'probability':np.round(p,4)})
    return report, scores
