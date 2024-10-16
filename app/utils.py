import os
import pandas as pd
from app import db
from app.models import UserTransaction
from werkzeug.utils import secure_filename
from flask import current_app
import logging
from sqlalchemy.exc import IntegrityError

def allowed_file(filename, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = {'csv'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, filename, subfolder=''):
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if subfolder:
        upload_folder = os.path.join(upload_folder, subfolder)
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    
    # Check if file already exists, if so, append a number
    base, extension = os.path.splitext(file_path)
    counter = 1
    while os.path.exists(file_path):
        file_path = f"{base}_{counter}{extension}"
        counter += 1
    
    file.save(file_path)
    return os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER'])

def process_csv(file, user_id):
    logging.info(f"Processing CSV file for user_id: {user_id}")
    try:
        df = pd.read_csv(file)
    except Exception as e:
        logging.error(f"Error reading CSV file: {str(e)}")
        return f"Error reading CSV file: {str(e)}", None
    
    # Define the mapping of expected headers to database columns
    header_mapping = {
        'Date': 'date',
        'Transaction description': 'transaction_description',
        'Paid in': 'paid_in',
        'Paid out': 'paid_out'
    }
    
    # Check if all required headers are present in the CSV
    missing_headers = [header for header in header_mapping.keys() if header not in df.columns]
    if missing_headers:
        error_msg = f"CSV file is missing required headers: {', '.join(missing_headers)}"
        logging.error(error_msg)
        return error_msg, None
    
    # Rename the columns to match the database fields
    df = df.rename(columns=header_mapping)
    
    # Ensure we only process the required columns
    df = df[list(header_mapping.values())]
    
    # Convert date to datetime and sort in descending order
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date', ascending=False)
    
    # Convert 'paid_in' and 'paid_out' columns to float, removing commas and handling 'nan' values
    df['paid_in'] = pd.to_numeric(df['paid_in'].replace('[\£,]', '', regex=True), errors='coerce')
    df['paid_out'] = pd.to_numeric(df['paid_out'].replace('[\£,]', '', regex=True), errors='coerce')
    
    UserSpecificTransaction = UserTransaction.create_table(user_id)
    
    new_records = []
    skipped_records = 0
    
    # Fetch all existing transactions for this user
    existing_transactions = UserSpecificTransaction.query.filter_by(user_id=user_id).all()
    
    # Create a set of tuples representing existing transactions (excluding id)
    existing_transaction_set = set(
        (t.date, t.transaction_description, t.paid_in, t.paid_out)
        for t in existing_transactions
    )

    for _, row in df.iterrows():
        new_transaction = UserSpecificTransaction(
            user_id=user_id,
            date=row['date'],
            transaction_description=row['transaction_description'],
            paid_in=row['paid_in'],
            paid_out=row['paid_out']
        )
        try:
            db.session.add(new_transaction)
            db.session.flush()  # This will check for integrity errors without committing
            new_records.append(new_transaction)
            logging.info(f"Added new record: {row['date']} - {row['transaction_description']}")
        except IntegrityError:
            db.session.rollback()  # Roll back the failed transaction
            skipped_records += 1
            logging.info(f"Skipped existing record: {row['date']} - {row['transaction_description']}")

    if new_records:
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error committing new records: {str(e)}")
            return f"Error committing new records: {str(e)}", None

    logging.info(f"CSV processing complete. Added {len(new_records)} new records, skipped {skipped_records} existing records.")
    return None, {'new': len(new_records), 'skipped': skipped_records}

def calculate_vat(paid_in, paid_out):
    if pd.notna(paid_in):
        amount = float(paid_in)
    elif pd.notna(paid_out):
        amount = -float(paid_out)  # Make paid_out negative
    else:
        amount = 0

    return 0.2 * amount  # 20% VAT
