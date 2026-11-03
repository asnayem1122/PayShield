enum RiskLevel { low, medium, high }

enum RiskAction { approve, review, block }

/// Centralized Risk Policy Constants and Thresholds.
///
/// NOTE: In accordance with PayShield architecture, this serves as the
/// client-side contract for displaying backend risk determinations.
/// Business decisions must never be hardcoded independently inside UI widgets.
class AppRiskConstants {
  static const int minScore = 0;
  static const int maxScore = 100;

  static const int lowRiskMaxScore = 39;
  static const int mediumRiskMaxScore = 74;

  /// Validates that a risk score is strictly an integer within [0, 100].
  ///
  /// Throws [ArgumentError] if the score is out of bounds (< 0 or > 100).
  /// This guarantees explicit runtime validation in both debug and release builds.
  static void validateScore(int score) {
    if (score < minScore || score > maxScore) {
      throw ArgumentError.value(
        score,
        'riskScore',
        'Risk score must be an integer between $minScore and $maxScore inclusive.',
      );
    }
  }

  /// Returns true if [score] is an integer within [0, 100].
  static bool isValidScore(int score) => score >= minScore && score <= maxScore;

  /// Determines [RiskLevel] for a validated risk score.
  static RiskLevel getLevelForScore(int score) {
    validateScore(score);
    if (score <= lowRiskMaxScore) {
      return RiskLevel.low;
    } else if (score <= mediumRiskMaxScore) {
      return RiskLevel.medium;
    } else {
      return RiskLevel.high;
    }
  }

  /// Determines recommended [RiskAction] for a validated risk score.
  static RiskAction getActionForScore(int score) {
    final level = getLevelForScore(score);
    switch (level) {
      case RiskLevel.low:
        return RiskAction.approve;
      case RiskLevel.medium:
        return RiskAction.review;
      case RiskLevel.high:
        return RiskAction.block;
    }
  }

  /// Label for UI display.
  static String actionLabel(RiskAction action) {
    switch (action) {
      case RiskAction.approve:
        return 'APPROVE';
      case RiskAction.review:
        return 'REVIEW';
      case RiskAction.block:
        return 'BLOCK';
    }
  }

  /// Educational & Simulation Disclaimers
  static const String simulationDisclaimer =
      'Simulated Telemetry — For Academic Demonstration Only. Not an automated financial decline.';

  static const String featureExplanationDisclaimer =
      'Illustrative Simulated Explanations (Demo Heuristic — Not Production ML SHAP Values).';

  static const String roleSecurityDisclaimer =
      'Frontend Demonstration Behavior Only: Screen filtering does not constitute real security or authorization.';
}
