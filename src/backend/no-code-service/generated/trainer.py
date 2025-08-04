"""Auto-generated training script."""

# Imports
import pandas as pd
import numpy as np
import talib as ta
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# Data Loading
data_dataSource_1754015711485 = pd.DataFrame()  # TODO load AAPL (1h)

# Feature Generation
data_dataSource_1754015711485['feature_technicalIndicator_1754015735164'] = ta.ADX(data_dataSource_1754015711485['close'], timeperiod=14)
data_dataSource_1754015711485['feature_technicalIndicator_1754015793751'] = ta.SMA(data_dataSource_1754015711485['close'], timeperiod=14)
data_dataSource_1754015711485['feature_technicalIndicator_1754028721500'] = ta.BB(data_dataSource_1754015711485['close'], timeperiod=20)
data_dataSource_1754015711485['feature_technicalIndicator_1754028825908'] = ta.SMA(data_dataSource_1754015711485['close'], timeperiod=20)

# Label Generation
data_technicalIndicator_1754015735164['target_condition_1754015842942'] = (data_technicalIndicator_1754015735164['feature_technicalIndicator_1754015735164'] > 0).astype(int)
data_technicalIndicator_1754028721500['target_condition_1754028183612'] = (data_technicalIndicator_1754028721500['feature_technicalIndicator_1754028721500'] > 0).astype(int)
data_technicalIndicator_1754028825908['target_condition_1754028865441'] = (data_technicalIndicator_1754028825908['feature_technicalIndicator_1754028825908'] > 0).astype(int)
data_technicalIndicator_1754028721500['target_condition_1754032689855'] = (data_technicalIndicator_1754028721500['feature_technicalIndicator_1754028721500'] > 0).astype(int)
data_technicalIndicator_1754028825908['target_condition_1754032770400'] = (data_technicalIndicator_1754028825908['feature_technicalIndicator_1754028825908'] > 0).astype(int)

# Model Training
feature_cols = ['feature_technicalIndicator_1754015735164', 'feature_technicalIndicator_1754015793751', 'feature_technicalIndicator_1754028721500', 'feature_technicalIndicator_1754028825908']
label_col = 'target_condition_1754015842942'
df = data_dataSource_1754015711485
X = df[feature_cols]
y = df[label_col]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Evaluation
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# Model Persistence
joblib.dump(model, 'trained_model.joblib')
