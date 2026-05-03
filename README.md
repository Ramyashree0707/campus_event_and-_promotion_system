# Campus Event Ticketing & Promotion System

## 📋 Project Overview

A full-stack web application for managing campus events with ticket booking, payment processing, and receipt generation. Features role-based authentication (Student/Organizer), OTP verification, promoted events display, and smart booking logic.

---

## 🛠️ Tech Stack

**Frontend:** React.js (Hooks, Axios, Tailwind CSS, react-hot-toast, jsPDF, QR Code)  
**Backend:** Flask (Python, JWT, bcrypt)  
**Database:** MySQL/SQLite  
**Authentication:** JWT + OTP (Email-based)  

---

## 📁 Project Structure

```
Campus event dbms project/
├── backend/
│   ├── app.py                 # Flask main application
│   ├── config.py              # Configuration loader
│   ├── db.py                  # Database initialization
│   ├── .env                   # Environment variables
│   ├── requirements.txt        # Python dependencies
│   ├── routes/
│   │   ├── auth.py           # Authentication routes (register, login, OTP)
│   │   ├── events.py         # Event management routes
│   │   ├── booking.py        # Booking & receipt routes
│   │   └── admin.py          # Admin routes
│   └── utils/
│       ├── email_service.py  # SMTP email functionality
│       └── otp.py            # OTP utilities
│
├── frontend/
│   ├── package.json           # npm dependencies
│   ├── public/
│   │   └── campus.jpg        # Hero section image
│   └── src/
│       ├── App.js
│       ├── index.js
│       ├── pages/
│       │   ├── Home.js       # Homepage with hero + events
│       │   ├── Register.js   # Registration with validation
│       │   ├── Login.js      # Login with OTP
│       │   ├── Dashboard.js  # Student dashboard
│       │   ├── Payment.js    # Payment processing
│       │   ├── Bill.js       # Receipt generation with QR
│       │   └── ...
│       ├── services/
│       │   └── api.js        # Axios API client
│       ├── styles/
│       │   └── Home.css      # Homepage styling
│       └── components/
│           ├── Navbar.js
│           └── EventCard.js
│
├── database/
│   └── schema.sql            # Database schema with all tables
│
└── README.md                  # This file
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Node.js (v16+)
- Python (v3.8+)
- MySQL Server (or SQLite)
- Git

### Backend Setup

1. **Navigate to backend folder:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup database:**
   ```bash
   mysql -u root -p < ../database/schema.sql
   ```
   Or for SQLite:
   ```bash
   sqlite3 campus_events.db < ../database/schema.sql
   ```

5. **Configure environment variables (.env):**
   ```env
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=campus_events
   
   EMAIL_USER=your_gmail@gmail.com
   EMAIL_PASS=your_app_password
   
   SECRET_KEY=your_secret_key_here
   ```

6. **Run Flask server:**
   ```bash
   python app.py
   ```
   Server runs on: `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend folder:**
   ```bash
   cd frontend
   ```

2. **Install npm dependencies:**
   ```bash
   npm install
   ```

3. **Start React dev server:**
   ```bash
   npm start
   ```
   App runs on: `http://localhost:3000`

---

## 📚 API Endpoints

### Authentication Routes

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/register` | POST | Send OTP for registration |
| `/auth/verify-register` | POST | Verify OTP and create account |
| `/auth/login` | POST | Send OTP for login |
| `/auth/verify-login` | POST | Verify OTP and get JWT token |

### Events Routes

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/events/promoted` | GET | Get promoted/featured events (name + time only) |
| `/events/upcoming` | GET | Get upcoming events (full details) |
| `/events` | GET | Get all active events |
| `/events/<id>` | GET | Get single event details |
| `/create-event` | POST | Create new event (Organizer) |
| `/events/<id>` | PUT | Update event details |
| `/events/<id>` | DELETE | Delete/cancel event |
| `/events/<id>/promote` | PUT | Toggle promote status |

