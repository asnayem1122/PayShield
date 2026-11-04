import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/network/api_client.dart';
import 'package:mobile/core/utils/money.dart';
import 'package:mobile/features/transactions/domain/transaction_model.dart';

void main() {
  group('ApiClient Unit Tests', () {
    test('Default base URL is configured properly for platform', () {
      final client = ApiClient();
      expect(client.baseUrl, isNotEmpty);
      expect(client.baseUrl, contains('/api/v1'));
    });

    test('Allows overriding base URL', () {
      final client = ApiClient();
      final orig = client.baseUrl;
      client.setBaseUrl('http://test-server:9000/api/v1');
      expect(client.baseUrl, equals('http://test-server:9000/api/v1'));
      client.setBaseUrl(orig);
    });
  });

  group('Decimal-Safe Money Value Object', () {
    test('Parses decimal string without floating-point conversion', () {
      final m1 = Money.fromDecimalString('1514.00');
      expect(m1.minorUnits, equals(151400));
      expect(m1.toDecimalString(), equals('1514.00'));
      expect(m1.toFormattedBdt(), equals('৳ 1,514.00'));

      final m2 = Money.fromDecimalString('280200.50');
      expect(m2.minorUnits, equals(28020050));
      expect(m2.toDecimalString(), equals('280200.50'));

      final sum = m1 + m2;
      expect(sum.minorUnits, equals(151400 + 28020050));
      expect(sum.toDecimalString(), equals('281714.50'));
    });

    test('Parses valid positive decimal strings up to NUMERIC(12, 2) maximum', () {
      final validTypical = Money.fromDecimalString('1250.00');
      expect(validTypical.minorUnits, equals(125000));
      expect(validTypical.toDecimalString(), equals('1250.00'));

      final maxMoney = Money.fromDecimalString('9999999999.99');
      expect(maxMoney.minorUnits, equals(999999999999));
      expect(maxMoney.toDecimalString(), equals('9999999999.99'));

      // Boundary: Minimum positive minor unit (0.01 BDT)
      final minPositive = Money.fromDecimalString('0.01');
      expect(minPositive.minorUnits, equals(1));
      expect(minPositive.toDecimalString(), equals('0.01'));

      // Legitimate zero-valued aggregate (e.g. 0.00 BDT blocked volume on clean dashboard)
      final zeroMoney = Money.fromDecimalString('0.00');
      expect(zeroMoney.minorUnits, equals(0));
      expect(zeroMoney.isZero, isTrue);
      expect(zeroMoney.toDecimalString(), equals('0.00'));
      expect(zeroMoney.toFormattedBdt(), equals('৳ 0.00'));
      expect(zeroMoney.toCompactBdt(), equals('৳ 0'));
    });

    test('Rejects malformed strings, invalid decimals, and bounds overflow', () {
      // Empty string
      expect(() => Money.fromDecimalString(''), throwsA(isA<FormatException>()));

      // Missing leading digits or trailing digits
      expect(() => Money.fromDecimalString('.50'), throwsA(isA<FormatException>()));
      expect(() => Money.fromDecimalString('50.'), throwsA(isA<FormatException>()));

      // Explicit plus sign or scientific notation
      expect(() => Money.fromDecimalString('+12.50'), throwsA(isA<FormatException>()));
      expect(() => Money.fromDecimalString('1e2'), throwsA(isA<FormatException>()));

      // Malformed string
      expect(() => Money.fromDecimalString('abc'), throwsA(isA<FormatException>()));

      // Leading, trailing, and internal whitespace (must not be silently trimmed)
      expect(() => Money.fromDecimalString(' 1250.00'), throwsA(isA<FormatException>()));
      expect(() => Money.fromDecimalString('1250.00 '), throwsA(isA<FormatException>()));
      expect(() => Money.fromDecimalString(' 1250.00 '), throwsA(isA<FormatException>()));
      expect(() => Money.fromDecimalString('12 50.00'), throwsA(isA<FormatException>()));

      // More than two decimal places
      expect(() => Money.fromDecimalString('12.345'), throwsA(isA<FormatException>()));

      // Single decimal place
      expect(() => Money.fromDecimalString('12.3'), throwsA(isA<FormatException>()));

      // Missing decimal point
      expect(() => Money.fromDecimalString('1250'), throwsA(isA<FormatException>()));

      // More than ten integer digits (exceeds NUMERIC(12, 2) max)
      expect(() => Money.fromDecimalString('10000000000.00'), throwsA(isA<FormatException>()));
    });

    test('Direct out-of-range minor units throws ArgumentError at runtime', () {
      // Values outside PostgreSQL NUMERIC(12, 2) bounds must throw ArgumentError at runtime
      expect(() => Money(1000000000000), throwsA(isA<ArgumentError>()));
      expect(() => Money(-1000000000000), throwsA(isA<ArgumentError>()));
      expect(() => Money.fromMinorUnits(999999999999999), throwsA(isA<ArgumentError>()));

      // Money.zero and boundary values must succeed
      expect(Money.zero.minorUnits, equals(0));
      expect(Money(Money.maxMinorUnits).minorUnits, equals(999999999999));
      expect(Money(Money.minMinorUnits).minorUnits, equals(-999999999999));
    });

    test('Repeated addition preserves exact integer minor units without floating-point error', () {
      var acc = Money.zero;
      for (var i = 0; i < 10; i++) {
        acc += Money.fromDecimalString('0.10');
      }
      expect(acc.minorUnits, equals(100)); // Exactly 1.00 BDT
      expect(acc.toDecimalString(), equals('1.00'));
    });
  });

  group('Transaction Serialization & Wire Contract', () {
    test('Transaction.fromJson accurately parses canonical JSON payload into Money', () {
      final json = {
        'id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
        'reference': 'tx_app_1157',
        'counterparty_name': 'PayShield Demo Merchant',
        'amount': '1514.00',
        'currency': 'BDT',
        'channel': 'MOBILE_APP',
        'device_model': 'Samsung Galaxy A53',
        'location_city': 'Dhaka',
        'is_location_anomaly': false,
        'risk_score': 25,
        'risk_level': 'LOW',
        'recommended_action': 'APPROVE',
        'transaction_status': 'APPROVED',
        'created_at': '2026-11-04T05:22:15.000000Z',
      };

      final tx = Transaction.fromJson(json);
      expect(tx.id, equals('tx_app_1157'));
      expect(tx.amount.minorUnits, equals(151400));
      expect(tx.amount.toDecimalString(), equals('1514.00'));
      expect(tx.currency, equals('BDT'));
      expect(tx.riskScore, equals(25));
      expect(tx.analystResolution, equals('MARK_LEGITIMATE'));
      expect(tx.deviceModel, equals('Samsung Galaxy A53'));
      expect(tx.location, equals('Dhaka'));
    });

    test('Transaction.fromJson strictly rejects JSON numbers and non-string amounts', () {
      final numericJson = {
        'reference': 'tx_invalid_1',
        'amount': 1250.00, // JSON double - must be rejected
      };
      expect(() => Transaction.fromJson(numericJson), throwsA(isA<FormatException>()));

      final intJson = {
        'reference': 'tx_invalid_2',
        'amount': 1250, // JSON int - must be rejected
      };
      expect(() => Transaction.fromJson(intJson), throwsA(isA<FormatException>()));

      final boolJson = {
        'reference': 'tx_invalid_bool',
        'amount': true,
      };
      expect(() => Transaction.fromJson(boolJson), throwsA(isA<FormatException>()));

      final listJson = {
        'reference': 'tx_invalid_list',
        'amount': ['1250.00'],
      };
      expect(() => Transaction.fromJson(listJson), throwsA(isA<FormatException>()));

      final emptyJson = {
        'reference': 'tx_invalid_empty',
        'amount': '',
      };
      expect(() => Transaction.fromJson(emptyJson), throwsA(isA<FormatException>()));

      final sciJson = {
        'reference': 'tx_invalid_sci',
        'amount': '1.5e3',
      };
      expect(() => Transaction.fromJson(sciJson), throwsA(isA<FormatException>()));
    });

    test('Transaction.fromJson strictly rejects missing or null amount field', () {
      final missingAmount = {
        'reference': 'tx_invalid_3',
      };
      expect(() => Transaction.fromJson(missingAmount), throwsA(isA<FormatException>()));

      final nullAmount = {
        'reference': 'tx_invalid_4',
        'amount': null,
      };
      expect(() => Transaction.fromJson(nullAmount), throwsA(isA<FormatException>()));
    });

    test('Transaction.fromJson strictly rejects non-positive transaction amounts', () {
      final zeroJson = {
        'reference': 'tx_invalid_zero',
        'amount': '0.00',
      };
      expect(() => Transaction.fromJson(zeroJson), throwsA(isA<FormatException>()));

      final negativeJson = {
        'reference': 'tx_invalid_neg',
        'amount': '-10.00',
      };
      expect(() => Transaction.fromJson(negativeJson), throwsA(isA<FormatException>()));
    });

    test('Transaction constructor rejects zero or negative amounts', () {
      expect(
        () => Transaction(
          id: 'tx_test_zero',
          amount: Money.zero,
          merchantName: 'PayShield Demo Merchant',
          merchantCategory: 'Retail',
          riskScore: 20,
          riskFactors: const [],
          deviceModel: 'Test Device',
          isNewDevice: false,
          location: 'Dhaka',
          transactionsLastHour: 1,
          previousChargebacks: 0,
          timestamp: DateTime.now(),
        ),
        throwsA(isA<ArgumentError>()),
      );

      expect(
        () => Transaction(
          id: 'tx_test_neg',
          amount: Money.fromDecimalString('-10.00'),
          merchantName: 'PayShield Demo Merchant',
          merchantCategory: 'Retail',
          riskScore: 20,
          riskFactors: const [],
          deviceModel: 'Test Device',
          isNewDevice: false,
          location: 'Dhaka',
          transactionsLastHour: 1,
          previousChargebacks: 0,
          timestamp: DateTime.now(),
        ),
        throwsA(isA<ArgumentError>()),
      );
    });

    test('Transaction.fromJson strictly rejects whitespace in wire amount', () {
      final leadingWhitespace = {
        'reference': 'tx_ws_1',
        'amount': ' 1500.00',
      };
      expect(() => Transaction.fromJson(leadingWhitespace), throwsA(isA<FormatException>()));

      final trailingWhitespace = {
        'reference': 'tx_ws_2',
        'amount': '1500.00 ',
      };
      expect(() => Transaction.fromJson(trailingWhitespace), throwsA(isA<FormatException>()));

      final internalWhitespace = {
        'reference': 'tx_ws_3',
        'amount': '15 00.00',
      };
      expect(() => Transaction.fromJson(internalWhitespace), throwsA(isA<FormatException>()));
    });

    test('Transaction.copyWith uses strongly typed Money? amount', () {
      final original = Transaction(
        id: 'tx_copy_test',
        amount: Money.fromDecimalString('1500.00'),
        currency: 'BDT',
        merchantName: 'PayShield Demo Merchant',
        merchantCategory: 'Retail',
        riskScore: 25,
        riskFactors: const ['NEW_DEVICE'],
        deviceModel: 'Test Device',
        isNewDevice: true,
        location: 'Dhaka',
        transactionsLastHour: 1,
        previousChargebacks: 0,
        timestamp: DateTime.parse('2026-11-04T00:00:00.000Z'),
      );

      final updated = original.copyWith(amount: Money.fromDecimalString('3000.00'));
      expect(updated.amount.toDecimalString(), equals('3000.00'));
      expect(updated.amount.minorUnits, equals(300000));
      expect(updated.id, equals(original.id));

      final unchanged = original.copyWith();
      expect(unchanged.amount, equals(original.amount));
    });

    test('Transaction decimal serialization round trip', () {
      final original = Transaction(
        id: 'tx_roundtrip_1001',
        amount: Money.fromDecimalString('2630.00'),
        currency: 'BDT',
        merchantName: 'PayShield Demo Merchant',
        merchantCategory: 'Retail',
        riskScore: 35,
        riskFactors: const ['NEW_DEVICE'],
        deviceModel: 'Customer Handset',
        isNewDevice: true,
        location: 'Chittagong',
        transactionsLastHour: 2,
        previousChargebacks: 0,
        timestamp: DateTime.parse('2026-11-04T00:00:00.000Z'),
      );

      final json = original.toJson();
      expect(json['amount'], equals('2630.00'));
      expect(json['amount'], isA<String>());

      final restored = Transaction.fromJson(json);
      expect(restored.id, equals(original.id));
      expect(restored.amount, equals(original.amount));
      expect(restored.amount.toDecimalString(), equals('2630.00'));
      expect(restored.currency, equals('BDT'));
    });
  });
}
