import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../domain/transaction_model.dart';
import 'canonical_transactions_fixture.dart';

export 'canonical_transactions_fixture.dart';

/// Provider for transaction state with live backend synchronization and offline fallback.
final transactionsProvider =
    StateNotifierProvider<TransactionsNotifier, List<Transaction>>((ref) {
  return TransactionsNotifier();
});

class TransactionsNotifier extends StateNotifier<List<Transaction>> {
  final ApiClient _api = ApiClient();

  TransactionsNotifier() : super(generateCanonicalTransactionsFixture()) {
    // Attempt background sync if backend is reachable
    fetchFromBackend();
  }

  /// Attempts to fetch live transactions from the backend database.
  Future<void> fetchFromBackend() async {
    try {
      final res = await _api.get('/transactions?limit=200');
      if (res is Map && res['items'] is List) {
        final list = (res['items'] as List)
            .map((item) => Transaction.fromJson(item as Map<String, dynamic>))
            .toList();
        if (list.isNotEmpty) {
          state = list;
        }
      }
    } catch (_) {
      // In offline/test mode, cleanly keep canonical seed state
    }
  }

  /// Modifies local state when an analyst resolves a suspicious case.
  void resolveCase(String transactionId, String outcome, String note) {
    state = [
      for (final tx in state)
        if (tx.id == transactionId)
          tx.copyWith(
            analystResolution: outcome,
            analystNotes: note,
          )
        else
          tx,
    ];

    _syncStatusToBackend(transactionId, outcome, note);
  }

  Future<void> _syncStatusToBackend(String ref, String outcome, String note) async {
    try {
      final apiStatus = outcome == 'CONFIRM_FRAUD'
          ? 'BLOCKED'
          : outcome == 'MARK_LEGITIMATE'
              ? 'APPROVED'
              : 'REVIEW';
      await _api.patch('/transactions/$ref/status', {
        'status': apiStatus,
        'notes': note,
        'actor_id': 'flutter_analyst',
      });
    } catch (_) {
      // Ignore network errors in demo/offline mode
    }
  }

  /// Adds a new simulated transaction submitted by a merchant.
  void addSimulatedTransaction(Transaction tx) {
    state = [tx, ...state];

    _submitToBackend(tx);
  }

  Future<void> _submitToBackend(Transaction tx) async {
    try {
      await _api.post('/transactions', {
        'counterparty_name': tx.merchantName,
        'amount': tx.amount.toDecimalString(),
        'currency': tx.currency,
        'channel': 'MOBILE_APP',
        'device_model': tx.deviceModel,
        'location_city': tx.location,
        'is_location_anomaly': tx.location.contains('km from Dhaka'),
        'is_new_device': tx.isNewDevice,
        'has_high_velocity': tx.transactionsLastHour > 3,
        'has_prior_chargebacks': tx.previousChargebacks > 0,
      });
    } catch (_) {
      // Ignore network errors in demo/offline mode
    }
  }
}
