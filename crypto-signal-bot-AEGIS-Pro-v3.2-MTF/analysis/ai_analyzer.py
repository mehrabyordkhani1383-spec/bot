"""
🤖 AI/ML Prediction Engine - پیش‌بینی با هوش مصنوعی
Random Forest + Gradient Boosting + Rule-based Fallback
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")
from loguru import logger

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib


class AIAnalyzer:
    def __init__(self, model_dir: str = "data/models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.rf_model = None
        self.gb_model = None
        self.scaler = StandardScaler()
        self._load_models()

    def _load_models(self):
        for name in ["random_forest.pkl", "gradient_boosting.pkl", "scaler.pkl"]:
            p = self.model_dir / name
            if p.exists():
                obj = joblib.load(p)
                if "random_forest" in name: self.rf_model = obj
                elif "gradient_boosting" in name: self.gb_model = obj
                else: self.scaler = obj

    def _save_models(self):
        if self.rf_model: joblib.dump(self.rf_model, self.model_dir / "random_forest.pkl")
        if self.gb_model: joblib.dump(self.gb_model, self.model_dir / "gradient_boosting.pkl")
        joblib.dump(self.scaler, self.model_dir / "scaler.pkl")
        logger.info("💾 Models saved!")

    def _rsi(self, prices, period=14):
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _extract_features(self, df):
        """استخراج ۳۶ ویژگی با مدیریت صحیح NaN (min_periods=2)"""
        df = df.copy()
        f = pd.DataFrame(index=df.index)
        
        f["close"] = df["close"]
        f["high_low"] = df["high"] / df["low"]
        f["close_open"] = df["close"] / df["open"]
        
        # Returns
        for p in [1, 3, 5, 10, 20]:
            f[f"ret_{p}"] = df["close"].pct_change(p)
        
        # Volatility - با min_periods=2 که همه NaN نباشه
        for p in [3, 5, 10, 20]:
            f[f"vol_{p}"] = df["close"].pct_change().rolling(p, min_periods=2).std()
        
        # Moving averages
        for p in [5, 10, 20, 50]:
            ma = df["close"].rolling(p, min_periods=2).mean()
            f[f"ma_{p}"] = ma
            f[f"c_ma_{p}"] = df["close"] / ma
        
        # RSI
        f["rsi_14"] = self._rsi(df["close"], 14)
        f["rsi_7"] = self._rsi(df["close"], 7)
        
        # Volume
        f["vol_ma5"] = df["volume"].rolling(5, min_periods=2).mean()
        f["vol_ratio"] = df["volume"] / f["vol_ma5"].replace(0, np.nan)
        
        # Price position
        for p in [10, 20, 50]:
            h = df["high"].rolling(p).max()
            l = df["low"].rolling(p).min()
            denom = (h - l).replace(0, np.nan)
            f[f"pos_{p}"] = (df["close"] - l) / denom
        
        # ATR
        tr = pd.concat([
            df["high"]-df["low"],
            (df["high"]-df["close"].shift()).abs(),
            (df["low"]-df["close"].shift()).abs()
        ], axis=1).max(axis=1)
        f["atr"] = tr.rolling(14, min_periods=2).mean()
        f["atr_pct"] = f["atr"] / df["close"]
        
        # Momentum
        f["mom_5"] = df["close"] - df["close"].shift(5)
        f["mom_10"] = df["close"] - df["close"].shift(10)
        f["roc"] = df["close"].pct_change(10)
        
        # Gap
        pc = df["close"].shift(1).replace(0, np.nan)
        f["gap"] = (df["open"] - df["close"].shift(1)) / pc
        
        # Williams %R
        h14 = df["high"].rolling(14).max()
        l14 = df["low"].rolling(14).min()
        dw = (h14 - l14).replace(0, np.nan)
        f["williams_r"] = -100 * (h14 - df["close"]) / dw
        
        # ================ CRITICAL: Fill NaN ================
        f = f.bfill().ffill()
        f = f.replace([np.inf, -np.inf], np.nan).bfill().ffill()
        
        return f

    def _prepare_training_data(self, df, horizon=5):
        features = self._extract_features(df)
        fp = df["close"].shift(-horizon)
        y = (fp > df["close"]).astype(int)
        
        # Drop all-NaN columns
        features = features.dropna(axis=1, how='all')
        
        # Drop target NaN
        mask = ~y.isna()
        X = features[mask].values
        y = y[mask].values
        
        # Drop rows with any NaN
        valid = ~np.isnan(X).any(axis=1)
        X = X[valid]
        y = y[valid]
        X = np.where(np.isinf(X), 0, X)
        
        return X, y

    def train(self, df, horizon=5):
        logger.info("🧠 Training AI models...")
        X, y = self._prepare_training_data(df, horizon)
        
        if len(X) < 100:
            logger.warning(f"⚠️ Only {len(X)} samples available (need 100+)")
            return {"error": f"insufficient_data: {len(X)} samples"}
        
        logger.info(f"📊 Training: {len(X)} samples, {X.shape[1]} features")
        
        X_scaled = self.scaler.fit_transform(X)
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, shuffle=False
        )
        
        results = {}
        
        # Random Forest
        self.rf_model = RandomForestClassifier(
            n_estimators=200, max_depth=10, min_samples_split=10,
            min_samples_leaf=5, random_state=42, n_jobs=-1
        )
        self.rf_model.fit(X_train, y_train)
        pred = self.rf_model.predict(X_test)
        results["random_forest"] = {
            "accuracy": accuracy_score(y_test, pred),
            "precision": precision_score(y_test, pred, zero_division=0),
            "recall": recall_score(y_test, pred, zero_division=0),
            "f1": f1_score(y_test, pred, zero_division=0),
        }
        
        # Gradient Boosting
        self.gb_model = GradientBoostingClassifier(
            n_estimators=150, max_depth=6, learning_rate=0.1,
            min_samples_leaf=5, random_state=42
        )
        self.gb_model.fit(X_train, y_train)
        pred = self.gb_model.predict(X_test)
        results["gradient_boosting"] = {
            "accuracy": accuracy_score(y_test, pred),
            "precision": precision_score(y_test, pred, zero_division=0),
            "recall": recall_score(y_test, pred, zero_division=0),
            "f1": f1_score(y_test, pred, zero_division=0),
        }
        
        self._save_models()
        logger.success(f"✅ Training done! RF Acc: {results['random_forest']['accuracy']:.2%}")
        return results

    def predict(self, df):
        if self.rf_model is None and self.gb_model is None:
            return self._rule_based(df)
        try:
            features = self._extract_features(df)
            latest = features.iloc[-1:].fillna(0).values
            X = self.scaler.transform(latest)
            probs, preds = [], []
            if self.rf_model:
                p = self.rf_model.predict_proba(X)[0]
                if len(p) > 1: probs.append(p[1]); preds.append(self.rf_model.predict(X)[0])
            if self.gb_model:
                p = self.gb_model.predict_proba(X)[0]
                if len(p) > 1: probs.append(p[1]); preds.append(self.gb_model.predict(X)[0])
            if probs:
                avg_p = float(np.mean(probs))
                conf = avg_p * 100
                dir_ = "UP" if (np.mean(preds) > 0.5) else "DOWN"
                strength = "VERY_STRONG" if conf > 80 else "STRONG" if conf > 65 else "MODERATE" if conf > 50 else "WEAK"
                return {"direction": dir_, "probability": round(conf, 1), "strength": strength,
                        "model_count": len(probs), "type": "ml_prediction"}
        except Exception as e:
            logger.error(f"❌ AI predict error: {e}")
        return self._rule_based(df)

    def _rule_based(self, df):
        if df is None or len(df) < 20:
            return {"direction": "NEUTRAL", "probability": 50, "strength": "WEAK", "type": "fallback"}
        c = df["close"]
        s20 = c.rolling(20).mean()
        s50 = c.rolling(50).mean() if len(c) >= 50 else s20
        trend = float(c.iloc[-1] - c.iloc[-10])
        ma = bool(c.iloc[-1] > s20.iloc[-1] and s20.iloc[-1] > s50.iloc[-1])
        rsi = float(self._rsi(c, 14).iloc[-1]) if not pd.isna(self._rsi(c, 14).iloc[-1]) else 50
        score = (20 if trend > 0 else -20) + (15 if ma else -15)
        if rsi < 30: score += 20
        elif rsi > 70: score -= 20
        elif 40 < rsi < 60: score += 5
        ns = max(0, min(100, (score + 55) / 110 * 100))
        return {"direction": "UP" if ns > 55 else "DOWN", "probability": round(ns, 1),
                "strength": "STRONG" if abs(ns-50) > 30 else "MODERATE" if abs(ns-50) > 15 else "WEAK",
                "rsi": round(rsi, 1), "type": "rule_based"}

    def predict_with_confidence(self, df):
        r = self.predict(df)
        return r.get("direction", "NEUTRAL"), r.get("probability", 50), \
               f"AI: {r.get('probability', 50)}% | {r.get('strength', 'WEAK')} | {r.get('type', 'unknown')}"
