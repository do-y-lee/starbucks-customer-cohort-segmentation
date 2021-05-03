import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from base_transforms import BaseTransformDF


if __name__ == '__main__':
    start_time = datetime.now()

    # read in raw tranascript data
    transcript = pd.read_json('data/transcript.json', orient='records', lines=True)

    # build all base dataframes - execute functions
    df_base = BaseTransformDF()
    df_transcript = df_base.create_transcript_copy(transcript)
    df_transactions = df_base.create_df_transactions(df_transcript)
    df_completed = df_base.create_df_base_completed(df_transcript)
    df_received = df_base.create_df_base_received(df_transcript)
    df_viewed = df_base.create_df_base_viewed(df_transcript)

    # read in raw offers data
    df_portfolio = pd.read_json('data/portfolio.json', orient='records', lines=True)
    df_portfolio.rename(columns={'id': 'offer_id'}, inplace=True)
    df_portfolio['duration'] = df_portfolio['duration'] * 24

    # groupby operations
    offer_received = df_received.groupby('offer_id')['offer_received'].sum().reset_index()
    offer_viewed = df_viewed.groupby('offer_id')['offer_viewed'].sum().reset_index()
    offer_completed = df_completed.groupby('offer_id')['offer_completed'].sum().reset_index()

    df_engagement_v1 = pd.merge(df_transactions, 
                            df_completed, 
                            how='inner', 
                            left_on=['customer_id','transaction_time'],
                            right_on=['customer_id','offer_completed_time'],
                            suffixes=['','_drop'])

    df_engagement_v1['offer_completed'] = df_engagement_v1['offer_completed'].fillna(0).astype(int)
    df_engagement_v1['offer_completed_time'] = df_engagement_v1['offer_completed_time'].fillna(-1).astype(int)
    df_engagement_v1['offer_id'] = df_engagement_v1['offer_id'].fillna('no-offer')

    offer_transaction_cnt = df_engagement_v1.groupby('offer_id')['transaction_id'].nunique().reset_index()
    offer_transaction_cnt.rename(columns={'transaction_id': 'transaction_cnt'}, inplace=True)

    offer_transaction_amount = df_engagement_v1.groupby('offer_id')['transaction_amount'].sum().reset_index()

    offer_customer_cnt = df_engagement_v1.groupby('offer_id')['customer_id'].nunique().reset_index()
    offer_customer_cnt.rename(columns={'customer_id': 'customer_cnt'}, inplace=True)

    # merge all data to create funnel analysis
    offer_funnel = offer_received
    merge_list = [offer_viewed, offer_completed, offer_transaction_cnt, offer_transaction_amount, offer_customer_cnt]
    for data in merge_list:
        offer_funnel = offer_funnel.merge(data, how='left', on='offer_id').fillna(0)

    offer_funnel['viewed_rate'] = 1.0 * offer_funnel['offer_viewed'] / offer_funnel['offer_received']
    offer_funnel['completion_rate'] = 1.0 * offer_funnel['offer_completed'] / offer_funnel['offer_received']
    offer_funnel['avg_transactions_per_customer'] = 1.0 * offer_funnel['transaction_cnt'] / offer_funnel['customer_cnt']
    offer_funnel['avg_spend_per_customer'] = 1.0 * offer_funnel['transaction_amount'] / offer_funnel['customer_cnt']
    offer_funnel = offer_funnel.fillna(0)

    offer_funnel_subset = offer_funnel[['offer_id','viewed_rate','completion_rate','avg_transactions_per_customer','avg_spend_per_customer']]
    offer_funnel_metrics = df_portfolio.merge(offer_funnel_subset, how='left', on='offer_id')


    # create data directory if not exists
    curr_dir = os.getcwd()
    data_dir = 'data'
    Path(os.path.join(curr_dir, data_dir)).mkdir(parents=True, exist_ok=True)

    # write df to gzipped csv file
    file_name = 'starbucks_offers_funnel_analysis.csv.gz'
    file_path = os.path.join(curr_dir, data_dir, file_name)

    try:
        offer_funnel_metrics.to_csv(file_path, index=False, compression='gzip')
        print("Success: {} created.".format(file_name))
        print("File_path_name: {}".format(file_path))
    except:
        print("Error: {} failed to save.".format(file_name))

    # measure script run time
    print('Script_run_time: {} (hour:minute:second:microsecond)'.format((datetime.now() - start_time)))


