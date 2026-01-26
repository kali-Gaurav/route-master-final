import pandas as pd

df = pd.read_csv('dataset/train_info.csv')
train_no_col = 'Train_No'

print('Sample data:')
print(df[[train_no_col, 'days']].head(10))
print(f'\nTrain_No dtype: {df[train_no_col].dtype}')
print(f'days dtype: {df["days"].dtype}')
print(f'\nSample days values:')
for i in range(5):
    print(f'  Train {df[train_no_col].iloc[i]}: "{df["days"].iloc[i]}"')

# Check if any nulls
print(f'\nNull values in days: {df["days"].isna().sum()}')
