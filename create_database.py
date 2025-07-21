#!/usr/bin/env python3
"""
Script to create and initialize the database with new schema
"""
from app import create_app, db
from app.models.user import User, UserAddress
from app.models.product import Product, Collection, ProductCollection, ProductImage, InventoryLog, Wishlist
from app.models.order import Order, OrderItem, Cart, PaymentTransaction, Discount, Review, Notification
from werkzeug.security import generate_password_hash
from datetime import datetime, date
import psycopg2

def create_database():
    app = create_app()
    
    with app.app_context():
        # Drop all tables with CASCADE to handle foreign key constraints
        print("Dropping all tables...")
        try:
            # Use raw SQL to drop all tables with CASCADE
            engine = db.engine
            with engine.connect() as conn:
                conn.execute(db.text("DROP SCHEMA public CASCADE;"))
                conn.execute(db.text("CREATE SCHEMA public;"))
                conn.execute(db.text("GRANT ALL ON SCHEMA public TO postgres;"))
                conn.execute(db.text("GRANT ALL ON SCHEMA public TO public;"))
                conn.commit()
            print("Successfully dropped all tables with CASCADE")
        except Exception as e:
            print(f"Error dropping tables: {e}")
            print("Trying alternative method...")
            try:
                db.drop_all()
            except Exception as e2:
                print(f"Alternative method also failed: {e2}")
                print("Please manually drop the database and recreate it")
                return
        
        print("Creating all tables...")
        db.create_all()
        
        # Create sample data
        print("Creating sample data...")
        create_sample_data()
        
        print("Database created successfully!")

def create_sample_data():
    """Create sample data for testing"""
    
    # Create admin user
    admin_user = User(
        first_name="Admin",
        last_name="User",
        username="admin",
        email="admin@popmart.com",
        password_hash=generate_password_hash("admin123"),
        is_admin=True,
        is_active=True
    )
    db.session.add(admin_user)
    
    # Create regular user
    regular_user = User(
        first_name="John",
        last_name="Doe",
        username="johndoe",
        email="john@example.com",
        password_hash=generate_password_hash("password123"),
        is_admin=False,
        is_active=True
    )
    db.session.add(regular_user)
    
    # Commit users first to get IDs
    db.session.commit()
    
    # Create collections
    dimoo_collection = Collection(
        name="Dimoo",
        description="Dimoo collection featuring cute characters"
    )
    db.session.add(dimoo_collection)
    
    pucky_collection = Collection(
        name="Pucky",
        description="Pucky collection with unique designs"
    )
    db.session.add(pucky_collection)
    
    skullpanda_collection = Collection(
        name="Skullpanda",
        description="Skullpanda collection with edgy designs"
    )
    db.session.add(skullpanda_collection)
    
    # Commit collections to get IDs
    db.session.commit()
    
    # Create products
    product1 = Product(
        name="Dimoo Space Traveler",
        description="Cute astronaut Dimoo figure",
        price=15.99,
        stock=50,
        is_active=True,
        is_featured=True,
        date_released=datetime.now()
    )
    db.session.add(product1)
    
    product2 = Product(
        name="Pucky Beach Series",
        description="Beach themed Pucky figure",
        price=12.99,
        stock=30,
        is_active=True,
        is_featured=False,
        date_released=datetime.now()
    )
    db.session.add(product2)
    
    product3 = Product(
        name="Skullpanda Night",
        description="Dark themed Skullpanda figure",
        price=18.99,
        stock=25,
        is_active=True,
        is_featured=True,
        date_released=datetime.now()
    )
    db.session.add(product3)
    
    # Commit products to get IDs
    db.session.commit()
    
    # Create product-collection relationships
    pc1 = ProductCollection(
        product_id=product1.id,
        collection_id=dimoo_collection.id
    )
    db.session.add(pc1)
    
    pc2 = ProductCollection(
        product_id=product2.id,
        collection_id=pucky_collection.id
    )
    db.session.add(pc2)
    
    pc3 = ProductCollection(
        product_id=product3.id,
        collection_id=skullpanda_collection.id
    )
    db.session.add(pc3)
    
    # Create product images
    image1 = ProductImage(
        product_id=product1.id,
        image_url="/static/img/dimoo_space.png",
        alt_text="Dimoo Space Traveler"
    )
    db.session.add(image1)
    
    image2 = ProductImage(
        product_id=product2.id,
        image_url="/static/img/pucky_beach.png",
        alt_text="Pucky Beach Series"
    )
    db.session.add(image2)
    
    image3 = ProductImage(
        product_id=product3.id,
        image_url="/static/img/skullpanda_night.png",
        alt_text="Skullpanda Night"
    )
    db.session.add(image3)
    
    # Create user address
    user_address = UserAddress(
        user_id=regular_user.id,
        recipient_name="John Doe",
        phone_number="+1234567890",
        address="123 Main Street",
        city="New York",
        postal_code="10001",
        country="USA",
        is_default=True
    )
    db.session.add(user_address)
    
    # Create discount
    discount = Discount(
        code="WELCOME10",
        value=10.0,
        is_percentage=True,
        min_order_amount=50.0,
        valid_from=date.today(),
        valid_to=date(2024, 12, 31)
    )
    db.session.add(discount)
    
    # Commit address and discount to get IDs
    db.session.commit()
    
    # Create sample order
    order = Order(
        user_id=regular_user.id,
        address_id=user_address.id,
        total_amount=28.98,
        status="pending",
        payment_status="unpaid",
        discount_id=discount.id
    )
    db.session.add(order)
    
    # Commit order to get ID
    db.session.commit()
    
    # Create order items
    order_item1 = OrderItem(
        order_id=order.id,
        product_id=product1.id,
        quantity=1,
        price=15.99
    )
    db.session.add(order_item1)
    
    order_item2 = OrderItem(
        order_id=order.id,
        product_id=product2.id,
        quantity=1,
        price=12.99
    )
    db.session.add(order_item2)
    
    # Create sample review
    review = Review(
        user_id=regular_user.id,
        product_id=product1.id,
        rating=5,
        comment="Amazing quality! Love this Dimoo figure."
    )
    db.session.add(review)
    
    # Create sample notification
    notification = Notification(
        user_id=regular_user.id,
        title="Order Confirmation",
        message="Your order #{} has been placed successfully!".format(order.id),
        is_read=False
    )
    db.session.add(notification)
    
    # Final commit
    db.session.commit()
    
    print(f"Created {User.query.count()} users")
    print(f"Created {Product.query.count()} products")
    print(f"Created {Collection.query.count()} collections")
    print(f"Created {Order.query.count()} orders")
    print(f"Created {Review.query.count()} reviews")

if __name__ == "__main__":
    create_database() 