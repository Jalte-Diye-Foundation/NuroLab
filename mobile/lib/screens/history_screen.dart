import 'package:flutter/material.dart';
import '../models/session_history.dart';
import '../services/api_service.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final ApiService _apiService = ApiService();

  // TODO: replace with the real logged-in user id once auth is added.
  final String userId = "vandana";

  late Future<List<SessionHistory>> _historyFuture;

  @override
  void initState() {
    super.initState();
    _historyFuture = _apiService.getSessionHistory(userId);
  }

  Future<void> _refresh() async {
    setState(() {
      _historyFuture = _apiService.getSessionHistory(userId);
    });
    await _historyFuture;
  }

  Color _riskColor(String riskTier) {
    switch (riskTier.toLowerCase()) {
      case "high":
        return Colors.red.shade200;
      case "moderate":
        return Colors.orange.shade200;
      case "mild":
        return Colors.yellow.shade200;
      default:
        return Colors.green.shade200;
    }
  }

  String _formatTimestamp(String rawTimestamp) {
    final parsed = DateTime.tryParse(rawTimestamp);

    if (parsed == null) return rawTimestamp;

    final local = parsed.toLocal();
    final datePart =
        "${local.year}-${local.month.toString().padLeft(2, '0')}-${local.day.toString().padLeft(2, '0')}";
    final timePart =
        "${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}";

    return "$datePart  $timePart";
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Session History"),
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<SessionHistory>>(
          future: _historyFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }

            if (snapshot.hasError) {
              return ListView(
                children: [
                  const SizedBox(height: 100),
                  Icon(
                    Icons.error_outline,
                    size: 48,
                    color: Colors.red.shade300,
                  ),
                  const SizedBox(height: 12),
                  const Center(
                    child: Text(
                      "Couldn't load session history.\nPull down to try again.",
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              );
            }

            final sessions = snapshot.data ?? [];

            if (sessions.isEmpty) {
              return ListView(
                children: [
                  const SizedBox(height: 100),
                  Icon(
                    Icons.history,
                    size: 48,
                    color: Colors.grey.shade400,
                  ),
                  const SizedBox(height: 12),
                  const Center(
                    child: Text(
                      "No sessions found",
                      style: TextStyle(fontSize: 16),
                    ),
                  ),
                ],
              );
            }

            return ListView.builder(
              itemCount: sessions.length,
              itemBuilder: (context, index) {
                final session = sessions[index];

                return Card(
                  margin: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              _formatTimestamp(session.timestamp),
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Chip(
                              label: Text(session.riskTier),
                              backgroundColor: _riskColor(session.riskTier),
                            ),
                          ],
                        ),

                        const SizedBox(height: 10),

                        Row(
                          mainAxisAlignment:
                              MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              "Alpha: ${session.alpha.toStringAsFixed(2)}",
                            ),
                            Text(
                              "Beta: ${session.beta.toStringAsFixed(2)}",
                            ),
                            Text(
                              "Theta: ${session.theta.toStringAsFixed(2)}",
                            ),
                          ],
                        ),

                        const SizedBox(height: 10),

                        Text(
                          "Deviation Score: ${session.deviationScore.toStringAsFixed(2)}",
                        ),
                        const SizedBox(height: 12),

SizedBox(
  width: double.infinity,
  child: ElevatedButton.icon(
    icon: const Icon(Icons.picture_as_pdf),
    label: const Text("Download PDF"),
    onPressed: () async {
      await _apiService.downloadPdfReport({
        "timestamp": session.timestamp,
        "alpha_de": session.alpha,
        "beta_de": session.beta,
        "theta_de": session.theta,
        "deviation_score": session.deviationScore,
        "risk_tier": session.riskTier,

        // Values expected by the backend PDF generator
        "delta_de": 0.0,
        "gamma_de": 0.0,
        "condition_label": "normal",
        "context": "session",
        "explanations": [],

        // Predictions (replace with real values later if you add them to history)
        "stress_prediction": 0.0,
        "attention_prediction": 0.0,
        "fatigue_prediction": 0.0,
      });

      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("PDF downloaded successfully"),
          ),
        );
      }
    },
  ),
),
                      ],
                    ),
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }
}