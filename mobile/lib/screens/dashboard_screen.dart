import 'dart:async';
import 'package:flutter/material.dart';
import '../services/websocket_service.dart';
import '../widgets/metric_card.dart';
import 'history_screen.dart';
import '../services/api_service.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final WebSocketService _webSocketService = WebSocketService();
  final ApiService _apiService = ApiService();

  double attention = 0;
  double stress = 0;
  double fatigue = 0;
  double signal = 0;

  List<double> attentionHistory = [];
  List<double> stressHistory = [];
  List<double> fatigueHistory = [];
  List<double> signalHistory = [];

  List<double> engagementHistory = [];
  List<double> relaxationHistory = [];
  List<double> cognitiveLoadHistory = [];

  List<double> alphaHistory = [];
  List<double> betaHistory = [];
  List<double> thetaHistory = [];

  double avgAttention = 0;
  double avgStress = 0;
  double avgFatigue = 0;
  double avgSignal = 0;

  double avgEngagement = 0;
  double avgRelaxation = 0;
  double avgCognitiveLoad = 0;

  double avgAlpha = 0;
  double avgBeta = 0;
  double avgTheta = 0;

  double delta = 0;
  double theta = 0;
  double alpha = 0;
  double beta = 0;
  double gamma = 0;

  double engagement = 0;
  double relaxation = 0;
  double cognitiveLoad = 0;

  double deviation = 0;

  String risk = "Normal";
  String sessionContext = "Study"; // renamed from "context" to avoid shadowing BuildContext context

  bool monitoring = false;

  Timer? sessionTimer;
  int elapsedSeconds = 0;

  void startMonitoring() {
    if (monitoring) return;

    monitoring = true;

    attentionHistory.clear();
    stressHistory.clear();
    fatigueHistory.clear();
    signalHistory.clear();

    engagementHistory.clear();
    relaxationHistory.clear();
    cognitiveLoadHistory.clear();

    alphaHistory.clear();
    betaHistory.clear();
    thetaHistory.clear();

    startSessionTimer();

    _webSocketService.connect(
      onData: (data) {
        if (!mounted) return;

        setState(() {
          attention =
              ((data["attention_prediction"] ?? 0) * 100).toDouble();

          stress =
              ((data["stress_prediction"] ?? 0) * 100).toDouble();

          fatigue =
              ((data["fatigue_prediction"] ?? 0) * 100).toDouble();

          signal =
              ((data["signal_quality"] ?? 0) * 100).toDouble();

          attentionHistory.add(attention);
          stressHistory.add(stress);
          fatigueHistory.add(fatigue);
          signalHistory.add(signal);

          delta = (data["delta_de"] ?? 0).toDouble();
          theta = (data["theta_de"] ?? 0).toDouble();
          alpha = (data["alpha_de"] ?? 0).toDouble();
          beta = (data["beta_de"] ?? 0).toDouble();
          gamma = (data["gamma_de"] ?? 0).toDouble();

          alphaHistory.add(alpha);
          betaHistory.add(beta);
          thetaHistory.add(theta);

          engagement = (data["engagement_index"] ?? 0).toDouble();
          relaxation = (data["relaxation_index"] ?? 0).toDouble();
          cognitiveLoad = (data["cognitive_load"] ?? 0).toDouble();

          engagementHistory.add(engagement);
          relaxationHistory.add(relaxation);
          cognitiveLoadHistory.add(cognitiveLoad);

          deviation = (data["deviation_score"] ?? 0).toDouble();

          risk = data["risk_tier"] ?? "Normal";
        });
      },
      onError: (error) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Connection Error: $error"),
            backgroundColor: Colors.red,
          ),
        );

        setState(() {
          monitoring = false;
        });

        stopSessionTimer();
      },
    );

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text("Monitoring Started"),
      ),
    );
  }

  void stopMonitoring() {
    if (!monitoring) return;

    avgAttention = calculateAverage(attentionHistory);
    avgStress = calculateAverage(stressHistory);
    avgFatigue = calculateAverage(fatigueHistory);
    avgSignal = calculateAverage(signalHistory);

    avgEngagement = calculateAverage(engagementHistory);
    avgRelaxation = calculateAverage(relaxationHistory);
    avgCognitiveLoad = calculateAverage(cognitiveLoadHistory);

    avgAlpha = calculateAverage(alphaHistory);
    avgBeta = calculateAverage(betaHistory);
    avgTheta = calculateAverage(thetaHistory);

    debugPrint("===== SESSION SUMMARY =====");
    debugPrint("Attention: $avgAttention");
    debugPrint("Stress: $avgStress");
    debugPrint("Fatigue: $avgFatigue");
    debugPrint("Signal: $avgSignal");
    debugPrint("Engagement: $avgEngagement");
    debugPrint("Relaxation: $avgRelaxation");
    debugPrint("Cognitive Load: $avgCognitiveLoad");
    debugPrint("Alpha: $avgAlpha");
    debugPrint("Beta: $avgBeta");
    debugPrint("Theta: $avgTheta");

    _webSocketService.disconnect();
    stopSessionTimer();

    setState(() {
      monitoring = false;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text("Monitoring Stopped"),
      ),
    );

    showSaveDialog();
  }

  void showSaveDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text("Session Finished"),
          content: const Text("Do you want to save this EEG session?"),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(dialogContext).pop();
                discardSession();
              },
              child: const Text("Discard"),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.of(dialogContext).pop();
                saveSession();
              },
              child: const Text("Save"),
            ),
          ],
        );
      },
    );
  }

  void discardSession() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text("Session discarded"),
      ),
    );
  }

 Future<void> saveSession() async {
  bool success = await _apiService.saveSession(
    userId: "vandana",
    alpha: avgAlpha,
    beta: avgBeta,
    theta: avgTheta,
    deviationScore: deviation,
    riskTier: risk,
    stressPrediction: avgStress,
    attentionPrediction: avgAttention,
    fatiguePrediction: avgFatigue,
  );

  if (!mounted) return;

  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text(
        success ? "Session Saved Successfully!" : "Failed to Save Session",
      ),
      backgroundColor: success ? Colors.green : Colors.red,
    ),
  );
}

  void startSessionTimer() {
    elapsedSeconds = 0;

    sessionTimer?.cancel();

    sessionTimer = Timer.periodic(
      const Duration(seconds: 1),
      (timer) {
        if (!mounted) return;

        setState(() {
          elapsedSeconds++;
        });
      },
    );
  }

  void stopSessionTimer() {
    sessionTimer?.cancel();
  }

  double calculateAverage(List<double> values) {
    if (values.isEmpty) return 0;

    double sum = 0;

    for (double value in values) {
      sum += value;
    }

    return sum / values.length;
  }

  String formatDuration(int totalSeconds) {
    final minutes = (totalSeconds ~/ 60).toString().padLeft(2, '0');
    final seconds = (totalSeconds % 60).toString().padLeft(2, '0');
    return "$minutes:$seconds";
  }

  @override
  void dispose() {
    sessionTimer?.cancel();
    _webSocketService.disconnect();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("EEG Dashboard"),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Card(
                color: Colors.green.shade100,
                child: ListTile(
                  leading: Icon(
                    monitoring
                        ? Icons.check_circle
                        : Icons.cancel,
                    color:
                        monitoring ? Colors.green : Colors.red,
                  ),
                  title: Text(
                    monitoring
                        ? "Device Connected"
                        : "Disconnected",
                  ),
                  subtitle: Text(
                    monitoring
                        ? "Receiving Live EEG Data"
                        : "Press Start Monitoring",
                  ),
                ),
              ),

              const SizedBox(height: 20),

              const Text(
                "Session Duration",
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 8),

              Text(
                formatDuration(elapsedSeconds),
                style: const TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 20),

              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisSpacing: 15,
                mainAxisSpacing: 15,
                childAspectRatio: 0.9,
                children: [
                  MetricCard(
                    title: "Attention",
                    value: "${attention.toStringAsFixed(1)}%",
                    icon: Icons.psychology,
                    color: Colors.blue,
                  ),

                  MetricCard(
                    title: "Fatigue",
                    value: "${fatigue.toStringAsFixed(1)}%",
                    icon: Icons.self_improvement,
                    color: Colors.green,
                  ),

                  MetricCard(
                    title: "Stress",
                    value: "${stress.toStringAsFixed(1)}%",
                    icon: Icons.favorite,
                    color: Colors.red,
                  ),

                  MetricCard(
                    title: "Signal",
                    value: "${signal.toStringAsFixed(1)}%",
                    icon: Icons.graphic_eq,
                    color: Colors.orange,
                  ),
                ],
              ),

              const SizedBox(height: 20),

              const Text(
                "Band Powers",
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 15),

              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisSpacing: 10,
                mainAxisSpacing: 10,
                childAspectRatio: 0.9,
                children: [
                  MetricCard(
                    title: "Delta",
                    value: delta.toStringAsFixed(2),
                    icon: Icons.waves,
                    color: Colors.deepPurple,
                  ),

                  MetricCard(
                    title: "Theta",
                    value: theta.toStringAsFixed(2),
                    icon: Icons.blur_on,
                    color: Colors.indigo,
                  ),

                  MetricCard(
                    title: "Alpha",
                    value: alpha.toStringAsFixed(2),
                    icon: Icons.auto_graph,
                    color: Colors.blue,
                  ),

                  MetricCard(
                    title: "Beta",
                    value: beta.toStringAsFixed(2),
                    icon: Icons.show_chart,
                    color: Colors.orange,
                  ),

                  MetricCard(
                    title: "Gamma",
                    value: gamma.toStringAsFixed(2),
                    icon: Icons.bolt,
                    color: Colors.red,
                  ),
                ],
              ),

              const SizedBox(height: 20),

              const Text(
                "Brain Indices",
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 15),

              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisSpacing: 10,
                mainAxisSpacing: 10,
                childAspectRatio: 0.9,
                children: [
                  MetricCard(
                    title: "Engagement",
                    value: engagement.toStringAsFixed(2),
                    icon: Icons.psychology_alt,
                    color: Colors.teal,
                  ),

                  MetricCard(
                    title: "Relaxation",
                    value: relaxation.toStringAsFixed(2),
                    icon: Icons.spa,
                    color: Colors.green,
                  ),

                  MetricCard(
                    title: "Cognitive Load",
                    value: cognitiveLoad.toStringAsFixed(2),
                    icon: Icons.memory,
                    color: Colors.deepOrange,
                  ),
                ],
              ),

              const SizedBox(height: 20),

              const Text(
                "Session Status",
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 15),

              Card(
                elevation: 4,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [

                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            "Deviation Score",
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            deviation.toStringAsFixed(2),
                            style: const TextStyle(
                              fontSize: 18,
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(height: 20),

                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            "Risk Tier",
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                            ),
                          ),

                          Chip(
                            label: Text(risk),
                            backgroundColor:
                                risk == "High"
                                    ? Colors.red.shade200
                                    : risk == "Moderate"
                                        ? Colors.orange.shade200
                                        : risk == "Mild"
                                            ? Colors.yellow.shade200
                                            : Colors.green.shade200,
                          ),
                        ],
                      ),

                      const SizedBox(height: 20),

                      const Text(
                        "Signal Quality",
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                        ),
                      ),

                      const SizedBox(height: 8),

                      LinearProgressIndicator(
                        value: signal / 100,
                        minHeight: 10,
                      ),

                      const SizedBox(height: 8),

                      Text("${signal.toStringAsFixed(1)} %"),

                      const SizedBox(height: 20),

                      DropdownButtonFormField<String>(
                        value: sessionContext,
                        decoration: const InputDecoration(
                          labelText: "Current Context",
                          border: OutlineInputBorder(),
                        ),
                        items: const [
                          DropdownMenuItem(
                            value: "Study",
                            child: Text("Study"),
                          ),
                          DropdownMenuItem(
                            value: "Work",
                            child: Text("Work"),
                          ),
                          DropdownMenuItem(
                            value: "Rest",
                            child: Text("Rest"),
                          ),
                          DropdownMenuItem(
                            value: "Meeting",
                            child: Text("Meeting"),
                          ),
                        ],
                        onChanged: (value) {
                          setState(() {
                            sessionContext = value!;
                          });
                        },
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 20),

              Column(
                children: [

                  SizedBox(
                    width: double.infinity,
                    child: monitoring
                        ? ElevatedButton.icon(
                            onPressed: stopMonitoring,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.red,
                              foregroundColor: Colors.white,
                            ),
                            icon: const Icon(Icons.stop),
                            label: const Text("Stop Monitoring"),
                          )
                        : ElevatedButton.icon(
                            onPressed: startMonitoring,
                            icon: const Icon(Icons.play_arrow),
                            label: const Text("Start Monitoring"),
                          ),
                  ),

                  const SizedBox(height: 15),

                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => const HistoryScreen(),
                          ),
                        );
                      },
                      icon: const Icon(Icons.history),
                      label: const Text("Session History"),
                    ),
                  ),

                ],
              ),

              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}