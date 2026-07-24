class SessionHistory {
  final String timestamp;
  final double alpha;
  final double beta;
  final double theta;
  final double deviationScore;
  final String riskTier;

  SessionHistory({
    required this.timestamp,
    required this.alpha,
    required this.beta,
    required this.theta,
    required this.deviationScore,
    required this.riskTier,
  });

  factory SessionHistory.fromJson(Map<String, dynamic> json) {
    return SessionHistory(
      timestamp: json["timestamp"],
      alpha: (json["alpha"] as num).toDouble(),
      beta: (json["beta"] as num).toDouble(),
      theta: (json["theta"] as num).toDouble(),
      deviationScore: (json["deviation_score"] as num).toDouble(),
      riskTier: json["risk_tier"],
    );
  }
}