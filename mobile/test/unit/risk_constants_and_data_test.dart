import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/config/app_risk_constants.dart';
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
    final notifier = TransactionsNotifier();
    final list = notifier.state;

    test('Dataset contains exactly 175 transactions', () {
      expect(list.length, equals(175));
    });

    test('Status counts match: 158 Approved, 14 Review, 3 Blocked', () {
      final approved = list.where((tx) => tx.recommendedAction == RiskAction.approve).length;
      final review = list.where((tx) => tx.recommendedAction == RiskAction.review).length;
      final blocked = list.where((tx) => tx.recommendedAction == RiskAction.block).length;

      expect(approved, equals(158));
      expect(review, equals(14));
      expect(blocked, equals(3));
      expect(approved + review + blocked, equals(175));

      final approvalRate = (approved / 175) * 100;
      final reviewRate = (review / 175) * 100;
      final blockRate = (blocked / 175) * 100;

      expect(approvalRate.toStringAsFixed(1), equals('90.3'));
      expect(reviewRate.toStringAsFixed(1), equals('8.0'));
      expect(blockRate.toStringAsFixed(1), equals('1.7'));
    });

    test('Total transaction volume sums exactly to ৳ 482,500.00', () {
      final totalVolume = list.fold<double>(0.0, (acc, tx) => acc + tx.amount);
      expect(totalVolume, equals(482500.0));
    });

    test('Local mock state modification updates analyst case resolution', () {
      final testTxId = list.first.id;
      notifier.resolveCase(testTxId, 'CONFIRM_FRAUD', 'Confirmed by automated test');

      final updated = notifier.state.firstWhere((tx) => tx.id == testTxId);
      expect(updated.analystResolution, equals('CONFIRM_FRAUD'));
      expect(updated.analystNotes, equals('Confirmed by automated test'));
    });
  });
}
