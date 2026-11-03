import 'package:flutter_riverpod/flutter_riverpod.dart';

enum DemoRole {
  merchant,
  analyst,
  admin,
}

extension DemoRoleX on DemoRole {
  String get displayName {
    switch (this) {
      case DemoRole.merchant:
        return 'Merchant';
      case DemoRole.analyst:
        return 'Fraud Analyst';
      case DemoRole.admin:
        return 'Admin';
    }
  }

  String get description {
    switch (this) {
      case DemoRole.merchant:
        return 'Store operations, transaction history, and risk summaries.';
      case DemoRole.analyst:
        return 'Review queue, suspicious cases, and forensic factor breakdown.';
      case DemoRole.admin:
        return 'Global system telemetry, threshold inspection, and audit logs.';
    }
  }
}

/// Simulated role provider for demonstration and defense presentation.
///
/// NOTE: In accordance with Master Documentation Rule 11, role-based screen
/// filtering is purely frontend simulation. Real authorization will be
/// enforced server-side by FastAPI in subsequent milestones.
final demoRoleProvider = StateNotifierProvider<DemoRoleNotifier, DemoRole>((ref) {
  return DemoRoleNotifier();
});

class DemoRoleNotifier extends StateNotifier<DemoRole> {
  DemoRoleNotifier() : super(DemoRole.merchant);

  void setRole(DemoRole role) {
    state = role;
  }
}
