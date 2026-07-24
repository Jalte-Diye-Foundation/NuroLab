import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketService {
  WebSocketChannel? _channel;

  /// Connect to FastAPI WebSocket
  void connect({
    required Function(Map<String, dynamic>) onData,
    required Function(dynamic) onError,
  }) {
    _channel = WebSocketChannel.connect(
      Uri.parse("ws://10.0.2.2:8000/ws/live"),
    );

    _channel!.stream.listen(
      (message) {
        try {
          final data = jsonDecode(message);
          print(data);
onData(data);
        } catch (e) {
          onError(e);
        }
      },
      onError: onError,
      onDone: () {
        print("WebSocket Closed");
      },
    );
  }

  /// Close connection
  void disconnect() {
    _channel?.sink.close();
  }
}