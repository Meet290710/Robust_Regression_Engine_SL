import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

st.set_page_config(page_title="Robust Regression Engine", page_icon="🏠", layout="wide")
st.title("Robust Regression Engine")
st.caption("Advanced House Price Prediction")

@st.cache_data
def prepare(path):
    df = pd.read_excel(path)
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df["sale_year"] = df["sale_date"].dt.year
    df["sale_month"] = df["sale_date"].dt.month
    df["sale_quarter"] = df["sale_date"].dt.quarter
    return df.drop(columns=["property_id", "sale_date"])

@st.cache_resource
def train(df):
    X = df.drop(columns="house_price_inr")
    y = df["house_price_inr"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.20, random_state=42)
    models = {}

    def grid(model, params):
        g = GridSearchCV(model, params, cv=5, scoring="neg_mean_squared_error", n_jobs=-1)
        g.fit(Xtr, ytr)
        return g.best_estimator_

    models["Ridge Regression"] = grid(
        Pipeline([("scaler", StandardScaler()), ("model", Ridge())]),
        {"model__alpha":[.01,.1,1,10,100,1000]})

    models["Lasso Regression"] = grid(
        Pipeline([("scaler", StandardScaler()), ("model", Lasso(max_iter=20000))]),
        {"model__alpha":[.01,.1,1,10,100,1000]})

    models["Decision Tree"] = grid(
        DecisionTreeRegressor(random_state=42),
        {"max_depth":[3,5,8,10,15,None],
         "min_samples_split":[2,5,10],
         "min_samples_leaf":[1,2,5]})

    models["Random Forest"] = grid(
        RandomForestRegressor(random_state=42, n_jobs=-1),
        {"n_estimators":[100,200],"max_depth":[None,10,20],
         "min_samples_split":[2,5],"min_samples_leaf":[1,2]})

    models["RBF SVR"] = grid(
        Pipeline([("scaler", StandardScaler()), ("svr", SVR(kernel="rbf"))]),
        {"svr__C":[1,10,100],"svr__gamma":["scale",.01,.1],
         "svr__epsilon":[.01,.1,.5]})

    rows, preds = [], {}
    for name, model in models.items():
        p = model.predict(Xte)
        preds[name] = p
        mse = mean_squared_error(yte,p)
        rows.append([name,mean_absolute_error(yte,p),mse,np.sqrt(mse),r2_score(yte,p)])
    results = pd.DataFrame(rows, columns=["Model","MAE","MSE","RMSE","R2"]).sort_values("RMSE").reset_index(drop=True)
    return X,y,Xtr,Xte,ytr,yte,models,preds,results

uploaded = st.file_uploader("Upload Advanced_Regression_HousePrice_Dataset_3800.xlsx", type="xlsx")
if uploaded:
    path = "house_price_dataset.xlsx"
    with open(path,"wb") as f: f.write(uploaded.getbuffer())
    df = prepare(path)
    X,y,Xtr,Xte,ytr,yte,models,preds,results = train(df)

    st.success("Dataset loaded and models trained successfully.")
    t1,t2,t3,t4 = st.tabs(["Overview","Model Comparison","Prediction","Feature Importance"])

    with t1:
        a,b,c = st.columns(3)
        a.metric("Records", f"{len(df):,}")
        b.metric("Features", X.shape[1])
        c.metric("Target", "house_price_inr")
        st.subheader("Dataset Preview")
        st.dataframe(df.head(10), use_container_width=True)
        fig,ax=plt.subplots(figsize=(9,4))
        ax.hist(df["house_price_inr"],bins=40)
        ax.set_title("Distribution of House Prices")
        ax.set_xlabel("House Price (INR)")
        ax.set_ylabel("Frequency")
        st.pyplot(fig)

    with t2:
        st.subheader("Model Evaluation")
        st.dataframe(results.style.format({"MAE":"{:,.2f}","MSE":"{:,.2f}","RMSE":"{:,.2f}","R2":"{:.4f}"}),use_container_width=True)
        fig,ax=plt.subplots(figsize=(10,5))
        ax.bar(results["Model"],results["RMSE"])
        ax.set_title("Model Comparison - RMSE")
        ax.set_ylabel("RMSE")
        ax.tick_params(axis="x",rotation=30)
        st.pyplot(fig)
        fig,ax=plt.subplots(figsize=(10,5))
        ax.bar(results["Model"],results["R2"])
        ax.set_title("Model Comparison - R²")
        ax.set_ylabel("R² Score")
        ax.tick_params(axis="x",rotation=30)
        st.pyplot(fig)

    with t3:
        model_name=st.selectbox("Select Model",list(models))
        vals={}
        for col in X.columns:
            vals[col]=st.number_input(col,value=float(X[col].median()))
        if st.button("Predict House Price"):
            pred=models[model_name].predict(pd.DataFrame([vals]))[0]
            st.success(f"Predicted House Price: ₹{pred:,.2f}")

    with t4:
        rf=models["Random Forest"]
        imp=pd.DataFrame({"Feature":X.columns,"Importance":rf.feature_importances_}).sort_values("Importance",ascending=False)
        st.dataframe(imp,use_container_width=True)
        fig,ax=plt.subplots(figsize=(9,6))
        ax.barh(imp["Feature"],imp["Importance"])
        ax.invert_yaxis()
        ax.set_title("Random Forest Feature Importance")
        st.pyplot(fig)
else:
    st.info("Upload the Excel dataset to start the application.")
