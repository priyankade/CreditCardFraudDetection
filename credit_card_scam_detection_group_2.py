# -*- coding: utf-8 -*-
"""Credit_Card_Scam_Detection_Group_2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1B3-YJj5fduqPj9sxYScrFbqZVm9vCV7j

## **Subject** : Data Analytics and Machine Learning MIS 637
## **Project** : Credit Card Scam Detection








---
"""

# Importing Required Libraries
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
import scipy.stats as stats

from imblearn.under_sampling import RandomUnderSampler
from imblearn.over_sampling import RandomOverSampler
from imblearn.over_sampling import SMOTE

from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC
from sklearn import tree
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB, BernoulliNB, MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier

from sklearn import metrics
from sklearn.model_selection import cross_val_score
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.metrics import precision_score, accuracy_score, f1_score, r2_score
from sklearn.metrics import precision_recall_curve, roc_curve

# Reading CSV File
fraud_test = pd.read_csv('fraudTest.csv')
fraud_train = pd.read_csv('fraudTrain.csv')

fraud_train.head(1)

fraud_test.head(1)

# Concatenating the two datasets
fraud_df = pd.concat([fraud_train, fraud_test]).reset_index()
fraud_df.drop(fraud_df.columns[:2], axis=1, inplace=True)

# Display first 5 rows of data
fraud_df.head()

fraud_df.shape

"""## **Preprocessing**

* Here, we cannot incorporate DOB into our model, so will derive age from the same.
* Similarly, will derive hour, day, month and year form trans_date_trans_time column, because we cannot use date-time object to implement any Machine Learning model.
"""

# Checking datatype of trans_date_trans_time column
print(fraud_df.dtypes['trans_date_trans_time'])

# Converting trans_date_trans_time into datetime
fraud_df['trans_date_trans_time'] = pd.to_datetime(fraud_df['trans_date_trans_time'])
print(fraud_df.dtypes['trans_date_trans_time'])
# fraud_data.head()

# Deriving age from 'dob' column
fraud_df['dob'] = pd.to_datetime(fraud_df['dob'])
fraud_df['age'] = np.round((fraud_df['trans_date_trans_time'] - fraud_df['dob'])/np.timedelta64(1, 'Y'))

# Deriving additonal columns from 'trans_date_trans_time' - hour, day, month-year
fraud_df['trans_hour'] = fraud_df['trans_date_trans_time'].dt.hour
fraud_df['trans_day_of_week'] = fraud_df['trans_date_trans_time'].dt.day_name()
fraud_df['trans_year_month'] = fraud_df['trans_date_trans_time'].dt.to_period('M')

fraud_df.head(2)

# Dropping columns
fraud_df.drop(['trans_date_trans_time', 'dob'] , axis=1, inplace=True)
print(len(fraud_df.columns))
print(fraud_df.columns)
print('------------------------------------------------------------------------------\n')

fraud_df.info()

"""Here, some of the columns' datatype is object and date-time period, which needs to be changed before implementing the models.

## **EDA (Exploratory Data Analysis)**
Now, will explore every features, so we can remove unnecessary data-columns and select only those data-columns which has significance to classify fraudy transactions.
"""

# Describing every column
fraud_df.describe()

# Chechking for missing values
print(fraud_df.isnull().values.any())

# Checking Target/Class variable frequency distribution
print(fraud_df['is_fraud'].value_counts())

# The classes are heavily skewed we need to solve this issue later.
print("No Fraud", round(fraud_df['is_fraud'].value_counts()[0]/len(fraud_df) * 100,2), '% of the dataset')
print("Fraud", round(fraud_df['is_fraud'].value_counts()[1]/len(fraud_df) * 100,2), '% of the dataset\n')

# Plotting Target class data
fig = plt.figure()
fig.set_figwidth(2)
fig.set_figheight(3)

sns.countplot(x = fraud_df['is_fraud'])
plt.title('Class Distributions \n (0: No Fraud || 1: Fraud)')

# Strating EDA from 'amt' column as it holds a lot of significance in credit card fraud analysis
pd.concat([fraud_df['amt'].describe().reset_index().rename(columns={'index': 'Distribution', 'amt':'Overall Distribution'}),
           fraud_df.loc[fraud_df['is_fraud']==0,['amt']].describe().reset_index(drop = 1).rename(columns={'amt':'Non-Fraud Distribution'}),
           fraud_df.loc[fraud_df['is_fraud']==1,['amt']].describe().reset_index(drop = 1).rename(columns={'amt':'Fraud Distribution'})], axis=1)