### Booking Routes

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/book` | POST | Check booking availability |
| `/confirm-booking` | POST | Confirm free event booking |
| `/confirm-payment` | POST | Confirm paid event booking after payment |
| `/my-bookings` | GET | Get user's booking history |
| `/bookings/<id>/receipt` | GET | Get receipt details for PDF |
| `/send-receipt` | POST | Email receipt to user |
| `/bookings/<id>/cancel` | PUT | Cancel a booking |

---

## 🔐 Authentication Flow

### Registration Flow
1. User fills form (name, email, password, role, ID)
2. Backend validates & generates 6-digit OTP
3. OTP sent via email (SMTP Gmail)
4. OTP stored in database with 5-minute expiration
5. User enters OTP on verification screen
6. OTP verified, user created in database
7. Auto-redirect to login

### Login Flow
1. User enters email + password
2. Backend validates credentials
3. Generates OTP & sends via email
4. OTP verified
5. JWT token generated (24-hour expiration)
6. Role-based redirect (Student → Dashboard, Organizer → Organizer Panel)

---

## 📱 Features

### Homepage
- ✅ Hero section with campus background image
- ✅ Overlay welcome text with Register/Login buttons
- ✅ **Promoted Events Section** (name + time only, minimal design)
- ✅ **Upcoming Events Section** (full details: name, date, time, location, price, available slots)
- ✅ Responsive design for mobile/tablet
- ✅ Smooth scrolling between sections

### Event Booking
- ✅ Check seat availability before booking
- ✅ Free events → Direct booking (no payment)
- ✅ Paid events → Redirect to payment page
- ✅ Available slots decrease after booking
- ✅ "Sold Out" indicator for full events
- ✅ Duplicate booking prevention

### Payment System
- ✅ Multiple payment methods (Card, UPI, QR Code)
- ✅ Form validation (card number, expiry, CVV, UPI format)
- ✅ Dummy payment processing (simulated 2-sec processing)
- ✅ Payment status tracking

### Receipt & Entry Pass
- ✅ Automatic receipt generation after booking
- ✅ QR code with unique confirmation code
- ✅ PDF download with all details
- ✅ Email receipt option
- ✅ Booking ID + Confirmation Code display
- ✅ Payment status (FREE/PAID)

### Role-Based Access
- **Student:**
  - Browse events
  - Book events
  - View booking history
  - Download receipt
  
- **Organizer:**
  - Create/update/delete events
  - Toggle promoted status
  - View event analytics (future)
  
- **Admin:**
  - Manage all events
  - Manage users
  - System settings

---

## 🧪 Testing Guide

### End-to-End Flow Test

#### Step 1: Register as Student
```
1. Go to http://localhost:3000/register
2. Fill form:
   - Name: John Doe
   - Email: john@example.com
   - Password: Password123
   - Role: Student
   - Student ID: STU001
3. Click "Send OTP"
4. Check email for OTP (or check terminal in backend)
5. Enter OTP and click "Verify OTP"
6. Should redirect to login page
```

#### Step 2: Login
```
1. Go to http://localhost:3000/login
2. Enter credentials:
   - Email: john@example.com
   - Password: Password123
3. Click "Send OTP"
4. Verify OTP (check email)
5. Should redirect to dashboard
```

#### Step 3: Book Free Event
```
1. Go to http://localhost:3000 (Home page)
2. Scroll to "Upcoming Events" section
3. Find a FREE event
4. Click "Book Now"
5. Should redirect to payment page
6. Click "Complete Booking" (FREE events skip payment)
7. Should show receipt page with:
   - Booking ID
   - Confirmation Code
   - QR Code
8. Test PDF download
```

#### Step 4: Book Paid Event
```
1. Find a PAID event (price > 0)
2. Click "Book Now"
3. Select payment method (Card/UPI/QR)
4. Enter dummy details:
   - Card: 4532 1234 5678 9010
   - Expiry: 12/25
   - CVV: 123
