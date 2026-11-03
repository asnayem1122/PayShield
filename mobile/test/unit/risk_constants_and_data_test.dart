import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/config/app_risk_constants.dart';
import 'package:mobile/features/transactions/data/mock_transactions.dart';
import 'package:mobile/features/transactions/domain/transaction_model.dart';

void main() {
  group('AppRiskConstants Unit Tests', () {
    test('Validates score strictly between 0 and 100', () {
      expect(() => AppRiskConstants.validateScore(0), returnsNormally);
      expect(() => AppRiskConstants.validateScore(50), returnsNormally);
      expect(() => AppRiskConstants.validateScore(100), returnsNormally);

      expect(() => AppRiskConstants.validateScore(-1), throwsArgumentError);
      expect(() => AppRiskConstants.validateScore(101), throwsArgumentError);
      expect(() => AppRiskConstants.validateScore(-50), throwsArgumentError);
      expect(() => AppRiskConstants.validateScore(999), throwsArgumentError);
    });

    test('Maps risk score to correct RiskLevel and RiskAction', () {
      expect(AppRiskConstants.getLevelForScore(0), equals(RiskLevel.low));
      expect(AppRiskConstants.getLevelForScore(39), equals(RiskLevel.low));
      expect(AppRiskConstants.getActionForScore(39), equals(RiskAction.approve));

      expect(AppRiskConstants.getLevelForScore(40), equals(RiskLevel.medium));
      expect(AppRiskConstants.getLevelForScore(74), equals(RiskLevel.medium));
      expect(AppRiskConstants.getActionForScore(74), equals(RiskAction.review));

      expect(AppRiskConstants.getLevelForScore(75), equals(RiskLevel.high));
      expect(AppRiskConstants.getLevelForScore(91), equals(RiskLevel.high));
      expect(AppRiskConstants.getLevelForScore(100), equals(RiskLevel.high));
      expect(AppRiskConstants.getActionForScore(91), equals(RiskAction.block));
    });

    test('Transaction entity rejects invalid risk score in constructor', () {
      expect(
        () => Transaction(
          id: 'test_invalid',
          amount: 500,
          merchantName: 'Test Store',
          merchantCategory: 'Retail',
          riskScore: 105, // Invalid
          riskFactors: const [],
          deviceModel: 'Test Device',
          isNewDevice: false,
          location: 'Dhaka',
          transactionsLastHour: 1,
          previousChargebacks: 0,
          timestamp: DateTime.now(),
        ),
        throwsArgumentError,
      );
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