"""Here, the mean/average of the 'fraud distribution' is way higher than the 'non-fraud distribution'. That means the amount lost in a fraud trnasaction is very high. Which is a usual behaviour looking at the real-life scenarios."""

# Plots to visualize the fraud vs non-fraud amount distribution
fig = plt.figure()
fig.set_figwidth(16)
fig.set_figheight(4)

# Limiting amount at max fraud transaction for better visualization
plt.subplot(1, 3, 1)
plt.hist(fraud_df[fraud_df.amt <= 1400].amt, bins=50, color='blue', edgecolor='black')
plt.title('Overall amt Dist')
plt.xlabel('Transaction Amount')
plt.ylabel('Number of transactions')

plt.subplot(1, 3, 2)
plt.hist(fraud_df[(fraud_df.is_fraud==0) & (fraud_df.amt<=1400)].amt, bins=50, color='green', edgecolor='black')
plt.title('Non Fraud amt Dist')

plt.subplot(1, 3, 3)
plt.hist(fraud_df[(fraud_df.is_fraud==1) & (fraud_df.amt<=1400)].amt, bins=50, color='red', edgecolor='black')
plt.title('Fraud amt Dist')

plt.show()

# Now, exploring time (year_month) vs transactions

df_fraud_transactions = fraud_df[fraud_df['is_fraud']==1]
df_non_fraud_transactions = fraud_df[fraud_df['is_fraud']==0]

df_fraud_time = df_fraud_transactions.groupby(df_fraud_transactions['trans_year_month'])[['trans_num','cc_num']].nunique().reset_index()
df_fraud_time.columns = ['year_month','num_of_transactions','customers']

df_non_fraud_time = df_non_fraud_transactions.groupby(df_non_fraud_transactions['trans_year_month'])[['trans_num','cc_num']].nunique().reset_index()
df_non_fraud_time.columns = ['year_month','num_of_transactions','customers']

fig = plt.figure()
fig.set_figwidth(16)
fig.set_figheight(10)

x1 = np.arange(0,len(df_fraud_time),1)
x0 = np.arange(0,len(df_non_fraud_time),1)

plt.subplot(2, 1, 1)
plt.plot(x1, df_fraud_time['num_of_transactions'], marker='o', color='r', linewidth=1.5, mfc='k')
plt.xticks(x1, df_fraud_time['year_month'], rotation ='vertical')
plt.title('Fraud Transaction Distribution', fontweight='bold')
plt.xlabel('Time (month-year)')
plt.ylabel('Number of transactions')

plt.subplot(2, 1, 2)
plt.plot(x0, df_non_fraud_time['num_of_transactions'], marker='s', linewidth=1.5, mfc='k')
plt.xticks(x0, df_non_fraud_time['year_month'], rotation ='vertical')
plt.title('Non-Fraud Transaction Distribution', fontweight='bold')
plt.xlabel('Time (month-year)')
plt.ylabel('Number of transactions')

plt.tight_layout(pad=2.0)
plt.show()

# Plotting Target class data
fig = plt.figure()
fig.set_figwidth(12)
fig.set_figheight(4)

plt.subplot(1, 3, 1)
sns.countplot(data=fraud_df, x="is_fraud", hue="gender")

plt.subplot(1, 3, 2)
sns.countplot(x = df_fraud_transactions['gender'])

plt.subplot(1, 3, 3)
sns.countplot(x = df_non_fraud_transactions['gender'])

"""Here, it can be seen that female has done more transactions compared to male, but both gender has faced almost equal number of fraud transactions."""

# Now, moving towards age
# Here, age is in continuous having min value 14 and max 96
# So, will categorize it in 3 groups (11-40, 41-70, 71-100)

# for i in range(len(fraud_df.age)):
#   if fraud_df.age[i] <= 40:
#     fraud_df.age[i] = 1.0
#   elif fraud_df.age[i] > 40 and fraud_df.age[i] <= 70:
#     fraud_df.age[i] = 2.0
#   else:
#     fraud_df.age[i] = 3.0

# fraud_df.age.head()

"""This step also covers feature encoding for age, but it takes huge amount of time and processing power to make it happen
<br>So, keeping age feature as it is, will move forward
"""

# EDA for state vs transactions

fig = plt.figure()
fig.set_figwidth(12)
fig.set_figheight(4)

graph = sns.countplot(data=fraud_df, x="state", hue="is_fraud")
graph.set_xticklabels(graph.get_xticklabels(), rotation=90)

plt.show()

None # To skip label objects

"""Looking at the graph most number of transactions are noted in 3 states (PA, TX and NY)."""

