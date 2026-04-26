# 💰 Shimmy Vision Sales & Distribution Consolidation

**Status**: Pre-v1.9.0 Verification Required  
**Last Updated**: January 9, 2026  
**Owner**: Michael A. Kuykendall

## 🎯 Purpose

Consolidate and verify the complete Shimmy Vision sales pipeline, licensing system, and distribution network to ensure:
1. No broken flows from v1.9.0 Kitchen Sink changes
2. License keys work with new binaries
3. Purchase → License → Vision API flow intact
4. All documentation accurate and current

---

## 🏗️ Architecture Overview

### Components
1. **Frontend**: GitHub Pages (https://michael-a-kuykendall.github.io/shimmy-vision)
2. **Payment**: Stripe (test + live modes)
3. **Webhook**: Cloudflare Worker (test + production environments)
4. **Licensing**: Keygen.sh with Ed25519 verification
5. **Backend**: Shimmy binary with vision feature flag

### Data Flow
```
User visits shimmy-vision site
  → Clicks pricing tier
  → Stripe checkout (embedded)
  → Payment processed
  → Stripe webhook → Cloudflare Worker
  → Worker calls Keygen API → Creates license
  → License key emailed to user
  → User sets SHIMMY_LICENSE_KEY
  → Shimmy validates via Keygen
  → Vision API unlocked
```

---

## 📊 Current Status (Pre-Verification)

### ✅ Known Working (as of v1.8.2)
- Test purchase flow with Stripe test cards
- License generation via Keygen API
- License validation in shimmy binary
- Vision API gating based on license

### ❓ Potentially Affected by v1.9.0
- **Binary naming changes**: New filenames might break download links
- **GPU backend flags**: License validation during GPU initialization
- **Vision performance**: Need to document CPU vs GPU expectations
- **Frontend API endpoints**: Verify still pointing to correct worker URLs

### 🔍 Needs Verification
See comprehensive checklist in [V1.9.0_RELEASE_CHECKLIST.md](../../V1.9.0_RELEASE_CHECKLIST.md) Phase 2.5

---

## 🔐 Stripe Configuration

### Test Environment
- **Dashboard**: https://dashboard.stripe.com/test
- **Publishable Key**: `pk_test_51RwqRv1g5xy1QMw5drOBCVy7G8isU0C07QL4wNYHzy9MTLTBiGDhrFVHmO03dbuPiq3PXDrK9aVMGKIMTne48AQV00n9v9cCIw`
- **Test Cards**: `4242 4242 4242 4242` (Visa), `5555 5555 5555 4444` (Mastercard)
- **Webhook Endpoint**: `https://shimmy-license-webhook-test.michaelallenkuykendall.workers.dev/stripe-webhook`

### Production Environment
- **Dashboard**: https://dashboard.stripe.com/live
- **Publishable Key**: `pk_live_51RwqRv1g5xy1QMw5P01z0dVCQWSnSqc2VQEfmscQyrfy2LAe1Un2gqE3b3kmxxxFlP8XyosxJVu2K1p81ShmgyDw009RQ8xU6Q`
- **Webhook Endpoint**: `https://shimmy-license-webhook.michaelallenkuykendall.workers.dev/stripe-webhook`

### Products & Pricing
| Tier | Monthly Price | Pages/Month | Machines |
|------|---------------|-------------|----------|
| Developer | $12 | 2,500 | 1 |
| Professional | $29 | 10,000 | 1 |
| Startup | $79 | 50,000 | 5 |
| Enterprise | $299 | Unlimited | Unlimited |
| Lifetime | $499 (one-time) | Unlimited | 1 |

**Metadata Required**: Each product must have `keygen_policy_id` and `tier` metadata.

---

## 🔑 Keygen Configuration

### Account Details
- **Account ID**: `6270bf9c-23ad-4483-9296-3a6d9178514a`
- **Dashboard**: https://app.keygen.sh/accounts/6270bf9c-23ad-4483-9296-3a6d9178514a
- **Public Key** (Ed25519): `42f313585a72a41513208800f730944f1a3b74a8acfff539f96ce244d029fa5d`

### Policies (One per Tier)
Each policy defines:
- **Max Uses**: Page processing limit per month
- **Duration**: License validity period (usually 30 days for subscriptions)
- **Entitlements**: `VISION_ANALYSIS`, `API_ACCESS`, `CLI_ACCESS`

### License Validation Flow
1. Shimmy reads `SHIMMY_LICENSE_KEY` environment variable
2. Calls Keygen API: `POST /licenses/actions/validate-key`
3. Keygen returns response with Ed25519 signature
4. Shimmy verifies signature using hardcoded public key
5. Checks entitlements and usage limits
6. Caches validation for 24 hours (offline grace period)

---

## ☁️ Cloudflare Worker

### Environments
- **Test**: `shimmy-license-webhook-test.michaelallenkuykendall.workers.dev`
- **Production**: `shimmy-license-webhook.michaelallenkuykendall.workers.dev`

### Required Secrets (per environment)
```bash
KEYGEN_ACCOUNT_ID          # 6270bf9c-23ad-4483-9296-3a6d9178514a
KEYGEN_PRODUCT_TOKEN       # prod-... (from Keygen)
STRIPE_SECRET_KEY          # sk_test_... or sk_live_...
STRIPE_WEBHOOK_SECRET      # whsec_... (from Stripe)
STRIPE_PRICE_DEVELOPER     # price_1SmK831g5xy1QMw5hCY8u2I4 (test)
STRIPE_PRICE_PROFESSIONAL  # price_1SmK861g5xy1QMw5z9EmJfK5 (test)
STRIPE_PRICE_STARTUP       # price_1SmK881g5xy1QMw5BPyc895U (test)
STRIPE_PRICE_ENTERPRISE    # price_1SmK9k1g5xy1QMw5a7PnDwDw (test)
STRIPE_PRICE_LIFETIME      # price_1SmK9o1g5xy1QMw5cHBG18Xr (test)
```

### Endpoints
- **Health Check**: `GET /health`
- **Create Checkout**: `GET /buy?tier=developer&email=user@example.com`
- **Customer Portal**: `POST /portal` (email in body)
- **License Retrieval**: `POST /license` (email in body)
- **Stripe Webhook**: `POST /stripe-webhook` (Stripe events)

### Deployment
```bash
# Set secrets
wrangler secret put KEYGEN_ACCOUNT_ID --env test
# ... (repeat for all secrets)

# Deploy
wrangler publish --env test       # Test environment
wrangler publish --env production # Production environment

# Monitor logs
wrangler tail --env production
```

---

## 🌐 Frontend (shimmy-vision)

### Repository
- **Public Repo**: https://github.com/Michael-A-Kuykendall/shimmy-vision (hypothetical - not created yet)
- **Deployment**: GitHub Pages via GitHub Actions
- **URL**: https://michael-a-kuykendall.github.io/shimmy-vision

### Key Files
- **index.html**: Marketing page with pricing tiers
- **checkout.html**: Stripe embedded checkout
- **success.html**: License key display after purchase
- **config.js**: API endpoint configuration (test vs live)

### Environment Configuration
```javascript
// config.js
const WORKER_URL = process.env.NODE_ENV === 'production'
  ? 'https://shimmy-license-webhook.michaelallenkuykendall.workers.dev'
  : 'https://shimmy-license-webhook-test.michaelallenkuykendall.workers.dev';
```

### Deployment
```bash
npm run build       # Build for production
npm run deploy      # Deploy to GitHub Pages (gh-pages package)
```

---

## 🧪 Testing Checklist

### Critical Tests (Must Pass Before Public Release)
- [ ] **Health Check**: Worker endpoints return 200 OK
- [ ] **Test Purchase**: Complete checkout with test card
- [ ] **Webhook Delivery**: Stripe events reach worker
- [ ] **License Creation**: Keygen creates license automatically
- [ ] **Email Delivery**: User receives license key (if configured)
- [ ] **License Validation**: Shimmy binary accepts test license
- [ ] **Vision API Gating**: Without license → 401, with license → 200
- [ ] **Portal Access**: User can view/manage subscription
- [ ] **License Retrieval**: Email lookup returns license key
- [ ] **Frontend Links**: All download links point to correct binaries
- [ ] **Frontend API**: Checkout calls correct worker environment

### Performance Tests
- [ ] **License Validation Latency**: <100ms for cached, <500ms for API call
- [ ] **Webhook Processing**: <2 seconds from Stripe event to license creation
- [ ] **Checkout Load Time**: <3 seconds on 3G connection
- [ ] **Vision API First Request**: <10 seconds (includes model download)

### Security Tests
- [ ] **Webhook Signature Verification**: Invalid signatures rejected
- [ ] **License Tampering**: Modified licenses rejected
- [ ] **SQL Injection**: Worker sanitizes all inputs
- [ ] **XSS Prevention**: Frontend escapes all user data
- [ ] **CORS Configuration**: Only shimmy-vision domain allowed

---

## 🚨 Known Issues & Workarounds

### Issue 1: Webhook Delays
**Problem**: Stripe webhook may take 5-30 seconds to deliver  
**Workaround**: Success page polls `/license` endpoint until key appears  
**Status**: Acceptable (UX shows "Generating license..." spinner)

### Issue 2: Model Download on First Vision API Call
**Problem**: First request takes 30-60 seconds (model download)  
**Workaround**: Document in README, add warming endpoint  
**Status**: Needs better UX (progress indicator)

### Issue 3: Test vs Live Environment Confusion
**Problem**: Frontend could accidentally use test worker in production  
**Workaround**: Build-time environment variable checks  
**Status**: Needs CI/CD validation step

---

## 📈 Metrics & Monitoring

### Key Metrics to Track
1. **Conversion Rate**: Site visits → purchases
2. **Purchase Success Rate**: Checkouts started → completed
3. **License Validation Rate**: API calls → valid licenses
4. **Vision API Usage**: Requests/day, pages processed
5. **Churn Rate**: Monthly cancellations

### Monitoring Tools
- **Stripe Dashboard**: Payment metrics, failed charges
- **Keygen Dashboard**: License creation, validation requests
- **Cloudflare Analytics**: Worker invocations, error rates
- **GitHub Pages Analytics**: Site traffic
- **Application Logs**: Vision API usage (via `SHIMMY_VISION_TRACE=1`)

### Alerts to Set Up
- [ ] Webhook delivery failure (Stripe → Worker)
- [ ] License creation failure (Worker → Keygen)
- [ ] High error rate on vision API (>5% 500 errors)
- [ ] Unusual purchase patterns (fraud detection)

---

## 🔄 Update Procedures

### Updating Stripe Products
1. Login to Stripe Dashboard → Products
2. Edit product → Update metadata: `keygen_policy_id`, `tier`
3. Update Cloudflare Worker secrets: `STRIPE_PRICE_<TIER>`
4. Deploy worker: `wrangler publish --env production`
5. Test with test card purchase

### Updating Keygen Policies
1. Login to Keygen Dashboard → Policies
2. Edit policy → Update max uses, duration, entitlements
3. Verify Stripe product metadata matches policy ID
4. Test license validation with new limits

### Updating Frontend
1. Edit `config.js` → Update worker URLs if needed
2. Update pricing tiers → Match Stripe products
3. Build: `npm run build`
4. Deploy: `npm run deploy`
5. Verify live site within 5 minutes

### Updating Shimmy Binary
1. Modify vision license validation code
2. Test locally with test license
3. Build binaries: `cargo build --release --features vision`
4. Test binary download → license validation flow
5. Deploy to GitHub Releases (v1.9.0)

---

## 🛠️ Troubleshooting

### Problem: Checkout Session Creation Fails
**Symptoms**: `/buy` endpoint returns 500  
**Check**:
1. Worker logs: `wrangler tail --env production`
2. Stripe secrets set: `wrangler secret list --env production`
3. Stripe API key valid: Test in Stripe Dashboard

### Problem: License Not Created After Payment
**Symptoms**: Webhook delivered, but no license in Keygen  
**Check**:
1. Worker logs for Keygen API errors
2. Keygen account quota (license limit)
3. Stripe webhook signature verification
4. Product metadata includes `keygen_policy_id`

### Problem: License Validation Fails in Shimmy
**Symptoms**: Valid license returns 403  
**Check**:
1. License key format: `XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX-V3`
2. Shimmy environment: `echo $SHIMMY_LICENSE_KEY`
3. Keygen account ID hardcoded correctly
4. Ed25519 public key matches Keygen account
5. System clock synchronized (for signature verification)

### Problem: Vision API Slow on CPU
**Symptoms**: 30+ seconds per image  
**Expected**: CPU is 5-10x slower than GPU  
**Solution**: Document in README, recommend GPU binaries

---

## 📋 Pre-Public-Release Verification

Before pushing v1.9.0 to public repo and creating production release:

### Critical Path Tests
1. [ ] **Test Purchase Flow**: Buy Developer tier with test card → receive license
2. [ ] **License Validation**: Set license in shimmy binary → vision API works
3. [ ] **Vision Performance**: Benchmark CPU vs GPU (document results)
4. [ ] **Frontend Links**: All download buttons point to v1.9.0 binaries
5. [ ] **Documentation**: README explains licensing clearly

### Sales Pipeline Health
1. [ ] Worker endpoints responding (test + production)
2. [ ] Stripe webhooks configured and delivering
3. [ ] Keygen policies active with correct limits
4. [ ] Frontend deployed and functional
5. [ ] All secrets set in Cloudflare Worker

### Rollback Plan
If any critical test fails:
1. **Do NOT push to public repo**
2. Fix issue in private repo
3. Retag: `git tag -d v1.9.0-test && git tag v1.9.0-test`
4. Retest until all critical tests pass
5. Document failure and fix in changelog

---

## 🎯 Success Criteria

**Definition of "Sales Pipeline Operational"**:
1. ✅ User can complete test purchase from frontend
2. ✅ License key delivered within 60 seconds
3. ✅ License validates in shimmy binary
4. ✅ Vision API accessible with valid license
5. ✅ Vision API returns 401 without license
6. ✅ Portal allows subscription management
7. ✅ All documentation accurate and current

**When to Declare Victory**:
- All 7 success criteria met
- No critical issues in testing phase
- Performance benchmarks documented
- Monitoring alerts configured
- Team confident in production readiness

---

## 📞 Support & Contacts

**Technical Issues**:
- Email: michaelallenkuykendall@gmail.com
- Subject: "SHIMMY VISION LICENSE ISSUE - [brief description]"

**Payment Issues**:
- Check Stripe Dashboard first
- Email with "PAYMENT ISSUE" in subject

**License Issues**:
- Check Keygen Dashboard first
- Include license key (first 10 chars only)

---

**Last Reviewed**: January 9, 2026  
**Next Review**: After v1.9.0 public release  
**Owner**: Michael A. Kuykendall
