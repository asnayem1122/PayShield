import '../../../core/utils/money.dart';
import '../domain/transaction_model.dart';

/// Explicit version identifier for the canonical transaction schedule.
const String canonicalFixtureVersion = 'v1.0.1-canonical-remediated';

/// Generates the authoritative 175-transaction canonical dataset.
/// Reconciled v1.0.1 amounts ensure:
/// - 158 Approved transactions sum to exactly ৳ 280,200.00
/// - 14 Review transactions sum to exactly ৳ 147,300.00
/// - 3 Blocked transactions sum to exactly ৳ 55,000.00
/// - Total monitored volume sums to exactly ৳ 482,500.00
/// - All 158 approved amounts are strictly positive (range: ৳ 1,007.00 - ৳ 2,630.00)
/// - Row 157 (tx_app_1157) is exactly ৳ 1,514.00 (derived via 1859 - 345 surplus offset)
List<Transaction> generateCanonicalTransactionsFixture() {
  final now = DateTime.utc(2026, 11, 4, 0, 0, 0);
  final list = <Transaction>[];

  // 1. Three High-Risk Blocked Transactions (Total: ৳ 55,000.00)
  list.add(
    Transaction(
      id: 'tx_c6b8d0f2_block',
      amount: Money.fromMajor(12500),
      currency: 'BDT',
      merchantName: 'TechPulse Gadgets Ltd',
      merchantCategory: 'Electronics',
      riskScore: 91,
      riskFactors: const [
        'NEW_DEVICE',
        'HIGH_VELOCITY',
        'UNUSUAL_LOCATION',
        'PREVIOUS_CHARGEBACK',
      ],
      deviceModel: 'Pixel 8 Pro (New device)',
      isNewDevice: true,
      location: 'Sylhet (240km from Dhaka)',
      transactionsLastHour: 7,
      previousChargebacks: 1,
      timestamp: now.subtract(const Duration(minutes: 12)),
    ),
  );

  list.add(
    Transaction(
      id: 'tx_7e9a4f10_block',
      amount: Money.fromMajor(24000),
      currency: 'BDT',
      merchantName: 'Dhaka Luxe Watch Boutique',
      merchantCategory: 'Jewelry',
      riskScore: 88,
      riskFactors: const [
        'HIGH_AMOUNT',
        'VELOCITY_BURST',
        'SUSPICIOUS_IP',
      ],
      deviceModel: 'iPhone 15 Pro Max',
      isNewDevice: true,
      location: 'Chittagong',
      transactionsLastHour: 9,
      previousChargebacks: 2,
      timestamp: now.subtract(const Duration(hours: 1, minutes: 40)),
    ),
  );

  list.add(
    Transaction(
      id: 'tx_3d2c1b99_block',
      amount: Money.fromMajor(18500),
      currency: 'BDT',
      merchantName: 'Apex Digital Hub',
      merchantCategory: 'Digital Goods',
      riskScore: 79,
      riskFactors: const [
        'RAPID_RETRY',
        'FOREIGN_BIN',
      ],
      deviceModel: 'Linux Desktop / Chrome',
      isNewDevice: true,
      location: 'Rajshahi',
      transactionsLastHour: 6,
      previousChargebacks: 0,
      timestamp: now.subtract(const Duration(hours: 3, minutes: 15)),
    ),
  );

  // 2. Fourteen Medium-Risk Under Review Transactions (Total: ৳ 147,300.00)
  final reviewData = [
    (8500, 58, 'Shwapno Superstore', 'Grocery', 'Dhaka', ['UNUSUAL_HOUR']),
    (14200, 68, 'TechPulse Gadgets Ltd', 'Electronics', 'Khulna', ['NEW_DEVICE']),
    (9800, 52, 'Aarong Lifestyle', 'Fashion', 'Dhaka', ['VELOCITY_WARN']),
    (11500, 71, 'Yellow Clothing Ltd', 'Fashion', 'Chittagong', ['HIGH_AMOUNT']),
    (7400, 48, 'Daraz Bangladesh Express', 'Retail', 'Sylhet', ['DISTANCE_DELTA']),
    (16000, 74, 'Star Tech IT Corner', 'Electronics', 'Dhaka', ['MULTIPLE_CARDS']),
    (8900, 61, 'Ryans Computers Ltd', 'Electronics', 'Barisal', ['DEVICE_MISMATCH']),
    (10200, 55, 'Pickaboo Mobile Store', 'Electronics', 'Dhaka', ['NEW_ACCOUNT']),
    (12800, 67, 'Chaldal Premium Store', 'Grocery', 'Dhaka', ['VELOCITY_WARN']),
    (6500, 44, 'Sailor Outlet', 'Fashion', 'Comilla', ['OFF_HOURS']),
    (9100, 59, 'Lotto Bangladesh Ltd', 'Footwear', 'Dhaka', ['DISTANCE_DELTA']),
    (13400, 72, 'TechPulse Gadgets Ltd', 'Electronics', 'Mymensingh', ['NEW_DEVICE']),
    (7800, 46, 'Agora Superstore', 'Grocery', 'Dhaka', ['UNUSUAL_HOUR']),
    (11200, 65, 'Cats Eye Fashion', 'Fashion', 'Dhaka', ['HIGH_AMOUNT']),
  ];

  for (var i = 0; i < reviewData.length; i++) {
    final (amountMajor, score, merchant, category, city, factors) = reviewData[i];
    list.add(
      Transaction(
        id: 'tx_rev_${100 + i}',
        amount: Money.fromMajor(amountMajor),
        currency: 'BDT',
        merchantName: merchant,
        merchantCategory: category,
        riskScore: score,
        riskFactors: factors,
        deviceModel: 'Samsung Galaxy A54',
        isNewDevice: factors.contains('NEW_DEVICE'),
        location: city,
        transactionsLastHour: 3,
        previousChargebacks: 0,
        timestamp: now.subtract(Duration(hours: i + 1, minutes: i * 7)),
      ),
    );
  }

  // 3. 158 Low-Risk Approved Transactions (Total: ৳ 280,200.00)
  // Deterministic amounts summing exactly to 280,200.00 BDT
  final approvedSeedAmounts = [
    1850, 1600, 1450, 2100, 1950, 1300, 2200, 1750, 2400, 1250,
    1900, 1700, 1550, 2050, 1800, 1400, 2150, 1650, 2300, 1350,
  ];

  final approvedMerchants = [
    ('TechPulse Gadgets Ltd', 'Electronics'),
    ('Aarong Lifestyle', 'Fashion'),
    ('Shwapno Superstore', 'Grocery'),
    ('Bata Bangladesh', 'Footwear'),
    ('Chaldal Express', 'Grocery'),
    ('Daraz Bangladesh', 'Retail'),
  ];

  for (var i = 0; i < 158; i++) {
    final fI = approvedSeedAmounts[i % approvedSeedAmounts.length] + ((i * 37) % 700);
    final deduction = i <= 150 ? 346 : 345;
    final amountMajor = fI - deduction;
    final amount = Money.fromMajor(amountMajor);

    final (merchant, category) = approvedMerchants[i % approvedMerchants.length];
    final score = 8 + (i % 28); // 8 to 35 (always Low Risk)

    list.add(
      Transaction(
        id: 'tx_app_${1000 + i}',
        amount: amount,
        currency: 'BDT',
        merchantName: merchant,
        merchantCategory: category,
        riskScore: score,
        riskFactors: const [],
        deviceModel: 'Verified Customer Device',
        isNewDevice: false,
        location: 'Dhaka',
        transactionsLastHour: 1,
        previousChargebacks: 0,
        timestamp: now.subtract(Duration(minutes: (i + 1) * 14)),
      ),
    );
  }

  return list;
}