# Moving towards category feature
fraud_df.category.value_counts()

# EDA for merchant column
len(fraud_df.merchant.unique())

fraud_df.merchant.value_counts()

"""Here, we have 693 different merchants and looking at the distribution it looks almost the same. In other words is very few variation in the number of transactions among all merchants.

## **Feature Encoding**
"""

# one-hot encoding for category and day of week
category_onehot = pd.get_dummies(fraud_df.category, prefix='category', drop_first=True)
day_of_week_onehot = pd.get_dummies(fraud_df.trans_day_of_week, prefix='day', drop_first=True)

# gender_onehot = pd.get_dummies(fraud_df.gender, prefix='gender', drop_first=True)
# age_onehot = pd.get_dummies(fraud_df.age, prefix='age', drop_first=True)

gender_mapping = {'F': 1.0, 'M': 2.0}
fraud_df['gender'] = fraud_df['gender'].map(gender_mapping)

# Adding encoded columns to dataframne
fraud_data = pd.concat([fraud_df, category_onehot, day_of_week_onehot], axis=1)

# Dropping unnecessary columns due to low significance or having been encoded
fraud_data.drop([ 'cc_num', 'trans_num', 'merchant', 'street', 'city', 'state', 'job', 'first', 'last',
                 'category', 'trans_day_of_week'],axis=1, inplace=True)

print(fraud_data.shape)

fraud_data.head()

# Checking correlations between the columns using heatmap
plt.figure(figsize=(15,10))
sns.heatmap(fraud_data.corr())
plt.show()

"""## **Balancing Data**"""

fraud_data.drop(['zip', 'lat', 'long', 'city_pop', 'unix_time', 'merch_lat', 'merch_long', 'trans_year_month'],
                axis=1, inplace=True)

fraud_data.info()

from google.colab import drive
drive.mount('drive')

fraud_data.to_csv('credit_card_processed_data.csv')
!cp credit_card_processed_data.csv "drive/My Drive/MIS637"

# Now, you can use processed data from the generated csv file and implement models

fraud_data = fraud_data.dropna(subset=['is_fraud'])
# Storing target variable count

non_fraud_count, fraud_count = fraud_data.is_fraud.value_counts()
print(non_fraud_count, fraud_count)

#storing all fraud transactions
fraud_trans = fraud_data[fraud_data['is_fraud'] == 1]
non_fraud_trans = fraud_data[fraud_data['is_fraud'] == 0]

#input-output split
X = fraud_data.drop(['is_fraud'],axis=1)
y = fraud_data.is_fraud

#scaling
scaler = StandardScaler()
X = scaler.fit_transform(X)

# Splitting data into train and test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.3, random_state = 42)

print(X_train.shape)
print(y_train.shape)
print(X_test.shape)
print(y_test.shape)

"""## **Logistic Regression without balancing dataset**"""

# Implementing logistic regression
lr = LogisticRegression(random_state=42)

# Creating model
model = lr.fit(X_train, y_train)
y_train_pred = model.predict(X_train)
print('y_train_pred: ', y_train_pred)

y_test_pred = model.predict(X_test)
print('y_test_pred: ', y_test_pred)

# Evaluating the model
model_name = 'Logistic Regression - Without Balancing'
train_score = model.score(X_train,y_train)
test_score = model.score(X_test,y_test)

acc_score = accuracy_score(y_test,y_test_pred)
f_score = f1_score(y_test, y_test_pred, average='weighted')
precision = precision_score(y_test, y_test_pred)
recall = metrics.recall_score(y_test,y_test_pred)

# Creating a dataframe
model_eval_data = [[model_name, train_score, test_score, acc_score, f_score, precision, recall]]
temp_df = pd.DataFrame(model_eval_data, columns=['Model Name', 'Training Score', 'Testing Score', 'Accuracy',
                                          'F1 Score', 'Precision', 'Recall'])
temp_df

"""## Sampling Data"""

# We have 3 different methods to remove biasness from dataset

# Random under sampling
rus = RandomUnderSampler()
X_rus, y_rus = rus.fit_resample(X, y)
print(y_rus.value_counts())

# Random Oversampling
ros = RandomOverSampler()
X_ros, y_ros = ros.fit_resample(X, y)
print(y_ros.value_counts())

# SMOTE method
smote = SMOTE(sampling_strategy='minority')
X_sm, y_sm = smote.fit_resample(X.astype('float'), y)
print(y_sm.value_counts)

"""We, will be using SMOTE method."""

# Checking Target/Class variable frequency distribution
print(y_sm.value_counts())

