import pandas as pd
import numpy as np
import logging
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import ta

logger = logging.getLogger(__name__)

class OpeningPricePredictor:
    """
    V59: ML-based Opening Price Predictor
    Predicts next session's opening price using historical patterns.
    """
    
    def __init__(self):
        self.model = None
        self.feature_names = []
        
    def engineer_features(self, df):
        """
        Create features for ML model from historical data.
        Returns: DataFrame with engineered features.
        """
        try:
            # Ensure we have enough data
            if len(df) < 50:
                return None
                
            features = pd.DataFrame(index=df.index)
            
            # 1. Previous Close (baseline)
            features['prev_close'] = df['Close'].shift(1)
            
            # 2. Volume Ratio (current vol / 20-day avg)
            avg_vol = df['Volume'].rolling(20).mean()
            features['vol_ratio'] = df['Volume'] / avg_vol
            
            # 3. RSI (momentum indicator)
            features['rsi'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
            
            # 4. MA Position (Close vs MA20 and MA50)
            ma20 = df['Close'].rolling(20).mean()
            ma50 = df['Close'].rolling(50).mean()
            features['close_vs_ma20'] = (df['Close'] - ma20) / ma20 * 100
            features['close_vs_ma50'] = (df['Close'] - ma50) / ma50 * 100
            
            # 5. Historical Gap Behavior (avg gap over last 20 days)
            gaps = ((df['Open'] - df['Close'].shift(1)) / df['Close'].shift(1)) * 100
            features['avg_gap_20d'] = gaps.rolling(20).mean()
            
            # 6. Momentum Score (Close vs Open yesterday)
            features['prev_momentum'] = ((df['Close'].shift(1) - df['Open'].shift(1)) / df['Open'].shift(1)) * 100
            
            # 7. Price Change (yesterday's change %)
            features['prev_change'] = ((df['Close'].shift(1) - df['Close'].shift(2)) / df['Close'].shift(2)) * 100
            
            # 8. Volatility (20-day std of returns)
            returns = df['Close'].pct_change()
            features['volatility'] = returns.rolling(20).std() * 100
            
            # Target: Next day's Open
            features['target_open'] = df['Open']
            
            # Drop NaN rows
            features = features.dropna()
            
            return features
            
        except Exception as e:
            logger.error(f"Feature engineering error: {e}")
            return None
    
    def train_model(self, df, model_type='linear'):
        """
        Train ML model on historical data.
        model_type: 'linear' or 'forest'
        """
        try:
            # Engineer features
            features_df = self.engineer_features(df)
            if features_df is None or len(features_df) < 30:
                return None
                
            # Separate features and target
            X = features_df.drop('target_open', axis=1)
            y = features_df['target_open']
            
            # Store feature names
            self.feature_names = X.columns.tolist()
            
            # Train-test split
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
            
            # Train model
            if model_type == 'forest':
                self.model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
            else:
                self.model = LinearRegression()
                
            self.model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Calculate confidence (based on R2 score)
            confidence = min(max(r2 * 100, 0), 100)
            
            return {
                'mae': mae,
                'r2': r2,
                'confidence': confidence,
                'test_samples': len(y_test)
            }
            
        except Exception as e:
            logger.error(f"Model training error: {e}")
            return None
    
    def predict_opening_price(self, df):
        """
        Predict next session's opening price.
        Returns: dict with prediction, gap, confidence, and reasoning.
        """
        try:
            if self.model is None:
                # Train model first
                train_stats = self.train_model(df)
                if train_stats is None:
                    return None
                    
            # Engineer features for latest data point
            features_df = self.engineer_features(df)
            if features_df is None or len(features_df) == 0:
                return None
                
            # Get latest features (excluding target)
            latest_features = features_df.drop('target_open', axis=1).iloc[-1:][self.feature_names]
            
            # Predict
            predicted_open = self.model.predict(latest_features)[0]
            
            # Calculate gap
            last_close = df['Close'].iloc[-1]
            gap_pct = ((predicted_open - last_close) / last_close) * 100
            
            # Get feature values for reasoning
            latest_vals = latest_features.iloc[0]
            
            # Generate reasoning
            reasoning = self._generate_reasoning(latest_vals, gap_pct)
            
            # Confidence (from model R2 score, or default)
            confidence = 70  # Default conservative confidence
            
            return {
                'predicted_open': predicted_open,
                'last_close': last_close,
                'gap_pct': gap_pct,
                'confidence': confidence,
                'reasoning': reasoning
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None
    
    def _generate_reasoning(self, features, gap_pct):
        """
        Generate human-readable reasoning for the prediction.
        """
        reasons = []
        
        # Check momentum
        if features['prev_momentum'] > 1:
            reasons.append("Momentum kuat kemarin (Close > Open)")
        elif features['prev_momentum'] < -1:
            reasons.append("Momentum lemah kemarin (Close < Open)")
            
        # Check RSI
        if features['rsi'] > 70:
            reasons.append("RSI Overbought (>70)")
        elif features['rsi'] < 30:
            reasons.append("RSI Oversold (<30)")
            
        # Check MA position
        if features['close_vs_ma20'] > 2:
            reasons.append("Harga di atas MA20 (Uptrend)")
        elif features['close_vs_ma20'] < -2:
            reasons.append("Harga di bawah MA20 (Downtrend)")
            
        # Check historical gap pattern
        if features['avg_gap_20d'] > 0.5:
            reasons.append("Historical pattern: Gap Up")
        elif features['avg_gap_20d'] < -0.5:
            reasons.append("Historical pattern: Gap Down")
            
        # Check volume
        if features['vol_ratio'] > 1.5:
            reasons.append("Volume tinggi (Akumulasi)")
            
        if not reasons:
            reasons.append("Prediksi berdasarkan historical pattern")
            
        return " + ".join(reasons[:3])  # Max 3 reasons

def predict_opening_price(ticker, period="6mo"):
    """
    Main function to predict opening price for a ticker.
    """
    from data_fetcher import get_historical_data
    
    try:
        # Fetch historical data
        df = get_historical_data(ticker, period=period)
        if df.empty or len(df) < 50:
            return None
            
        # Create predictor and predict
        predictor = OpeningPricePredictor()
        result = predictor.predict_opening_price(df)
        
        if result:
            result['ticker'] = ticker
            
        return result
        
    except Exception as e:
        logger.error(f"Opening price prediction failed for {ticker}: {e}")
        return None
