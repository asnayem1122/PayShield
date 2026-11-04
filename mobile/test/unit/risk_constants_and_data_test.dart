import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/config/app_risk_constants.dart';
import 'package:mobile/core/utils/money.dart';
import 'package:mobile/features/transactions/data/mock_transactions.dart';
import 'package:mobile/features/transactions/domain/transaction_model.dart';

void main() {
  group('AppRiskConstants Unit Tests', () {
    test('Validates score strictly between 0 and 100 with explicit ArgumentError', () {
      // Boundary valid values
      expect(() => AppRiskConstants.validateScore(0), returnsNormally);
      expect(AppRiskConstants.isValidScore(0), isTrue);

      expect(() => AppRiskConstants.validateScore(50), returnsNormally);
      expect(AppRiskConstants.isValidScore(50), isTrue);

      expect(() => AppRiskConstants.validateScore(100), returnsNormally);
      expect(AppRiskConstants.isValidScore(100), isTrue);

      // Boundary invalid values
      expect(() => AppRiskConstants.validateScore(-1), throwsA(isA<ArgumentError>()));
      expect(AppRiskConstants.isValidScore(-1), isFalse);

      expect(() => AppRiskConstants.validateScore(101), throwsA(isA<ArgumentError>()));
      expect(AppRiskConstants.isValidScore(101), isFalse);

      expect(() => AppRiskConstants.validateScore(-50), throwsA(isA<ArgumentError>()));
      expect(AppRiskConstants.isValidScore(-50), isFalse);

      expect(() => AppRiskConstants.validateScore(999), throwsA(isA<ArgumentError>()));
      expect(AppRiskConstants.isValidScore(999), isFalse);
    });

    test('Maps risk score to correct RiskLevel and RiskAction', () {
      expect(AppRiskConstants.getLevelForScore(0), equals(RiskLevel.low));
      expect(AppRiskConstants.getLevelForScore(39), equals(RiskLevel.low));
      expect(AppRiskConstants.getActionForScore(0), equals(RiskAction.approve));
      expect(AppRiskConstants.getActionForScore(39), equals(RiskAction.approve));

      expect(AppRiskConstants.getLevelForScore(40), equals(RiskLevel.medium));
      expect(AppRiskConstants.getLevelForScore(74), equals(RiskLevel.medium));
      expect(AppRiskConstants.getActionForScore(40), equals(RiskAction.review));
      expect(AppRiskConstants.getActionForScore(74), equals(RiskAction.review));

      expect(AppRiskConstants.getLevelForScore(75), equals(RiskLevel.high));
      expect(AppRiskConstants.getLevelForScore(91), equals(RiskLevel.high));
      expect(AppRiskConstants.getLevelForScore(100), equals(RiskLevel.high));
      expect(AppRiskConstants.getActionForScore(75), equals(RiskAction.block));
      expect(AppRiskConstants.getActionForScore(91), equals(RiskAction.block));
      expect(AppRiskConstants.getActionForScore(100), equals(RiskAction.block));

      // Out-of-bounds score mapping throws ArgumentError
      expect(() => AppRiskConstants.getLevelForScore(-1), throwsA(isA<ArgumentError>()));
      expect(() => AppRiskConstants.getLevelForScore(101), throwsA(isA<ArgumentError>()));
      expect(() => AppRiskConstants.getActionForScore(-1), throwsA(isA<ArgumentError>()));
      expect(() => AppRiskConstants.getActionForScore(101), throwsA(isA<ArgumentError>()));
    });

    test('Transaction entity constructor rejects invalid scores with ArgumentError and accepts 0 and 100', () {
      Transaction createTx(int score) => Transaction(
            id: 'test_tx_$score',
            amount: 500,
            merchantName: 'Test Store',
            merchantCategory: 'Retail',
            riskScore: score,
            riskFactors: const [],
            deviceModel: 'Test Device',
            isNewDevice: false,
            location: 'Dhaka',
            transactionsLastHour: 1,
            previousChargebacks: 0,
            timestamp: DateTime(2026, 11, 4),
          );

      // Score -1 must throw ArgumentError (not AssertionError)
      expect(() => createTx(-1), throwsA(isA<ArgumentError>()));

      // Score 101 must throw ArgumentError (not AssertionError)
      expect(() => createTx(101), throwsA(isA<ArgumentError>()));

      // Score 0 must be accepted
      expect(() => createTx(0), returnsNormally);
      final tx0 = createTx(0);
      expect(tx0.riskScore, equals(0));
      expect(tx0.riskLevel, equals(RiskLevel.low));
      expect(tx0.recommendedAction, equals(RiskAction.approve));

      // Score 100 must be accepted
      expect(() => createTx(100), returnsNormally);
      final tx100 = createTx(100);
      expect(tx100.riskScore, equals(100));
      expect(tx100.riskLevel, equals(RiskLevel.high));
      expect(tx100.recommendedAction, equals(RiskAction.block));

      // copyWith must also enforce ArgumentError
      expect(() => tx0.copyWith(riskScore: -1), throwsA(isA<ArgumentError>()));
      expect(() => tx0.copyWith(riskScore: 101), throwsA(isA<ArgumentError>()));
      expect(() => tx0.copyWith(riskScore: 100), returnsNormally);
    });
  });

  group('Canonical Mock Dataset Reconciled Consistency', () {
    final list = generateCanonicalTransactionsFixture();

    test('Dataset contains exactly 175 transactions with unique references', () {
      expect(list.length, equals(175));
      final uniqueIds = list.map((tx) => tx.id).toSet();
      expect(uniqueIds.length, equals(175));
    });

    test('Status counts match: 158 Approved, 14 Review, 3 Blocked', () {
      final approved = list.where((tx) => tx.recommendedAction == RiskAction.approve).toList();
      final review = list.where((tx) => tx.recommendedAction == RiskAction.review).toList();
      final blocked = list.where((tx) => tx.recommendedAction == RiskAction.block).toList();

      expect(approved.length, equals(158));
      expect(review.length, equals(14));
      expect(blocked.length, equals(3));
      expect(approved.length + review.length + blocked.length, equals(175));

      final approvalRate = (approved.length / 175) * 100;
      final reviewRate = (review.length / 175) * 100;
      final blockRate = (blocked.length / 175) * 100;

      expect(approvalRate.toStringAsFixed(1), equals('90.3'));
      expect(reviewRate.toStringAsFixed(1), equals('8.0'));
      expect(blockRate.toStringAsFixed(1), equals('1.7'));
    });

    test('All 175 transactions have strictly positive amounts', () {
      for (final tx in list) {
        expect(tx.amount.minorUnits > 0, isTrue,
            reason: '${tx.id} has non-positive amount ${tx.amount.toDecimalString()}');
      }

      final approvedTxs = list.where((t) => t.recommendedAction == RiskAction.approve).toList();
      final minApp = approvedTxs.map((t) => t.amount.minorUnits).reduce((a, b) => a < b ? a : b);
      final maxApp = approvedTxs.map((t) => t.amount.minorUnits).reduce((a, b) => a > b ? a : b);

      expect(minApp, equals(100700)); // ৳ 1,007.00
      expect(maxApp, equals(263000)); // ৳ 2,630.00
    });

    test('Merchant category counts are correctly distributed', () {
      final categories = <String, int>{};
      for (final tx in list) {
        categories[tx.merchantCategory] = (categories[tx.merchantCategory] ?? 0) + 1;
      }

      expect(categories.containsKey('Electronics'), isTrue);
      expect(categories.containsKey('Fashion'), isTrue);
      expect(categories.containsKey('Grocery'), isTrue);
      expect(categories.containsKey('Footwear'), isTrue);
      expect(categories.containsKey('Retail'), isTrue);
      expect(categories.containsKey('Jewelry'), isTrue);
      expect(categories.containsKey('Digital Goods'), isTrue);
    });

    test('Exact financial volumes in integer minor units without floating-point error', () {
      final appVol = list
          .where((t) => t.recommendedAction == RiskAction.approve)
          .fold<Money>(Money.zero, (acc, tx) => acc + tx.amount);
      final revVol = list
          .where((t) => t.recommendedAction == RiskAction.review)
          .fold<Money>(Money.zero, (acc, tx) => acc + tx.amount);
      final blkVol = list
          .where((t) => t.recommendedAction == RiskAction.block)
          .fold<Money>(Money.zero, (acc, tx) => acc + tx.amount);
      final totVol = list.fold<Money>(Money.zero, (acc, tx) => acc + tx.amount);

      expect(appVol.minorUnits, equals(28020000)); // ৳ 280,200.00
      expect(appVol.toDecimalString(), equals('280200.00'));

      expect(revVol.minorUnits, equals(14730000)); // ৳ 147,300.00
      expect(revVol.toDecimalString(), equals('147300.00'));

      expect(blkVol.minorUnits, equals(5500000)); // ৳ 55,000.00
      expect(blkVol.toDecimalString(), equals('55000.00'));

      expect(totVol.minorUnits, equals(48250000)); // ৳ 482,500.00
      expect(totVol.toDecimalString(), equals('482500.00'));
    });

    test('tx_app_1157 specific regression test for v1.0.1 canonical remediation', () {
      final tx1157 = list.firstWhere((tx) => tx.id == 'tx_app_1157');
      expect(tx1157.id, equals('tx_app_1157'));
      expect(tx1157.amount.minorUnits, equals(151400));
      expect(tx1157.amount.toDecimalString(), equals('1514.00'));
      expect(tx1157.riskScore, equals(25));
      expect(tx1157.riskLevel, equals(RiskLevel.low));
      expect(tx1157.recommendedAction, equals(RiskAction.approve));
      expect(tx1157.currency, equals('BDT'));
    });

    test('Local mock state modification updates analyst case resolution', () {
      final notifier = TransactionsNotifier();
      final testTxId = list.first.id;
      notifier.resolveCase(testTxId, 'CONFIRM_FRAUD', 'Confirmed by automated test');

      final updated = notifier.state.firstWhere((tx) => tx.id == testTxId);
      expect(updated.analystResolution, equals('CONFIRM_FRAUD'));
      expect(updated.analystNotes, equals('Confirmed by automated test'));
    });
  });
}