# Splitting data into training and testing dataset
X_train_sm, X_test_sm, y_train_sm, y_test_sm = train_test_split(X_sm, y_sm, test_size = 0.3, random_state = 0)

"""## Logistic Regression"""

# Implementing logistic regression
lr = LogisticRegression(random_state=42)

# Creating model
model = lr.fit(X_train_sm, y_train_sm)
y_train_pred = model.predict(X_train_sm)
print('y_train_pred: ', y_train_pred)

y_test_pred = model.predict(X_test_sm)
print('y_test_pred: ', y_test_pred)

#evaluating the model
model_name = 'Logistic Regression - SMOTE'
train_score = model.score(X_train_sm,y_train_sm)
test_score = model.score(X_test_sm,y_test_sm)

acc_score = accuracy_score(y_test_sm, y_test_pred)
f_score = f1_score(y_test_sm, y_test_pred, average='weighted')
precision = precision_score(y_test_sm, y_test_pred)
recall = metrics.recall_score(y_test_sm, y_test_pred)

# Creating a dataframe
model_eval_data = [[model_name, train_score, test_score, acc_score, f_score, precision, recall]]
model_eval_df = pd.DataFrame(model_eval_data, columns=['Model Name', 'Training Score', 'Testing Score', 'Accuracy',
                                          'F1 Score', 'Precision', 'Recall'])
model_eval_df

cm = metrics.confusion_matrix(y_test_sm, y_test_pred)
cm_display = metrics.ConfusionMatrixDisplay(confusion_matrix = cm, display_labels = [False, True])

cm_display.plot()
plt.show()

"""## Gaussian Naive Bayes"""

# Implementing GaussianNB
model = GaussianNB()

model.fit(X_train_sm, y_train_sm)
y_train_pred = model.predict(X_train_sm)
print('y_train_pred: ', y_train_pred)

y_test_pred = model.predict(X_test_sm)
print('y_test_pred: ', y_test_pred)

#evaluating the model
model_name = 'Gaussian Naive Bayes - SMOTE'
train_score = model.score(X_train_sm,y_train_sm)
test_score = model.score(X_test_sm,y_test_sm)

acc_score = accuracy_score(y_test_sm, y_test_pred)
f_score = f1_score(y_test_sm, y_test_pred, average='weighted')
precision = precision_score(y_test_sm, y_test_pred)
recall = metrics.recall_score(y_test_sm, y_test_pred)

#creating a dataframe to compare the performance of different models
model_eval_data = [model_name, train_score, test_score, acc_score, f_score, precision, recall]
model_eval_dict = {model_eval_df.columns[i]:model_eval_data[i] for i in range(len(model_eval_data))}
model_eval_df = model_eval_df.append(model_eval_dict, ignore_index=True)

model_eval_df

cm = metrics.confusion_matrix(y_test_sm, y_test_pred)
cm_display = metrics.ConfusionMatrixDisplay(confusion_matrix = cm, display_labels = [False, True])

cm_display.plot()
plt.show()

"""## Decision Tree"""

# Implementing Decision Tree Classifier
model = tree.DecisionTreeClassifier()

model.fit(X_train_sm, y_train_sm)
y_train_pred = model.predict(X_train_sm)
print('y_train_pred: ', y_train_pred)

y_test_pred = model.predict(X_test_sm)
print('y_test_pred: ', y_test_pred)

#evaluating the model
model_name = 'Decision Tree Classifier - SMOTE'
train_score = model.score(X_train_sm,y_train_sm)
test_score = model.score(X_test_sm,y_test_sm)

acc_score = accuracy_score(y_test_sm, y_test_pred)
f_score = f1_score(y_test_sm, y_test_pred, average='weighted')
precision = precision_score(y_test_sm, y_test_pred)
recall = metrics.recall_score(y_test_sm, y_test_pred)

#creating a dataframe to compare the performance of different models
model_eval_data = [model_name, train_score, test_score, acc_score, f_score, precision, recall]
model_eval_dict = {model_eval_df.columns[i]:model_eval_data[i] for i in range(len(model_eval_data))}
model_eval_df = model_eval_df.append(model_eval_dict, ignore_index=True)

model_eval_df

cm = metrics.confusion_matrix(y_test_sm, y_test_pred)
cm_display = metrics.ConfusionMatrixDisplay(confusion_matrix = cm, display_labels = [False, True])

cm_display.plot()
plt.show()

"""## Random Forest Classifier"""

# Implementing Random Forest Classifier
model = RandomForestClassifier()

