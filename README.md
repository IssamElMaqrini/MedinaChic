# MedinaChic E-Commerce Platform

## Recent Updates and Improvements

### 1. Fixed Stripe Integration

#### Issues Fixed:
- **Security Enhancement**: Removed hardcoded Stripe webhook secret from code
- **Environment Variables**: Webhook secret is now stored in `.env` file
- **Error Handling**: Improved error messages in webhook handler
- **Shipping Address Bug**: Fixed syntax error in `ShippingAddress.set_defaults()` method

#### Configuration:
1. Copy `.env.example` to `.env`
2. Add your Stripe API keys:
   ```
   STRIPE_API_KEY=sk_test_your_stripe_secret_key_here
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
   ```
3. Set up Stripe webhook endpoint at: `https://yourdomain.com/store/stripe-webhook/`

### 2. Order History Feature

#### What's New:
- **Order Tracking**: All completed orders are now saved to the database
- **History Page**: Users can view their past orders with full details
- **Navbar Integration**: "Mes commandes" / "Mijn bestellingen" link appears when logged in
- **Bilingual Support**: Available in both French and Dutch

#### Models Created:
- `OrderHistory`: Stores order metadata (user, date, total amount, Stripe session ID)
- `OrderHistoryItem`: Stores individual items in each order

#### Access:
- French: Navigate to "Mes commandes" in navbar (when logged in)
- Dutch: Navigate to "Mijn bestellingen" in navbar (when logged in)
- Direct URLs: `/store/history/` or `/store/nl/history/`

### 3. Account Deletion Feature

#### What's New:
- **Self-Service Deletion**: Users can delete their own accounts
- **Security**: Requires password confirmation
- **Modal Dialog**: Safe confirmation dialog prevents accidental deletion
- **Bilingual**: Available in both French and Dutch profiles

#### How It Works:
1. Navigate to profile page
2. Scroll to "Zone Dangereuse" / "Gevaarlijke Zone" section
3. Click "Supprimer mon compte" / "Verwijder mijn account"
4. Enter password in confirmation modal
5. Account and all associated data are permanently deleted

## Installation & Setup

### Prerequisites
- Python 3.x
- Virtual environment

### Installation Steps

1. **Clone the repository**
   ```bash
   cd /home/samehh/dev/MedinaChic
   ```

2. **Activate virtual environment**
   ```bash
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Stripe credentials
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (if needed)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

## Testing the New Features

### Test Order History:
1. Create a test account
2. Add products to cart
3. Complete a checkout (use Stripe test cards)
4. After successful payment, navigate to "Mes commandes"
5. Verify your order appears with correct details

### Test Account Deletion:
1. Log into a test account
2. Navigate to profile page
3. Scroll to bottom and click "Supprimer mon compte"
4. Enter password in modal
5. Confirm account is deleted and redirected to homepage

### Test Stripe Webhook:
1. Set up Stripe CLI or use Stripe dashboard webhooks
2. Complete a test purchase
3. Verify webhook is received and order is saved
4. Check that order appears in history

## Admin Panel

Access the admin panel at `/admin/` to:
- View all orders and order history
- Manage products and categories
- View shipping addresses
- Manage user accounts

## Project Structure

```
MedinaChic/
├── accounts/          # User authentication and profile management
├── store/             # E-commerce functionality
├── templates/         # Base templates (base.html, base_nl.html)
├── media/             # Uploaded product images
├── MedinaChic/        # Project settings
├── manage.py
├── db.sqlite3
├── .env              # Environment variables (not in git)
└── .env.example      # Template for environment variables
```

## Bilingual Support

The site supports both French and Dutch:
- French: Main site at `/`
- Dutch: Alternative site at `/nl/`

All major features have both language versions.

## Security Notes

1. **Never commit `.env` file** - It contains sensitive API keys
2. **Stripe Test Mode**: Use test API keys during development
3. **Password Verification**: Account deletion requires password confirmation
4. **HTTPS Required**: Stripe webhooks require HTTPS in production

## Troubleshooting

### Virtual Environment Not Activated
```bash
source .venv/bin/activate
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### Database Errors
```bash
python manage.py migrate
```

### Stripe Webhook Issues
- Verify webhook secret in `.env` matches Stripe dashboard
- Check webhook endpoint is accessible
- Use Stripe CLI for local testing: `stripe listen --forward-to localhost:8000/store/stripe-webhook/`

## Support

For issues or questions:
1. Check the Django admin panel for data consistency
2. Review Stripe dashboard for payment logs
3. Check Django logs for error messages

## Future Enhancements

Potential improvements:
- Email notifications for order confirmations
- Order status tracking
- Product reviews and ratings
- Advanced search and filtering
- Wishlist functionality
