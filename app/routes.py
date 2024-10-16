from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file, current_app, make_response
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, UserTransaction
from app.forms import LoginForm, RegistrationForm
from app.utils import allowed_file, save_file, process_csv, calculate_vat
import os
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
from flask import send_from_directory
import math
from weasyprint import HTML
import tempfile
from app.email import send_email

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        if not user.confirmed:
            flash('Please confirm your account before logging in.', 'warning')
            return redirect(url_for('auth.login'))
        login_user(user)
        return redirect(url_for('main.index'))
    return render_template('login.html', title='Sign In', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            
            # Generate confirmation token
            token = user.generate_confirmation_token()
            confirm_url = url_for('auth.confirm_email', token=token, _external=True)
            html = render_template('email/confirm_email.html', confirm_url=confirm_url)
            subject = "Please confirm your email"
            send_email(user.email, subject, html)

            flash('A confirmation email has been sent via email.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error during user registration: {str(e)}")
            flash('An error occurred during registration. Please try again.')
    return render_template('register.html', title='Register', form=form)

@auth.route('/confirm/<token>')
def confirm_email(token):
    try:
        user = User.verify_confirmation_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
    if user.confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.confirm_email()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('main.index'))

@main.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    UserSpecificTransaction = UserTransaction.get_user_model(current_user.id)
    if UserSpecificTransaction is None:
        # If the user-specific transaction model doesn't exist, create it
        UserSpecificTransaction = UserTransaction.create_table(current_user.id)

    query = UserSpecificTransaction.query.filter_by(user_id=current_user.id)

    if start_date:
        query = query.filter(UserSpecificTransaction.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(UserSpecificTransaction.date <= datetime.strptime(end_date, '%Y-%m-%d').date())

    user_transactions = query.order_by(UserSpecificTransaction.date.desc()).paginate(page=page, per_page=10)

    # Convert 'nan' values to None
    for transaction in user_transactions.items:
        if isinstance(transaction.paid_in, float) and math.isnan(transaction.paid_in):
            transaction.paid_in = None
        if isinstance(transaction.paid_out, float) and math.isnan(transaction.paid_out):
            transaction.paid_out = None

    return render_template('index.html', transactions=user_transactions, start_date=start_date, end_date=end_date)

@main.route('/upload_csv', methods=['POST'])
@login_required
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        try:
            error, result = process_csv(file, current_user.id)
            if error:
                logging.error(f"Error processing CSV: {error}")
                return jsonify({'error': error}), 400
            logging.info(f"CSV processing result: Added {result['new']} new records, skipped {result['skipped']} existing records for user {current_user.id}")
            return jsonify({
                'message': f"CSV processed successfully. Added {result['new']} new records, skipped {result['skipped']} existing records.",
                'new_records': result['new'],
                'skipped_records': result['skipped']
            }), 200
        except Exception as e:
            logging.exception(f"Exception occurred while processing CSV: {str(e)}")
            return jsonify({'error': 'An error occurred while processing the CSV file'}), 500
    return jsonify({'error': 'Invalid file type'}), 400

@main.route('/add_comment', methods=['POST'])
@login_required
def add_comment():
    data = request.json
    transaction_id = data.get('transaction_id')
    comment = data.get('comment')
    UserSpecificTransaction = UserTransaction.get_user_model(current_user.id)
    transaction = UserSpecificTransaction.query.get(transaction_id)
    if transaction and transaction.user_id == current_user.id:
        transaction.comment = comment
        db.session.commit()
        return jsonify({'message': 'Comment added successfully'}), 200
    return jsonify({'error': 'Transaction not found'}), 404

@main.route('/upload_invoice', methods=['POST'])
@login_required
def upload_invoice():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename, ['pdf', 'jpg', 'jpeg', 'png']):
        transaction_id = request.form.get('transaction_id')
        UserSpecificTransaction = UserTransaction.get_user_model(current_user.id)
        transaction = UserSpecificTransaction.query.get(transaction_id)
        if transaction and transaction.user_id == current_user.id:
            try:
                file_extension = os.path.splitext(file.filename)[1]
                unique_filename = f"{transaction.date.strftime('%Y-%m-%d')}_{transaction.transaction_description[:30]}{file_extension}"
                unique_filename = secure_filename(unique_filename)
                
                # Create user-specific subfolder
                user_subfolder = f"user_{current_user.id}"
                date_subfolder = transaction.date.strftime('%Y-%m')
                relative_path = save_file(file, unique_filename, subfolder=os.path.join(user_subfolder, date_subfolder))
                transaction.invoice = relative_path
                db.session.commit()
                logging.info(f"Invoice uploaded successfully for transaction {transaction_id}")
                return jsonify({'message': 'Invoice uploaded successfully', 'file_path': relative_path}), 200
            except Exception as e:
                logging.error(f"Error uploading invoice: {str(e)}")
                return jsonify({'error': 'An error occurred while uploading the invoice'}), 500
    return jsonify({'error': 'Invalid file type'}), 400

@main.route('/calculate_vat', methods=['POST'])
@login_required
def calculate_vat_route():
    data = request.json
    transaction_id = data.get('transaction_id')
    UserSpecificTransaction = UserTransaction.get_user_model(current_user.id)
    transaction = UserSpecificTransaction.query.get(transaction_id)
    if transaction and transaction.user_id == current_user.id:
        try:
            logging.info(f"Calculating VAT for transaction {transaction_id}")
            logging.info(f"Paid in: {transaction.paid_in}, Paid out: {transaction.paid_out}")
            vat = calculate_vat(transaction.paid_in, transaction.paid_out)
            logging.info(f"Calculated VAT: {vat}")
            transaction.vat = vat
            db.session.commit()
            return jsonify({'message': 'VAT calculated successfully', 'vat': vat}), 200
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error calculating VAT: {str(e)}")
            return jsonify({'error': f'Error calculating VAT: {str(e)}'}), 500
    return jsonify({'error': 'Transaction not found'}), 404

@main.route('/remove_vat', methods=['POST'])
@login_required
def remove_vat():
    data = request.json
    transaction_id = data.get('transaction_id')
    UserSpecificTransaction = UserTransaction.get_user_model(current_user.id)
    transaction = UserSpecificTransaction.query.get(transaction_id)
    if transaction and transaction.user_id == current_user.id:
        transaction.vat = 0
        db.session.commit()
        return jsonify({'message': 'VAT removed successfully'}), 200
    return jsonify({'error': 'Transaction not found'}), 404

@main.route('/export_pdf')
@login_required
def export_pdf():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    UserSpecificTransaction = UserTransaction.get_user_model(current_user.id)
    query = UserSpecificTransaction.query.filter_by(user_id=current_user.id)

    if start_date:
        query = query.filter(UserSpecificTransaction.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(UserSpecificTransaction.date <= datetime.strptime(end_date, '%Y-%m-%d').date())

    transactions = query.order_by(UserSpecificTransaction.date.desc()).all()

    # Check if all transactions have invoices
    all_invoices_attached = all(transaction.invoice is not None for transaction in transactions)

    if all_invoices_attached:
        return jsonify({'message': 'All invoices are attached. Do you want to continue to highlight the rows?', 'all_invoices_attached': True}), 200
    else:
        # If not all invoices are attached, proceed with PDF generation without prompting
        return generate_pdf()

@main.route('/generate_pdf')
@login_required
def generate_pdf():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    UserSpecificTransaction = UserTransaction.get_user_model(current_user.id)
    query = UserSpecificTransaction.query.filter_by(user_id=current_user.id)

    if start_date:
        query = query.filter(UserSpecificTransaction.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(UserSpecificTransaction.date <= datetime.strptime(end_date, '%Y-%m-%d').date())

    transactions = query.order_by(UserSpecificTransaction.date.desc()).all()

    # Handle 'nan' values and calculate totals
    total_paid_in = 0
    total_paid_out = 0
    total_vat = 0
    for transaction in transactions:
        if isinstance(transaction.paid_in, float) and math.isnan(transaction.paid_in):
            transaction.paid_in = None
        if isinstance(transaction.paid_out, float) and math.isnan(transaction.paid_out):
            transaction.paid_out = None
        if isinstance(transaction.vat, float) and math.isnan(transaction.vat):
            transaction.vat = None
        
        total_paid_in += transaction.paid_in or 0
        total_paid_out += transaction.paid_out or 0
        total_vat += transaction.vat or 0

    # Calculate Gross Balance
    gross_balance = total_paid_in - total_paid_out

    # Determine VAT label
    if total_vat > 0:
        vat_label = f"Total VAT Owed: £{total_vat:.2f}"
    elif total_vat < 0:
        vat_label = f"Total VAT Rebate: £{abs(total_vat):.2f}"
    else:
        vat_label = "Total VAT: £0.00"

    # Render the template
    html_content = render_template('pdf_template.html', 
                                   transactions=transactions, 
                                   total_vat=total_vat,
                                   vat_label=vat_label,
                                   gross_balance=gross_balance,
                                   start_date=start_date,
                                   end_date=end_date)

    # Generate PDF
    pdf = HTML(string=html_content).write_pdf()

    # Create response
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=transactions.pdf'

    return response

@main.route('/view_invoice/<path:filename>')
@login_required
def view_invoice(filename):
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        user_subfolder = f"user_{current_user.id}"
        file_path = os.path.join(user_subfolder, filename)
        return send_from_directory(upload_folder, file_path)
    except Exception as e:
        logging.error(f"Error viewing invoice: {str(e)}")
        return jsonify({'error': 'Invoice not found'}), 404

@main.route('/delete_invoice', methods=['POST'])
@login_required
def delete_invoice():
    data = request.json
    transaction_id = data.get('transaction_id')
    UserSpecificTransaction = UserTransaction.get_user_model(current_user.id)
    transaction = UserSpecificTransaction.query.get(transaction_id)
    if transaction and transaction.user_id == current_user.id:
        try:
            if transaction.invoice:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], transaction.invoice)
                if os.path.exists(file_path):
                    os.remove(file_path)
            transaction.invoice = None
            db.session.commit()
            logging.info(f"Invoice deleted successfully for transaction {transaction_id}")
            return jsonify({'message': 'Invoice deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting invoice: {str(e)}")
            return jsonify({'error': 'An error occurred while deleting the invoice'}), 500
    return jsonify({'error': 'Transaction not found'}), 404

@main.route('/toggle_highlight', methods=['POST'])
@login_required
def toggle_highlight():
    data = request.json
    transaction_id = data.get('transaction_id')
    UserSpecificTransaction = UserTransaction.get_user_model(current_user.id)
    transaction = UserSpecificTransaction.query.get(transaction_id)
    if transaction and transaction.user_id == current_user.id:
        transaction.highlight = not transaction.highlight
        db.session.commit()
        return jsonify({'message': 'Highlight toggled successfully', 'highlight': transaction.highlight}), 200
    return jsonify({'error': 'Transaction not found'}), 404

@main.route('/test_email')
def test_email():
    try:
        send_email('hellol@tarex.co.uk', 'Test Email', '<h1>This is a test email</h1>')
        return 'Email sent successfully'
    except Exception as e:
        return f'Failed to send email: {str(e)}'
