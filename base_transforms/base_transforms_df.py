import os
import uuid
import pandas as pd


class BaseTransformDF:
	"""create base dataframes: portfolio_expanded, transactions, offer_completed, offer_viewed, offer_received"""

	@classmethod
	def portfolio_expanded(cls, df) -> pd.DataFrame:
	    df_portfolio = df.copy()
	    
	    # add new features to portfolio dataframe
	    df_portfolio['num_channels'] = df_portfolio['channels'].apply(lambda x: len(x))
	    df_portfolio['duration'] = df_portfolio['duration'] * 24
	    df_portfolio.rename(columns={'id': 'offer_id'}, inplace=True)

	    channel_list = ['ch_web', 'ch_email', 'ch_mobile', 'ch_social']
	    for _ch in channel_list:
	        channel = _ch.replace('ch_','') 
	        df_portfolio[_ch] = df_portfolio['channels'].apply(lambda x: 1 if channel in x else 0)

	    type_list = ['type_' + offer_type for offer_type in df_portfolio['offer_type'].unique()]
	    for _type in type_list:
	        offer_type = _type.replace('type_','')
	        df_portfolio[_type] = df_portfolio['offer_type'].apply(lambda x: 1 if x==offer_type else 0)
	    
	    return df_portfolio

	@classmethod
	def create_transcript_copy(cls, df) -> pd.DataFrame:
		# make copy of transcript
		df_copy = df.copy()
		# flatten JSON and extract value 
		df_copy['value_flat'] = df_copy['value'].apply(lambda x: list(x.items())[0][1])
		# rename and drop columns
		df_copy = df_copy.rename(columns={'person': 'customer_id'}).drop(columns=['value'])
		 
		return df_copy

	@classmethod
	def create_df_transactions(cls, df_transcript) -> pd.DataFrame:
		rename_columns={'time':'transaction_time', 'value_flat':'transaction_amount'}

		# create dataframe with only transaction events
		df_transactions = df_transcript[df_transcript['event']=='transaction'].rename(columns=rename_columns)

		# convert transaction_amount into float
		df_transactions['transaction_amount'] = df_transactions['transaction_amount'].apply(lambda x: float(x))

		# create transaction_id's and drop event column 
		transaction_ids = []
		n = len(df_transactions)
		for _ in range(n):
		    _id = uuid.uuid4().hex
		    transaction_ids.append(_id)

		# add transaction_id as first column in df_transactions
		df_transactions.insert(loc=0, column='transaction_id', value=transaction_ids)
		df_transactions.drop(columns=['event'], inplace=True)

		return df_transactions

	@classmethod
	def create_df_base_completed(cls, df_transcript) -> pd.DataFrame:
		rename_columns={'time':'offer_completed_time', 'value_flat':'offer_id'}
		df_completed = df_transcript[df_transcript['event']=='offer completed'].rename(columns=rename_columns)
		# create new column as second column location with all values 1
		df_completed.insert(loc=1, column='offer_completed', value=1)
		df_completed.drop(columns=['event'], inplace=True)
		
		return df_completed

	@classmethod
	def create_df_base_received(cls, df_transcript) -> pd.DataFrame:
		rename_columns = {'event': 'offer_received', 'value_flat': 'offer_id', 'time': 'offer_received_time'}
		df_received = df_transcript[df_transcript['event']=='offer received'].rename(columns=rename_columns)
		df_received['offer_received'] = df_received['offer_received'].apply(lambda x: 1 if not pd.isnull(x) else 0)
		
		return df_received

	@classmethod
	def create_df_base_viewed(cls, df_transcript) -> pd.DataFrame:
		rename_columns = {'event': 'offer_viewed', 'value_flat': 'offer_id', 'time': 'offer_viewed_time'}
		df_viewed = df_transcript[df_transcript['event']=='offer viewed'].rename(columns=rename_columns)
		df_viewed['offer_viewed'] = df_viewed['offer_viewed'].apply(lambda x: 1 if not pd.isnull(x) else 0)
		
		return df_viewed
