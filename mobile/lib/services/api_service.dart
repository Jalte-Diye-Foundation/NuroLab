import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:path_provider/path_provider.dart';
import 'package:open_filex/open_filex.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/session_history.dart';

class ApiService {
  static const String baseUrl = "http://10.0.2.2:8000";

  Future<bool> checkHealth() async {
    try {
      final response = await http.get(
        Uri.parse("$baseUrl/health"),
      );

      return response.statusCode == 200;
    } catch (e) {
      debugPrint("Health Check Failed: $e");
      return false;
    }
  }

  Future<bool> saveSession({
    required String userId,
    required double alpha,
    required double beta,
    required double theta,
    required double deviationScore,
    required String riskTier,
    required double stressPrediction,
    required double attentionPrediction,
    required double fatiguePrediction,
  }) async {
    try {
      final response = await http
          .post(
            Uri.parse("$baseUrl/session/save"),
            headers: {
              "Content-Type": "application/json",
            },
            body: jsonEncode({
              "user_id": userId,
              "alpha": alpha,
              "beta": beta,
              "theta": theta,
              "deviation_score": deviationScore,
              "risk_tier": riskTier.toLowerCase(),
              "stress_prediction": stressPrediction,
              "attention_prediction": attentionPrediction,
              "fatigue_prediction": fatiguePrediction,
            }),
          )
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200 || response.statusCode == 201) {
        return true;
      }

      // Non-success status: log the body so you can see the backend's
      // actual error message (e.g. a validation error) instead of just "false".
      debugPrint(
        "saveSession failed: ${response.statusCode} ${response.body}",
      );
      return false;
    } on SocketException {
      debugPrint("saveSession failed: no internet connection or server unreachable");
      return false;
    } on HttpException {
      debugPrint("saveSession failed: could not reach server");
      return false;
    } on FormatException {
      debugPrint("saveSession failed: bad response format from server");
      return false;
    } catch (e) {
      debugPrint("saveSession failed: $e");
      return false;
    }
  }

  Future<List<SessionHistory>> getSessionHistory(String userId) async {
    try {
      final response = await http
          .get(
            Uri.parse("$baseUrl/session/history/$userId"),
          )
          .timeout(const Duration(seconds: 10));
           debugPrint("History Status: ${response.statusCode}");
    debugPrint("History Body: ${response.body}");

      if (response.statusCode == 200) {
        final List data = jsonDecode(response.body);

        return data
            .map((item) => SessionHistory.fromJson(item))
            .toList();
      }

      debugPrint(
        "getSessionHistory failed: ${response.statusCode} ${response.body}",
      );
      return [];
    } on SocketException {
      debugPrint("History Error: no internet connection or server unreachable");
      return [];
    } on HttpException {
      debugPrint("History Error: could not reach server");
      return [];
    } on FormatException {
      debugPrint("History Error: bad response format from server");
      return [];
    } catch (e) {
      debugPrint("History Error: $e");
      return [];
    }
  }
  Future<void> downloadPdfReport(Map<String, dynamic> sessionData) async {
  try {
    final response = await http.post(
      Uri.parse("$baseUrl/report/generate"),
      headers: {
        "Content-Type": "application/json",
      },
      body: jsonEncode(sessionData),
    );

    if (response.statusCode == 200) {
      final Uint8List pdfBytes = response.bodyBytes;

      final directory = await getApplicationDocumentsDirectory();
      final file = File("${directory.path}/nurolab_report.pdf");

      await file.writeAsBytes(pdfBytes);

      debugPrint("PDF saved at: ${file.path}");

      final result = await OpenFilex.open(file.path);
debugPrint("OpenFile Result: ${result.type}");
debugPrint("Saved Path: ${file.path}");
    } else {
      debugPrint(
        "PDF generation failed: ${response.statusCode} ${response.body}",
      );
    }
  } catch (e) {
    debugPrint("Download PDF Error: $e");
  }
}
}