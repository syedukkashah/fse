# test_store_routes.py
import os, sys
sys.path.append('c:/Users/Hp/OneDrive/Desktop/FSE_final_project-master/FSE_final_project-master')

from app import create_app, db
from app.models import User, StoreManager, Inventory, Supplier

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    db.drop_all()
    db.create_all()
    # create a store manager user
    user = User(username='storemgr', email='store@example.com', password='test', role='store_manager')
    db.session.add(user)
    db.session.commit()
    sm = StoreManager(user_id=user.id, first_name='Test', last_name='Mgr', contact_number='1234567890', email='store@example.com')
    db.session.add(sm)
    # add a supplier for foreign keys
    supplier = Supplier(name='Test Supplier', contact_number='1112223333', email='supplier@example.com', address='123 Street')
    db.session.add(supplier)
    db.session.commit()
    # add inventory item for testing order items
    inventory_item = Inventory(item_name='Bandage', category='supplies', description='Bandage desc', unit_price=1.5, stock_quantity=10, reorder_level=5, supplier_id=supplier.id)
    db.session.add(inventory_item)
    db.session.commit()

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    # Test dashboard
    resp = client.get('/store/dashboard')
    print('Dashboard status', resp.status_code)
    # Test inventory list
    resp = client.get('/store/inventory')
    print('Inventory status', resp.status_code)
    # Test adding inventory item GET
    resp = client.get('/store/inventory/new')
    print('Add inventory GET status', resp.status_code)
    # Test creating order GET
    resp = client.get('/store/orders/new')
    print('Create order GET status', resp.status_code)
    # Test creating order POST (valid)
    resp = client.post('/store/orders/new', data={'supplier': supplier.id, 'notes': 'Test order'}, follow_redirects=True)
    print('Create order POST status', resp.status_code)
    # Extract order id from redirect location if any
    # Test adding order item POST
    # First, get order from DB
    from app.models import Order
    order = Order.query.filter_by(supplier_id=supplier.id).first()
    if order:
        resp = client.post(f'/store/orders/{order.id}/items/add', data={'inventory_item': inventory_item.id, 'quantity': 2, 'unit_price': 1.5, 'add_another': ''}, follow_redirects=True)
        print('Add order item POST status', resp.status_code)
    else:
        print('No order created')

    from app.models import Patient, Doctor, Prescription, PrescriptionMedication, User as UserModel
    from datetime import date
    patient = Patient(first_name='John', last_name='Doe', date_of_birth=date(1990, 1, 1), gender='Male', contact_number='123', email='john@ex.com', address='123')
    db.session.add(patient)
    doctor_user = UserModel(username='doc', email='doc@ex.com', password='test', role='doctor')
    db.session.add(doctor_user)
    db.session.commit()
    doctor = Doctor(user_id=doctor_user.id, first_name='Dr', last_name='Smith', specialization='GP', qualification='MBBS', contact_number='123', email='doc@ex.com')
    db.session.add(doctor)
    db.session.commit()
    
    prescription = Prescription(patient_id=patient.id, doctor_id=doctor.id, notes='Test')
    db.session.add(prescription)
    db.session.commit()
    
    pm = PrescriptionMedication(prescription_id=prescription.id, inventory_id=inventory_item.id, dosage='10mg', frequency='Daily', duration='7 days', quantity=2)
    db.session.add(pm)
    db.session.commit()
    
    # Test view prescriptions
    resp = client.get('/store/prescriptions')
    print('View prescriptions status', resp.status_code)
    
    # Test dispense
    old_qty = inventory_item.stock_quantity
    resp = client.post(f'/store/prescriptions/{pm.id}/dispense', follow_redirects=True)
    print('Dispense status', resp.status_code)
    db.session.refresh(inventory_item)
    print('Stock quantity after dispense:', inventory_item.stock_quantity, '(Old:', old_qty, ')')
    
    if inventory_item.stock_quantity == old_qty - 2:
        print('Dispensing stock deduction: SUCCESS')
    else:
        print('Dispensing stock deduction: FAILED')
