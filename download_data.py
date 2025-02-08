import pandas as pd
import numpy as np

def read_data (transactions_file="transactions.csv", users_file="users.csv"):
    ts = pd.read_csv(transactions_file)
    us = pd.read_csv(users_file)

    transactions = ts.to_numpy()
    transactions = transactions[transactions[:, 0] != transactions[:, 1], :] # Removes self-sells

    unique_pairs, inverse_idx = np.unique(transactions[:, :2].astype("str"), axis=0, return_inverse=True)
    sums=np.zeros(shape=(unique_pairs.shape[0],))
    np.add.at(sums, inverse_idx, transactions[:, 2])

    transactions = np.column_stack([unique_pairs, sums])
    
    users = us[["name", "role"]].to_numpy()
    return (transactions, users)

