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

    test('Rejects floating-point arithmetic errors on repeated fractional addition', () {
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
        'counterparty_name': 'Shadhin Pay',
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

    test('Transaction.toJson accurately produces decimal wire format', () {
      final tx = Transaction(
        id: 'tx_app_1157',
        amount: Money.fromMajor(1514),
        currency: 'BDT',
        merchantName: 'Shadhin Pay',
        merchantCategory: 'Retail',
        riskScore: 25,
        riskFactors: const ['NEW_DEVICE'],
        deviceModel: 'Samsung Galaxy A53',
        isNewDevice: true,
        location: 'Dhaka',
        transactionsLastHour: 1,
        previousChargebacks: 0,
        timestamp: DateTime.parse('2026-11-04T05:22:15.000Z'),
        analystResolution: 'MARK_LEGITIMATE',
      );

      final json = tx.toJson();
      expect(json['reference'], equals('tx_app_1157'));
      expect(json['amount'], equals('1514.00'));
      expect(json['currency'], equals('BDT'));
      expect(json['transaction_status'], equals('APPROVED'));
    });
  });
}
