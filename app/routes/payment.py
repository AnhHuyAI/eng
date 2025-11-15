# app/routes/payment.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models.payment import PaymentRequest
from app.utils.helpers import save_upload_file
from datetime import datetime

bp = Blueprint('payment', __name__, url_prefix='/payment')

@bp.route('/packages')
@login_required
def packages():
    """Payment packages page"""
    packages = current_app.config['PAYMENT_PACKAGES']
    bank_info = current_app.config['BANK_INFO']
    
    return render_template('payment/packages.html',
                         packages=packages,
                         bank_info=bank_info)


@bp.route('/request', methods=['POST'])
@login_required
def create_request():
    """Create payment request"""
    
    package_id = request.form.get('package_id')
    payment_method = request.form.get('payment_method')
    transaction_id = request.form.get('transaction_id', '')
    transfer_note = request.form.get('transfer_note', '')
    proof_image = request.files.get('proof_image')
    
    # Validate
    packages = current_app.config['PAYMENT_PACKAGES']
    if package_id not in packages:
        flash('Gói thanh toán không hợp lệ.', 'danger')
        return redirect(url_for('payment.packages'))
    
    if not proof_image:
        flash('Vui lòng upload ảnh chứng từ thanh toán.', 'danger')
        return redirect(url_for('payment.packages'))
    
    # Save proof image
    proof_url = save_upload_file(proof_image, 'payment-proofs')
    
    if not proof_url:
        flash('Lỗi khi upload ảnh. Vui lòng thử lại.', 'danger')
        return redirect(url_for('payment.packages'))
    
    # Get package info
    package = packages[package_id]
    
    # Create payment request
    payment_req = PaymentRequest(
        user_id=current_user.id,
        amount=package['price'],
        credits_requested=package['credits'],
        package_id=package_id,
        payment_method=payment_method,
        proof_image_url=proof_url,
        transaction_id=transaction_id,
        transfer_note=transfer_note,
        status='pending'
    )
    
    db.session.add(payment_req)
    db.session.commit()
    
    # TODO: Notify admin (email, Telegram, etc.)
    
    flash('Yêu cầu nạp tiền đã được gửi. Chúng tôi sẽ xử lý trong 15-30 phút.', 'success')
    return redirect(url_for('payment.history'))


@bp.route('/history')
@login_required
def history():
    """Payment history"""
    
    payments = PaymentRequest.query.filter_by(user_id=current_user.id)\
        .order_by(PaymentRequest.created_at.desc()).all()
    
    return render_template('payment/history.html', payments=payments)


@bp.route('/request/<int:request_id>')
@login_required
def view_request(request_id):
    """View payment request details"""
    
    payment = PaymentRequest.query.get_or_404(request_id)
    
    # Check ownership
    if payment.user_id != current_user.id and not current_user.is_admin():
        flash('Bạn không có quyền xem yêu cầu này.', 'danger')
        return redirect(url_for('payment.history'))
    
    return render_template('payment/view_request.html', payment=payment)