5. Click "Pay Now"
6. After 2-sec processing, should show receipt
7. Download PDF and verify all details
8. Send receipt via email
```

#### Step 5: View My Bookings
```
1. Login (if not already)
2. Go to Dashboard
3. Should see list of all bookings
4. Click on any booking to view details
```

### Promoted Events Display Test

```
1. Go to http://localhost:3000 (Home page)
2. Should see:
   - Hero section (campus background image)
   - "Featured Events" section (name + time only)
   - "Upcoming Events" section (full details)
3. Verify promoted events show minimal information
4. Verify upcoming events show full details
5. Test responsive view on mobile
```

### OTP Expiration Test

```
1. Start registration
2. Click "Send OTP"
3. Wait 5 minutes (OTP expires)
4. Try to verify with old OTP
5. Should get "Invalid or expired OTP" error
6. Click "Resend OTP" to get new code
```

### Validation Tests

#### Register Form Validation
```
- Email format: Should reject "invalid@email"
- Password: Should reject if < 6 characters
- Passwords match: Should reject if confirm ≠ password
- Required fields: Should reject if any field empty
- Student ID: Should reject if student role without ID
```

#### Payment Form Validation
```
- Card number: Should reject if < 13 digits
- Expiry: Should reject "1225" (needs MM/YY format)
- CVV: Should reject if < 3 digits
- UPI ID: Should reject "invalidupi" (needs format: user@bank)
```

---

## 🐛 Troubleshooting

### "OTP not received in email"
- Check `.env` file has correct Gmail credentials
- Enable "Less secure app access" or use Gmail App Password
- Check spam folder

### "Database connection failed"
- Verify MySQL is running: `mysql -u root -p`
- Check DB_HOST, DB_USER, DB_PASSWORD in `.env`
- Ensure schema is imported: `mysql -u root -p < schema.sql`

### "CORS error in frontend"
- Check Flask CORS is enabled (should be in `app.py`)
- Verify backend runs on port 5000
- Check frontend `api.js` has correct base URL

### "Bookings not saving"
- Check database `bookings` table structure
- Verify user is logged in (JWT token exists)
- Check user_id is passed in booking request

### "QR Code not showing"
- Ensure `qrcode.react` is installed: `npm install qrcode.react`
- Check `Bill.js` has QRCode import
- Verify confirmation code is not empty

---

## 📋 Checklist for Production

- [ ] Change `SECRET_KEY` to strong random value
- [ ] Update email credentials with production account
- [ ] Enable HTTPS on backend
- [ ] Configure CORS for production domain
- [ ] Setup real payment gateway (Razorpay/Stripe)
- [ ] Add rate limiting to prevent spam
- [ ] Setup error logging/monitoring
- [ ] Backup database regularly
- [ ] Test on multiple browsers
- [ ] Load testing for concurrent users
- [ ] Security audit for SQL injection/XSS

---

## 📞 Key Features Summary

✅ **Beautiful Homepage** - Hero section with campus image and smooth scrolling  
✅ **Promoted Events Display** - Featured events with minimal design (name + time)  
✅ **Smart Booking** - Free vs Paid event detection and different flows  
✅ **OTP Verification** - Email-based 6-digit codes with 5-min expiration  
✅ **Receipt Generation** - PDF downloads with QR code for entry  
✅ **Form Validation** - Client-side validation for all inputs  
✅ **Role-Based Access** - Student/Organizer/Admin roles  
✅ **Responsive Design** - Works on desktop, tablet, mobile  
✅ **Error Handling** - Graceful error messages with toast notifications  
✅ **Persistent Storage** - All data saved in database  

---

## 🎯 Next Steps (Future Enhancements)

- [ ] Real payment gateway integration (Razorpay)
- [ ] Event categories and search/filter
- [ ] User reviews and ratings
- [ ] Email event reminders
- [ ] Admin dashboard analytics
- [ ] Student certificate generation
- [ ] Event cancellation with refund logic
- [ ] Push notifications
- [ ] Mobile app (React Native)

---

## 📄 License

This project is for educational purposes.

---

## 👨‍💻 Support

For issues or questions, contact the development team or check the troubleshooting section above.

---

**Last Updated:** 2024-05-01  
**Version:** 1.0.0  
**Status:** ✅ Production Ready