model.fit(X_train_sm, y_train_sm)
y_train_pred = model.predict(X_train_sm)
print('y_train_pred: ', y_train_pred)

y_test_pred = model.predict(X_test_sm)
print('y_test_pred: ', y_test_pred)

#evaluating the model
model_name = 'Random Forest Classifier - SMOTE'
train_score = model.score(X_train_sm,y_train_sm)
test_score = model.score(X_test_sm,y_test_sm)

acc_score = accuracy_score(y_test_sm, y_test_pred)
f_score = f1_score(y_test_sm, y_test_pred, average='weighted')
precision = precision_score(y_test_sm, y_test_pred)
recall = metrics.recall_score(y_test_sm, y_test_pred)

#creating a dataframe to compare the performance of different models
model_eval_data = [model_name, train_score, test_score, acc_score, f_score, precision, recall]
model_eval_dict = {model_eval_df.columns[i]:model_eval_data[i] for i in range(len(model_eval_data))}
model_eval_df = model_eval_df.append(model_eval_dict, ignore_index=True)

model_eval_df

cm = metrics.confusion_matrix(y_test_sm, y_test_pred)
cm_display = metrics.ConfusionMatrixDisplay(confusion_matrix = cm, display_labels = [False, True])

cm_display.plot()
plt.show()

fig, axes = plt.subplots(nrows = 1,ncols = 1,figsize = (4,5), dpi=200)
rm_tree = tree.plot_tree(model.estimators_[0], filled=True)

"""## KNN"""

# Splitting data into training and testing dataset
X_train_rus, X_test_rus, y_train_rus, y_test_rus = train_test_split(X_rus, y_rus, test_size = 0.3, random_state = 0)

# No of nearest neighbores (KNN)
n = 3

# Creating instance of classifier
model = KNeighborsClassifier(n)

model.fit(X_train_rus, y_train_rus)
y_train_pred = model.predict(X_train_rus)
print('y_train_pred: ', y_train_pred)

y_test_pred = model.predict(X_test_rus)
print('y_test_pred: ', y_test_pred)

#evaluating the model
model_name = 'KNN - RUS'
train_score = model.score(X_train_rus,y_train_rus)
test_score = model.score(X_test_rus,y_test_rus)

acc_score = accuracy_score(y_test_rus, y_test_pred)
f_score = f1_score(y_test_rus, y_test_pred, average='weighted')
precision = precision_score(y_test_rus, y_test_pred)
recall = metrics.recall_score(y_test_rus, y_test_pred)

#creating a dataframe to compare the performance of different models
model_eval_data = [model_name, train_score, test_score, acc_score, f_score, precision, recall]

# Creating a dataframe
model_eval_data = [[model_name, train_score, test_score, acc_score, f_score, precision, recall]]
model_eval_rus_df = pd.DataFrame(model_eval_data, columns=['Model Name', 'Training Score', 'Testing Score', 'Accuracy',
                                          'F1 Score', 'Precision', 'Recall'])
model_eval_rus_df

cm = metrics.confusion_matrix(y_test_rus, y_test_pred)
cm_display = metrics.ConfusionMatrixDisplay(confusion_matrix = cm, display_labels = [False, True])

cm_display.plot()
plt.show()

"""## Support Vector Machine"""

# Implementing SVC
model = SVC()

model.fit(X_train_rus, y_train_rus)
y_train_pred = model.predict(X_train_rus)
print('y_train_pred: ', y_train_pred)

y_test_pred = model.predict(X_test_rus)
print('y_test_pred: ', y_test_pred)

#evaluating the model
model_name = 'SVM - RUS'
train_score = model.score(X_train_rus,y_train_rus)
test_score = model.score(X_test_rus,y_test_rus)

acc_score = accuracy_score(y_test_rus, y_test_pred)
f_score = f1_score(y_test_rus, y_test_pred, average='weighted')
precision = precision_score(y_test_rus, y_test_pred)
recall = metrics.recall_score(y_test_rus, y_test_pred)

#creating a dataframe to compare the performance of different models
model_eval_data = [model_name, train_score, test_score, acc_score, f_score, precision, recall]
model_eval_dict = {model_eval_rus_df.columns[i]:model_eval_data[i] for i in range(len(model_eval_data))}
model_eval_rus_df = model_eval_rus_df.append(model_eval_dict, ignore_index=True)

model_eval_rus_df

cm = metrics.confusion_matrix(y_test_rus, y_test_pred)
cm_display = metrics.ConfusionMatrixDisplay(confusion_matrix = cm, display_labels = [False, True])

cm_display.plot()
plt.show()
