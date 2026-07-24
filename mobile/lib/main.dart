import 'package:flutter/material.dart';
import 'screens/welcome_screen.dart';

void main() {
  runApp(const EEGApp());
}

class EEGApp extends StatelessWidget {
  const EEGApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'EEG Brain Monitoring',
      theme: ThemeData(
        colorSchemeSeed: Colors.indigo,
        useMaterial3: true,
      ),
      home: const WelcomeScreen(),
    );
  }
}